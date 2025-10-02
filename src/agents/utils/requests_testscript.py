import requests
import json

"""
Script that sends a request to the local endpoint of the docker container to test the chatbot agent.
"""

# URL for the local endpoint to docker (`docker build` and `docker run`)
url = "http://localhost:8080/2015-03-31/functions/function/invocations"

# File path for the input text
path = "src/agents/utils/example_inputs/"
input_file = path + "example_input_1.json"

# Step 1: Read the input file
with open(input_file, "r") as file:
    data = file.read()

payload = json.dumps({"body": data})
print(payload)
headers = {
  'Content-Type': 'application/json'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)
