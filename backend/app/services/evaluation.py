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


def build_eval_prompt(
    clause_type: ClauseType,
    segment_texts: list[str],
    context: dict | None,
    playbook_rules: list[dict],
) -> str:
    settings = get_settings()
    segment_blob = "\n\n---\n\n".join(segment_texts)
    segment_blob = segment_blob[: settings.llm_max_input_chars]
    rule_fields = [
        {
            "rule_id": rule.get("rule_id"),
            "clause_type": rule.get("clause_type"),
            "requirement": rule.get("requirement"),
            "severity": rule.get("severity"),
            "keywords": rule.get("keywords"),
        }
        for rule in playbook_rules
    ]
    prompt = (
        "You are a DPA clause evaluator. Return ONLY valid JSON (no markdown) "
        "with keys: risk_label, short_reason, suggested_change, candidate_quotes, "
        "triggered_rule_ids. risk_label must be one of GREEN, YELLOW, RED. "
        "candidate_quotes must be verbatim excerpts from the clause text. "
        "triggered_rule_ids must be a subset of the provided rule_ids.\n"
        f"Clause: {clause_type.value}\n"
        f"Context JSON:\n{json.dumps(context or {}, indent=2)}\n"
        f"Playbook rules:\n{json.dumps(rule_fields, indent=2)}\n"
        f"Clause text:\n{segment_blob}"
    )
    return prompt


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


def _parse_eval_json(payload: str) -> dict:
    cleaned = _strip_fences(payload)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid JSON") from exc
    if not isinstance(data, dict):
        raise ValueError("Invalid payload")
    required = {
        "risk_label",
        "short_reason",
        "suggested_change",
        "candidate_quotes",
        "triggered_rule_ids",
    }
    if not required.issubset(data.keys()):
        raise ValueError("Missing keys")
    if data["risk_label"] not in {label.value for label in RiskLabel}:
        raise ValueError("Invalid risk_label")
    if not isinstance(data["short_reason"], str):
        raise ValueError("Invalid short_reason")
    if not isinstance(data["suggested_change"], str):
        raise ValueError("Invalid suggested_change")
    if not isinstance(data["candidate_quotes"], list) or not all(
        isinstance(item, str) for item in data["candidate_quotes"]
    ):
        raise ValueError("Invalid candidate_quotes")
    if not isinstance(data["triggered_rule_ids"], list) or not all(
        isinstance(item, str) for item in data["triggered_rule_ids"]
    ):
        raise ValueError("Invalid triggered_rule_ids")
    return data


def call_llm_openai(prompt: str) -> str:
    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError("Missing OpenAI API key")
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    try:
        response = client.responses.create(
            model=settings.openai_model,
            input=prompt,
            temperature=settings.llm_temperature,
        )
        if hasattr(response, "output_text"):
            return response.output_text
    except Exception:
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=settings.llm_temperature,
        )
        return response.choices[0].message.content or ""
    raise RuntimeError("Empty LLM response")


def _fallback_eval(message: str) -> dict:
    return {
        "risk_label": RiskLabel.YELLOW.value,
        "short_reason": message,
        "suggested_change": "Manual review recommended.",
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
        return {
            "risk_label": RiskLabel.YELLOW.value,
            "short_reason": "LLM disabled; no automated evaluation performed.",
            "suggested_change": "Enable LLM or review manually.",
            "candidate_quotes": [],
            "triggered_rule_ids": [],
        }

    prompt = build_eval_prompt(clause_type, segment_texts, context, playbook_rules)
    try:
        response = call_llm_openai(prompt)
        return _parse_eval_json(response)
    except Exception:
        return _fallback_eval("Evaluation unavailable (LLM error).")
