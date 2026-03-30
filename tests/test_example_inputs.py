import unittest
import json
import os
from index import handler
from tests.utils import assert_valid_chat_request, assert_valid_chat_response

EXAMPLE_INPUTS_DIR = "tests/example_inputs"


class TestExampleInputs(unittest.TestCase):
    """
    End-to-end tests for each example input in tests/example_inputs/.
    Each file must be a valid muEd ChatRequest and produce a valid muEd ChatResponse.
    """

    def _test(self, filename: str):
        with open(os.path.join(EXAMPLE_INPUTS_DIR, filename)) as f:
            payload = json.load(f)
        assert_valid_chat_request(self, payload)
        result = handler({"body": json.dumps(payload)}, None)
        assert_valid_chat_response(self, result)
        return payload, json.loads(result["body"])

    def test_example_input_0_simple(self):
        self._test("example_input_0.json")

    def test_example_input_1(self):
        self._test("example_input_1.json")

    def test_example_input_2_metadata_persists(self):
        """Example input 2 has an existing summary and conversationalStyle — verifies they persist in the response."""
        payload, result_body = self._test("example_input_2.json")
        self.assertEqual(result_body["metadata"]["summary"], payload["context"]["summary"])
        self.assertEqual(result_body["metadata"]["conversationalStyle"], payload["user"]["preference"]["conversationalStyle"])

    def test_example_input_3_metadata_updates(self):
        """Example input 3 has 13 messages — enough to trigger summarisation.
        Verifies that summary and conversationalStyle are populated in the response."""
        _, result_body = self._test("example_input_3.json")
        self.assertGreater(len(result_body["metadata"]["summary"]), 0, "summary should be populated after summarisation")
        self.assertGreater(len(result_body["metadata"]["conversationalStyle"]), 0, "conversationalStyle should be populated after summarisation")
