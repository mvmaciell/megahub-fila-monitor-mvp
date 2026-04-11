from __future__ import annotations

import argparse

from .browser import BrowserSession
from .collectors import build_collector
from .config import NotificationProfileConfig, Settings, SourceConfig
from .errors import ConfigurationError, MonitorError
from .logging_setup import configure_logging
from .notifiers import TeamsWorkflowNotifier
from .repository import SQLiteRepository
from .services import LoadAnalyzer, MonitorService, NotificationRouter, RunOnceService, TicketDetector


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Monitor multi-fonte do MegaHub.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    login_parser = subparsers.add_parser("login", help="Abre o navegador com perfil persistente para login manual.")
    login_parser.add_argument("--context", dest="context_id", help="Id do contexto configurado.")
    login_parser.add_argument("--source", dest="source_id", help="Id da fonte usada para validar o login.")

    notify_parser = subparsers.add_parser("notify-test", help="Envia um card de teste para os perfis configurados.")
    notify_parser.add_argument("--profile", dest="profile_id", help="Id de um perfil especifico.")
    notify_parser.add_argument(
        "--recipient",
        dest="profile_id_legacy",
        help=argparse.SUPPRESS,
    )

    snapshot_parser = subparsers.add_parser("snapshot", help="Captura a fonte e imprime um resumo.")
    snapshot_parser.add_argument("--source", dest="source_id", help="Id da fonte configurada.")

    subparsers.add_parser("run-once", help="Executa um ciclo unico. Comando recomendado para o agendador.")
    subparsers.add_parser("monitor", help="Mantem o monitor em loop continuo.")

    forget_parser = subparsers.add_parser(
        "forget-ticket",
        help="Remove um chamado da base local para forcar reprocessamento em demo.",
    )
    forget_parser.add_argument("ticket_number", help="Numero do chamado.")
    forget_parser.add_argument("--source", dest="source_id", help="Id da fonte. Se omitido, remove em todas.")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    settings = Settings.load()
    logger = configure_logging(settings.log_file_path)

    repository = SQLiteRepository(settings.database_path, logger)
    repository.initialize()

    detector = TicketDetector(repository, logger)
    load_analyzer = LoadAnalyzer()
    router = NotificationRouter(settings, repository, logger)
    notifier = TeamsWorkflowNotifier(settings, logger)
    run_once_service = RunOnceService(
        settings=settings,
        repository=repository,
        detector=detector,
        load_analyzer=load_analyzer,
        router=router,
        notifier=notifier,
        logger=logger,
    )
    monitor_service = MonitorService(settings, run_once_service, logger)

    try:
        if args.command == "login":
            source = _resolve_login_source(settings, args.source_id, args.context_id)
            collector = build_collector(settings, source, logger)
            browser_session = BrowserSession(settings, settings.get_context(source.context_id), logger)
            browser_session.interactive_login(source.url, collector.page_title)
            logger.info("Sessao persistida com sucesso para o contexto '%s'.", source.context_id)
            return 0

        if args.command == "notify-test":
            profile_id = args.profile_id or args.profile_id_legacy
            profiles = _resolve_profiles(settings, profile_id)
            for profile in profiles:
                result = notifier.send_test_message(profile.name, profile.role, profile.webhook_url)
                logger.info(
                    "Teste de notificacao concluido para o perfil '%s'. HTTP=%s",
                    profile.id,
                    result.status_code,
                )
            return 0

        if args.command == "snapshot":
            source = _resolve_source(settings, args.source_id)
            tickets = run_once_service.run_snapshot(source)
            logger.info("Resumo da captura da fonte '%s':", source.id)
            for ticket in tickets:
                logger.info(
                    "Chamado=%s | Tipo=%s | Prioridade=%s | Consultor=%s | Titulo=%s",
                    ticket.number,
                    ticket.ticket_type or "-",
                    ticket.priority or "-",
                    ticket.consultant or "-",
                    ticket.title or "-",
                )
            return 0

        if args.command == "run-once":
            return run_once_service.run()

        if args.command == "monitor":
            return monitor_service.run_forever()

        if args.command == "forget-ticket":
            deleted = repository.forget_ticket(args.ticket_number, args.source_id)
            if deleted:
                logger.info(
                    "Chamado %s removido da base local%s.",
                    args.ticket_number,
                    f" na fonte '{args.source_id}'" if args.source_id else "",
                )
            else:
                logger.warning("Chamado %s nao existia na base local.", args.ticket_number)
            return 0

        parser.print_help()
        return 1
    except (ConfigurationError, MonitorError) as exc:
        logger.error(str(exc))
        return 1


def _resolve_source(settings: Settings, source_id: str | None) -> SourceConfig:
    if source_id:
        return settings.get_source(source_id)

    enabled_sources = settings.enabled_sources()
    if not enabled_sources:
        raise ConfigurationError("Nenhuma fonte habilitada encontrada.")
    return enabled_sources[0]


def _resolve_login_source(settings: Settings, source_id: str | None, context_id: str | None) -> SourceConfig:
    if source_id:
        return settings.get_source(source_id)

    if context_id:
        for source in settings.sources.values():
            if source.context_id == context_id:
                return source
        raise ConfigurationError(f"Nenhuma fonte referencia o contexto '{context_id}'.")

    return _resolve_source(settings, None)


def _resolve_profiles(settings: Settings, profile_id: str | None) -> list[NotificationProfileConfig]:
    if profile_id:
        profile = settings.get_profile(profile_id)
        if not profile.webhook_url:
            raise ConfigurationError(f"Perfil '{profile_id}' esta sem webhook configurado.")
        return [profile]

    profiles = [
        profile
        for profile in settings.profiles.values()
        if profile.enabled and profile.webhook_url
    ]
    if not profiles:
        raise ConfigurationError("Nenhum perfil habilitado com webhook configurado.")
    return profiles
