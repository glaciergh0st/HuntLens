"""
schema.py

Purpose:
- Define and validate the JSON schema used for HuntLens playbooks.
- Enforce NIST 800-61 structured outputs: detection, analysis, containment,
  eradication, recovery, post_incident.

Functions:
- get_schema() -> dict
    Return the schema loaded from docs/schema.json.
- ensure_schema(obj: dict) -> dict
    Validate obj against schema.json using jsonschema.
    Raise ValidationError if invalid, otherwise return obj unchanged.

Safety rules:
- Never modify input objects.
- Fail fast on invalid fields.
- Schema is the single source of truth for playbook structure.
"""

import os
import json
from jsonschema import validate, ValidationError

# Resolve schema path relative to repo root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEMA_PATH = os.path.join(BASE_DIR, "..", "..", "docs", "schema.json")

# Load schema once at module import
with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
    _schema = json.load(f)


def get_schema() -> dict:
    """
    Return the current HuntLens JSON schema definition.

    Returns:
        dict: The loaded JSON schema.
    """
    return _schema


def ensure_schema(obj: dict) -> dict:
    """
    Validate an object against the HuntLens schema.

    Args:
        obj (dict): Candidate playbook-like object.

    Returns:
        dict: The same object if validation succeeds.

    Raises:
        jsonschema.ValidationError: If validation fails.
    """
    validate(instance=obj, schema=_schema)
    return obj
