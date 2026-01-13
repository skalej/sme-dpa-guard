from io import BytesIO

import pytest
from fastapi import HTTPException
from docx import Document

from app.config import get_settings
from app.services import extraction


def test_pdf_scanned_detection(monkeypatch) -> None:
    class FakePage:
        def extract_text(self) -> str:
            return ""

    class FakeReader:
        def __init__(self, *_args, **_kwargs) -> None:
            self.pages = [FakePage()]

    monkeypatch.setattr(extraction, "PdfReader", FakeReader)
    monkeypatch.setenv("TEXT_DENSITY_THRESHOLD", "0.9")
    get_settings.cache_clear()

    with pytest.raises(HTTPException) as exc_info:
        extraction.extract_text_from_pdf(b"%PDF-1.4 test")

    assert exc_info.value.status_code == 400
    assert "Scanned PDFs" in exc_info.value.detail



def test_docx_extraction_returns_text(monkeypatch) -> None:
    monkeypatch.setenv("MAX_FILE_SIZE_MB", "25")
    get_settings.cache_clear()

    document = Document()
    document.add_paragraph("Hello DPA Guard")
    buffer = BytesIO()
    document.save(buffer)

    result = extraction.extract_document(
        buffer.getvalue(),
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    assert "Hello DPA Guard" in result["raw_text"]
    assert result["paragraph_count"] == 1
