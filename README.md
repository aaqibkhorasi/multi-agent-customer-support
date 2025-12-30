# Multi-Agent Customer Support Platform

A production-ready, intelligent customer support system built with **Amazon Bedrock AgentCore** and **AWS Strands Agents**. The platform uses a sophisticated multi-agent architecture where specialized AI agents collaborate via the A2A (Agent-to-Agent) protocol to deliver personalized, context-aware customer support.

## 🏗️ Architecture Overview

### Core Components
- **AgentCore Runtime** - Supervisor agent with memory and identity
- **A2A Protocol** - Agent-to-agent communication
- **MCP Gateway** - Lambda function integration
- **Bedrock Models** - Configurable AI models (default: Claude Haiku)
- **S3 Vector Storage** - Knowledge base with embeddings
- **Cognito Authentication** - OAuth and JWT support
- **Lambda Functions** - Sentiment analysis, knowledge search, ML classification

### Multi-Agent System
```
Customer Request → Supervisor Agent (AgentCore)
                      ↓
    ┌─────────────────────────────────────────────────────┐
    │  SentimentAgent (9001): Emotion analysis & urgency │
    │  KnowledgeAgent (9002): S3 vector search & solutions│
    │  TicketAgent (9003): Lifecycle management & tracking│
    │  ResolutionAgent (9005): Personalized responses    │
    │  EscalationAgent (9006): Human-in-the-loop escalation│
    └─────────────────────────────────────────────────────┘
                      ↓
              Lambda Functions (MCP)
    ┌─────────────────────────────────────────────────────┐
    │  sentiment_analysis: Amazon Comprehend integration  │
    │  knowledge_search: S3 vector embeddings search     │
    │  ticket_management: CRUD operations for tickets   │
    │  knowledge_ingestion: Article management (admin)   │
    └─────────────────────────────────────────────────────┘
```

## 🚀 Quick Start for New Developers

Get the system up and running in 5 simple steps:

### Prerequisites

1. **AWS CLI** configured with appropriate permissions
2. **Terraform** installed (>= 1.0)
3. **Python 3.11+** with virtual environment support
4. **AgentCore CLI** installed (`pip install bedrock-agentcore-starter-toolkit`)

### Step 1: Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd multi-agent-customer-support

# Run the main setup script (creates venv, installs dependencies, creates .env)
./setup.sh

# Activate virtual environment
source venv/bin/activate
```

**What `setup.sh` does:**
- ✅ Checks prerequisites (Python, AWS CLI, Terraform, AgentCore CLI)
- ✅ Creates virtual environment
- ✅ Installs all Python dependencies
- ✅ Creates `.env` file with defaults

### Step 2: Configure AWS Credentials

```bash
# Configure AWS credentials (if not already done)
aws configure

# Enter your:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region (e.g., us-east-1)
# - Default output format (json)
```

### Step 3: Deploy Infrastructure

```bash
# Navigate to infrastructure directory
cd infrastructure/minimal

# Initialize Terraform
terraform init

# Review what will be created
terraform plan

# Deploy infrastructure
terraform apply

# Return to project root
cd ../..
```

**What gets deployed:**
- DynamoDB tables (tickets, customers, feedback)
- S3 buckets (knowledge base, vector storage)
- Lambda functions (sentiment analysis, knowledge search, ticket management)
- Cognito User Pool (authentication)
- AgentCore Gateway (MCP Gateway for Lambda integration)
- IAM roles and policies
- SSM Parameter Store (for Gateway URL and Cognito credentials)

### Step 4: Update Configuration and Initialize Knowledge Base

```bash
# Update .env file with Terraform outputs
./scripts/setup/update_env.sh

# Initialize S3 Vector knowledge base with sample articles
python scripts/deploy/initialize_s3_vectors.py
```

**What these scripts do:**
- `update_env.sh`: Reads Terraform outputs and updates `.env` file
- `initialize_s3_vectors.py`: Creates S3 Vector indexes and ingests sample articles

### Step 5: Deploy AgentCore

```bash
# Deploy the supervisor agent to AgentCore Runtime
./scripts/deploy/deploy_agentcore.sh

# Verify deployment
agentcore status
```

**What gets deployed:**
- Supervisor agent with memory (STM_AND_LTM)
- HTTP endpoint at `/invocations`
- Session management enabled
- MCP tools integration

### Step 6: Test the System

```bash
# Test with a simple invocation
agentcore invoke '{"prompt": "How do I reset my password?", "session_id": "test-001"}'

# Or use the test scripts
./tests/test_all_agents.sh
```

## 📋 Quick Reference

**Setup (first time):**
```bash
./setup.sh                    # Initial setup
aws configure                 # Configure AWS credentials
cd infrastructure/minimal && terraform apply  # Deploy infrastructure
./scripts/setup/update_env.sh # Update configuration
python scripts/deploy/initialize_s3_vectors.py  # Initialize knowledge base
./scripts/deploy/deploy_agentcore.sh  # Deploy AgentCore
```

**Daily development:**
```bash
source venv/bin/activate      # Activate virtual environment
./scripts/deploy/start_dev.sh  # Start local development server
# OR
agentcore dev                  # Direct AgentCore dev command
```

**Running the UI:**
```bash
source venv/bin/activate
streamlit run ui/ui.py         # Start Streamlit UI
```

**Testing:**
```bash
./tests/test_all_agents.sh    # Test all agents
python tests/test_session_memory_complete.py  # Test memory
```

## 📁 Project Structure

```
multi-agent-customer-support/
├── setup.sh                  # Main setup script (run this first!)
├── Dockerfile                 # AgentCore deployment (supervisor + agents in same container)
├── agent.py                   # Supervisor agent entry point
├── requirements.txt           # All Python dependencies (UI included)
├── scripts/
│   ├── setup/                # Configuration scripts
│   │   ├── update_env.sh     # Update .env from Terraform
│   │   └── setup_venv.sh     # Virtual environment setup
│   └── deploy/               # Deployment scripts
│       ├── deploy_agentcore.sh
│       ├── start_dev.sh      # Start AgentCore dev server
│       ├── initialize_s3_vectors.py
│       └── manage_knowledge_base.py
├── tests/                    # Test scripts
│   ├── test_all_agents.sh
│   ├── test_session_memory_complete.py
│   └── check_bedrock_access.py
├── ui/                       # UI application
│   └── ui.py                 # Main Streamlit UI with authentication
├── infrastructure/           # Terraform infrastructure
├── agents/                   # Agent implementations
├── lambda/                   # Lambda functions
└── README.md                 # This file
```

See `scripts/README.md` and `tests/README.md` for detailed documentation.

## 🔧 Configuration

### Environment Variables (.env)

```bash
# AWS Configuration
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0

# Agent URLs (for local development)
SENTIMENT_AGENT_URL=http://127.0.0.1:9001
KNOWLEDGE_AGENT_URL=http://127.0.0.1:9002
TICKET_AGENT_URL=http://127.0.0.1:9003
RESOLUTION_AGENT_URL=http://127.0.0.1:9005
ESCALATION_AGENT_URL=http://127.0.0.1:9006

# AgentCore Gateway (automatically configured via Parameter Store)
# For local dev only - cloud deployments read from Parameter Store automatically
# AGENTCORE_GATEWAY_URL=https://your-gateway-url.amazonaws.com  # Optional for local dev

# Cognito (from Terraform outputs)
COGNITO_USER_POOL_ID=us-east-1_xxxxx
COGNITO_CLIENT_ID=xxxxx
COGNITO_DOMAIN=your-domain.auth.us-east-1.amazoncognito.com

# DynamoDB Tables (from Terraform outputs)
TICKETS_TABLE=dev-customer-support-tickets
CUSTOMERS_TABLE=dev-customer-support-customers
FEEDBACK_TABLE=dev-customer-support-feedback

# S3 Buckets (from Terraform outputs)
KNOWLEDGE_BASE_BUCKET=dev-customer-support-knowledge-base
VECTOR_BUCKET_NAME=dev-customer-support-vectors
```

### Terraform Variables (terraform.tfvars)

```hcl
aws_region = "us-east-1"
environment = "dev"
project_name = "customer-support"
admin_email = "your-admin@company.com"
```

## 🤖 Agent Architecture

### **Supervisor Agent** (AgentCore Runtime)
- **File**: `agent.py`
- **Role**: Central orchestrator and entry point
- **Features**: Memory persistence, A2A coordination, MCP integration
- **Endpoint**: `/invocations` (HTTP)
- **Session Management**: Automatic via `runtimeSessionId`

### **Specialized Agents** (A2A Servers)
1. **SentimentAgent** (Port 9001) - Emotion analysis & escalation
2. **KnowledgeAgent** (Port 9002) - S3 vector search & solutions  
3. **TicketAgent** (Port 9003) - Complete ticket lifecycle
4. **ResolutionAgent** (Port 9005) - Personalized response generation
5. **EscalationAgent** (Port 9006) - Human-in-the-loop escalation


See [agents/README.md](agents/README.md) for complete agent documentation.

## 📚 Request Formats

The agent supports **both** standard HTTP agent format and extended format for maximum compatibility.

### Standard HTTP Format (Recommended)

```bash
curl -X POST http://localhost:8081/invocations \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "user question",
    "session_id": "your-session-id"
  }'
```

**Fields:**
- `prompt` (required): The user's question or prompt
- `session_id` (optional): Session identifier for conversation continuity

### Extended Format

For more advanced use cases with additional context:

```bash
curl -X POST http://localhost:8081/invocations \
  -H "Content-Type: application/json" \
  -d '{
    "question": "user question",
    "context": {
      "runtimeSessionId": "session-id-from-agentcore",
      "user_id": "user123",
      "conversation_history": [
        {"role": "user", "content": "Previous question"},
        {"role": "assistant", "content": "Previous response"}
      ]
    }
  }'
```

**Fields:**
- `question` (required): The user's question
- `context` (optional): Additional context object
  - `user_id`: User identifier for LTM
  - `runtimeSessionId`: AgentCore session ID (33+ characters)
  - `conversation_history`: Previous messages in the session

## 🧠 Session Memory

The system uses **AgentCore Runtime** for session management with **STM_AND_LTM** (Short-Term Memory + Long-Term Memory).

### Memory Types

**STM (Short-Term Memory):**
- Session-level conversation context
- Cleared when session ends (15 min idle, 8 hours max)
- Use case: Current conversation flow

**LTM (Long-Term Memory):**
- Persistent user context across sessions
- 30-day expiry
- Use case: User preferences, past interactions

### Testing Memory

```bash
SESSION_ID="my-session-123"

# First message (establishes context)
curl -X POST http://localhost:8081/invocations \
  -H "Content-Type: application/json" \
  -d "{
    \"prompt\": \"My name is John and I need help with password reset\",
    \"session_id\": \"$SESSION_ID\"
  }"

# Follow-up (remembers context)
curl -X POST http://localhost:8081/invocations \
  -H "Content-Type: application/json" \
  -d "{
    \"prompt\": \"What was my issue?\",
    \"session_id\": \"$SESSION_ID\"
  }"

# Cross-session (LTM - different session, same user_id)
curl -X POST http://localhost:8081/invocations \
  -H "Content-Type: application/json" \
  -d "{
    \"prompt\": \"What did I tell you before?\",
    \"context\": {
      \"user_id\": \"user123\",
      \"runtimeSessionId\": \"new-session-456\"
    }
  }"
```

**Note**: Session IDs must be **33+ characters** (AgentCore requirement). Use UUIDs for session IDs.

## 🛠️ Development

### Local Development

```bash
# Run supervisor locally (specialized agents start automatically in background threads)
agentcore dev --port 8081

# Test the system
python tests/test_session_memory_complete.py
```

### Testing Examples

**Test Knowledge Agent:**
```bash
curl -X POST http://localhost:8081/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "How do I reset my password?", "session_id": "test-001"}'
```

**Test Sentiment Analysis:**
```bash
curl -X POST http://localhost:8081/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "I am very frustrated!", "session_id": "test-002"}'
```

**Test Ticket Creation:**
```bash
curl -X POST http://localhost:8081/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create a ticket for billing issue", "session_id": "test-003"}'
```

**Test Memory (STM):**
```bash
# First message
curl -X POST http://localhost:8081/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "My name is John", "session_id": "memory-test-001"}'

# Follow-up (should remember name)
curl -X POST http://localhost:8081/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is my name?", "session_id": "memory-test-001"}'
```

## 📊 Monitoring

### AgentCore Status

```bash
# Check agent status
agentcore status

# View logs
agentcore logs

# Monitor in real-time
agentcore dev --verbose
```

### AWS Resources

- **CloudWatch**: Logs and metrics
- **X-Ray**: Distributed tracing
- **Lambda**: Function monitoring
- **S3**: Storage metrics

## 🔒 Security Features

- **Cognito Authentication**: OAuth 2.0 and JWT
- **IAM Roles**: Least privilege access
- **Encryption**: Data in transit and at rest
- **Environment Variables**: No hardcoded secrets
- **Session Management**: Secure session handling

## 📚 Documentation

### Folder-Based Documentation

- **[agents/README.md](agents/README.md)** - Complete agent documentation, architecture, and workflows
- **[lambda/README.md](lambda/README.md)** - Lambda functions documentation, testing, and deployment
- **[infrastructure/README.md](infrastructure/README.md)** - Terraform infrastructure, Gateway setup, Cognito, and Bedrock configuration

### Quick Reference

- **Agents**: See `agents/README.md` for agent roles, communication protocols, and testing
- **Lambda Functions**: See `lambda/README.md` for Lambda operations, input/output formats, and monitoring
- **Infrastructure**: See `infrastructure/README.md` for deployment, Gateway, Cognito, and Bedrock setup

## 🎯 Production Deployment

1. **Set Production Environment**:
   ```bash
   export ENVIRONMENT=production
   ```

2. **Update Terraform Variables**:
   ```hcl
   environment = "prod"
   enable_vpc = true  # Recommended for production
   ```

3. **Deploy**:
   ```bash
   terraform apply
   python scripts/deploy/initialize_s3_vectors.py
   agentcore deploy
   ```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with proper configuration
4. Test with deployment checklist
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Built with ❤️ using Amazon Bedrock AgentCore and AWS Strands Agents**
