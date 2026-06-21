"""Celery application for the edu-platform backend.

Importing ``config.celery.app`` (re-exported from ``config/__init__.py`` as
``celery_app``) is what binds every ``@shared_task`` to a real app and enables
autodiscovery. When ``CELERY_TASK_ALWAYS_EAGER`` is true (dev), ``.delay()``
runs the task inline in-process, so the learning loop works without a broker.
"""
from __future__ import annotations

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("edu")

# Read all CELERY_* settings from Django settings.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Discover each app's tasks.py.
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):  # pragma: no cover - diagnostic helper
    print(f"Request: {self.request!r}")
