from src.agent.llm_factory import GoogleAILLMs
from src.agent.prompts import \
    role_prompt, conv_pref_prompt, update_conv_pref_prompt, summary_prompt, update_summary_prompt, summary_system_prompt

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, RemoveMessage, HumanMessage, AIMessage
from langchain_core.runnables.config import RunnableConfig
from langgraph.graph.message import add_messages
from typing import Annotated, TypeAlias
from typing_extensions import TypedDict

"""
Base agent: LLM chat with automatic conversation summarisation and style analysis.

Nodes:
- call_llm:               responds to the student using role_prompt + optional question context + conversation summary
- summarize_conversation: triggered after max_messages_to_summarize messages; compresses history and
                          analyses the student's conversational style (returned in output metadata only)
"""

ValidMessageTypes: TypeAlias = SystemMessage | HumanMessage | AIMessage
AllMessageTypes: TypeAlias = ValidMessageTypes | RemoveMessage

class State(TypedDict):
    messages: Annotated[list[AllMessageTypes], add_messages]
    summary: str
    conversationalStyle: str

class BaseAgent:
    def __init__(self):
        # Main chat LLM — change to GoogleAILLMs(), AzureLLMs(), or OllamaLLMs() if preferred
        self.llm = GoogleAILLMs().get_llm()
        # Summarisation LLM — can be set to a different/cheaper model than the chat LLM
        self.summarisation_llm = GoogleAILLMs().get_llm()

        self.max_messages_to_summarize = 11
        self.role_prompt = role_prompt
        self.summary_prompt = summary_prompt
        self.update_summary_prompt = update_summary_prompt
        self.conversation_preference_prompt = conv_pref_prompt
        self.update_conversation_preference_prompt = update_conv_pref_prompt

        workflow = StateGraph(State)
        workflow.add_node("call_llm", self.call_model)
        workflow.add_node("summarize_conversation", self.summarize_conversation)
        workflow.add_conditional_edges(source=START, path=self.should_summarize)
        workflow.add_edge("summarize_conversation", "call_llm")
        workflow.add_edge("call_llm", END)
        self.app = workflow.compile()

    def call_model(self, state: State, config: RunnableConfig) -> dict:
        """Invoke the chat LLM with role prompt, optional question context, and conversation summary."""
        system_message = self.role_prompt

        context_prompt = config.get("configurable", {}).get("context_prompt", "")
        if context_prompt:
            system_message += f"## Known Question Materials: {context_prompt} \n\n"

        summary = state.get("summary", "")
        conversationalStyle = state.get("conversationalStyle", "")
        if summary:
            system_message += summary_system_prompt.format(summary=summary)
        if conversationalStyle:
            system_message += f"## Known conversational style and preferences of the student for this conversation: {conversationalStyle}. \n\nYour answer must be in line with this conversational style."

        messages = [SystemMessage(content=system_message)] + state["messages"]
        response = self.llm.invoke(self._valid(messages))
        return {"messages": [response]}

    def summarize_conversation(self, state: State) -> dict:
        """Summarise history and analyse conversational style when message count exceeds the threshold."""
        summary = state.get("summary", "")
        conversationalStyle = state.get("conversationalStyle", "")

        summary_message = (
            f"This is summary of the conversation to date: {summary}\n\n" + self.update_summary_prompt
        ) if summary else self.summary_prompt

        style_message = (
            f"This is the previous conversational style of the student for this conversation: {conversationalStyle}\n\n" + self.update_conversation_preference_prompt
        ) if conversationalStyle else self.conversation_preference_prompt

        summary_response = self.summarisation_llm.invoke(self._valid(state["messages"][:-1] + [HumanMessage(content=summary_message)]))
        conversational_style_response = self.summarisation_llm.invoke(self._valid(state["messages"][:-1] + [HumanMessage(content=style_message)]))

        delete_messages: list[AllMessageTypes] = [RemoveMessage(id=m.id) for m in state["messages"][:-3]]
        return {"summary": summary_response.content, "conversationalStyle": conversational_style_response.content, "messages": delete_messages}

    def should_summarize(self, state: State) -> str:
        valid = self._valid(state["messages"])
        if not valid:
            raise Exception("Internal Error: No valid messages found in the conversation history.")
        nr_messages = len(valid) - (1 if "system" in valid[-1].type else 0)
        return "summarize_conversation" if nr_messages > self.max_messages_to_summarize else "call_llm"

    def _valid(self, messages: list[AllMessageTypes]) -> list[ValidMessageTypes]:
        return [m for m in messages if m.type != "remove"]


agent = BaseAgent()

def invoke_base_agent(messages: list, summary: str, conversationalStyle: str, context_prompt: str, session_id: str | None = None) -> dict:
    """
    Invoke the agent with the full conversation history and return the chatbot reply plus updated metadata.
    Summarisation and style analysis trigger automatically once message count exceeds max_messages_to_summarize.
    """
    print(f"in invoke_base_agent(), thread_id = {session_id}")
    config: RunnableConfig = {"configurable": {"context_prompt": context_prompt}}
    state = agent.app.invoke(
        State(messages=messages, summary=summary, conversationalStyle=conversationalStyle),
        config=config,
    )
    print("in invoke_base_agent(), response generated by chatbot")
    return {
        "output": state["messages"][-1].content,
        "summary": state.get("summary", ""),
        "conversationalStyle": state.get("conversationalStyle", ""),
    }
