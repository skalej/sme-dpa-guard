from __future__ import annotations

import os
from pathlib import Path

import yaml

from app.config import get_settings
from app.models.clause_type import ClauseType
from app.playbook.schema import PlaybookFile


def normalize(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


YAML_TO_ENUM = {normalize(clause.value): clause for clause in ClauseType}
YAML_TO_ENUM.update(
    {
        "parties_and_roles": ClauseType.ROLES,
        "subject_matter_duration": ClauseType.SUBJECT_DURATION,
        "purpose_and_nature": ClauseType.PURPOSE_NATURE,
        "nature_purpose": ClauseType.PURPOSE_NATURE,
        "data_categories_subjects": ClauseType.DATA_CATEGORIES_SUBJECTS,
        "data_categories": ClauseType.DATA_CATEGORIES_SUBJECTS,
        "documented_instructions": ClauseType.ROLES,
        "security_measures": ClauseType.SECURITY_TOMS,
        "audit_and_inspections": ClauseType.AUDIT_RIGHTS,
        "audit_rights": ClauseType.AUDIT_RIGHTS,
        "deletion_or_return": ClauseType.DELETION_RETURN,
        "deletion_return": ClauseType.DELETION_RETURN,
        "data_subject_rights_assistance": ClauseType.DSAR_ASSISTANCE,
        "data_subject_rights": ClauseType.DSAR_ASSISTANCE,
        "international_transfers": ClauseType.TRANSFERS,
    }
)

_CACHE: dict[str, object] = {"path": None, "version": None, "rules": None}


def _resolve_playbook_path(path: str) -> Path:
    resolved = Path(path)
    if resolved.is_absolute():
        return resolved
    base_dir = Path(__file__).resolve().parents[2]
    return base_dir / resolved


def load_playbook_from_yaml(path: str) -> tuple[str, dict[ClauseType, list[dict]]]:
    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    playbook = PlaybookFile.model_validate(data)

    rules_by_clause: dict[ClauseType, list[dict]] = {clause: [] for clause in ClauseType}
    for rule in playbook.playbook.rules:
        clause_key = normalize(rule.clause_type)
        if clause_key not in YAML_TO_ENUM:
            raise ValueError(f"Unknown clause_type: {rule.clause_type}")
        clause_type = YAML_TO_ENUM[clause_key]
        rules_by_clause[clause_type].append(rule.model_dump())

    return playbook.playbook.version, rules_by_clause


def _get_loaded() -> tuple[str, dict[ClauseType, list[dict]]]:
    settings = get_settings()
    path = _resolve_playbook_path(settings.playbook_yaml_path)
    cached_path = _CACHE["path"]
    cached_rules = _CACHE["rules"]
    cached_version = _CACHE["version"]
    if cached_path == path and cached_rules is not None and cached_version is not None:
        return cached_version, cached_rules  # type: ignore[return-value]

    if not path.exists():
        empty_rules = {clause: [] for clause in ClauseType}
        _CACHE.update({"path": path, "version": "0", "rules": empty_rules})
        return "0", empty_rules

    version, rules_by_clause = load_playbook_from_yaml(str(path))
    _CACHE.update({"path": path, "version": version, "rules": rules_by_clause})
    return version, rules_by_clause


def get_rules_for_clause_type(clause_type: ClauseType) -> list[dict]:
    _version, rules = _get_loaded()
    return rules.get(clause_type, [])


def get_rules() -> list[dict]:
    _version, rules = _get_loaded()
    all_rules: list[dict] = []
    for rule_list in rules.values():
        all_rules.extend(rule_list)
    return all_rules


def get_playbook_version() -> str:
    version, _rules = _get_loaded()
    return version


def get_classification_keywords() -> dict[ClauseType, list[str]]:
    _version, rules = _get_loaded()
    keywords_map: dict[ClauseType, list[str]] = {clause: [] for clause in ClauseType}
    for clause_type, rule_list in rules.items():
        existing = keywords_map[clause_type]
        seen = set(existing)
        for rule in rule_list:
            keywords = rule.get("keywords", [])
            if not isinstance(keywords, list):
                continue
            for keyword in keywords:
                if not isinstance(keyword, str):
                    continue
                normalized = keyword.strip().lower()
                if not normalized or normalized in seen:
                    continue
                existing.append(normalized)
                seen.add(normalized)
    return keywords_map
