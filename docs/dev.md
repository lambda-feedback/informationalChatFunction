# YourFunctionName
*Brief description of what this chat function does, from the developer perspective*

## Inputs
*Specific input parameters which can be supplied when calling this chat function.*

## Outputs
*Output schema/values for this function*

## Examples
*List of example inputs and outputs for this function, each under a different sub-heading*

## Testing the Chat Function

To test your function, you can run the unit tests, call the code directly through a python script, or build the respective chat function docker container locally and call it through an API request. Below you can find details on those processes.

### Run Unit Tests

You can run the unit tests using `pytest`.

```bash
pytest
```

### Run the Chat Script

You can also use the `manual_agent_run.py` script to test the agents with example inputs from Lambda Feedback questions and synthetic conversations.
```bash
python tests/manual_agent_run.py
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
--data '{"body":"{\"conversationId\": \"12345Test\", \"messages\": [{\"role\": \"USER\", \"content\": \"hi\"}], \"user\": {\"type\": \"LEARNER\"}}"}'
```

#### Call Docker Container
##### A. Call Docker with Python Requests

In the `tests/` folder you can find the `manual_agent_requests.py` script that calls the POST URL of the running docker container. It reads any kind of input files with the expected schema. You can use this to test your curl calls of the chatbot.

##### B. Call Docker Container through API request

POST URL:

```bash
http://localhost:8080/2015-03-31/functions/function/invocations
```

Body (stringified within body for API request):

```JSON
{"body":"{\"conversationId\": \"12345Test\", \"messages\": [{\"role\": \"USER\", \"content\": \"hi\"}], \"user\": {\"type\": \"LEARNER\"}}"}
```

Body with optional fields:
```json
{
  "conversationId": "<uuid>",
  "messages": [
    { "role": "USER", "content": "<previous user message>" },
    { "role": "ASSISTANT", "content": "<previous assistant reply>" },
    { "role": "USER", "content": "<current message>" }
  ],
  "user": {
    "type": "LEARNER",
    "preference": {
      "conversationalStyle": "<stored style string>"
    },
    "taskProgress": {
      "timeSpentOnQuestion": "30 minutes",
      "accessStatus": "a good amount of time spent on this question today.",
      "markedDone": "This question is still being worked on.",
      "currentPart": {
        "position": 0,
        "timeSpentOnPart": "10 minutes",
        "markedDone": "This part is not marked done.",
        "responseAreas": [
          {
            "responseType": "EXPRESSION",
            "totalSubmissions": 3,
            "wrongSubmissions": 2,
            "latestSubmission": {
              "submission": "<student's last answer>",
              "feedback": "<feedback text from evaluator>",
              "answer": "<reference answer used for evaluation>"
            }
          }
        ]
      }
    }
  },
  "context": {
    "summary": "<compressed conversation history>",
    "set": {
      "title": "Fundamentals",
      "number": 2,
      "description": "<set description>"
    },
    "question": {
      "title": "Understanding Polymorphism",
      "number": 3,
      "guidance": "<teacher guidance>",
      "content": "<master question content>",
      "estimatedTime": "15-25 minutes",
      "parts": [
        {
          "position": 0,
          "content": "<part prompt>",
          "answerContent": "<part answer>",
          "workedSolutionSections": [
            { "position": 0, "title": "Step 1", "content": "..." }
          ],
          "structuredTutorialSections": [
            { "position": 0, "title": "Hint", "content": "..." }
          ],
          "responseAreas": [
            {
              "position": 0,
              "responseType": "EXPRESSION",
              "answer": "<reference answer>",
              "preResponseText": "<label shown before input>"
            }
          ]
        }
      ]
    }
  }
}
```

Response:

```json
{
  "output": {
    "role": "ASSISTANT",
    "content": "<assistant reply text>"
  },
  "metadata": {
    "summary": "<updated conversation summary>",
    "conversationalStyle": "<updated style string>",
    "processingTimeMs": 1234
  }
}
```
