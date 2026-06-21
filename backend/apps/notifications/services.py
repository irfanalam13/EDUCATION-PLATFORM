from django.utils import timezone
from django.db import transaction

from .models import Notification


def create_notification(*, user, title, body="", type="SYSTEM", data=None, push=True) -> Notification:
    if data is None:
        data = {}
    notification = Notification.objects.create(
        user=user,
        title=title,
        body=body,
        type=type,
        data=data,
    )

    # Best-effort push after the surrounding transaction commits (so workers see
    # the row and we never block in-app notifications on push delivery).
    if push:
        user_id = user.id

        def _enqueue_push():
            try:
                from .tasks import send_push_to_user
                send_push_to_user.delay(user_id, title, body, data)
            except Exception:
                pass

        transaction.on_commit(_enqueue_push)

    return notification


@transaction.atomic
def mark_notifications_read(*, user, ids=None, mark_all=False) -> int:
    qs = Notification.objects.for_user(user).filter(is_read=False)

    if mark_all:
        updated = qs.update(is_read=True, read_at=timezone.now())
        return updated

    if not ids:
        return 0

    updated = qs.filter(id__in=ids).update(is_read=True, read_at=timezone.now())
    return updated
