import importlib

modules = {
    "config": "core",
    "router": "core",
    "validator": "core",
    "orchestrator": "core",
    "schemas.task_schema": "core",
    "schemas.log_schema": "core",
    "state.state_manager": "core",
    "api": "optional-api",
    "rag_ingest": "optional-rag",
    "rag_query": "optional-rag",
    "rag_mcp": "optional-mcp",
    "web_ops_mcp": "optional-mcp",
    "RAG_corpus_crawl_sba": "optional-rag",
}
for name, group in modules.items():
    try:
        importlib.import_module(name)
        print(f"PASS\t{group}\t{name}")
    except Exception as exc:
        print(f"FAIL\t{group}\t{name}\t{type(exc).__name__}: {exc}")

for name in ["pydantic", "yaml", "dotenv", "pytest", "fastapi", "uvicorn", "httpx", "chromadb", "pdfplumber", "requests"]:
    try:
        importlib.import_module(name)
        print(f"PKG\tPASS\t{name}")
    except Exception as exc:
        print(f"PKG\tFAIL\t{name}\t{type(exc).__name__}: {exc}")
