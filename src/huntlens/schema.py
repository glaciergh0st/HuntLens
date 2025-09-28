"""Load docs/schema.json and implement ensure_schema(obj) using jsonschema; raise ValidationError on failure."""
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
