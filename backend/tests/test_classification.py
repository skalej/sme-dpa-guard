from app.models.clause_type import ClauseType
from app.services.classification import classify_segment_rules


def test_rules_classification_security() -> None:
    text = "We apply technical and organizational measures including encryption."
    results = classify_segment_rules(text)

    types = [result["clause_type"] for result in results]
    assert ClauseType.SECURITY_TOMS in types


def test_rules_confidence_cap() -> None:
    text = "technical and organizational measures encryption security measures"
    results = classify_segment_rules(text)

    for result in results:
        assert result["confidence"] <= 0.9


def test_top_k_sorted() -> None:
    text = "controller processor confidentiality audit inspection"
    results = classify_segment_rules(text)

    confidences = [result["confidence"] for result in results]
    assert confidences == sorted(confidences, reverse=True)
