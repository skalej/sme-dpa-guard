from __future__ import annotations

import json
import os

from app.config import get_settings
from app.models.clause_type import ClauseType
from app.playbook.rules import get_classification_keywords

FALLBACK_CLASSIFICATION_RULES: dict[ClauseType, list[str]] = {
    ClauseType.ROLES: ["controller", "processor", "sub-processor", "subprocessor"],
    ClauseType.SUBJECT_DURATION: ["term", "duration", "effective date", "expiry"],
    ClauseType.PURPOSE_NATURE: ["purpose", "processing", "nature of processing"],
    ClauseType.DATA_CATEGORIES_SUBJECTS: [
        "data subjects",
        "categories of data",
        "personal data",
    ],
    ClauseType.SECURITY_TOMS: [
        "technical and organizational measures",
        "organizational measures",
        "security measures",
        "encryption",
    ],
    ClauseType.SUBPROCESSORS: ["subprocessor", "sub-processor", "subprocessors"],
    ClauseType.TRANSFERS: ["transfer", "cross-border", "international transfer"],
    ClauseType.BREACH_NOTIFICATION: ["breach", "security incident", "notification"],
    ClauseType.DSAR_ASSISTANCE: ["data subject request", "dsar", "assistance"],
    ClauseType.DELETION_RETURN: ["deletion", "return", "destroy"],
    ClauseType.AUDIT_RIGHTS: ["audit", "inspection", "records"],
    ClauseType.CONFIDENTIALITY: ["confidential", "confidentiality"],
    ClauseType.LIABILITY: ["liability", "indemnity", "damages"],
    ClauseType.GOVERNING_LAW: ["governing law", "jurisdiction"],
    ClauseType.ORDER_OF_PRECEDENCE: ["order of precedence", "conflict"],
}


def classify_segment_rules(segment_text: str) -> list[dict]:
    normalized = segment_text.lower()
    results: list[dict] = []
    keywords_map = get_classification_keywords()
    for clause_type in ClauseType:
        keywords = keywords_map.get(clause_type) or FALLBACK_CLASSIFICATION_RULES.get(
            clause_type, []
        )
        if not keywords:
            continue
        score = sum(1 for keyword in keywords if keyword in normalized)
        if score > 0:
            confidence = min((score / len(keywords)) * 2, 0.9)
            results.append(
                {
                    "clause_type": clause_type,
                    "confidence": confidence,
                    "method": "RULES",
                }
            )
    results.sort(key=lambda item: (-item["confidence"], item["clause_type"].value))
    settings = get_settings()
    top_k = settings.classify_top_k
    return results[:top_k]


def _strip_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        return stripped.strip()
    return stripped


def classify_segment_llm(_segment_text: str) -> list[dict]:
    settings = get_settings()
    if not settings.use_llm_classification:
        return []
    if not os.getenv("LLM_API_KEY"):
        return []
    # LLM integration will be added later.
    payload = os.getenv("LLM_CLASSIFICATION_RESPONSE", "")
    if not payload:
        return []
    return _parse_llm_output(payload)


def _parse_llm_output(payload: str) -> list[dict]:
    cleaned = _strip_fences(payload)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    results = []
    for item in data:
        if not isinstance(item, dict):
            continue
        clause = item.get("clause_type")
        confidence = item.get("confidence")
        if clause is None or confidence is None:
            continue
        try:
            clause_type = ClauseType(clause)
        except ValueError:
            continue
        results.append(
            {
                "clause_type": clause_type,
                "confidence": float(confidence),
                "method": "LLM",
            }
        )
    return results


def classify_segment(segment_text: str) -> list[dict]:
    settings = get_settings()
    rules_results = classify_segment_rules(segment_text)
    if rules_results:
        top_conf = rules_results[0]["confidence"]
        if top_conf >= settings.classify_rules_min_conf:
            return rules_results
    llm_results = classify_segment_llm(segment_text)
    if llm_results:
        return llm_results
    return rules_results
