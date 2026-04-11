from __future__ import annotations

import unicodedata
from logging import Logger

from ..config import RecipientConfig, RoutingRuleConfig, Settings, SourceConfig
from ..models import DeliveryRequest, LoadEntry, Ticket
from ..repository.sqlite_repository import SQLiteRepository


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value or "")
    normalized = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    return normalized.strip().lower()


class NotificationRouter:
    def __init__(self, settings: Settings, repository: SQLiteRepository, logger: Logger) -> None:
        self.settings = settings
        self.repository = repository
        self.logger = logger

    def build_deliveries(
        self,
        source: SourceConfig,
        new_tickets: list[Ticket],
        load_entries: list[LoadEntry],
    ) -> list[DeliveryRequest]:
        deliveries: list[DeliveryRequest] = []

        for ticket in new_tickets:
            for rule in self.settings.rules:
                if not rule.enabled or source.id not in rule.source_ids:
                    continue
                if not self._matches_rule(rule, ticket):
                    continue

                for recipient_id in rule.recipient_ids:
                    recipient = self.settings.get_recipient(recipient_id)
                    if not recipient.enabled:
                        continue
                    if not recipient.webhook_url:
                        self.logger.warning(
                            "Destinatario '%s' esta sem webhook configurado. Regra '%s' ignorada.",
                            recipient.id,
                            rule.id,
                        )
                        continue
                    if self.repository.has_delivery(source.id, rule.id, recipient.id, ticket.number):
                        continue

                    deliveries.append(
                        DeliveryRequest(
                            source_id=source.id,
                            source_name=source.name,
                            rule_id=rule.id,
                            title_prefix=rule.title_prefix,
                            recipient_id=recipient.id,
                            recipient_name=recipient.name,
                            recipient_role=recipient.role,
                            webhook_url=recipient.webhook_url,
                            ticket=ticket,
                            load_entries=load_entries if rule.include_load else [],
                        )
                    )

        return deliveries

    def _matches_rule(self, rule: RoutingRuleConfig, ticket: Ticket) -> bool:
        if rule.ticket_types and _normalize(ticket.ticket_type) not in rule.ticket_types:
            return False
        if rule.priorities and _normalize(ticket.priority) not in rule.priorities:
            return False
        return True

