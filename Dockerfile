ARG PYTHON_VERSION=3.13

FROM public.ecr.aws/lambda/python:${PYTHON_VERSION}

# Set working directory
WORKDIR ${LAMBDA_TASK_ROOT}

RUN pip install --upgrade pip 
RUN dnf install -y git \
    && dnf install -y \
      gcc \
      gcc-c++ \
      make \
      python3-devel \
    && dnf clean all

COPY requirements.txt .
RUN pip install -r requirements.txt

# Precompile python files for faster startup
RUN python -m compileall -q .

# Copy the function code
COPY src ./src

COPY index.py .

COPY index_test.py .

# Set the Lambda function handler
CMD ["index.handler"]