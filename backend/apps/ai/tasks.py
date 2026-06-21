from __future__ import annotations

from celery import shared_task

from .models import AIDocument
from .services import process_document


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def process_ai_document_task(self, document_id: int) -> int:
    document = AIDocument.objects.get(id=document_id)
    process_document(document)
    return document.id
