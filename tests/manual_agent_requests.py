import requests

"""
Script that sends requests straight to shimmy's muEd chat routes on the
locally running docker container (`docker build` and `docker run`) to test
the chatbot agent end-to-end, behind the shim.
"""

base_url = "http://localhost:8080"

headers = {
    'Content-Type': 'application/json',
    'X-Api-Version': '0.1.0',
}

# Health check
health_response = requests.get(f"{base_url}/chat/health", headers=headers)
print("GET /chat/health ->", health_response.status_code)
print(health_response.text)

# File path for the input text
path = "tests/example_inputs/"
input_file = path + "example_input_1.json"

# Step 1: Read the input file
with open(input_file, "r") as file:
    payload = file.read()

print(payload)

response = requests.post(f"{base_url}/chat", headers=headers, data=payload)

print("POST /chat ->", response.status_code)
print(response.text)
