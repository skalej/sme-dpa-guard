import importlib
from textwrap import dedent

import app.playbook.rules as rules
from app.config import get_settings
from app.models.clause_type import ClauseType


def test_playbook_yaml_loads_rules(tmp_path, monkeypatch) -> None:
    yaml_path = tmp_path / "playbook.yml"
    yaml_path.write_text(
        dedent(
            """
            playbook:
              id: dpa-test
              version: "1.0"
              rules:
                - rule_id: DPA-LAW-01
                  clause_type: governing_law
                  requirement: Governing law is stated.
                  severity: low
                  mandatory: false
                  keywords: ["governing law", "jurisdiction"]
            """
        )
    )
    monkeypatch.setenv("PLAYBOOK_YAML_PATH", str(yaml_path))
    get_settings.cache_clear()
    importlib.reload(rules)

    result = rules.get_rules_for_clause_type(ClauseType.GOVERNING_LAW)
    assert result
    assert result[0]["rule_id"] == "DPA-LAW-01"
