# Tests

This directory contains test scripts for the Multi-Agent Customer Support Platform.

## Test Scripts

### `test_all_agents.sh`
Quick test script that tests all agents and memory functionality.

**Usage:**
```bash
./tests/test_all_agents.sh
```

**What it tests:**
- Knowledge Agent (password reset query)
- Sentiment Agent (negative sentiment detection)
- Memory (STM - short-term memory)
- Multi-agent workflow

### `test_session_memory_complete.py`
Comprehensive memory testing script.

**Usage:**
```bash
python tests/test_session_memory_complete.py
```

**What it tests:**
- Short-Term Memory (STM) - same session
- Long-Term Memory (LTM) - cross-session
- Conversation history persistence

### `test_ui_comprehensive.py`
UI testing script for Streamlit interface.

**Usage:**
```bash
python tests/test_ui_comprehensive.py
```

**What it tests:**
- UI authentication
- Agent invocation
- Response parsing
- Session management

### `check_bedrock_access.py`
Verify AWS Bedrock access and permissions.

**Usage:**
```bash
python tests/check_bedrock_access.py
```

**What it checks:**
- AWS credentials
- Bedrock model access
- Required permissions

## Running All Tests

```bash
# Run all tests
./tests/test_all_agents.sh
python tests/test_session_memory_complete.py
python tests/test_ui_comprehensive.py
python tests/check_bedrock_access.py
```

## Prerequisites

- Virtual environment activated
- AWS credentials configured
- AgentCore deployed (for agent tests)
- Infrastructure deployed (for full tests)

