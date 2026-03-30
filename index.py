import json
from pydantic import ValidationError

from lf_toolkit.chat import ChatRequest
from src.module import chat_module


def handler(event, context):
    """
    Lambda handler function
    """
    if "body" in event:
        try:
            event = json.loads(event["body"])
        except json.JSONDecodeError:
            return {
                "statusCode": 400,
                "body": "Invalid JSON format in the body. Please check the input.",
            }

    try:
        request = ChatRequest.model_validate(event)
    except ValidationError as e:
        return {"statusCode": 400, "body": e.json()}

    try:
        result = chat_module(request)
    except Exception as e:
        return {
            "statusCode": 500,
            "body": f"An error occurred within the chat_module(): {str(e)}",
        }

    response = {"statusCode": 200, "body": result.model_dump_json()}
    print("Returning response:", " ".join(json.dumps(response, indent=2).splitlines()))
    return response
