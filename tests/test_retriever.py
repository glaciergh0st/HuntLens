"""
Tests for retriever.py
"""

import os
import json
import pytest
from src.huntlens import retriever

def test_load_corpus():
    docs = retriever.load_corpus()
    assert isinstance(docs, list)
    assert all("content" in d for d in docs)

def test_search_mimikatz(tmp_path):
    # Create fake doc
    doc_path = tmp_path / "mimikatz.json"
    fake_doc = {"artifact": "mimikatz", "description": "Credential dumping"}
    with open(doc_path, "w") as f:
        json.dump(fake_doc, f)

    # Patch DATA_DIRS
    retriever.DATA_DIRS = [str(tmp_path)]

    results = retriever.search("mimikatz")
    assert results
    assert results[0]["id"] == "mimikatz.json"
    assert "content" in results[0]

def test_search_no_match(tmp_path):
    retriever.DATA_DIRS = [str(tmp_path)]
    results = retriever.search("notfound")
    assert results == []


