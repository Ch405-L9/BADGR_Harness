"""
web_ops_mcp.py
MCP stdio server exposing web operations to Claude in badgr_harness sessions.

Run: /home/t0n34781/projects/pro_hunter/.venv/bin/python web_ops_mcp.py

Tools:
  web_fetch   — fetch a URL, return cleaned text
  web_search  — DuckDuckGo search, return title+url+snippet list
  web_extract — fetch + BeautifulSoup full-text extract (strips nav/ads)
"""
import asyncio
import json
import sys
import logging
import re
from pathlib import Path

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("web_ops_mcp")

TOOLS = [
    {
        "name": "web_fetch",
        "description": "Fetch a URL and return the raw text content (HTML stripped). Fast, no JS rendering.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to fetch"},
                "max_chars": {"type": "integer", "description": "Max chars to return (default 6000)", "default": 6000},
                "timeout": {"type": "integer", "description": "Request timeout in seconds (default 15)", "default": 15},
            },
            "required": ["url"],
        },
    },
    {
        "name": "web_search",
        "description": "DuckDuckGo search. Returns list of {title, url, snippet}. No API key needed.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "description": "Max results (default 5, max 20)", "default": 5},
                "region": {"type": "string", "description": "DDG region code e.g. us-en (default us-en)", "default": "us-en"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "web_extract",
        "description": "Fetch a URL with Playwright (JS rendering) and extract clean article text. Slower than web_fetch but works on SPAs.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to fetch and extract"},
                "max_chars": {"type": "integer", "description": "Max chars to return (default 8000)", "default": 8000},
                "wait_ms": {"type": "integer", "description": "Wait ms after page load for JS (default 1500)", "default": 1500},
            },
            "required": ["url"],
        },
    },
]


def _strip_html(html: str) -> str:
    text = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&[a-z]+;", "", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


async def handle_web_fetch(args: dict) -> dict:
    import httpx
    url = args["url"]
    max_chars = args.get("max_chars", 6000)
    timeout = args.get("timeout", 15)
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
    }
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            text = _strip_html(resp.text)
            return {
                "url": str(resp.url),
                "status": resp.status_code,
                "chars": len(text),
                "content": text[:max_chars],
                "truncated": len(text) > max_chars,
            }
    except Exception as e:
        return {"error": str(e), "url": url}


async def handle_web_search(args: dict) -> dict:
    from duckduckgo_search import DDGS
    query = args["query"]
    max_results = min(args.get("max_results", 5), 20)
    region = args.get("region", "us-en")
    try:
        results = []
        with DDGS() as ddg:
            for r in ddg.text(query, region=region, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", "")[:300],
                })
        return {"query": query, "results": results, "count": len(results)}
    except Exception as e:
        return {"error": str(e), "query": query}


async def handle_web_extract(args: dict) -> dict:
    from playwright.async_api import async_playwright
    from bs4 import BeautifulSoup
    url = args["url"]
    max_chars = args.get("max_chars", 8000)
    wait_ms = args.get("wait_ms", 1500)
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(wait_ms)
            html = await page.content()
            await browser.close()
        soup = BeautifulSoup(html, "lxml")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        text = re.sub(r"\s{2,}", " ", text).strip()
        return {
            "url": url,
            "chars": len(text),
            "content": text[:max_chars],
            "truncated": len(text) > max_chars,
        }
    except Exception as e:
        return {"error": str(e), "url": url}


async def handle_tool(name: str, args: dict) -> dict:
    if name == "web_fetch":
        return await handle_web_fetch(args)
    elif name == "web_search":
        return await handle_web_search(args)
    elif name == "web_extract":
        return await handle_web_extract(args)
    return {"error": f"Unknown tool: {name}"}


async def main():
    logger.info("Web Ops MCP server starting on stdio")
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
                    "serverInfo": {"name": "web-ops", "version": "1.0.0"},
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
