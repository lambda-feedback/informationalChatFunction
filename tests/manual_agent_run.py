"""
Conversation turn-based Testbench of the agent's performance.
Select an example input file and write your query. Then run the agent to get the response.
"""

import json
from lf_toolkit.chat import ChatRequest
from src.module import chat_module

# File path for the input text
path = "tests/example_inputs/"
input_file = path + "example_input_1.json"

# Step 1: Read the input file
with open(input_file, "r") as file:
    raw_text = file.read()

# Step 2: Parse into JSON
try:
    parsed_json = json.loads(raw_text)

    # NOTE: #### This is the testing message #####
    message = "Hi, how do I solve this problem?"
    # NOTE: ########################################

    # Replace the last message content with the testing message
    parsed_json["messages"][-1]["content"] = message

    # Step 3: Validate into a ChatRequest
    request = ChatRequest.model_validate(parsed_json)

    # Step 4: Call the chat module to get a response
    response = chat_module(request)

    print(json.dumps(json.loads(response.model_dump_json()), indent=4))

except json.JSONDecodeError as e:
    print("Error decoding JSON:", e)
