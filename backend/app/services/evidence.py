from __future__ import annotations

from app.models.segment import ReviewSegment


def validate_evidence_spans(
    candidate_quotes: list[str],
    segments: list[ReviewSegment],
) -> list[dict]:
    spans: list[dict] = []
    for quote in candidate_quotes:
        if not quote:
            continue
        for segment in segments:
            if quote in segment.text:
                spans.append(
                    {
                        "segment_id": segment.id,
                        "quote": quote,
                        "page_start": segment.page_start,
                        "page_end": segment.page_end,
                    }
                )
                break
    return spans
