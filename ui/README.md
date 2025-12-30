# UI

This directory contains the Streamlit UI for testing the Multi-Agent Customer Support System.

## Files

- **`ui.py`** - Main UI application (active, use this)
- **`ui.py`** - Main Streamlit UI with authentication and memory testing

## Running the UI

```bash
# Activate virtual environment
source venv/bin/activate

# Run the UI
streamlit run ui/ui.py
```

The UI will be available at `http://localhost:8501`

## Features

- **Cognito Authentication** - Sign in with Cognito User Pool
- **Session Management** - Test STM (Short-Term Memory) with session IDs
- **Agent Invocation** - Test all agents through the UI
- **Memory Testing** - Test both STM and LTM
- **Response Tracing** - See which agents and tools were used
- **Real-time Chat** - Interactive chat interface

## Configuration

The UI automatically fetches configuration from:
1. Environment variables
2. SSM Parameter Store
3. Terraform outputs
4. Hardcoded defaults (fallback)

## Usage

1. **Sign In**: Use Cognito credentials to authenticate
2. **Set Session ID**: Use a UUID-based session ID (33+ characters)
3. **Ask Questions**: Test different agents and workflows
4. **Check Memory**: Test STM by asking follow-up questions in the same session
5. **View Details**: Expand "Response Details" to see agent routing and tool usage

## Testing

See `../tests/README.md` for comprehensive test scripts.

