from __future__ import annotations

from logging import Logger

from ..config import SourceConfig
from ..models import DetectionResult, Ticket
from ..repository.sqlite_repository import SQLiteRepository


class TicketDetector:
    def __init__(self, repository: SQLiteRepository, logger: Logger) -> None:
        self.repository = repository
        self.logger = logger

    def process(self, source: SourceConfig, tickets: list[Ticket], collected_at: str) -> DetectionResult:
        if not self.repository.is_baseline_initialized(source.id):
            self.repository.upsert_seen_tickets(source.id, tickets, collected_at)
            self.repository.mark_baseline_initialized(source.id, collected_at)
            self.logger.info(
                "Fonte '%s': baseline inicial criado com %s chamado(s).",
                source.id,
                len(tickets),
            )
            return DetectionResult(
                source_id=source.id,
                source_name=source.name,
                is_baseline=True,
                total_tickets=len(tickets),
                new_tickets=[],
            )

        known_numbers = self.repository.get_known_numbers(source.id, (ticket.number for ticket in tickets))
        new_tickets = [ticket for ticket in tickets if ticket.number not in known_numbers]

        self.repository.upsert_seen_tickets(source.id, tickets, collected_at)
        return DetectionResult(
            source_id=source.id,
            source_name=source.name,
            is_baseline=False,
            total_tickets=len(tickets),
            new_tickets=new_tickets,
        )
