from dataclasses import dataclass

from app.models.clause_type import ClauseType
from app.models.risk_label import RiskLabel
from app.services.summary import build_executive_summary


@dataclass
class StubEvaluation:
    clause_type: ClauseType
    risk_label: RiskLabel
    short_reason: str
    suggested_change: str


def _eval(clause_type, risk_label, reason="r", change="c"):
    return StubEvaluation(
        clause_type=clause_type,
        risk_label=risk_label,
        short_reason=reason,
        suggested_change=change,
    )


def test_summary_critical_red_reject() -> None:
    evaluations = [_eval(ClauseType.SECURITY_TOMS, RiskLabel.RED)]
    decision, summary = build_executive_summary(evaluations)

    assert decision == "REJECT"
    assert summary["critical_reds"] == [ClauseType.SECURITY_TOMS.value]


def test_summary_noncritical_red_needs_changes() -> None:
    evaluations = [_eval(ClauseType.LIABILITY, RiskLabel.RED)]
    decision, _summary = build_executive_summary(evaluations)

    assert decision == "NEEDS_CHANGES"


def test_summary_yellow_review() -> None:
    evaluations = [_eval(ClauseType.GOVERNING_LAW, RiskLabel.YELLOW)]
    decision, _summary = build_executive_summary(evaluations)

    assert decision == "REVIEW"


def test_summary_all_green_ok() -> None:
    evaluations = [_eval(ClauseType.GOVERNING_LAW, RiskLabel.GREEN)]
    decision, _summary = build_executive_summary(evaluations)

    assert decision == "OK"
