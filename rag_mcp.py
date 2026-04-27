"""
rag_mcp.py
MCP stdio server exposing badgr_harness RAG collections to Claude sessions.

Run: /home/t0n34781/projects/pro_hunter/.venv/bin/python rag_mcp.py
(System python3 has pydantic conflict with chromadb — must use pro_hunter venv.)

Tools:
  query_corpus  — semantic search over badgr_corpus (2087 AI/tech docs)
  query_jobs    — semantic search over job_opportunities (pro_hunter feed)
  rag_stats     — collection counts and last-updated info
  rag_upsert    — add or update a document in a collection
"""
import asyncio
import json
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("rag_mcp")

RAG_DB = Path(__file__).resolve().parent / "rag_db"

TOOLS = [
    {
        "name": "query_corpus",
        "description": (
            "Semantic search over badgr_corpus — 2087 AI/tech reference documents "
            "(papers, guides, validated repos). Use to get background context on a "
            "technology, pattern, or topic before generating or scoring content."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Natural language query"},
                "k": {"type": "integer", "description": "Number of results (default 4)", "default": 4},
                "topic_filter": {
                    "type": "string",
                    "description": "Optional topic tag filter (e.g. 'llm', 'python', 'devops') — only applies if corpus has been labeled by rag_label.py",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "query_jobs",
        "description": (
            "Semantic search over job_opportunities — scored job postings from pro_hunter pipeline. "
            "Filter by min fit score or skill profile."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Natural language query"},
                "k": {"type": "integer", "description": "Number of results (default 5)", "default": 5},
                "min_score": {"type": "number", "description": "Minimum fit_score filter (0-100)", "default": 0},
                "skill_profile": {"type": "string", "description": "Filter by skill profile key (e.g. 'ai-sw-engineer')"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "rag_stats",
        "description": "Return document counts and collection info for all RAG collections.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "rag_upsert",
        "description": "Add or update a document in a RAG collection.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "collection": {"type": "string", "description": "Collection name: 'badgr_corpus' or 'job_opportunities'"},
                "doc_id": {"type": "string", "description": "Unique document ID"},
                "text": {"type": "string", "description": "Document text to embed and store"},
                "metadata": {"type": "object", "description": "Key-value metadata (string values only)"},
            },
            "required": ["collection", "doc_id", "text"],
        },
    },
]


def _get_client():
    import chromadb
    return chromadb.PersistentClient(path=str(RAG_DB))


async def handle_query_corpus(args: dict) -> dict:
    try:
        client = _get_client()
        col = client.get_collection("badgr_corpus")
        total = col.count()
        k = min(args.get("k", 4), total)
        if k == 0:
            return {"results": [], "count": 0, "total_docs": total}

        where = None
        topic = args.get("topic_filter")
        if topic:
            where = {"topic": {"$eq": topic}}

        query_kwargs = {"query_texts": [args["query"]], "n_results": k}
        if where:
            query_kwargs["where"] = where

        results = col.query(**query_kwargs)
        hits = []
        for doc, meta, dist in zip(
            results["documents"][0], results["metadatas"][0], results["distances"][0]
        ):
            hits.append({
                "source": meta.get("source", ""),
                "topic": meta.get("topic", ""),
                "skill_tags": meta.get("skill_tags", ""),
                "relevance": meta.get("relevance", ""),
                "chunk": meta.get("chunk", ""),
                "distance": round(dist, 4),
                "excerpt": doc[:400],
            })
        return {"results": hits, "count": len(hits), "total_docs": total}
    except Exception as e:
        return {"error": f"query_corpus failed: {e}"}


async def handle_query_jobs(args: dict) -> dict:
    try:
        client = _get_client()
        col = client.get_collection("job_opportunities")
        total = col.count()
        k = min(args.get("k", 5), max(total, 1))
        if total == 0:
            return {"results": [], "count": 0, "total_docs": 0}

        where = None
        profile = args.get("skill_profile")
        if profile:
            where = {"skill_profile": {"$eq": profile}}

        query_kwargs = {"query_texts": [args["query"]], "n_results": k}
        if where:
            query_kwargs["where"] = where

        results = col.query(**query_kwargs)
        min_score = args.get("min_score", 0)
        hits = []
        for doc, meta, dist in zip(
            results["documents"][0], results["metadatas"][0], results["distances"][0]
        ):
            fit_score = float(meta.get("fit_score", 0) or 0)
            if fit_score < min_score:
                continue
            hits.append({
                "job_id": meta.get("job_id", ""),
                "job_title": meta.get("job_title", ""),
                "company": meta.get("company", ""),
                "source_site": meta.get("source_site", ""),
                "location_type": meta.get("location_type", ""),
                "tech_stack": meta.get("tech_stack", ""),
                "fit_score": fit_score,
                "skill_profile": meta.get("skill_profile", ""),
                "distance": round(dist, 4),
                "excerpt": doc[:300],
            })
        return {"results": hits, "count": len(hits), "total_docs": total}
    except Exception as e:
        return {"error": f"query_jobs failed: {e}"}


async def handle_rag_stats(args: dict) -> dict:
    try:
        client = _get_client()
        stats = {}
        for col in client.list_collections():
            stats[col.name] = {"count": col.count()}
        return {"collections": stats, "rag_db": str(RAG_DB)}
    except Exception as e:
        return {"error": f"rag_stats failed: {e}"}


async def handle_rag_upsert(args: dict) -> dict:
    try:
        client = _get_client()
        col_name = args["collection"]
        try:
            col = client.get_collection(col_name)
        except Exception:
            col = client.create_collection(col_name)

        metadata = {k: str(v) for k, v in (args.get("metadata") or {}).items()}
        col.upsert(
            ids=[args["doc_id"]],
            documents=[args["text"]],
            metadatas=[metadata] if metadata else None,
        )
        return {"status": "ok", "collection": col_name, "doc_id": args["doc_id"], "total": col.count()}
    except Exception as e:
        return {"error": f"rag_upsert failed: {e}"}


async def handle_tool(name: str, args: dict) -> dict:
    if name == "query_corpus":
        return await handle_query_corpus(args)
    elif name == "query_jobs":
        return await handle_query_jobs(args)
    elif name == "rag_stats":
        return await handle_rag_stats(args)
    elif name == "rag_upsert":
        return await handle_rag_upsert(args)
    return {"error": f"Unknown tool: {name}"}


async def main():
    logger.info("RAG MCP server starting on stdio")
    while True:
        line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
        if not line:
            break
        try:
            req = json.loads(line.strip())
        except json.JSONDecodeError:
            continue

        req_id = req.get("id")
        method = req.get("method", "")

        if method == "initialize":
            resp = {
                "jsonrpc": "2.0", "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "rag-badgr", "version": "1.0.0"},
                },
            }
        elif method == "tools/list":
            resp = {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
        elif method == "tools/call":
            params = req.get("params", {})
            tool_name = params.get("name", "")
            tool_args = params.get("arguments", {})
            try:
                result = await handle_tool(tool_name, tool_args)
                resp = {
                    "jsonrpc": "2.0", "id": req_id,
                    "result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]},
                }
            except Exception as e:
                resp = {
                    "jsonrpc": "2.0", "id": req_id,
                    "result": {"content": [{"type": "text", "text": f"Error: {e}"}], "isError": True},
                }
        else:
            resp = {"jsonrpc": "2.0", "id": req_id, "result": {}}

        print(json.dumps(resp), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
