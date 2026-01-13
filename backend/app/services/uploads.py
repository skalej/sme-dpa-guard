from __future__ import annotations

import hashlib
import os
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.domain.status_flow import assert_transition
from app.models.review import Review, ReviewStatus
from app.storage.base import StorageClient
from app.storage.minio import get_storage_client

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


class UnsupportedFileType(ValueError):
    pass


def _sanitize_filename(filename: str) -> str:
    if not filename:
        return "file"
    base = os.path.basename(filename)
    sanitized = "".join(ch if ch.isalnum() or ch in ".-_" else "_" for ch in base)
    return sanitized or "file"


def upload_review_document(
    db: Session,
    review: Review,
    content_type: str,
    filename: str,
    data: bytes,
    storage_client: StorageClient | None = None,
) -> Review:
    if content_type not in ALLOWED_MIME_TYPES:
        raise UnsupportedFileType(f"Unsupported content type: {content_type}")

    assert_transition(review.status, ReviewStatus.UPLOADED)

    storage_client = storage_client or get_storage_client()
    size_bytes = len(data)
    sha256 = hashlib.sha256(data).hexdigest()
    safe_filename = _sanitize_filename(filename)
    storage_key = f"reviews/{review.id}/source/{uuid4()}_{safe_filename}"

    storage_client.put_bytes(storage_key, data, content_type)

    review.status = ReviewStatus.UPLOADED
    review.doc_filename = safe_filename
    review.doc_mime = content_type
    review.doc_size_bytes = size_bytes
    review.doc_sha256 = sha256
    review.doc_storage_key = storage_key

    db.add(review)
    db.commit()
    db.refresh(review)
    return review
