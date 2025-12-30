# Dockerfile for AgentCore Runtime Deployment
# This builds a single container with:
# - Supervisor Agent (AgentCore entry point)
# - All specialized agents (running in background threads via localhost)

# Use AWS ECR Public Gallery to avoid Docker Hub rate limits
FROM public.ecr.aws/docker/library/python:3.11-slim

# Install build dependencies including Rust for tiktoken
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    curl \
    && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Add Rust to PATH
ENV PATH="/root/.cargo/bin:${PATH}"

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY agent.py .
COPY agents/ ./agents/
COPY shared/ ./shared/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DOCKER_CONTAINER=1

# AgentCore Runtime expects the app to be importable and runnable
# The @app.entrypoint decorator registers the handler
# Specialized agents are started automatically in background threads
# when DOCKER_CONTAINER=1 is set (see agent.py)
# We use opentelemetry-instrument for observability (required by AgentCore)
CMD ["opentelemetry-instrument", "python", "agent.py"]
