#!/bin/bash
# Start AgentCore in development mode (local testing)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "🚀 Starting AgentCore Dev Server"
echo "================================="
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "✅ Activating virtual environment..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "✅ Activating virtual environment..."
    source .venv/bin/activate
fi

# Set AWS environment variables
export AWS_REGION=${AWS_REGION:-us-east-1}
export AWS_DEFAULT_REGION=$AWS_REGION

# Load .env if it exists
if [ -f ".env" ]; then
    echo "✅ Loading .env file..."
    set -a
    source .env
    set +a
fi

# Verify AWS credentials
echo "🔍 Verifying AWS credentials..."
python3 << 'PYTHON'
import boto3
import sys

try:
    session = boto3.Session(region_name='us-east-1')
    creds = session.get_credentials()
    if creds:
        print(f"✅ Credentials found: {creds.access_key[:10]}...")
    else:
        print("❌ No credentials found!")
        sys.exit(1)
    
    # Test Bedrock
    bedrock = session.client('bedrock-runtime')
    print("✅ Bedrock Runtime client created")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
PYTHON

if [ $? -ne 0 ]; then
    echo "❌ AWS credentials check failed"
    exit 1
fi

echo ""
echo "✅ Environment ready"
echo "   Region: $AWS_REGION"
echo "   Starting agentcore dev..."
echo ""

# Start agentcore dev
exec agentcore dev

