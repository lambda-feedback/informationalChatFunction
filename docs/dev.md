# YourFunctionName
*Brief description of what this chat function does, from the developer perspective*

## Inputs
*Specific input parameters which can be supplied when the calling this chat function.*

## Outputs
*Output schema/values for this function*

## Examples
*List of example inputs and outputs for this function, each under a different sub-heading*

## Testing the Chat Function

To test your function, you can either call the code directly through a python script. Or you can build the respective chat function docker container locally and call it through an API request. Below you can find details on those processes.

### Run the Chat Script

You can run the Python function itself. Make sure to have a main function in either `src/module.py` or `index.py`.

```bash
python src/module.py
```

You can also use the `testbench_agents.py` script to test the agents with example inputs from Lambda Feedback questions and synthetic conversations.
```bash
python src/agents/utils/testbench_agents.py
```

### Calling the Docker Image Locally

To build the Docker image, run the following command:

```bash
docker build -t llm_chat .
```

#### Running the Docker Image

To run the Docker image, use the following command:

##### A. Without .env file:

```bash
docker run -e OPENAI_API_KEY={your key} -e OPENAI_MODEL={your LLM chosen model name} -p 8080:8080 llm_chat
```

##### B. With container name (for interaction, e.g. copying file from inside the docker container):

```bash
docker run --env-file .env -it --name my-lambda-container -p 8080:8080 llm_chat
```

This will start the chat function and expose it on port `8080` and it will be open to be curl:

```bash
curl --location 'http://localhost:8080/2015-03-31/functions/function/invocations' \
--header 'Content-Type: application/json' \
--data '{"body":"{\"message\": \"hi\", \"params\": {\"conversation_id\": \"12345Test\", \"conversation_history\": [{\"type\": \"user\", 
```

#### Call Docker Container
##### A. Call Docker with Python Requests

In the `src/agents/utils` folder you can find the `requests_testscript.py` script that calls the POST URL of the running docker container. It reads any kind of input files with the expected schema. You can use this to test your curl calls of the chatbot.

##### B. Call Docker Container through API request

POST URL:

```bash
http://localhost:8080/2015-03-31/functions/function/invocations
```

Body (stringified within body for API request):

```JSON
{"body":"{\"message\": \"hi\", \"params\": {\"conversation_id\": \"12345Test\", \"conversation_history\": [{\"type\": \"user\", \"content\": \"hi\"}]}}"}
```

Body with optional Params:
```JSON
{
    "message":"hi",
    "params":{
        "conversation_id":"12345Test",
        "conversation_history":[{"type":"user","content":"hi"}],
        "summary":" ",
        "conversational_style":" ",
        "question_response_details": "",
        "include_test_data": true,
        "agent_type": {agent_name}
    }
}
```

