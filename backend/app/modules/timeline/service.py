from __future__ import annotations

from uuid import UUID


class TimelineService:
    """Stub for P10. P09 calls record_event() on each ticket action.
    P10 will replace this stub with real persistence to ticket_events table."""

    async def record_event(
        self,
        *,
        event_type: str,
        ticket_id: UUID,
        actor_id: UUID,
        payload: dict | None = None,
    ) -> None:
        pass
