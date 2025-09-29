"""
prompt_engine.py

Purpose:
- Centralize prompt templates for HuntLens' AI SOC Copilot.
- Generate context-aware inputs for the LLM, aligned with schema + NIST phases.

Functions:
1. build_prompt(artifact: str, artifact_type: str, context: dict = None) -> str
   - Construct a structured prompt for the LLM.
   - Include artifact, type, and optional context (repo snapshot, ATT&CK mapping, etc).

2. build_playbook_prompt(validated_data: dict) -> str
   - Take schema-validated data and generate a playbook request.
   - Ensure alignment with NIST 800-61 (Detection → Resolution).

Safety Rules:
- Prompts must remain deterministic and reproducible.
- Never inject sensitive / uncontrolled data directly.
- Always sanitize artifact inputs.
"""

import json
from typing import Dict, Optional


def build_prompt(artifact: str, artifact_type: str, context: Optional[Dict] = None) -> str:
    """
    Construct a structured prompt for the LLM.

    Args:
        artifact (str): The SOC artifact (IOC, process, MITRE ID, etc.).
        artifact_type (str): Type of artifact.
        context (dict, optional): Extra information (e.g., repo snapshot, ATT&CK mapping).

    Returns:
        str: Prompt text to send to the LLM.
    """
    safe_artifact = artifact.strip()
    safe_type = artifact_type.strip().lower()
    ctx = json.dumps(context, indent=2) if context else "{}"

    return (
        f"You are HuntLens, an AI SOC copilot.\n"
        f"Artifact: {safe_artifact}\n"
        f"Type: {safe_type}\n"
        f"Context: {ctx}\n\n"
        "Generate a NIST 800-61 aligned playbook (Detection, Analysis, Containment, "
        "Eradication, Recovery, Post-Incident). Include rationale and references."
    )


def build_playbook_prompt(validated_data: Dict) -> str:
    """
    Generate a playbook prompt from schema-validated data.

    Args:
        validated_data (dict): Data already validated against schema.json.

    Returns:
        str: Playbook generation prompt.
    """
    return (
        "You are HuntLens. Based on the following validated SOC input, "
        "generate a structured playbook aligned with schema.json.\n\n"
        f"{json.dumps(validated_data, indent=2)}"
    )

