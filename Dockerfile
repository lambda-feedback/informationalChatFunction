ARG BASE_VERSION=python:3.12

# evaluation-function-base's python image bundles the shimmy binary,
# the Lambda RIE, and the entrypoint.sh that picks between them.
FROM ghcr.io/lambda-feedback/evaluation-function-base/${BASE_VERSION}

RUN apt-get update && apt-get install -y \
      build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

COPY requirements.txt .
RUN pip install -r requirements.txt

# Precompile python files for faster startup
RUN python -m compileall -q .

# Copy the function code
COPY src ./src

COPY index.py .

COPY tests ./tests

# Command shimmy uses to start the chat function worker
ENV FUNCTION_COMMAND="python"

# Args to start the chat function worker with
ENV FUNCTION_ARGS="index.py"

# The transport to use for the RPC server
ENV FUNCTION_RPC_TRANSPORT="ipc"

ENV FUNCTION_WORKER_SEND_TIMEOUT="170s"

ENV LOG_LEVEL="debug"
