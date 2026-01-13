from __future__ import annotations

import hashlib
import re


HEADING_PATTERNS = [
    re.compile(r"^\s*(\d+\.)\s+([A-Z][^\n]+)"),
    re.compile(r"^\s*(\d+\.\d+)\s+([A-Z][^\n]+)"),
    re.compile(r"^\s*\(([a-z])\)\s+([^\n]+)"),
    re.compile(r"^\s*([A-Z][A-Z\s]{3,})$"),
]


def _hash_text(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def _find_page(text: str, pages: list[dict] | None) -> tuple[int | None, int | None]:
    if not pages:
        return None, None
    snippet = text.strip()[:40]
    if not snippet:
        return None, None
    for page in pages:
        page_text = page.get("text") or ""
        if snippet in page_text:
            page_num = page.get("page_num")
            return page_num, page_num
    return None, None


def _match_heading(line: str) -> tuple[str | None, str | None]:
    for index, pattern in enumerate(HEADING_PATTERNS):
        match = pattern.match(line)
        if not match:
            continue
        if index == 3:
            heading = match.group(1).strip()
            return heading, None
        section_number = match.group(1).strip()
        heading = match.group(2).strip()
        return heading, section_number
    return None, None


def segment_document(text: str, pages: list[dict] | None = None) -> list[dict]:
    segments: list[dict] = []
    current_lines: list[str] = []
    current_heading: str | None = None
    current_section: str | None = None

    def flush_segment() -> None:
        nonlocal current_lines, current_heading, current_section
        if not current_lines:
            return
        segment_text = "\n".join(current_lines).strip()
        if not segment_text:
            current_lines = []
            return
        page_start, page_end = _find_page(segment_text, pages)
        segments.append(
            {
                "segment_index": len(segments),
                "heading": current_heading,
                "section_number": current_section,
                "text": segment_text,
                "hash": _hash_text(segment_text),
                "page_start": page_start,
                "page_end": page_end,
            }
        )
        current_lines = []

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        heading, section_number = _match_heading(line)
        if heading is not None or section_number is not None:
            flush_segment()
            current_heading = heading
            current_section = section_number
        current_lines.append(line)

    flush_segment()
    return segments
