
"""
schema.py

Purpose:
- Define and validate the JSON schema used for all HuntLens outputs.
- Enforce that Detection-to-Resolution playbooks are structured, safe, and machine-readable.

Functions / Classes to implement:
1. get_schema() -> dict
   - Return the current JSON schema definition for HuntLens playbooks.
2. ensure_schema(data: dict) -> dict
   - Validate `data` against the schema.
   - Raise a clear exception if invalid.
   - Return `data` unchanged if valid.

Requirements:
- Schema should align with NIST 800-61 phases:
  detection, analysis, containment, eradication, recovery, post_incident.
- Must allow optional SOAR playbook stubs, references, and rationale fields.
- Use `jsonschema` for validation.

Safety Rules:
- Never modify input data during validation.
- Fail fast on invalid or unexpected fields.
- Keep schema definitions versioned and extendable.
- Schema is the single source of truth for all generated playbooks.
"""


"""Load docs/schema.json and implement ensure_schema(obj) using jsonschema; raise ValidationError on failure.
"""


import json
import os
from jsonschema import validate, ValidationError

# Path to docs/schema.json relative to this file
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), '..', 'docs', 'schema.json')

# Load schema once at module import
with open(SCHEMA_PATH, 'r') as f:
    _schema = json.load(f)

def ensure_schema(obj: dict):
    """
    Validates the given object against docs/schema.json.
    Raises jsonschema.ValidationError if validation fails.
    """
    validate(instance=obj, schema=_schema)
