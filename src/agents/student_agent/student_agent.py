try:
    from ..llm_factory import OpenAILLMs
    from .student_prompts import \
        base_student_persona, curious_student_persona, contradicting_student_persona, reliant_student_persona, confused_student_persona, unrelated_student_persona, \
        process_prompt
    from ..utils.types import InvokeAgentResponseType
except ImportError:
    from src.agents.llm_factory import OpenAILLMs
    from src.agents.student_agent.student_prompts import \
        base_student_persona, curious_student_persona, contradicting_student_persona, reliant_student_persona, confused_student_persona, unrelated_student_persona, \
        process_prompt
    from src.agents.utils.types import InvokeAgentResponseType

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, RemoveMessage, HumanMessage, AIMessage
from langchain_core.runnables.config import RunnableConfig
from langgraph.graph.message import add_messages
from typing import Annotated, TypeAlias
from typing_extensions import TypedDict

"""
Student agent for synthetic evaluation of the other LLM tutors. This agent is designed to be a student that requires help in the conversation. 
[LLM workflow with a summarisation, and chat agent that receives an external conversation history].

This agent is designed to:
- [role_prompt]             role of a student to ask questions on the topic  
- [student_type]            student's learning profile and comprehension level [many profiles can be chosen from the student_prompts.py]
"""

ValidMessageTypes: TypeAlias = SystemMessage | HumanMessage | AIMessage
AllMessageTypes: TypeAlias = ValidMessageTypes | RemoveMessage

class State(TypedDict):
    messages: Annotated[list[AllMessageTypes], add_messages]
    summary: str

class StudentAgent:
    def __init__(self, student_type: str):
        llm = OpenAILLMs(temperature=0.75)
        self.llm = llm.get_llm()
        self.summary = ""
        self.conversationalStyle = ""
        self.type = student_type

        # Define Agent's specific Personas
        self.role_prompt = process_prompt
        if self.type == "base":
            self.role_prompt += base_student_persona
        elif self.type == "curious":
            self.role_prompt += curious_student_persona
        elif self.type == "contradicting":
            self.role_prompt += contradicting_student_persona
        elif self.type == "reliant":
            self.role_prompt += reliant_student_persona
        elif self.type == "confused":
            self.role_prompt += confused_student_persona
        elif self.type == "unrelated":
            self.role_prompt += unrelated_student_persona
        else:
            raise Exception("Unknown Student Agent Type")
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
            # convert "my" to "your" in the question_response_details to preserve the student agent as the user
            question_response_details = question_response_details.replace("My", "Your")
            question_response_details = question_response_details.replace("my", "your")
            question_response_details = question_response_details.replace("I am", "you are")
            system_message += f"\n\n## Known Learning Materials: {question_response_details} \n\n"

        # Adding summary and conversational style to the system message
        summary = state.get("summary", "")
        previous_summary = config["configurable"].get("summary", "")
        if previous_summary:
            summary = previous_summary
        if summary:
            system_message += f"## Summary of conversation earlier: {summary} \n\n"

        messages = [SystemMessage(content=system_message)] + state['messages']

        valid_messages = self.check_for_valid_messages(messages)
        response = self.llm.invoke(valid_messages)

        # Save summary for fetching outside the class
        self.summary = summary

        return {"summary": summary, "messages": [response]}
    
    def check_for_valid_messages(self, messages: list[AllMessageTypes]) -> list[ValidMessageTypes]:
        """ Removing the RemoveMessage() from the list of messages """

        valid_messages: list[ValidMessageTypes] = []
        for message in messages:
            if message.type != 'remove':
                valid_messages.append(message)
        return valid_messages  

    def workflow_definition(self) -> None:
        self.workflow.add_node("call_llm", self.call_model)

        self.workflow.add_edge(START, "call_llm")
        self.workflow.add_edge("call_llm", END)

    def get_summary(self) -> str:
        return self.summary

    def print_update(self, update: dict) -> None:
        for k, v in update.items():
            for m in v["messages"]:
                m.pretty_print()
            if "summary" in v:
                print(v["summary"])

    def pretty_response_value(self, event: dict) -> str:
        return event["messages"][-1].content
    
def invoke_student_agent(query: str, conversation_history: list, summary: str, student_type:str, question_response_details: str, session_id: str) -> InvokeAgentResponseType:
    """
    Call a base student agents that forms a basic conversation with the tutor agent.
    """
    print(f'in invoke_student_agent(), student_type: {student_type}')
    agent = StudentAgent(student_type=student_type)

    config = {"configurable": {"thread_id": session_id, "summary": summary, "question_response_details": question_response_details}}
    response_events = agent.app.invoke({"messages": conversation_history + [AIMessage(content=query)]}, config=config, stream_mode="values") #updates
    pretty_printed_response = agent.pretty_response_value(response_events) # get last event/ai answer in the response

    # Gather Metadata from the agent
    summary = agent.get_summary()

    return {
        "input": query,
        "output": pretty_printed_response,
        "intermediate_steps": [str(summary), conversation_history]
    }