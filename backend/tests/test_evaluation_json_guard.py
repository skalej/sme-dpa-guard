import json

from app.config import get_settings
from app.models.clause_type import ClauseType
from app.services import evaluation


def test_eval_parses_fenced_json(monkeypatch) -> None:
    monkeypatch.setenv("USE_LLM_EVAL", "true")
    get_settings.cache_clear()

    payload = {
        "risk_label": "GREEN",
        "short_reason": "Looks good.",
        "suggested_change": "No change.",
        "candidate_quotes": ["quote"],
        "triggered_rule_ids": ["RULE-1"],
    }
    monkeypatch.setattr(evaluation, "call_llm", lambda _prompt: f"```json\n{json.dumps(payload)}\n```")

    result = evaluation.evaluate_clause(
        ClauseType.GOVERNING_LAW,
        ["segment"],
        {},
        [],
    )

    assert result["risk_label"] == "GREEN"
    assert result["candidate_quotes"] == ["quote"]


def test_eval_invalid_json_fallback(monkeypatch) -> None:
    monkeypatch.setenv("USE_LLM_EVAL", "true")
    get_settings.cache_clear()

    monkeypatch.setattr(evaluation, "call_llm", lambda _prompt: "not json")

    result = evaluation.evaluate_clause(
        ClauseType.GOVERNING_LAW,
        ["segment"],
        {},
        [],
    )

    assert result["risk_label"] == "YELLOW"
    assert result["candidate_quotes"] == []
