#!/bin/bash
# Main setup script for Multi-Agent Customer Support Platform
# This script helps new developers get started quickly

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Multi-Agent Customer Support Platform - Setup"
echo "=================================================="
echo ""

# Step 1: Check prerequisites
echo "📋 Step 1: Checking prerequisites..."
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi
echo "✅ Python 3: $(python3 --version)"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "⚠️  AWS CLI not found. Please install: https://aws.amazon.com/cli/"
    echo "   Continuing with setup, but you'll need AWS CLI for deployment..."
else
    echo "✅ AWS CLI: $(aws --version)"
fi

# Check Terraform
if ! command -v terraform &> /dev/null; then
    echo "⚠️  Terraform not found. Please install: https://www.terraform.io/downloads"
    echo "   Continuing with setup, but you'll need Terraform for infrastructure..."
else
    echo "✅ Terraform: $(terraform version | head -n 1)"
fi

# Check AgentCore CLI
if ! command -v agentcore &> /dev/null; then
    echo "⚠️  AgentCore CLI not found. Installing..."
    pip3 install bedrock-agentcore-starter-toolkit
    echo "✅ AgentCore CLI installed"
else
    echo "✅ AgentCore CLI: $(agentcore --version 2>/dev/null || echo 'installed')"
fi

echo ""
echo "📦 Step 2: Setting up virtual environment..."
echo ""

# Create virtual environment
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists. Removing old one..."
    rm -rf venv
fi

python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
echo ""
echo "📥 Installing Python dependencies..."
pip install -r requirements.txt

# All dependencies are in requirements.txt (UI included)

echo ""
echo "✅ Virtual environment setup complete!"
echo ""

# Step 3: Create .env file if it doesn't exist
echo "📝 Step 3: Setting up configuration..."
echo ""

if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cat > .env << 'EOF'
# AWS Configuration
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0

# Agent URLs (for local development)
SENTIMENT_AGENT_URL=http://127.0.0.1:9001
KNOWLEDGE_AGENT_URL=http://127.0.0.1:9002
TICKET_AGENT_URL=http://127.0.0.1:9003
RESOLUTION_AGENT_URL=http://127.0.0.1:9005
ESCALATION_AGENT_URL=http://127.0.0.1:9006

# These will be populated after Terraform deployment
# COGNITO_USER_POOL_ID=
# COGNITO_CLIENT_ID=
# COGNITO_DOMAIN=
# TICKETS_TABLE=
# KNOWLEDGE_BASE_BUCKET=
# VECTOR_BUCKET_NAME=
EOF
    echo "✅ Created .env file"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Configure AWS credentials:"
echo "   aws configure"
echo ""
echo "2. Deploy infrastructure:"
echo "   cd infrastructure/minimal"
echo "   terraform init"
echo "   terraform plan"
echo "   terraform apply"
echo ""
echo "3. Update .env with Terraform outputs:"
echo "   ./scripts/setup/update_env.sh"
echo ""
echo "4. Initialize knowledge base:"
echo "   python scripts/deploy/initialize_s3_vectors.py"
echo ""
echo "5. Deploy AgentCore:"
echo "   ./scripts/deploy/deploy_agentcore.sh"
echo ""
echo "6. Test the system:"
echo "   ./tests/test_all_agents.sh"
echo ""
echo "📚 For detailed instructions, see README.md"
echo ""
echo "To activate the virtual environment:"
echo "   source venv/bin/activate"

