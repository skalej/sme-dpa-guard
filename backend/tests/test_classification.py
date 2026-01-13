import importlib
from textwrap import dedent

from app.config import get_settings
from app.models.clause_type import ClauseType
import app.playbook.rules as playbook_rules
import app.services.classification as classification


def _reload_with_playbook(tmp_path, yaml_content: str, monkeypatch):
    path = tmp_path / "rules.yaml"
    path.write_text(dedent(yaml_content))
    monkeypatch.setenv("PLAYBOOK_YAML_PATH", str(path))
    get_settings.cache_clear()
    importlib.reload(playbook_rules)
    importlib.reload(classification)
    return classification


def test_rules_classification_security(tmp_path, monkeypatch) -> None:
    module = _reload_with_playbook(
        tmp_path,
        """
        playbook:
          id: test
          version: "1.0"
          rules:
            - rule_id: DPA-LAW-01
              clause_type: governing_law
              requirement: Governing law is stated.
              severity: low
              keywords: ["governing law", "jurisdiction"]
        """,
        monkeypatch,
    )
    text = "We apply technical and organizational measures including encryption."
    results = module.classify_segment_rules(text)

    types = [result["clause_type"] for result in results]
    assert ClauseType.SECURITY_TOMS in types


def test_rules_playbook_governing_law(tmp_path, monkeypatch) -> None:
    module = _reload_with_playbook(
        tmp_path,
        """
        playbook:
          id: test
          version: "1.0"
          rules:
            - rule_id: DPA-LAW-01
              clause_type: governing_law
              requirement: Governing law is stated.
              severity: low
              keywords: ["governing law", "jurisdiction"]
        """,
        monkeypatch,
    )
    text = "This agreement is subject to governing law and jurisdiction."
    results = module.classify_segment_rules(text)

    types = [result["clause_type"] for result in results]
    assert ClauseType.GOVERNING_LAW in types


def test_rules_confidence_cap(tmp_path, monkeypatch) -> None:
    module = _reload_with_playbook(
        tmp_path,
        """
        playbook:
          id: test
          version: "1.0"
          rules: []
        """,
        monkeypatch,
    )
    text = "technical and organizational measures encryption security measures"
    results = module.classify_segment_rules(text)

    for result in results:
        assert result["confidence"] <= 0.9


def test_top_k_sorted(tmp_path, monkeypatch) -> None:
    module = _reload_with_playbook(
        tmp_path,
        """
        playbook:
          id: test
          version: "1.0"
          rules: []
        """,
        monkeypatch,
    )
    text = "controller processor confidentiality audit inspection"
    results = module.classify_segment_rules(text)

    confidences = [result["confidence"] for result in results]
    assert confidences == sorted(confidences, reverse=True)
