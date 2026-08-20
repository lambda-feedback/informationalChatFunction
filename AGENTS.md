# AGENTS.md

This file provides guidance to AI agents when working with code in this repository.

## Project Overview

This is a chat function connecting students to an AI educational chatbot that is integrated with the **Lambda-Feedback** educational platform. It's containerized via Docker and deployed behind [shimmy](https://github.com/lambda-feedback/shimmy), a shim that spawns this function as a persistent JSON-RPC worker process and exposes it as the muEd `/chat` / `/chat/health` HTTP API (both locally and as an AWS Lambda container). It receives student chat messages with educational context and returns LLM-powered chatbot responses. Incoming requests follow the [muEd API](https://mued.org/) schema (`context`, `user`, `messages`).

## Commands

**Testing:**
```bash
PYTHONPATH=. pytest                 # Run all unit tests (CI sets PYTHONPATH=. too)
python tests/manual_agent_run.py   # Test agent locally with example inputs
python tests/manual_agent_requests.py  # Test running Docker container
```

**Docker:**
```bash
docker build -t llm_chat .
docker run --env-file .env -p 8080:8080 llm_chat
```

**Manual API test (while Docker is running):**
```bash
curl -X POST http://localhost:8080/chat \
  -H 'Content-Type: application/json' \
  -H 'X-Api-Version: 0.1.0' \
  -d '{"messages": [{"role": "USER", "content": "hi"}]}'

curl http://localhost:8080/chat/health -H 'X-Api-Version: 0.1.0'
```

**Run a single test:**
```bash
pytest tests/test_module.py        # Run specific test file
pytest tests/test_module.py::TestChatModuleFunction::test_response_format  # Run specific test
```

## Architecture

### Request Flow

```
shimmy (shim, container entrypoint)
  → spawns index.py as a persistent worker subprocess (lf_toolkit RPC server)
  → forwards POST /chat / GET /chat/health as JSON-RPC "chat" / "chat/health" calls
  → index.py registers src/module.py's chat_module / chat_health_module as handlers
    → lf_toolkit validates the request body against the muEd ChatRequest schema
    → src/module.py (chat_module)
      → extracts muEd API context (messages, conversationId, question context, user type)
      → parses educational context to prompt text via src/agent/context.py
      → src/agent/agent.py (BaseAgent / LangGraph)
        → routes to call_llm or summarize_conversation node
        → calls LLM provider (OpenAI / Google / Azure / Ollama)
    → returns ChatResponse (output, summary, conversationalStyle, processingTime)
```

### Key Files

| File | Role |
|------|------|
| `index.py` | Worker entrypoint; registers `chat_module`/`chat_health_module` with `lf_toolkit`'s RPC server (`create_server()` + `run()`) |
| `src/module.py` | Transforms muEd API request → invokes agent → builds ChatResponse; also exposes `chat_health_module()` |
| `src/agent/agent.py` | LangGraph stateful graph; manages message history and summarization |
| `src/agent/prompts.py` | System prompts for tutor behavior, summarization, style detection |
| `src/agent/llm_factory.py` | Factory classes for each LLM provider (OpenAI, Google, Azure, Ollama) |
| `src/agent/context.py` | Converts muEd question/submission context dicts to LLM prompt text |
| `tests/utils.py` | Shared test helpers: `assert_valid_chat_request`, `assert_valid_chat_response` |
| `tests/example_inputs/` | Real muEd payloads used for end-to-end tests |

### Agent Logic (LangGraph)

`BaseAgent` maintains a state graph with two nodes:
- **`call_llm`**: Invokes the LLM with system prompt + conversation summary + conversational style preference
- **`summarize_conversation`**: Triggered when message count exceeds ~11; summarizes history and also extracts the student's preferred conversational style

Messages are trimmed after summarization to keep context window manageable. The `summary` and `conversationalStyle` fields persist across calls via the `ChatRequest` metadata.

### muEd API Format

`src/module.py` handles the muEd request format (https://mued.org/). The `context` field in `ChatRequest` contains nested educational data (question parts, student submissions, task info) that gets parsed into a tutoring prompt via `src/agent/context.py`.

### LLM Configuration

LLM provider and model are set via environment variables (see `.env.example`). The `llm_factory.py` selects the provider at runtime. The Lambda function name/identity is set in `config.json`.

The agent uses **two separate LLM instances** — `self.llm` for chat responses and `self.summarisation_llm` for conversation summarisation and style analysis. By default both use the same provider, but you can point them at different models (e.g. a cheaper model for summarisation) by changing the class in `agent.py`.

## Deployment

- Pull requests: `.github/workflows/test-lint.yml` runs pytest only
- Pushing to `main`: `.github/workflows/staging-deploy.yml` runs tests then deploys to AWS staging via the shared `lambda-feedback/chat-function-workflows` reusable workflows
- Production: `.github/workflows/production-deploy.yml` is `workflow_dispatch`-only with a `version-bump` input; redeploys staging, pauses on the `production-override` GitHub Environment for manual approval, then creates a `vX.Y.Z` tag + GitHub Release and deploys to prod
- All environment variables (API keys, model names) are injected via GitHub Actions secrets/variables — do not hardcode them
