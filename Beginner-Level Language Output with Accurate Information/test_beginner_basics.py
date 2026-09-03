from __future__ import annotations

from router import classify_task
from schemas.task_schema import TaskType
from web_research import format_user_answer


def test_beginner_math_question_uses_research_path() -> None:
    assert classify_task("What is 12 times 8?") == TaskType.RESEARCH


def test_beginner_writing_question_uses_research_path() -> None:
    assert classify_task("What is a clear topic sentence?") == TaskType.RESEARCH


def test_beginner_tech_question_uses_research_path() -> None:
    assert classify_task("Can a browser read a JSON file?") == TaskType.RESEARCH


def test_research_answer_keeps_source_and_uses_short_plain_format() -> None:
    answer = format_user_answer(
        "What is a JSON file?",
        [{
            "title": "MDN JSON guide",
            "url": "https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Scripting/JSON",
            "snippet": "JSON is a text format for storing and transporting data.",
        }],
    )
    assert "Source: https://developer.mozilla.org" in answer
    assert "According to" in answer
    assert "JSON is a text format" in answer
    assert "```" not in answer


def test_research_answer_does_not_claim_success_without_evidence() -> None:
    answer = format_user_answer(
        "What is a fact?",
        [{"title": "Empty result", "url": "https://example.com", "snippet": ""}],
    )
    assert "not contain enough detail" in answer
    assert "Source: https://example.com" in answer


def test_code_and_planning_questions_keep_their_specialized_routes() -> None:
    assert classify_task("How do I fix this Python bug?") == TaskType.CODE
    assert classify_task("How do I plan a small app?") == TaskType.PLANNING


def test_non_question_general_prompt_stays_general() -> None:
    assert classify_task("Give me a friendly greeting") == TaskType.GENERAL


def test_beginner_prompt_is_present_in_worker_prompt() -> None:
    from pathlib import Path

    text = (Path(__file__).resolve().parents[1] / "prompts" / "worker_system.txt").read_text()
    assert "beginner-level language" in text
    assert "Do not copy long passages" in text
    assert "invent facts" in text


def test_math_result_is_not_silently_presented_as_live_evidence() -> None:
    # The harness must not turn an empty source set into a confident factual answer.
    assert format_user_answer("What is 2 + 2?", []) == "No source-backed answer was found for this request."


def test_writing_result_is_beginner_readable() -> None:
    answer = format_user_answer(
        "What is a topic sentence?",
        [{"title": "Writing guide", "url": "https://example.edu/writing", "snippet": "A topic sentence tells the reader the main idea of a paragraph."}],
    )
    assert answer.count("\n") == 1
    assert len(answer.split()) < 35


def test_technology_result_has_provenance() -> None:
    answer = format_user_answer(
        "Can a browser read a JSON file?",
        [{"title": "Web API reference", "url": "https://developer.mozilla.org/en-US/docs/Web/API", "snippet": "Web APIs let web pages use browser features."}],
    )
    assert "Source: https://developer.mozilla.org" in answer
    assert "Web APIs" in answer


def test_broad_question_routing_is_case_and_whitespace_tolerant() -> None:
    assert classify_task("  IS the Earth round? ") == TaskType.RESEARCH
    assert classify_task("What\nare simple variables?") == TaskType.RESEARCH


def test_explicit_source_request_still_wins() -> None:
    assert classify_task("Find sources for a beginner explanation of databases") == TaskType.RESEARCH


def test_factual_question_without_question_mark_is_not_overrouted() -> None:
    assert classify_task("Explain databases for a beginner") == TaskType.GENERAL


def test_math_writing_and_tech_are_distinctly_supported() -> None:
    goals = ["What is a prime number?", "What is a paragraph?", "What is an operating system?"]
    assert all(classify_task(goal) == TaskType.RESEARCH for goal in goals)


def test_plain_answer_does_not_include_internal_provider_metadata() -> None:
    answer = format_user_answer(
        "What is a browser?",
        [{"title": "Reference", "url": "https://example.org", "snippet": "A browser displays web pages."}],
    )
    assert "provider" not in answer.lower()
    assert "ranking" not in answer.lower()


def test_source_url_is_plain_text() -> None:
    answer = format_user_answer(
        "What is a test?",
        [{"title": "Reference", "url": "https://example.org/test", "snippet": "A test checks whether software behaves as expected."}],
    )
    assert "[" not in answer and "](" not in answer
    assert "Source: https://example.org/test" in answer


def test_no_long_raw_snippet_ellipsis_leaks() -> None:
    answer = format_user_answer(
        "What is a fact?",
        [{"title": "Reference", "url": "https://example.org/fact", "snippet": "A fact is supported by evidence... more text"}],
    )
    assert "..." not in answer


# These are intentionally small beginner checks. They verify routing and output
# contracts without pretending that a unit test can prove universal factual truth.
MATH_BEGINNER_TEST = "What is 12 times 8?"
WRITING_BEGINNER_TEST = "What is a clear topic sentence?"
TECH_BEGINNER_TEST = "Can a browser read a JSON file?"
