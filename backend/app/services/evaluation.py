from __future__ import annotations

from app.models.clause_type import ClauseType
from app.models.risk_label import RiskLabel

CRITICAL_MISSING_CLAUSES = {
    ClauseType.SECURITY_TOMS,
    ClauseType.BREACH_NOTIFICATION,
    ClauseType.DELETION_RETURN,
    ClauseType.TRANSFERS,
}


def evaluate_missing_clause(clause_type: ClauseType) -> dict:
    if clause_type in CRITICAL_MISSING_CLAUSES:
        risk_label = RiskLabel.RED
        reason_prefix = "Critical clause missing"
    else:
        risk_label = RiskLabel.YELLOW
        reason_prefix = "Clause missing"

    short_reason = f"{reason_prefix}: {clause_type.value}."
    suggested_change = (
        f"Add a {clause_type.value} clause that meets GDPR requirements."
    )

    return {
        "risk_label": risk_label.value,
        "short_reason": short_reason,
        "suggested_change": suggested_change,
        "candidate_quotes": [],
        "triggered_rule_ids": [],
    }
