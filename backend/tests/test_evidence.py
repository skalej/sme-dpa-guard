from dataclasses import dataclass

from app.services.evidence import validate_evidence_spans


@dataclass
class StubSegment:
    id: int
    text: str
    page_start: int
    page_end: int


def _segment(segment_id: int, text: str, page_start: int, page_end: int) -> StubSegment:
    return StubSegment(
        id=segment_id, text=text, page_start=page_start, page_end=page_end
    )


def test_validate_evidence_spans_filters_missing() -> None:
    seg1 = _segment(1, "This contract includes encryption requirements.", 1, 1)
    seg2 = _segment(2, "No mention of audits here.", 2, 2)

    spans = validate_evidence_spans(
        ["encryption requirements", "missing quote"],
        [seg1, seg2],
    )

    assert len(spans) == 1
    assert spans[0]["segment_id"] == 1
    assert spans[0]["quote"] == "encryption requirements"
