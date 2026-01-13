from __future__ import annotations

from app.models.clause_evaluation import ClauseEvaluation
from app.models.clause_type import ClauseType
from app.models.risk_label import RiskLabel

CRITICAL_CLAUSE_TYPES = {
    ClauseType.SECURITY_TOMS,
    ClauseType.BREACH_NOTIFICATION,
    ClauseType.DELETION_RETURN,
    ClauseType.TRANSFERS,
}


def build_executive_summary(
    evaluations: list[ClauseEvaluation],
) -> tuple[str, dict]:
    counts = {RiskLabel.GREEN.value: 0, RiskLabel.YELLOW.value: 0, RiskLabel.RED.value: 0}
    for evaluation in evaluations:
        counts[evaluation.risk_label.value] += 1

    critical_reds = [
        evaluation.clause_type.value
        for evaluation in evaluations
        if evaluation.risk_label == RiskLabel.RED
        and evaluation.clause_type in CRITICAL_CLAUSE_TYPES
    ]

    if critical_reds:
        decision = "REJECT"
    elif counts[RiskLabel.RED.value] > 0:
        decision = "NEEDS_CHANGES"
    elif counts[RiskLabel.YELLOW.value] > 0:
        decision = "REVIEW"
    else:
        decision = "OK"

    issues = [
        {
            "clause_type": evaluation.clause_type.value,
            "risk_label": evaluation.risk_label.value,
            "short_reason": evaluation.short_reason,
            "suggested_change": evaluation.suggested_change,
        }
        for evaluation in evaluations
        if evaluation.risk_label != RiskLabel.GREEN
    ]
    issues.sort(key=lambda item: (item["risk_label"] != RiskLabel.RED.value, item["clause_type"]))

    summary = {
        "counts": counts,
        "critical_reds": critical_reds,
        "issues": issues,
    }

    return decision, summary
