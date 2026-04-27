"""
rag_label.py
Enriches badgr_corpus documents with skill/topic metadata tags using a local Ollama model.
Processes in batches, skips already-tagged docs.
Run with: /home/t0n34781/projects/pro_hunter/.venv/bin/python rag_label.py
"""
import chromadb
import requests
import json
import logging
import time

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

RAG_DB = "/home/t0n34781/projects/badgr_harness/rag_db"
COLLECTION = "badgr_corpus"
OLLAMA_URL = "http://localhost:11434"
MODEL = "mistral:7b"
BATCH_SIZE = 10
DELAY = 2  # seconds between batches to avoid queue buildup

SKILL_TAGS = [
    "ai-ml", "python", "llm", "automation", "devops", "cloud",
    "full-stack", "security", "data-engineering", "nlp",
    "vector-db", "networking", "federal-gov", "documentation"
]

def tag_document(text: str) -> dict:
    prompt = f"""Analyze this technical document excerpt and return ONLY valid JSON.

Fields:
- topic: one short phrase (e.g. "LLM fine-tuning", "Docker CI/CD", "Python automation")
- skill_tags: array of 1-3 tags from this list only: {json.dumps(SKILL_TAGS)}
- relevance: "high" | "medium" | "low" (how useful for AI/tech job search context)

Document excerpt (first 500 chars):
{text[:500]}"""

    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": MODEL, "prompt": prompt, "stream": False, "format": "json"},
            timeout=120
        )
        r.raise_for_status()
        return json.loads(r.json()["response"])
    except Exception as e:
        logger.warning("Tag failed: %s", e)
        return {"topic": "unknown", "skill_tags": [], "relevance": "low"}


def main():
    client = chromadb.PersistentClient(path=RAG_DB)
    col = client.get_collection(COLLECTION)
    total = col.count()
    logger.info("badgr_corpus: %d docs total", total)

    # Get all IDs
    all_ids = col.get(include=[])["ids"]
    to_process = [id_ for id_ in all_ids]

    logger.info("Processing %d docs in batches of %d", len(to_process), BATCH_SIZE)

    tagged = 0
    skipped = 0

    for i in range(0, len(to_process), BATCH_SIZE):
        batch_ids = to_process[i:i + BATCH_SIZE]
        batch = col.get(ids=batch_ids, include=["documents", "metadatas"])

        updates_ids = []
        updates_meta = []

        for doc_id, doc, meta in zip(batch["ids"], batch["documents"], batch["metadatas"]):
            if "topic" in meta:
                skipped += 1
                continue

            tags = tag_document(doc)
            new_meta = {**meta}
            new_meta["topic"] = tags.get("topic", "unknown")
            new_meta["skill_tags"] = "|".join(tags.get("skill_tags", []))
            new_meta["relevance"] = tags.get("relevance", "low")

            updates_ids.append(doc_id)
            updates_meta.append(new_meta)
            tagged += 1

        if updates_ids:
            col.update(ids=updates_ids, metadatas=updates_meta)
            logger.info("Batch %d/%d — tagged %d, skipped %d so far",
                        i // BATCH_SIZE + 1, len(to_process) // BATCH_SIZE + 1,
                        tagged, skipped)

        time.sleep(DELAY)

    logger.info("Done. Tagged: %d | Skipped (already tagged): %d", tagged, skipped)


if __name__ == "__main__":
    main()
