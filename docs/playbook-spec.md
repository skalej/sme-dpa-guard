# Playbook Spec

Path (default): `playbook/rules.yaml` (configurable via `PLAYBOOK_YAML_PATH`).

## Structure

```yaml
playbook:
  id: dpa-sme-standard-v1
  version: "1.0"
  scope: "Data Processing Agreements (GDPR Addendum)"
  audience: "EU / Germany-based SMEs"
  disclaimer: "Decision-support only. Not legal advice."

  rules:
    - rule_id: DPA-ROLE-01
      clause_type: parties_and_roles
      title: Parties & Roles
      gdpr_references:
        - article: "4"
          description: "Definitions of Controller and Processor"
      requirement: Clear identification of Controller and Processor roles.
      preferred_position: Explicit identification of Controller and Processor.
      fallback_position: Roles defined implicitly but unambiguous.
      red_flag: Roles missing or Processor claims independent control.
      severity: high
      mandatory: true
      rationale: GDPR processor obligations depend on correct role allocation.
      keywords: ["controller", "processor", "acting on behalf"]
```

## Clause type mapping

YAML `clause_type` is normalized (lowercase, spaces/hyphens -> underscore) and mapped to `ClauseType`.
Unknown values cause the loader to skip or fail fast (based on code configuration).

## Classification keywords

Keywords are aggregated across all rules by ClauseType and used for deterministic classification.
