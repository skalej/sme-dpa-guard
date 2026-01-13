from __future__ import annotations

import json

from app.config import get_settings
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


def _strip_fences(payload: str) -> str:
    stripped = payload.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return stripped


def _parse_eval_json(payload: str) -> dict | None:
    cleaned = _strip_fences(payload)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    required = {"risk_label", "short_reason", "suggested_change", "candidate_quotes", "triggered_rule_ids"}
    if not required.issubset(data.keys()):
        return None
    if data["risk_label"] not in {label.value for label in RiskLabel}:
        return None
    if not isinstance(data["candidate_quotes"], list) or not all(
        isinstance(item, str) for item in data["candidate_quotes"]
    ):
        return None
    if not isinstance(data["triggered_rule_ids"], list) or not all(
        isinstance(item, str) for item in data["triggered_rule_ids"]
    ):
        return None
    return data


def call_llm(_prompt: str) -> str:
    raise RuntimeError("LLM provider not configured")


def _fallback_eval(message: str) -> dict:
    return {
        "risk_label": RiskLabel.YELLOW.value,
        "short_reason": message,
        "suggested_change": "Evaluation not available.",
        "candidate_quotes": [],
        "triggered_rule_ids": [],
    }


def evaluate_clause(
    clause_type: ClauseType,
    segment_texts: list[str],
    context: dict | None,
    playbook_rules: list[dict],
) -> dict:
    settings = get_settings()
    if not settings.use_llm_eval:
        return _fallback_eval("LLM disabled")

    prompt = (
        f"Clause: {clause_type.value}\\n"
        f"Rules: {json.dumps(playbook_rules)}\\n"
        f"Context: {json.dumps(context or {})}\\n"
        f"Segments: {json.dumps(segment_texts)[: settings.llm_max_input_chars]}"
    )
    try:
        response = call_llm(prompt)
        parsed = _parse_eval_json(response)
        if parsed is None:
            return _fallback_eval("Evaluation unavailable")
        return parsed
    except Exception:
        return _fallback_eval("Evaluation unavailable")
