import unittest
import json
from index import handler
from tests.utils import assert_valid_chat_request, assert_valid_chat_response


def make_event(body: dict) -> dict:
    return {"body": json.dumps(body)}


BASE_BODY = {
    "messages": [{"role": "USER", "content": "Hello, World"}],
    "conversationId": "1234Test",
}


class TestChatIndexFunction(unittest.TestCase):

    def test_missing_messages(self):
        body = {k: v for k, v in BASE_BODY.items() if k != "messages"}
        result = handler(make_event(body), None)
        self.assertEqual(result.get("statusCode"), 400)

    def test_invalid_json_body(self):
        result = handler({"body": "not valid json"}, None)
        self.assertEqual(result.get("statusCode"), 400)

    def test_response_format(self):
        assert_valid_chat_request(self, BASE_BODY)
        assert_valid_chat_response(self, handler(make_event(BASE_BODY), None))
