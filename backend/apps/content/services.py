import hashlib
from django.core.files.base import ContentFile

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def make_dummy_zip_bytes(name: str) -> bytes:
    # placeholder: later replace with real zip builder
    return f"PACK:{name}".encode("utf-8")

def attach_pack_file(pack, filename: str, blob: bytes):
    pack.file.save(filename, ContentFile(blob), save=False)
    pack.size = len(blob)
    pack.checksum = sha256_bytes(blob)
