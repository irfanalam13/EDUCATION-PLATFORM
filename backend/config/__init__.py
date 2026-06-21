# config package
# Ensure the Celery app is loaded when Django starts so that shared_task
# decorators bind to it and @app.task autodiscovery works.
from .celery import app as celery_app

__all__ = ("celery_app",)
