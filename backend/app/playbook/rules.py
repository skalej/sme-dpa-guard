from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from app.models.clause_type import ClauseType

CLAUSE_TYPE_ALIASES = {
    "PARTIES_AND_ROLES": ClauseType.ROLES,
}

PLAYBOOK_YAML_PATH = os.getenv("PLAYBOOK_YAML_PATH", "playbook/rules.yaml")


def _resolve_playbook_path() -> Path:
    path = Path(PLAYBOOK_YAML_PATH)
    if path.is_absolute():
        return path
    base_dir = Path(__file__).resolve().parents[2]
    return base_dir / path


def _parse_clause_type(value: Any) -> ClauseType | None:
    if isinstance(value, ClauseType):
        return value
    if not isinstance(value, str):
        return None
    normalized = value.strip().upper().replace(" ", "_").replace("-", "_")
    if normalized in CLAUSE_TYPE_ALIASES:
        return CLAUSE_TYPE_ALIASES[normalized]
    if normalized in ClauseType.__members__:
        return ClauseType[normalized]
    try:
        return ClauseType(normalized)
    except ValueError:
        return None


@lru_cache
def _load_rules() -> list[dict]:
    path = _resolve_playbook_path()
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if isinstance(data, dict) and isinstance(data.get("playbook"), dict):
        rules = data["playbook"].get("rules", [])
    else:
        return []
    return [rule for rule in rules if isinstance(rule, dict)]


def get_rules() -> list[dict]:
    return _load_rules()


def get_rules_for_clause_type(clause_type: ClauseType) -> list[dict]:
    return [
        rule
        for rule in _load_rules()
        if _parse_clause_type(rule.get("clause_type")) == clause_type
    ]


def get_classification_keywords() -> dict[ClauseType, list[str]]:
    keywords_map: dict[ClauseType, list[str]] = {clause: [] for clause in ClauseType}
    for rule in _load_rules():
        clause_type = _parse_clause_type(rule.get("clause_type"))
        if clause_type is None:
            continue
        keywords = rule.get("keywords", [])
        if not isinstance(keywords, list):
            continue
        existing = keywords_map[clause_type]
        seen = set(existing)
        for keyword in keywords:
            if not isinstance(keyword, str):
                continue
            normalized = keyword.strip().lower()
            if not normalized or normalized in seen:
                continue
            existing.append(normalized)
            seen.add(normalized)
    return keywords_map
