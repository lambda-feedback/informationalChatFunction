try:
    from ..llm_factory import OpenAILLMs, GoogleAILLMs
    from .base_prompts import \
        role_prompt, conv_pref_prompt, update_conv_pref_prompt, summary_prompt, update_summary_prompt, summary_system_prompt
    from ..utils.types import InvokeAgentResponseType
except ImportError:
    from src.agents.llm_factory import OpenAILLMs, GoogleAILLMs
    from src.agents.base_agent.base_prompts import \
        role_prompt, conv_pref_prompt, update_conv_pref_prompt, summary_prompt, update_summary_prompt, summary_system_prompt
    from src.agents.utils.types import InvokeAgentResponseType

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, RemoveMessage, HumanMessage, AIMessage
from langchain_core.runnables.config import RunnableConfig
from langgraph.graph.message import add_messages
from typing import Annotated, TypeAlias
from typing_extensions import TypedDict

"""
Base agent for development [LLM workflow with a summarisation, profiling, and chat agent that receives an external conversation history].

This agent is designed to:
- [summarise_prompt]        summarise the conversation after 'max_messages_to_summarize' number of messages is reached in the conversation
- [conv_pref_prompt]        analyse the conversation style of the student 
- [role_prompt]             role of a tutor to answer student's questions on the topic  
"""

ValidMessageTypes: TypeAlias = SystemMessage | HumanMessage | AIMessage
AllMessageTypes: TypeAlias = ValidMessageTypes | RemoveMessage

class State(TypedDict):
    messages: Annotated[list[AllMessageTypes], add_messages]
    summary: str
    conversationalStyle: str

class BaseAgent:
    def __init__(self):
        llm = OpenAILLMs()                  # OpenAILLMs() or GoogleAILLMs()
        self.llm = llm.get_llm()
        summarisation_llm = OpenAILLMs()    # OpenAILLMs() or GoogleAILLMs()
        self.summarisation_llm = summarisation_llm.get_llm()
        self.summary = ""
        self.conversationalStyle = ""

        # Define Agent's specific Parameters
        self.max_messages_to_summarize = 11
        self.role_prompt = role_prompt
        self.summary_prompt = summary_prompt
        self.update_summary_prompt = update_summary_prompt
        self.conversation_preference_prompt = conv_pref_prompt
        self.update_conversation_preference_prompt = update_conv_pref_prompt

        # Define a new graph for the conversation & compile it
        self.workflow = StateGraph(State)
        self.workflow_definition()
        self.app = self.workflow.compile()

    def call_model(self, state: State, config: RunnableConfig) -> str:
        """Call the LLM model knowing the role system prompt, the summary and the conversational style."""
        
        # Default AI tutor role prompt
        system_message = self.role_prompt

        # Adding external student progress and question context details from data queries
        question_response_details = config["configurable"].get("question_response_details", "")
        if question_response_details:
            system_message += f"## Known Question Materials: {question_response_details} \n\n"

        # Adding summary and conversational style to the system message
        summary = state.get("summary", "")
        conversationalStyle = state.get("conversationalStyle", "")
        if summary:
            system_message += summary_system_prompt.format(summary=summary)
        if conversationalStyle:
            system_message += f"## Known conversational style and preferences of the student for this conversation: {conversationalStyle}. \n\nYour answer must be in line with this conversational style."

        messages = [SystemMessage(content=system_message)] + state['messages']

        valid_messages = self.check_for_valid_messages(messages)
        response = self.llm.invoke(valid_messages)

        # Save summary for fetching outside the class
        self.summary = summary
        self.conversationalStyle = conversationalStyle

        return {"summary": summary, "messages": [response]}
    
    def check_for_valid_messages(self, messages: list[AllMessageTypes]) -> list[ValidMessageTypes]:
        """ Removing the RemoveMessage() from the list of messages """

        valid_messages: list[ValidMessageTypes] = []
        for message in messages:
            if message.type != 'remove':
                valid_messages.append(message)
        return valid_messages
    
    def summarize_conversation(self, state: State, config: RunnableConfig) -> dict:
        """Summarize the conversation."""

        summary = state.get("summary", "")
        previous_summary = config["configurable"].get("summary", "")
        previous_conversationalStyle = config["configurable"].get("conversational_style", "")
        if previous_summary:
            summary = previous_summary
        
        if summary:
            summary_message = (
                f"This is summary of the conversation to date: {summary}\n\n" +
                self.update_summary_prompt
            )
        else:
            summary_message = self.summary_prompt
        
        if previous_conversationalStyle:
            conversationalStyle_message = (
                f"This is the previous conversational style of the student for this conversation: {previous_conversationalStyle}\n\n" +
                self.update_conversation_preference_prompt
            )
        else:
            conversationalStyle_message = self.conversation_preference_prompt

        # STEP 1: Summarize the conversation
        messages = state["messages"][:-1] + [HumanMessage(content=summary_message)] 
        valid_messages = self.check_for_valid_messages(messages)
        summary_response = self.summarisation_llm.invoke(valid_messages)

        # STEP 2: Analyze the conversational style
        messages = state["messages"][:-1] + [HumanMessage(content=conversationalStyle_message)]
        valid_messages = self.check_for_valid_messages(messages)
        conversationalStyle_response = self.summarisation_llm.invoke(valid_messages)

        # Delete messages that are no longer wanted, except the last ones
        delete_messages: list[AllMessageTypes] = [RemoveMessage(id=m.id) for m in state["messages"][:-3]]

        return {"summary": summary_response.content, "conversationalStyle": conversationalStyle_response.content, "messages": delete_messages}
    
    def should_summarize(self, state: State) -> str:
        """
        Return the next node to execute. 
        If there are more than X messages, then we summarize the conversation.
        Otherwise, we call the LLM.
        """

        messages = state["messages"]
        valid_messages = self.check_for_valid_messages(messages)
        nr_messages = len(valid_messages)
        if len(valid_messages) == 0:
            raise Exception("Internal Error: No valid messages found in the conversation history. Conversation history might be empty.")
        if "system" in valid_messages[-1].type:
            nr_messages -= 1

        # always pairs of (sent, response) + 1 latest message
        if nr_messages > self.max_messages_to_summarize:
            return "summarize_conversation"
        return "call_llm"    

    def workflow_definition(self) -> None:
        self.workflow.add_node("call_llm", self.call_model)
        self.workflow.add_node("summarize_conversation", self.summarize_conversation)

        self.workflow.add_conditional_edges(source=START, path=self.should_summarize)
        self.workflow.add_edge("summarize_conversation", "call_llm")
        self.workflow.add_edge("call_llm", END)

    def get_summary(self) -> str:
        return self.summary
    
    def get_conversational_style(self) -> str:
        return self.conversationalStyle

    def print_update(self, update: dict) -> None:
        for k, v in update.items():
            for m in v["messages"]:
                m.pretty_print()
            if "summary" in v:
                print(v["summary"])

    def pretty_response_value(self, event: dict) -> str:
        return event["messages"][-1].content
    
agent = BaseAgent()
def invoke_base_agent(query: str, conversation_history: list, summary: str, conversationalStyle: str, question_response_details: str, session_id: str) -> InvokeAgentResponseType:
    """
    Call an agent that has no conversation memory and expects to receive all past messages in the params and the latest human request in the query.
    If conversation history longer than X, the agent will summarize the conversation and will provide a conversational style analysis.
    """
    print(f'in invoke_base_agent(), thread_id = {session_id}')

    config = {"configurable": {"thread_id": session_id, "summary": summary, "conversational_style": conversationalStyle, "question_response_details": question_response_details}}
    response_events = agent.app.invoke({"messages": conversation_history, "summary": summary, "conversational_style": conversationalStyle}, config=config, stream_mode="values") #updates
    pretty_printed_response = agent.pretty_response_value(response_events) # get last event/ai answer in the response

    # Gather Metadata from the agent
    summary = agent.get_summary()
    conversationalStyle = agent.get_conversational_style()

    print(f'in invoke_base_agent(), response generated by chatbot')

    return {
        "input": query,
        "output": pretty_printed_response,
        "intermediate_steps": [str(summary), conversationalStyle, conversation_history]
    }