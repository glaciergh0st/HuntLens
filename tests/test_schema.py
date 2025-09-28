"""
Tests for schema.py
"""

import pytest
from src.huntlens import schema


def test_valid_playbook_passes():
    data = {
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
        "soar_playbook_template": None,
        "references": []
    }
    validated = schema.ensure_schema(data)
    assert validated == data


def test_missing_required_field_fails():
    bad_data = {
        "artifact_type": "process",
        "nist_phase_playbook": {}
    }
    with pytest.raises(Exception):
        schema.ensure_schema(bad_data)


def test_unexpected_field_fails():
    bad_data = {
        "artifact": "mimikatz.exe",
        "artifact_type": "process",
        "extra_field": "bad",
        "nist_phase_playbook": {
            "detection": [],
            "analysis": [],
            "containment": [],
            "eradication": [],
            "recovery": [],
            "post_incident": []
        }
    }
    with pytest.raises(Exception):
        schema.ensure_schema(bad_data)
