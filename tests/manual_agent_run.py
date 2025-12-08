"""
 Conversation turn-based Testbench of the agent's performance.
 Select an example input file and write your query. Then run the agent to get the response.
"""

import json
from src.module import chat_module

# File path for the input text
path = "src/agent/utils/example_inputs/"
input_file = path + "example_input_1.json"

# Step 1: Read the input file
with open(input_file, "r") as file:
    raw_text = file.read()
    
# Step 5: Parse into JSON
try:
    parsed_json = json.loads(raw_text)

    """
      STEP 2: Extract the parameters from the JSON
    """
    # NOTE: #### This is the testing message #####
    message = "Hi, how do I solve this problem?" 
    # NOTE: ########################################

    # In the JSON, replace "mock" in the message and conversation history with the testing message
    parsed_json["message"] = message
    parsed_json["params"]["conversation_history"][-1]["content"] = message

    params = parsed_json["params"]

    """
      STEP 3: Call the chat module to get a response to the user's message
    """
    response = chat_module(message, params)
    
    print(json.dumps(response, indent=4))
    

except json.JSONDecodeError as e:
    print("Error decoding JSON:", e)



