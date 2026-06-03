from __future__ import annotations

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "manutencao",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.modules.sla.tasks"],
)

celery_app.conf.update(
    timezone="UTC",
    enable_utc=True,
    # P12: both sweeps run every 5 minutes (spec requirement)
    beat_schedule={
        "sla-breach-sweep": {
            "task": "app.modules.sla.tasks.breach_sweep",
            "schedule": 300.0,
        },
        "sla-alert-sweep": {
            "task": "app.modules.sla.tasks.alert_sweep",
            "schedule": 300.0,
        },
    },
)
