"""
Tests for capability_mapper.py
"""

from src.huntlens import capability_mapper as cm


def test_classify_ioc_variants():
    assert cm.classify_ioc("8.8.8.8") == "ip"
    assert cm.classify_ioc("evil.example.com") == "domain"
    assert cm.classify_ioc("a"*64) == "sha256"
    assert cm.classify_ioc("b"*40) == "sha1"
    assert cm.classify_ioc("c"*32) == "md5"
    assert cm.classify_ioc("not-an-ioc") is None


def test_generate_for_ip():
    res = cm.generate_detection_queries("10.10.10.10", "ioc")
    q = res["queries"]
    assert "10.10.10.10" in q["splunk"]
    assert "10.10.10.10" in q["kql"]
    assert "10.10.10.10" in q["eql"]
    assert res["family"] == "ioc"
    assert res["severity_hint"] in {"medium", "high"}


def test_generate_for_process():
    res = cm.generate_detection_queries("mimikatz.exe", "process")
    q = res["queries"]
    assert "mimikatz.exe" in q["splunk"]
    assert "mimikatz.exe" in q["kql"]
    assert "mimikatz.exe" in q["eql"]
    assert res["family"] == "process"


def test_generate_for_mitre():
    res = cm.generate_detection_queries("T1059.001", "mitre")
    q = res["queries"]
    assert "T1059.001" in q["splunk"]
    assert "T1059.001" in q["kql"]
    assert "T1059.001" in q["eql"]
    assert res["family"] == "mitre"


def test_generate_for_repo_keyword():
    res = cm.generate_detection_queries("SharpHound", "repo")
    assert res["family"] == "repo"
    assert "SharpHound" in res["queries"]["splunk"]

