import json
import unittest
from lf_toolkit.chat import ChatRequest, ChatResponse


def assert_valid_chat_request(test: unittest.TestCase, payload: dict):
    """Assert a dict is a valid muEd ChatRequest (at least one message)."""
    try:
        request = ChatRequest.model_validate(payload)
    except Exception as e:
        test.fail(f"Payload is not a valid ChatRequest: {e}")
    test.assertGreater(len(request.messages), 0, "messages must not be empty")


def assert_valid_chat_response(test: unittest.TestCase, result):
    """
    Assert a result matches the expected muEd ChatResponse format.
    Accepts either a ChatResponse object or a Lambda handler result dict.
    """
    if isinstance(result, ChatResponse):
        body = json.loads(result.model_dump_json())
    else:
        test.assertEqual(result.get("statusCode"), 200)
        body = json.loads(result["body"])

    output = body.get("output", {})
    test.assertEqual(output.get("role"), "ASSISTANT")
    test.assertIsInstance(output.get("content"), str)
    test.assertGreater(len(output["content"]), 0)

    metadata = body.get("metadata", {})
    test.assertIsInstance(metadata.get("summary"), str)
    test.assertIsInstance(metadata.get("conversationalStyle"), str)
    test.assertIsInstance(metadata.get("processingTimeMs"), int)
    test.assertGreaterEqual(metadata["processingTimeMs"], 0)
