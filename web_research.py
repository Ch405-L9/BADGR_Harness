"""Provider-backed web research with explicit provenance and safe failure behavior."""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class ResearchError(RuntimeError):
    """Raised when no configured search provider can produce a result."""


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    snippet: str
    provider: str

    def as_dict(self) -> dict[str, str]:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "provider": self.provider,
        }


def _request_json(url: str, *, headers: dict[str, str], timeout: float) -> dict[str, Any]:
    req = Request(url, headers=headers, method="GET")
    try:
        with urlopen(req, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise ResearchError(f"search provider HTTP {exc.code}") from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise ResearchError(f"search provider request failed: {exc}") from exc
    if not isinstance(payload, dict):
        raise ResearchError("search provider returned a non-object JSON response")
    return payload


def _brave(query: str, count: int, timeout: float) -> list[SearchResult]:
    key = os.getenv("BRAVE_SEARCH_API_KEY", "").strip()
    if not key:
        raise ResearchError("BRAVE_SEARCH_API_KEY is not configured")
    params = urlencode({"q": query, "count": min(count, 20), "safesearch": "moderate", "extra_snippets": "true"})
    payload = _request_json(
        f"https://api.search.brave.com/res/v1/web/search?{params}",
        headers={"Accept": "application/json", "X-Subscription-Token": key},
        timeout=timeout,
    )
    raw = payload.get("web", {}).get("results", [])
    return [
        SearchResult(
            title=str(item.get("title", "")).strip(),
            url=str(item.get("url", "")).strip(),
            snippet=str(item.get("description", "")).strip(),
            provider="brave",
        )
        for item in raw
        if item.get("url")
    ][:count]


def _serpapi(query: str, count: int, timeout: float) -> list[SearchResult]:
    key = os.getenv("SERPAPI_API_KEY", "").strip()
    if not key:
        raise ResearchError("SERPAPI_API_KEY is not configured")
    params = urlencode({"engine": "google", "q": query, "api_key": key, "output": "json", "num": min(count, 20)})
    payload = _request_json(f"https://serpapi.com/search?{params}", headers={"Accept": "application/json"}, timeout=timeout)
    if payload.get("error"):
        raise ResearchError(str(payload["error"]))
    return [
        SearchResult(
            title=str(item.get("title", "")).strip(),
            url=str(item.get("link", "")).strip(),
            snippet=str(item.get("snippet", "")).strip(),
            provider="serpapi",
        )
        for item in payload.get("organic_results", [])
        if item.get("link")
    ][:count]


def _clean_goal(goal: str) -> str:
    text = re.sub(r"\s+", " ", goal or "").strip()
    text = re.sub(r"^(?:use )?(?:live )?(?:web )?research to (?:answer|find)\s*:?\s*", "", text, flags=re.I)
    text = re.split(r"\b(?:prefer an? |give me|return|summarize|answer in)\b", text, maxsplit=1, flags=re.I)[0]
    text = re.sub(r"\s+", " ", text).strip(" .,:;")
    return text or goal.strip()


def _authority_score(result: SearchResult, goal: str) -> int:
    url = result.url.lower()
    score = 0
    if "official" in goal.lower():
        score += 1 if any(domain in url for domain in (".gov", ".edu", "ubuntu.com", "python.org")) else 0
    if any(domain in url for domain in (".gov", ".edu", "ubuntu.com", "python.org")):
        score += 2
    return score


def _three_sentence_summary(query: str, results: list[SearchResult]) -> str:
    def safe_sentence_text(value: str) -> str:
        value = re.sub(r"(\d)\.(\d)", r"\1 point \2", value)
        return value.replace(".", ";").replace("!", ";").replace("?", ";").strip(" ;")

    if not results:
        safe_query = safe_sentence_text(query)
        return f'No search results were returned for "{safe_query}". The claim could not be verified from live web evidence. No source-backed answer is available.'
    safe_query = safe_sentence_text(query)
    excerpts = [
        safe_sentence_text(re.sub(r"\s+", " ", r.snippet).strip())
        for r in results[:2]
        if r.snippet
    ]
    first = excerpts[0] if excerpts else "The leading result did not provide a readable snippet"
    second = excerpts[1] if len(excerpts) > 1 else "No second independent snippet was returned"
    return (
        f'Live search returned {len(results)} source result(s) for "{safe_query}". '
        f"The highest-ranked evidence states: {first}. "
        f"A second result reports: {second}."
    )


def research_goal(goal: str, *, count: int = 5, timeout: float = 15.0) -> dict[str, Any]:
    """Search the web and return an auditable result; never fabricate an answer."""
    query = _clean_goal(goal)
    configured = os.getenv("SEARCH_PROVIDER", "auto").strip().lower()
    providers = {"brave": _brave, "serpapi": _serpapi}.get(configured)
    attempts: list[str] = []
    funcs = [(configured, providers)] if providers else [("brave", _brave), ("serpapi", _serpapi)]
    results: list[SearchResult] = []
    provider_used = ""
    for name, func in funcs:
        if func is None:
            continue
        try:
            results = func(query, count, timeout)
            provider_used = name
            if results:
                break
            attempts.append(f"{name}: empty result set")
        except ResearchError as exc:
            attempts.append(f"{name}: {exc}")
            if configured in {"brave", "serpapi"}:
                break
    if not results:
        raise ResearchError("No live search results available; " + "; ".join(attempts))
    results.sort(key=lambda item: _authority_score(item, goal), reverse=True)
    return {
        "task_type": "research",
        "summary": _three_sentence_summary(query, results),
        "confidence": 0.0,
        "recommended_action": "Review the cited sources before acting; snippets are evidence, not a substitute for reading the source.",
        "needs_clarification": False,
        "clarification_question": None,
        "query": query,
        "provider": provider_used,
        "sources": [result.as_dict() for result in results],
        "source_urls": [result.url for result in results],
        "evidence": [result.snippet for result in results if result.snippet],
        "source_count": len(results),
        "live": True,
    }


researchgoal = research_goal
SearchResultDict = dict[str, str]
