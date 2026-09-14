# informationalChatFunction
This chatbot aims to complete all the relevant tasks the student requests based on the current Question they are working on. The Chatbot is aware of the Question details, answer, worked solution and guidance from the lecturer.

Some technical details:
<pre style="white-space: pre-wrap;">
<code>LLM model: Gemini-2.5-flash-lite (Google)
response time (on average): ~10 seconds

Helping approach: encourages self-discovery of the answer, but will reveal the solution if requested
</code>
</pre>

## Behavioural Prompt

**Role:** A patient AI tutor focused on student-centred learning — aims to foster critical thinking, active engagement, and confidence-building.

**Key behaviours from the role prompt**

- **Step-by-step guidance:** breaks problems into smaller steps and offers hints or intermediate steps before giving the final answer. Will share the complete answer if the student explicitly asks, but only after first encouraging exploration.
- **Error reflection:** treats mistakes as opportunities — helps the student work out *why* something went wrong rather than silently correcting it.
- **Awareness of materials:** grounds responses in the question's content, answer, worked solution, and the teacher's guidance — paraphrasing rather than quoting verbatim.
- **Adaptive support:** if the student keeps struggling, evaluates their progress and time spent on the question and gradually offers more detailed and specific guidance.
- **Engagement:** ends interactions with a question to keep the dialogue going and gauge comprehension.
- **Praise** is reserved for genuine effort or breakthroughs to avoid sounding insincere.
- **Stays on topic:** politely redirects students who ask about unrelated material.

## Testing the Chat Function

To test your function, you can run the unit tests, call the code directly through a python script, or build the respective chat function docker container locally and call it through an API request. Below you can find details on those processes.

### Run Unit Tests

You can run the unit tests using `pytest`. Run it from the repository root with `PYTHONPATH=.` set (as CI does) so the `tests` and `src` packages resolve correctly:

```bash
PYTHONPATH=. pytest
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

This starts shimmy (the [Lambda Feedback shim](https://github.com/lambda-feedback/shimmy)) as the container's entrypoint, which spawns this function as a worker subprocess and exposes it on port `8080` as the muEd chat API:

```bash
curl --location 'http://localhost:8080/chat' \
--header 'Content-Type: application/json' \
--header 'X-Api-Version: 0.1.0' \
--data '{"conversationId": "12345Test", "messages": [{"role": "USER", "content": "hi"}], "user": {"type": "LEARNER"}}'
```

Health check:

```bash
curl --location 'http://localhost:8080/chat/health' \
--header 'X-Api-Version: 0.1.0'
```

#### Call Docker Container
##### A. Call Docker with Python Requests

In the `tests/` folder you can find the `manual_agent_requests.py` script that calls the `/chat` and `/chat/health` routes of the running docker container. It reads any kind of input files with the expected schema. You can use this to test your curl calls of the chatbot.

##### B. Call Docker Container through API request

POST URL:

```bash
http://localhost:8080/chat
```

Body (requests may include an `X-Api-Version: 0.1.0` header):

```JSON
{"conversationId": "12345Test", "messages": [{"role": "USER", "content": "hi"}], "user": {"type": "LEARNER"}}
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
        "position": 1,
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
          "position": 1,
          "content": "<part prompt>",
          "answerContent": "<part answer>",
          "workedSolutionSections": [
            { "position": 1, "title": "Step 1", "content": "..." }
          ],
          "structuredTutorialSections": [
            { "position": 1, "title": "Hint", "content": "..." }
          ],
          "responseAreas": [
            {
              "position": 1,
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
All `position` and `number` fields are **1-indexed**.

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
