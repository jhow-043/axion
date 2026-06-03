from __future__ import annotations

from uuid import UUID


class NotificationService:
    """Stub for P14. P09 calls notify() on each ticket action.
    P14 will replace this stub with real notification dispatch."""

    async def notify(
        self,
        *,
        event_type: str,
        ticket_id: UUID,
        actor_id: UUID | None,
        payload: dict | None = None,
    ) -> None:
        pass
