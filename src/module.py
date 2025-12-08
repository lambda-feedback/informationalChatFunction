import time
from typing import Any
from lf_toolkit.chat.result import ChatResult as Result
from lf_toolkit.chat.params import ChatParams as Params

from src.agent.utils.parse_json_context_to_prompt import parse_json_to_prompt
from src.agent.agent import invoke_base_agent
from src.agent.utils.types import JsonType

def chat_module(message: Any, params: Params) -> JsonType:
    """
    Function used by student to converse with a chatbot.
    ---
    The handler function passes three arguments to module():

    - `message` which is the message sent by the student.
    - `params` which are any extra parameters that may be useful,
        e.g., conversation history and summary, conversational style of user, conversation id.

    The output of this function is what is returned as the API response
    and therefore must be JSON-encodable. It must also conform to the
    response schema.

    Any standard python library may be used, as well as any package
    available on pip (provided it is added to requirements.txt).

    The way you wish to structure you code (all in this function, or
    split into many) is entirely up to you. All that matters are the
    return types and that module() is the main function used
    to output the Chatbot response.
    """

    result = Result()

    # EXTRACT PARAMETERS
    conversation_id = params.get("conversation_id", None)
    if conversation_id is None:
        raise Exception("Internal Error: The conversation id is required in the parameters of the chat module.")

    include_test_data = params.get("include_test_data", False) or False
    conversation_history = params.get("conversation_history", []) or []
    summary = params.get("summary", "") or ""
    conversationalStyle = params.get("conversational_style", "") or ""

    question_response_details = params.get("question_response_details", {})
    if isinstance(question_response_details, dict):
        question_submission_summary = question_response_details.get("questionSubmissionSummary", [])
        question_information = question_response_details.get("questionInformation", {})
        question_access_information = question_response_details.get("questionAccessInformation", {})
    else:
        print("ERROR:: question_response_details is not a dict")
        raise Exception("Internal Error: The question response details parameter is malformed.")
    
    # PARSE QUESTION RESPONSE DETAILS TO PROMPT
    try:
        question_response_details_prompt = parse_json_to_prompt(
            question_submission_summary,
            question_information,
            question_access_information
        )
    except Exception as e:
        print("ERROR:: ", e)
        raise Exception("Internal Error: The question response details could not be parsed.")
    

    # RUN THE AGENT AND MEASURE PROCESSING TIME
    start_time = time.time()

    chatbot_response = invoke_base_agent(query=message, \
                            conversation_history=conversation_history, \
                            summary=summary, \
                            conversationalStyle=conversationalStyle, \
                            question_response_details=question_response_details_prompt, \
                            session_id=conversation_id)

    end_time = time.time()

    result._processing_time = end_time - start_time
    result.add_response("chatbot_response", chatbot_response["output"])
    result.add_metadata("summary", chatbot_response["intermediate_steps"][0])
    result.add_metadata("conversational_style", chatbot_response["intermediate_steps"][1])
    result.add_metadata("conversation_history", chatbot_response["intermediate_steps"][2])
    result.add_processing_time(end_time - start_time)

    return result.to_dict(include_test_data=include_test_data)