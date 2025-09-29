"""Implement hybrid_retrieve(query, topk=20) combining BM25 and vectors; rerank by trust/recency/diversity."""
"""
retriever.py

Purpose:
- Retrieve relevant knowledge snippets for a given SOC artifact.
- Acts as the first step of HuntLens RAG pipeline.

Functions:
1. load_corpus() -> List[dict]
   - Loads all JSON docs from data/golden_set and data/corpus.
2. search(query: str, max_results: int = 3) -> List[dict]
   - Simple keyword-based search over the corpus.
   - Returns ranked results with match scores.

Notes:
- Hybrid search placeholder (can later be swapped for embeddings/vector DB).
- Keeps results lightweight and schema-agnostic.
"""

import os
import json
import re
from typing import List, Dict

DATA_DIRS = [
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "golden_set"),
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "corpus"),
]

def load_corpus() -> List[Dict]:
    """
    Load all JSON documents from data directories.
    Returns: List of dicts with keys {id, source, content}.
    """
    docs = []
    for d in DATA_DIRS:
        if not os.path.exists(d):
            continue
        for f in os.listdir(d):
            if f.endswith(".json"):
                path = os.path.join(d, f)
                try:
                    with open(path, "r") as fh:
                        content = json.load(fh)
                    docs.append({
                        "id": f,
                        "source": d,
                        "content": content
                    })
                except Exception as e:
                    print(f"Warning: failed to load {path}: {e}")
    return docs

def search(query: str, max_results: int = 3) -> List[Dict]:
    """
    Search corpus for documents matching the query.
    Very simple scoring: count of keyword matches in JSON string.
    """
    corpus = load_corpus()
    scored = []
    for doc in corpus:
        text = json.dumps(doc["content"]).lower()
        q = query.lower()
        score = len(re.findall(re.escape(q), text))
        if score > 0:
            scored.append({
                "id": doc["id"],
                "source": doc["source"],
                "match_score": score,
                "content": doc["content"]
            })
    # sort high → low
    scored = sorted(scored, key=lambda x: x["match_score"], reverse=True)
    return scored[:max_results]

