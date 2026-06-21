import json
import logging
import urllib.request

from celery import shared_task
from django.utils import timezone

from .models import ScheduledNotification, ScheduledStatus, Device
from .services import create_notification

logger = logging.getLogger(__name__)

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


def _get_device_tokens_for_user(user_id: int) -> list[str]:
    """Active Expo push tokens registered for this user."""
    return list(
        Device.objects.filter(user_id=user_id, is_active=True)
        .exclude(token__isnull=True)
        .exclude(token__exact="")
        .values_list("token", flat=True)
    )


def _send_push(tokens: list[str], payload: dict) -> None:
    """Send a push via the Expo Push API.

    Expo accepts a batch of messages as a JSON array. Errors are logged, never
    raised, so notification creation is never blocked by push delivery.
    """
    if not tokens:
        return
    messages = [
        {
            "to": token,
            "title": payload.get("title", ""),
            "body": payload.get("body", ""),
            "data": payload.get("data", {}),
            "sound": "default",
        }
        for token in tokens
    ]
    try:
        req = urllib.request.Request(
            EXPO_PUSH_URL,
            data=json.dumps(messages).encode("utf-8"),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310 (fixed host)
            resp.read()
    except Exception:  # pragma: no cover - network
        logger.exception("Expo push send failed for %d token(s)", len(tokens))


@shared_task
def send_push_to_user(user_id: int, title: str, body: str = "", data: dict | None = None) -> dict:
    tokens = _get_device_tokens_for_user(user_id)
    _send_push(tokens, {"title": title, "body": body, "data": data or {}})
    return {"user_id": user_id, "tokens": len(tokens)}


@shared_task
def send_scheduled_notifications():
    now = timezone.now()
    pending = (
        ScheduledNotification.objects
        .select_related("user")
        .filter(status=ScheduledStatus.PENDING, send_at__lte=now)
        .order_by("send_at")[:500]
    )

    for s in pending:
        try:
            n = create_notification(
                user=s.user,
                title=s.title,
                body=s.body,
                type=s.type,
                data=s.data,
            )

            # optional push
            tokens = _get_device_tokens_for_user(s.user_id)
            _send_push(tokens, {
                "title": n.title,
                "body": n.body,
                "type": n.type,
                "data": n.data,
            })

            s.status = ScheduledStatus.SENT
            s.last_error = ""
            s.save(update_fields=["status", "last_error"])
        except Exception as e:
            s.status = ScheduledStatus.FAILED
            s.last_error = str(e)[:2000]
            s.save(update_fields=["status", "last_error"])
