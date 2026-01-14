from __future__ import annotations

import json

from app.config import get_settings
from app.models.clause_type import ClauseType
from app.models.risk_label import RiskLabel
from app.services.openai_retry import retry_with_backoff

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
            "title": rule.get("title"),
            "requirement": rule.get("requirement"),
            "preferred_position": rule.get("preferred_position"),
            "fallback_position": rule.get("fallback_position"),
            "red_flag": rule.get("red_flag"),
            "severity": rule.get("severity"),
            "mandatory": rule.get("mandatory"),
            "rationale": rule.get("rationale"),
            "gdpr_references": rule.get("gdpr_references"),
        }
        for rule in playbook_rules
    ]
    prompt = (
        "You are a DPA clause evaluator. Use ONLY the provided clause text, rules, "
        "and context JSON. Do not infer facts that are not in the text. Return ONLY "
        "valid JSON (no markdown). Return exactly the schema keys - no extra keys.\n\n"
        "JSON schema:\n"
        "{\n"
        '  \"risk_label\": \"GREEN|YELLOW|RED\",\n'
        '  \"short_reason\": \"string (1-2 sentences, <300 chars)\",\n'
        '  \"suggested_change\": \"string or null (1-2 sentences, <300 chars)\",\n'
        '  \"candidate_quotes\": [\"verbatim excerpts from the clause text\"],\n'
        '  \"triggered_rule_ids\": [\"rule_id\"],\n'
        "}\n\n"
        "Rubric:\n"
        "- GREEN: clause fully satisfies mandatory requirements with clear coverage.\n"
        "- YELLOW: partially satisfies requirements or wording is ambiguous.\n"
        "- RED: missing mandatory requirements, contradicts rules, or has red_flag.\n"
        "- If preferred_position is provided and not met, you MUST return YELLOW (even if requirement is met).\n"
        "- GREEN requires meeting preferred_position when it exists.\n"
        "- If clause text contains the red_flag concept or explicitly negates the "
        "obligation, set RED.\n"
        "- If clause text is empty or clearly unrelated, set YELLOW and explain "
        "that no relevant clause text was found.\n"
        "Evidence:\n"
        "- candidate_quotes must be exact substrings from the clause text.\n"
        "- Do not use ellipses (...) or brackets. Copy exact text and punctuation.\n"
        "- Keep each quote 10-80 words.\n"
        "- If risk_label is YELLOW or RED, include at least 1 quote if relevant text exists.\n"
        "- If no relevant text exists, keep quotes empty and explain why in short_reason.\n"
        "Rules:\n"
        "- triggered_rule_ids must be a subset of provided rule_id values.\n"
        "- If risk_label is GREEN, suggested_change MUST be null.\n\n"
        "Example output:\n"
        "{\"risk_label\":\"YELLOW\",\"short_reason\":\"...\",\"suggested_change\":null,"
        "\"candidate_quotes\":[\"...\"],\"triggered_rule_ids\":[\"R1\"]}\n\n"
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
    if set(data.keys()) != required:
        raise ValueError("Invalid keys")
    if data["risk_label"] not in {label.value for label in RiskLabel}:
        raise ValueError("Invalid risk_label")
    if not isinstance(data["short_reason"], str):
        raise ValueError("Invalid short_reason")
    if data["suggested_change"] is not None and not isinstance(
        data["suggested_change"], str
    ):
        raise ValueError("Invalid suggested_change")
    if data["risk_label"] == RiskLabel.GREEN.value and data["suggested_change"] is not None:
        raise ValueError("Suggested_change must be null for GREEN")
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

    def _call() -> str:
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

    return retry_with_backoff(_call)


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
