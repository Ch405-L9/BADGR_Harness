#!/usr/bin/env python3
"""
rag_query.py
Retrieval layer for BADGR harness.
Import retrieve() into orchestrator, or run standalone to test.

Usage:
    python rag_query.py "what are BADGR's service packages and pricing?"
"""

import sys
import requests
import chromadb

CHROMA_DIR  = "rag_db"
COLLECTION  = "badgr_corpus"
OLLAMA_URL  = "http://localhost:11434"
EMBED_MODEL = "nomic-embed-text"
TOP_K       = 5


def _embed(text: str) -> list[float]:
    r = requests.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["embedding"]


def retrieve(query: str, k: int = TOP_K) -> list[dict]:
    """
    Returns up to k relevant chunks with source and text.
    Each result: {"source": str, "chunk": str, "distance": float}
    """
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    col = client.get_or_create_collection(name=COLLECTION)

    if col.count() == 0:
        return []

    vec = _embed(query)
    results = col.query(query_embeddings=[vec], n_results=min(k, col.count()))

    hits = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        hits.append({
            "source":   meta.get("source", "unknown"),
            "chunk":    doc,
            "distance": round(dist, 4),
        })
    return hits


def format_context(hits: list[dict]) -> str:
    """Format retrieved chunks as a context block for prompting."""
    if not hits:
        return ""
    parts = []
    for h in hits:
        parts.append(f"[Source: {h['source']}]\n{h['chunk']}")
    return "\n\n---\n\n".join(parts)


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What services does BADGR offer?"
    print(f"Query: {query}\n{'─'*60}")

    hits = retrieve(query)
    if not hits:
        print("No results — run rag_ingest.py first.")
        sys.exit(0)

    for i, h in enumerate(hits, 1):
        print(f"\n[{i}] {h['source']}  (dist={h['distance']})")
        print(h['chunk'][:400] + ("..." if len(h['chunk']) > 400 else ""))
