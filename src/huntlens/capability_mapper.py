"""
capability_mapper.py

Purpose:
- Map SOC artifacts to detection query templates across Splunk SPL, Sentinel KQL, and Elastic EQL.
- Provide light rationale + severity hints so downstream playbook phases have a strong 'Detection' start.

Public API:
- generate_detection_queries(artifact: str, artifact_type: str) -> dict
- classify_ioc(artifact: str) -> str | None  # (ip|domain|sha1|sha256|md5)
- normalize_artifact_type(t: str) -> str

Design notes:
- Deterministic (no network calls).
- Conservative defaults; callers can enrich later with external intel.
- MITRE IDs: accept forms like "T1003", "t1059.001" (case-insensitive).
"""

from __future__ import annotations
import re
from typing import Dict, Optional

_IP_RE = re.compile(
    r"^(?:25[0-5]|2[0-4]\d|1?\d{1,2})(?:\.(?:25[0-5]|2[0-4]\d|1?\d{1,2})){3}$"
)
_DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)(?:[A-Za-z0-9-]{1,63}(?<!-)\.)+[A-Za-z]{2,63}$"
)
_SHA256_RE = re.compile(r"^[A-Fa-f0-9]{64}$")
_SHA1_RE = re.compile(r"^[A-Fa-f0-9]{40}$")
_MD5_RE = re.compile(r"^[A-Fa-f0-9]{32}$")
_MITRE_RE = re.compile(r"^t\d{4}(?:\.\d{3})?$", re.IGNORECASE)


def normalize_artifact_type(t: str) -> str:
    t = (t or "").strip().lower()
    aliases = {
        "ioc": "ioc",
        "indicator": "ioc",
        "process": "process",
        "proc": "process",
        "mitre": "mitre",
        "technique": "mitre",
        "repo": "repo",
        "github": "repo",
        "url": "ioc",
        "hash": "ioc",
    }
    return aliases.get(t, t or "other")


def classify_ioc(artifact: str) -> Optional[str]:
    s = (artifact or "").strip()
    if _IP_RE.match(s):
        return "ip"
    if _DOMAIN_RE.match(s):
        return "domain"
    if _SHA256_RE.match(s):
        return "sha256"
    if _SHA1_RE.match(s):
        return "sha1"
    if _MD5_RE.match(s):
        return "md5"
    return None


def _queries_for_ioc(artifact: str, ioc_type: str) -> Dict[str, str]:
    # These are intentionally generic, platform-safe templates.
    if ioc_type == "ip":
        return {
            "splunk": f"""index=* (dest_ip="{artifact}" OR src_ip="{artifact}") OR (dest="{artifact}" OR src="{artifact}")""",
            "kql": f"""union isfuzzy=true
  (SecurityEvent, DeviceNetworkEvents, CommonSecurityLog)
  | where RemoteIP == "{artifact}" or DestinationIp == "{artifact}" or SourceIp == "{artifact}" """,
            "eql": f"""network where destination.ip == "{artifact}" or source.ip == "{artifact}" """
        }
    if ioc_type == "domain":
        return {
            "splunk": f"""index=* (query="{artifact}" OR dest="{artifact}" OR url="*{artifact}*")""",
            "kql": f"""union isfuzzy=true (DnsEvents, DeviceNetworkEvents)
  | where Name == "{artifact}" or Url has "{artifact}" """,
            "eql": f"""dns where dns.question.name == "{artifact}" or stringcontains(url.original, "{artifact}") """
        }
    if ioc_type in {"sha256", "sha1", "md5"}:
        return {
            "splunk": f"""index=* (file_hash="{artifact}" OR Hash="{artifact}" OR sha256="{artifact}" OR sha1="{artifact}" OR md5="{artifact}")""",
            "kql": f"""union isfuzzy=true (DeviceFileEvents, DeviceProcessEvents)
  | where SHA256 == "{artifact}" or SHA1 == "{artifact}" or MD5 == "{artifact}" """,
            "eql": f"""file where file.hash.sha256 == "{artifact}" or file.hash.sha1 == "{artifact}" or file.hash.md5 == "{artifact}" """
        }
    # Fallback (should not hit)
    return {
        "splunk": f'index=* "{artifact}"',
        "kql": f"""union isfuzzy=true (*) | where tostring(*) has "{artifact}" """,
        "eql": f"""any where stringcontains(string(all), "{artifact}") """
    }


def _queries_for_process(name: str) -> Dict[str, str]:
    safe = name.strip().strip('"').strip("'")
    return {
        "splunk": f"""index=* sourcetype=XmlWinEventLog:Microsoft-Windows-Sysmon/Operational EventCode=1 Image="*\\{safe}" OR OriginalFileName="{safe}" OR process_name="{safe}" """,
        "kql": f"""DeviceProcessEvents
| where ProcessName =~ "{safe}" or FileName =~ "{safe}" or InitiatingProcessFileName =~ "{safe}" """,
        "eql": f"""process where process.name == "{safe}" or process.pe.original_file_name == "{safe}" """
    }


def _queries_for_mitre(tech: str) -> Dict[str, str]:
    t = tech.upper()
    # Provide generic technique anchors so analysts can refine.
    return {
        "splunk": f"""index=* ("{t}" OR "ATT&CK {t}")""",
        "kql": f"""union isfuzzy=true (*) | where tostring(*) has "{t}" """,
        "eql": f"""any where stringcontains(string(all), "{t}") """
    }


def generate_detection_queries(artifact: str, artifact_type: str) -> Dict[str, object]:
    """
    Generate cross-platform detection query templates and a brief rationale.

    Returns:
        {
          "artifact": str,
          "artifact_type": str,
          "family": "ioc|process|mitre|repo|other",
          "queries": {"splunk": str, "kql": str, "eql": str},
          "rationale": str,
          "severity_hint": "low|medium|high"
        }
    """
    a_type = normalize_artifact_type(artifact_type)
    sev = "medium"
    rationale = ""
    queries: Dict[str, str]

    if a_type == "ioc":
        ioc_kind = classify_ioc(artifact)
        if ioc_kind:
            queries = _queries_for_ioc(artifact, ioc_kind)
            rationale = f"Indicator search by {ioc_kind}; refine with time range, host scope, and known-good baselines."
            sev = "high" if ioc_kind in {"sha256", "sha1", "md5"} else "medium"
            fam = "ioc"
        else:
            # Treat unknown as domain-like keyword
            queries = _queries_for_ioc(artifact, "domain")
            rationale = "Free-text IOC; treated as domain-like keyword for broad visibility."
            fam = "ioc"
    elif a_type == "process":
        queries = _queries_for_process(artifact)
        rationale = "Process name triage; include parent/child correlation and command-line examination."
        sev = "medium"
        fam = "process"
    elif a_type == "mitre" or _MITRE_RE.match(artifact or ""):
        queries = _queries_for_mitre(artifact)
        rationale = "Technique pivot; pair with telemetry-specific detections for the sub-technique."
        sev = "medium"
        fam = "mitre"
    elif a_type == "repo":
        # Without analysis, just keyword presence
        queries = {
            "splunk": f'index=* "{artifact}"',
            "kql": f'union isfuzzy=true (*) | where tostring(*) has "{artifact}"',
            "eql": f'any where stringcontains(string(all), "{artifact}")'
        }
        rationale = "Repository keyword pivot; combine with code/parser analysis to derive concrete behaviors."
        sev = "low"
        fam = "repo"
    else:
        queries = {
            "splunk": f'index=* "{artifact}"',
            "kql": f'union isfuzzy=true (*) | where tostring(*) has "{artifact}"',
            "eql": f'any where stringcontains(string(all), "{artifact}")'
        }
        rationale = "Generic keyword pivot; refine by telemetry source and timeframe."
        sev = "low"
        fam = "other"

    return {
        "artifact": artifact,
        "artifact_type": a_type,
        "family": fam,
        "queries": queries,
        "rationale": rationale,
        "severity_hint": sev,
    }

