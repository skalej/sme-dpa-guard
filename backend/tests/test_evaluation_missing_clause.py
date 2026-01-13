from app.models.clause_type import ClauseType
from app.models.risk_label import RiskLabel
from app.services.evaluation import evaluate_missing_clause


def test_missing_clause_critical_is_red() -> None:
    result = evaluate_missing_clause(ClauseType.SECURITY_TOMS)

    assert result["risk_label"] == RiskLabel.RED.value
    assert result["candidate_quotes"] == []
    assert result["triggered_rule_ids"] == []


def test_missing_clause_noncritical_is_yellow() -> None:
    result = evaluate_missing_clause(ClauseType.GOVERNING_LAW)

    assert result["risk_label"] == RiskLabel.YELLOW.value
    assert result["candidate_quotes"] == []
    assert result["triggered_rule_ids"] == []
