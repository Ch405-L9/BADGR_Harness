from __future__ import annotations

import json
from unittest.mock import patch

import pytest

import web_research
from router import classify_task
from schemas.task_schema import TaskType


def test_research_language_routes_before_classification():
    assert classify_task("Use live web research to classify this claim and cite sources") == TaskType.RESEARCH


def test_brave_response_is_normalized_and_cited(monkeypatch):
    monkeypatch.setenv("BRAVE_SEARCH_API_KEY", "test-key")
    monkeypatch.delenv("SERPAPI_API_KEY", raising=False)
    payload = {"web": {"results": [{"title": "Official Ubuntu", "url": "https://ubuntu.com/blog/python", "description": "Python 3.12 is available."}]}}

    with patch.object(web_research, "_request_json", return_value=payload):
        result = web_research.research_goal("Is Python available? Prefer an official source, give me the URL")

    assert result["task_type"] == "research"
    assert result["provider"] == "brave"
    assert result["sources"] == [{
        "title": "Official Ubuntu",
        "url": "https://ubuntu.com/blog/python",
        "snippet": "Python 3.12 is available.",
        "provider": "brave",
    }]
    assert result["source_count"] == 1
    assert result["live"] is True
    assert result["summary"].count(".") >= 3


def test_serpapi_fallback_is_used(monkeypatch):
    monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)
    monkeypatch.setenv("SERPAPI_API_KEY", "test-key")
    payload = {"organic_results": [{"title": "Python", "link": "https://python.org", "snippet": "Official Python site."}]}

    with patch.object(web_research, "_request_json", return_value=payload):
        result = web_research.research_goal("research Python official source")

    assert result["provider"] == "serpapi"
    assert result["sources"][0]["url"] == "https://python.org"


def test_no_provider_fails_without_fabricating(monkeypatch):
    monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)
    monkeypatch.delenv("SERPAPI_API_KEY", raising=False)
    with pytest.raises(web_research.ResearchError, match="No live search results"):
        web_research.research_goal("research a current fact")


def test_search_result_serialization_is_json_safe():
    item = web_research.SearchResult("Title", "https://example.com", "Snippet", "brave")
    assert json.loads(json.dumps(item.as_dict()))["provider"] == "brave"


def test_user_formatter_prefers_official_source():
    answer = web_research.format_user_answer(
        "Is Python available?",
        [
            {
                "title": "Blog",
                "url": "https://example.com",
                "snippet": "A blog claim.",
            },
            {
                "title": "Ubuntu docs",
                "url": "https://ubuntu.com/docs",
                "snippet": "Python 3.12 is available.",
            },
        ],
    )

    assert 'According to "Ubuntu docs",' in answer
    assert "Python 3.12 is available." in answer
    assert answer.endswith("Source: https://ubuntu.com/docs")
    assert "Live search returned" not in answer
    assert "The top official source" not in answer


def test_ubuntu_python_benchmark_answer_is_exactly_three_lines():
    answer = web_research.format_user_answer(
        (
            "Use live web research to answer: Is Python 3.12 currently "
            "available for Ubuntu 24.04 LTS?"
        ),
        [
            {
                "title": "Available Python versions - Ubuntu for Developers",
                "url": (
                    "https://ubuntu.com/developers/docs/reference/"
                    "availability/python/"
                ),
                "snippet": "Python versions available ... 24.04 LTS ...",
            }
        ],
    )

    assert answer.startswith("Yes, Python 3.12")
    assert "ubuntu.com/developers/docs/reference/availability/python/" in answer
    assert answer.count("\n") == 2
    assert "..." not in answer
    assert "The top official source" not in answer
    assert "[https://" not in answer
