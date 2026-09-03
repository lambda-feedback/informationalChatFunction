"""
Tests that the agent reports intermediate feedback via lf_toolkit's
report_progress() around each LLM stage, and stays a no-op when
EVAL_PROGRESS_URL isn't set (the case for every other test in this repo).

Mirrors LLM_Caller/evaluation_function/progress_test.py. The chat LLM and the
summarisation LLM are replaced with a fake streaming stub so no network call is
made; only the progress side channel is exercised.
"""
import json
import os
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock, patch

# src.agent.agent instantiates BaseAgent() (and an OpenRouter ChatOpenAI) at
# import time — give it dummy creds so importing the module never touches config.
os.environ.setdefault("OPENROUTER_API_KEY", "test")
os.environ.setdefault("OPENROUTER_MODEL", "google/gemini-2.5-flash")
os.environ.setdefault("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

from lf_toolkit.chat import ChatRequest  # noqa: E402
from src.agent import agent as agent_module  # noqa: E402
from src.module import chat_module  # noqa: E402

EXAMPLE_INPUTS_DIR = "tests/example_inputs"


def _wait_for_progress_executor():
    """Block until all currently-submitted background progress posts finish."""
    import lf_toolkit.evaluation.progress as progress_module

    progress_module._executor.shutdown(wait=True)
    progress_module._executor = ThreadPoolExecutor(
        max_workers=1, thread_name_prefix="lf-progress"
    )


class _FakeChunk:
    """Stands in for a LangChain message / AIMessageChunk."""

    def __init__(self, content=None, reasoning=None):
        self.content = content or ""
        self.additional_kwargs = {"reasoning": reasoning} if reasoning else {}


class _FakeStreamingLLM:
    """
    .stream() yields any reasoning pieces first, then a single content chunk
    (same shape as LLM_Caller's _mock_stream). .invoke() returns the content
    chunk directly (used by the summarisation node).
    """

    def __init__(self, content="Here is an answer.", reasoning_parts=None):
        self.content = content
        self.reasoning_parts = reasoning_parts or []

    def stream(self, messages):
        for piece in self.reasoning_parts:
            yield _FakeChunk(reasoning=piece)
        yield _FakeChunk(content=self.content)

    def invoke(self, messages):
        return _FakeChunk(content=self.content)


def _patch_llms(chat_llm, summarisation_llm=None):
    """Swap the module-level agent singleton's LLMs for the test doubles."""
    summarisation_llm = summarisation_llm or _FakeStreamingLLM(content="A summary.")
    return (
        patch.object(agent_module.agent, "llm", chat_llm),
        patch.object(agent_module.agent, "summarisation_llm", summarisation_llm),
    )


def _run_chat(request: ChatRequest, chat_llm, summarisation_llm=None):
    chat_patch, summ_patch = _patch_llms(chat_llm, summarisation_llm)
    with chat_patch, summ_patch:
        chat_module(request)
    _wait_for_progress_executor()


def _simple_request():
    return ChatRequest.model_validate(
        {"messages": [{"role": "USER", "content": "Hello, World"}], "conversationId": "progress-test"}
    )


class TestChatModuleProgress(unittest.TestCase):

    def test_no_progress_reported_when_env_var_unset(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("EVAL_PROGRESS_URL", None)
            with patch("lf_toolkit.evaluation.progress.requests.post") as mock_post:
                _run_chat(_simple_request(), _FakeStreamingLLM())

        mock_post.assert_not_called()

    def test_reports_stage_progress_for_a_short_conversation(self):
        with patch.dict(os.environ, {"EVAL_PROGRESS_URL": "http://127.0.0.1:9999"}):
            with patch("lf_toolkit.evaluation.progress.requests.post") as mock_post:
                mock_post.return_value = Mock(ok=True)
                _run_chat(_simple_request(), _FakeStreamingLLM())

        messages = [call.kwargs["json"]["message"] for call in mock_post.call_args_list]
        self.assertEqual(
            messages,
            ["Reading your message...", "Generating response...", "Response ready."],
        )

    def test_reasoning_lines_reported_between_checkpoints(self):
        chat_llm = _FakeStreamingLLM(reasoning_parts=["line one\nline two\n"])

        with patch.dict(os.environ, {"EVAL_PROGRESS_URL": "http://127.0.0.1:9999"}):
            with patch("lf_toolkit.evaluation.progress.requests.post") as mock_post:
                mock_post.return_value = Mock(ok=True)
                _run_chat(_simple_request(), chat_llm)

        calls = mock_post.call_args_list
        self.assertEqual(
            [call.kwargs["json"]["message"] for call in calls],
            [
                "Reading your message...",
                "Generating response...",
                "response reasoning",
                "response reasoning",
                "Response ready.",
            ],
        )
        self.assertEqual(calls[2].kwargs["json"]["data"], {"text": "line one"})
        self.assertEqual(calls[3].kwargs["json"]["data"], {"text": "line two"})

    def test_reasoning_chunks_coalesce_until_newline_and_flush_trailing_text(self):
        chat_llm = _FakeStreamingLLM(
            reasoning_parts=["Wor", "d1 ", "word2\n", "trailing text with no newline"]
        )

        with patch.dict(os.environ, {"EVAL_PROGRESS_URL": "http://127.0.0.1:9999"}):
            with patch("lf_toolkit.evaluation.progress.requests.post") as mock_post:
                mock_post.return_value = Mock(ok=True)
                _run_chat(_simple_request(), chat_llm)

        reasoning_events = [
            call.kwargs["json"]["data"]["text"]
            for call in mock_post.call_args_list
            if call.kwargs["json"]["message"] == "response reasoning"
        ]
        self.assertEqual(reasoning_events, ["Word1 word2", "trailing text with no newline"])

    def test_reports_summarisation_progress_when_history_is_long(self):
        with open(os.path.join(EXAMPLE_INPUTS_DIR, "example_input_3.json")) as f:
            request = ChatRequest.model_validate(json.load(f))  # 13 messages -> triggers summarisation

        with patch.dict(os.environ, {"EVAL_PROGRESS_URL": "http://127.0.0.1:9999"}):
            with patch("lf_toolkit.evaluation.progress.requests.post") as mock_post:
                mock_post.return_value = Mock(ok=True)
                _run_chat(request, _FakeStreamingLLM())

        messages = [call.kwargs["json"]["message"] for call in mock_post.call_args_list]
        self.assertEqual(
            messages,
            [
                "Reading your message...",
                "Summarising the conversation so far...",
                "Analysing your conversational style...",
                "Generating response...",
                "Response ready.",
            ],
        )


if __name__ == "__main__":
    unittest.main()
