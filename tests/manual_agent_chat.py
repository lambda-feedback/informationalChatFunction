"""
Interactive multi-turn testbench of the agent's performance.

Keeps the conversation history across turns and feeds the returned metadata
(summary, conversationalStyle) back into the next request, the way the platform
does — so summarisation and style analysis behave as they do in production.

Usage:
    python tests/manual_agent_chat.py                    # defaults to example_input_3.json
    python tests/manual_agent_chat.py 1                  # use example_input_1.json
    python tests/manual_agent_chat.py 1 --keep-seed      # keep the file's canned messages as history

Commands (at the prompt):
    exit / quit     end the session
    /state          show the current summary and conversational style
    /system         show the system prompt that would be sent for the next turn
    /history        show the conversation history
    /reset          clear history, summary and style
"""

import json
import sys
import time

try:  # line editing and history at the input() prompt
    import readline  # noqa: F401
except ImportError:
    pass

from lf_toolkit.chat import ChatRequest
from src.module import chat_module

PATH = "tests/example_inputs/"
SUMMARISE_AFTER = 11  # mirrors BaseAgent.max_messages_to_summarize


def build_request(payload: dict, messages: list, summary: str, style: str) -> ChatRequest:
    """Assemble the next ChatRequest from the running conversation state."""
    payload = json.loads(json.dumps(payload))  # deep copy, leave the file's data untouched
    payload["messages"] = messages
    payload.setdefault("context", {})["summary"] = summary
    payload.setdefault("user", {}).setdefault("preference", {})["conversationalStyle"] = style
    return ChatRequest.model_validate(payload)


def show_system_prompt(payload: dict, messages: list, summary: str, style: str) -> None:
    """Render the system prompt for the next turn without calling the LLM."""
    from unittest.mock import patch

    captured = {}

    class CaptureLLM:
        def invoke(self, msgs):
            captured["prompt"] = msgs[0].content
            raise SystemExit  # stop before the network call

    with patch("src.agent.llm_factory.OpenAILLMs.get_llm", return_value=CaptureLLM()):
        from src.agent.agent import BaseAgent

        try:
            BaseAgent().call_model(
                {"messages": [], "summary": summary, "conversationalStyle": style},
                {"configurable": {"context_prompt": _context_prompt(payload)}},
            )
        except SystemExit:
            pass
    print(captured.get("prompt", "(no prompt captured)"))


def _context_prompt(payload: dict) -> str:
    from src.agent.context import parse_json_to_prompt

    return parse_json_to_prompt(
        payload.get("context") or {},
        (payload.get("user") or {}).get("taskProgress") or {},
    )


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    keep_seed = "--keep-seed" in sys.argv
    index = args[0] if args else "1"
    input_file = f"{PATH}example_input_{index}.json"

    with open(input_file) as f:
        payload = json.load(f)

    seed = payload.get("messages", []) if keep_seed else []
    messages = list(seed)
    summary = (payload.get("context") or {}).get("summary", "") or ""
    style = ((payload.get("user") or {}).get("preference") or {}).get("conversationalStyle", "") or ""

    print(f"Loaded {input_file}"
          f"{f' with {len(seed)} seeded messages' if seed else ' (fresh history)'}")
    print("Type your message, or 'exit' to quit. '/system' shows the assembled system prompt.\n")

    while True:
        try:
            user_input = input("you > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye")
            return

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            print("bye")
            return
        if user_input == "/state":
            print(f"\n[summary]\n{summary or '(empty)'}\n\n[style]\n{style or '(empty)'}\n")
            continue
        if user_input == "/system":
            show_system_prompt(payload, messages, summary, style)
            continue
        if user_input == "/history":
            for m in messages:
                print(f"  {m['role']:<9} {m['content'][:100]}")
            print()
            continue
        if user_input == "/reset":
            messages, summary, style = list(seed), "", ""
            print("history, summary and style cleared\n")
            continue

        messages.append({"role": "USER", "content": user_input})

        # The agent summarises once the history passes the threshold; flag it so the
        # effect on the next turn's system prompt is visible.
        if len(messages) > SUMMARISE_AFTER:
            print(f"[{len(messages)} messages — summarisation will trigger this turn]")

        try:
            request = build_request(payload, messages, summary, style)
            start = time.time()
            response = chat_module(request)
        except Exception as e:
            messages.pop()  # don't leave a turn half-applied
            print(f"[error] {type(e).__name__}: {e}\n")
            continue

        reply = response.output.content
        print(f"\nbot > {reply}\n")

        messages.append({"role": "ASSISTANT", "content": reply})

        metadata = response.metadata or {}
        new_summary = metadata.get("summary", "") or ""
        new_style = metadata.get("conversationalStyle", "") or ""
        if new_summary != summary:
            print("[summary updated — '/state' to view]")
            # history was trimmed server-side; keep only what the summary doesn't cover
            messages = messages[-3:]
        if new_style != style:
            print("[conversational style updated — '/state' to view]")
        summary, style = new_summary, new_style

        print(f"[{round((time.time() - start) * 1000)} ms, {len(messages)} messages in history]\n")


if __name__ == "__main__":
    main()
