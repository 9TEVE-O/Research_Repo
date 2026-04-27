"""Append-only audit log for all knowledge graph mutations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AuditEvent:
    """A single recorded mutation event."""

    event_type: str
    target_id: str
    payload: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "event_type": self.event_type,
            "target_id": self.target_id,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
        }


class AuditLog:
    """Append-only record of knowledge graph mutations."""

    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    def record(self, event: AuditEvent) -> None:
        self._events.append(event)

    def all_events(self) -> list[AuditEvent]:
        return list(self._events)

    def events_by_type(self, event_type: str) -> list[AuditEvent]:
        return [e for e in self._events if e.event_type == event_type]

    def events_for(self, target_id: str) -> list[AuditEvent]:
        return [e for e in self._events if e.target_id == target_id]

    def to_dict(self) -> dict:
        return {
            "event_count": len(self._events),
            "events": [e.to_dict() for e in self._events],
        }
