import unittest
from lf_toolkit.chat import ChatRequest
from src.module import chat_module
from tests.utils import assert_valid_chat_response


def make_request(**kwargs):
    defaults = {
        "messages": [{"role": "USER", "content": "Hello, World"}],
        "conversationId": "1234Test",
    }
    defaults.update(kwargs)
    return ChatRequest.model_validate(defaults)


class TestChatModuleFunction(unittest.TestCase):

    def test_response_format(self):
        assert_valid_chat_response(self, chat_module(make_request()))
