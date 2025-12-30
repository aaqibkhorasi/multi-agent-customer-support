#!/bin/bash
# Deploy AgentCore supervisor agent

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "🚀 Deploying AgentCore Supervisor Agent"
echo "========================================="
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment not activated. Activating..."
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        echo "❌ Virtual environment not found. Please run ./setup.sh first."
        exit 1
    fi
fi

# Check if AgentCore CLI is available
if ! command -v agentcore &> /dev/null; then
    echo "❌ AgentCore CLI not found. Please install:"
    echo "   pip install bedrock-agentcore-starter-toolkit"
    exit 1
fi

# Check if .bedrock_agentcore.yaml exists
if [ ! -f ".bedrock_agentcore.yaml" ]; then
    echo "❌ .bedrock_agentcore.yaml not found"
    exit 1
fi

echo "📋 Checking AgentCore configuration..."
agentcore status 2>/dev/null || echo "⚠️  No existing deployment found (this is OK for first deployment)"

echo ""
echo "📦 Deploying AgentCore..."
echo ""

# Deploy AgentCore
agentcore deploy

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "  1. Verify deployment: agentcore status"
echo "  2. Test the agent: agentcore invoke '{\"prompt\": \"Hello\", \"session_id\": \"test-001\"}'"
echo "  3. View logs: agentcore logs"
echo ""

