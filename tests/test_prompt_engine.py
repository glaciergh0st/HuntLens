import re
import pytest
from src.huntlens import prompt_engine


def test_build_prompt_basic():
    text = prompt_engine.build_prompt("mimikatz.exe", "process")
    assert "mimikatz.exe" in text
    assert "process" in text
    assert "NIST 800-61" in text


def test_build_prompt_with_context():
    ctx = {"commits": ["init", "add feature"]}
    text = prompt_engine.build_prompt("repo", "git", context=ctx)
    assert "repo" in text
    assert "git" in text
    assert "commits" in text
    assert re.search(r"init", text)


def test_build_playbook_prompt():
    validated = {"artifact": "mimikatz", "artifact_type": "process"}
    text = prompt_engine.build_playbook_prompt(validated)
    assert "mimikatz" in text
    assert "validated SOC input" in text

