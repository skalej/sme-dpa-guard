from __future__ import annotations

from io import BytesIO

from fastapi import HTTPException
from pypdf import PdfReader
from docx import Document

from app.config import get_settings

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def validate_file(content: bytes, mime_type: str) -> None:
    settings = get_settings()
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail="File too large")
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported document type")


def extract_text_from_pdf(content: bytes) -> dict:
    settings = get_settings()
    reader = PdfReader(BytesIO(content))

    pages = []
    texts = []
    for index, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        pages.append({"page_num": index + 1, "text": text})
        texts.append(text)

    raw_text = "\n".join(texts)
    content_len = len(content)
    text_density = len(raw_text.strip()) / content_len if content_len > 0 else 0.0
    is_scanned = text_density < settings.text_density_threshold
    if is_scanned:
        raise HTTPException(
            status_code=400,
            detail="Scanned PDFs are not supported. Please upload a text-based PDF.",
        )

    return {
        "raw_text": raw_text,
        "pages": pages,
        "page_count": len(pages),
        "is_scanned": is_scanned,
        "text_density": text_density,
    }


def extract_text_from_docx(content: bytes) -> dict:
    document = Document(BytesIO(content))
    paragraphs = []
    texts = []
    for paragraph in document.paragraphs:
        text = paragraph.text or ""
        paragraphs.append({"text": text, "style": paragraph.style.name})
        texts.append(text)

    raw_text = "\n".join(texts)
    return {
        "raw_text": raw_text,
        "paragraphs": paragraphs,
        "paragraph_count": len(paragraphs),
        "is_scanned": False,
        "text_density": 1.0,
    }


def extract_document(content: bytes, mime_type: str) -> dict:
    validate_file(content, mime_type)
    if mime_type == "application/pdf":
        return extract_text_from_pdf(content)
    return extract_text_from_docx(content)
