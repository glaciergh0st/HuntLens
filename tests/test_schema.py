"""
Tests for schema.py
"""

import pytest
from jsonschema import ValidationError
from src.huntlens import schema


def test_get_schema_returns_dict():
    s = schema.get_schema()
    assert isinstance(s, dict)
    assert "properties" in s  # sanity check


def test_ensure_schema_accepts_valid_object():
    valid_obj = {
        "artifact": "mimikatz.exe",
        "artifact_type": "process",
        "nist_phase_playbook": {
            "detection": [],
            "analysis": [],
            "containment": [],
            "eradication": [],
            "recovery": [],
            "post_incident": []
        },
        "references": []
    }

    result = schema.ensure_schema(valid_obj)
    assert result == valid_obj


def test_ensure_schema_rejects_invalid_object():
    invalid_obj = {"not_in_schema": "oops"}
    with pytest.raises(ValidationError):
        schema.ensure_schema(invalid_obj)
