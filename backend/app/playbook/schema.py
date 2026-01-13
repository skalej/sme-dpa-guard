from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PlaybookMeta(BaseModel):
    id: str
    version: str
    scope: str | None = None
    audience: str | None = None
    disclaimer: str | None = None


class PlaybookRule(BaseModel):
    rule_id: str
    clause_type: str
    title: str | None = None
    gdpr_references: list[dict[str, Any]] | None = None
    requirement: str
    preferred_position: str | None = None
    fallback_position: str | None = None
    red_flag: str | None = None
    severity: str
    mandatory: bool = False
    rationale: str | None = None
    keywords: list[str] = Field(default_factory=list)


class PlaybookBlock(BaseModel):
    id: str
    version: str
    scope: str | None = None
    audience: str | None = None
    disclaimer: str | None = None
    rules: list[PlaybookRule] = Field(default_factory=list)


class PlaybookFile(BaseModel):
    playbook: PlaybookBlock
