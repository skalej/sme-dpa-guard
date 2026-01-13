from app.services.segmentation import segment_document


def test_segment_document_headings() -> None:
    text = """
1. Definitions
This section defines terms.
7. Security Measures
Details about security.
(a) Access Controls
Controls must be enforced.
CONFIDENTIALITY
All parties must comply.
""".strip()

    segments = segment_document(text)

    headings = [segment["heading"] for segment in segments]
    sections = [segment["section_number"] for segment in segments]

    assert "Definitions" in headings
    assert "Security Measures" in headings
    assert "Access Controls" in headings
    assert "CONFIDENTIALITY" in headings

    assert "1." in sections
    assert "7." in sections
    assert "a" in sections

    for segment in segments:
        assert segment["text"]
        if segment["heading"]:
            assert segment["heading"] in segment["text"]



def test_segment_hashes_stable() -> None:
    text = "1. Definitions\nAlpha\n"
    first = segment_document(text)
    second = segment_document(text)

    assert first
    assert [seg["hash"] for seg in first] == [seg["hash"] for seg in second]
