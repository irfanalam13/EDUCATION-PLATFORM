from celery import shared_task
from django.utils import timezone
from .models import DownloadablePack
from .services import make_dummy_zip_bytes, attach_pack_file

@shared_task
def generate_pack_task(pack_id: int):
    pack = DownloadablePack.objects.get(pk=pack_id)
    try:
        pack.status = DownloadablePack.Status.PENDING
        pack.save(update_fields=["status"])

        name = f"topic_{pack.topic_id}" if pack.topic_id else f"chapter_{pack.chapter_id}"
        blob = make_dummy_zip_bytes(name)

        filename = f"{name}_v{pack.version}_{timezone.now():%Y%m%d}.zip"
        attach_pack_file(pack, filename, blob)

        pack.status = DownloadablePack.Status.READY
        pack.save()
    except Exception:
        pack.status = DownloadablePack.Status.FAILED
        pack.save(update_fields=["status"])
        raise
