from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class Ticket:
    number: str
    title: str = ""
    customer_ticket_number: str = ""
    activity: str = ""
    company: str = ""
    ticket_type: str = ""
    priority: str = ""
    ticket_status: str = ""
    activity_status: str = ""
    available_estimate: str = ""
    start_date: str = ""
    end_date: str = ""
    due_date: str = ""
    time_to_expire: str = ""
    consultant: str = ""
    source_view: str = "Minha Fila"
    collected_at: str = field(default_factory=utc_now_iso)
    raw_fields: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "number": self.number,
            "title": self.title,
            "customer_ticket_number": self.customer_ticket_number,
            "activity": self.activity,
            "company": self.company,
            "ticket_type": self.ticket_type,
            "priority": self.priority,
            "ticket_status": self.ticket_status,
            "activity_status": self.activity_status,
            "available_estimate": self.available_estimate,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "due_date": self.due_date,
            "time_to_expire": self.time_to_expire,
            "consultant": self.consultant,
            "source_view": self.source_view,
            "collected_at": self.collected_at,
            "raw_fields": self.raw_fields,
        }

    def short_text(self) -> str:
        title = self.title or "Sem titulo"
        return f"{self.number} - {title}"


@dataclass(slots=True)
class DetectionResult:
    is_baseline: bool
    total_tickets: int
    new_tickets: list[Ticket]


@dataclass(slots=True)
class NotificationResult:
    success: bool
    status_code: int | None
    response_text: str
    payload: dict[str, Any]

