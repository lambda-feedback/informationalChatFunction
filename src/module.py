import time
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from lf_toolkit.chat import ChatRequest, ChatResponse, Message
from lf_toolkit.shared.mued_api_v0_1_0 import Role

from src.agent.context import parse_json_to_prompt
from src.agent.agent import invoke_base_agent


def chat_module(request: ChatRequest) -> ChatResponse:
    """
    Main entry point — receives a ChatRequest and returns a ChatResponse.

    The ChatRequest contains:
    - `messages`: conversation history; the last message is the current student input.
    - `conversationId`: unique session identifier.
    - `user`: optional user info (preference, task progress).
    - `context`: optional educational context (question details, prior conversation summary).

    Edit src/agent/prompts.py to change the chatbot's behaviour.
    Edit src/agent/agent.py to change the agent logic (summarisation threshold, LLM provider, etc.).
    """

    conversation_id = request.conversationId

    context = request.context or {}
    task_progress = (request.user.taskProgress or {}) if request.user else {}

    summary = context.get("summary", "") or ""

    conversationalStyle = ""
    if request.user and request.user.preference:
        conversationalStyle = request.user.preference.model_dump().get("conversationalStyle", "") or ""

    messages = _to_langchain_messages(request.messages)

    try:
        context_prompt = parse_json_to_prompt(context, task_progress)
    except Exception as e:
        print("ERROR:: ", e)
        raise Exception("Internal Error: The context prompt could not be parsed.")

    start_time = time.time()
    chatbot_response = invoke_base_agent(
        messages=messages,
        summary=summary,
        conversationalStyle=conversationalStyle,
        context_prompt=context_prompt,
        session_id=conversation_id,
    )
    end_time = time.time()

    return ChatResponse(
        output=Message(role=Role.ASSISTANT, content=chatbot_response["output"]),
        metadata={
            "summary": chatbot_response["summary"],
            "conversationalStyle": chatbot_response["conversationalStyle"],
            "processingTimeMs": round((end_time - start_time) * 1000),
        },
    )


def _to_langchain_messages(messages):
    result = []
    for m in messages:
        role = str(m.role).upper()
        if role == "USER":
            result.append(HumanMessage(content=m.content))
        elif role == "ASSISTANT":
            result.append(AIMessage(content=m.content))
        elif role == "SYSTEM":
            result.append(SystemMessage(content=m.content))
    return result
