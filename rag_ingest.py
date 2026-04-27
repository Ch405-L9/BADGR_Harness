#!/usr/bin/env python3
"""
rag_ingest.py
Extracts text from corpus_harvest/tier1_badgr, chunks it,
embeds via nomic-embed-text (Ollama), stores in ChromaDB.
Run once to build the vector store. Safe to re-run (skips existing).
"""

import hashlib, json, re, sys, time
from pathlib import Path

import chromadb
import pdfplumber
import requests

# ── CONFIG ────────────────────────────────────────────────────────────────────
CORPUS_DIR  = Path("corpus_harvest/tier1_badgr")
CHROMA_DIR  = Path("rag_db")
COLLECTION  = "badgr_corpus"
OLLAMA_URL  = "http://localhost:11434"
EMBED_MODEL = "nomic-embed-text"
CHUNK_SIZE  = 600    # tokens (approx chars ÷ 4)
CHUNK_OVER  = 80     # overlap
# ─────────────────────────────────────────────────────────────────────────────

SUPPORTED = {'.txt', '.md', '.pdf', '.csv', '.json', '.html', '.py', '.sh', '.yaml', '.yml'}


# ── Extraction ────────────────────────────────────────────────────────────────

def extract_text(path: Path) -> str:
    ext = path.suffix.lower()
    try:
        if ext == '.pdf':
            with pdfplumber.open(path) as pdf:
                return '\n'.join(p.extract_text() or '' for p in pdf.pages)
        elif ext in {'.txt', '.md', '.csv', '.py', '.sh', '.yaml', '.yml', '.html'}:
            return path.read_text(errors='ignore')
        elif ext == '.json':
            raw = path.read_text(errors='ignore')
            # Flatten JSON to readable text
            try:
                obj = json.loads(raw)
                return json.dumps(obj, indent=2)
            except Exception:
                return raw
    except Exception as e:
        return ''
    return ''


# ── Chunking ──────────────────────────────────────────────────────────────────

def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVER) -> list[str]:
    words = text.split()
    if not words:
        return []
    chunks = []
    i = 0
    while i < len(words):
        chunk = ' '.join(words[i:i + size])
        if chunk.strip():
            chunks.append(chunk.strip())
        i += size - overlap
    return chunks


# ── Embedding ─────────────────────────────────────────────────────────────────

def embed(texts: list[str]) -> list[list[float]]:
    embeddings = []
    for text in texts:
        # Truncate oversized chunks to prevent Ollama 500s
        safe = text[:2000] if len(text) > 2000 else text
        for attempt in range(3):
            try:
                r = requests.post(
                    f"{OLLAMA_URL}/api/embeddings",
                    json={"model": EMBED_MODEL, "prompt": safe},
                    timeout=60,
                )
                r.raise_for_status()
                embeddings.append(r.json()["embedding"])
                break
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(2)
    return embeddings


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Verify embed model
    try:
        test = embed(["test"])
        print(f"Embed model OK — dim={len(test[0])}")
    except Exception as e:
        print(f"ERROR: nomic-embed-text not ready: {e}")
        print("Run: ollama pull nomic-embed-text")
        sys.exit(1)

    # ChromaDB
    CHROMA_DIR.mkdir(exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    col = client.get_or_create_collection(
        name=COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )
    existing_ids = set(col.get()["ids"])
    print(f"ChromaDB collection '{COLLECTION}': {len(existing_ids)} existing chunks")

    files = sorted(f for f in CORPUS_DIR.iterdir() if f.is_file() and f.suffix.lower() in SUPPORTED)
    print(f"Files to ingest: {len(files)}\n")

    total_chunks = 0
    skipped = 0
    errors = 0

    for i, fpath in enumerate(files, 1):
        file_id = hashlib.sha256(fpath.name.encode()).hexdigest()[:12]

        # Check if already ingested
        if any(eid.startswith(file_id) for eid in existing_ids):
            skipped += 1
            continue

        text = extract_text(fpath)
        if not text or len(text.strip()) < 50:
            errors += 1
            continue

        chunks = chunk_text(text)
        if not chunks:
            continue

        print(f"[{i}/{len(files)}] {fpath.name[:55]:<55} {len(chunks)} chunks", end='', flush=True)

        try:
            embeddings = embed(chunks)
            ids  = [f"{file_id}_{j}" for j in range(len(chunks))]
            metas = [{
                "source": fpath.name,
                "chunk": j,
                "total_chunks": len(chunks),
                "ext": fpath.suffix.lower(),
            } for j in range(len(chunks))]

            col.add(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metas)
            total_chunks += len(chunks)
            print(f"  ✓", flush=True)
        except Exception as e:
            print(f"  ERR: {e}", flush=True)
            errors += 1

    print(f"\n{'─'*60}")
    print(f"  Ingested : {total_chunks} chunks from {len(files)-skipped-errors} files")
    print(f"  Skipped  : {skipped} (already in DB)")
    print(f"  Errors   : {errors}")
    print(f"  DB total : {col.count()} chunks")
    print(f"  Path     : {CHROMA_DIR.resolve()}")


if __name__ == "__main__":
    main()
