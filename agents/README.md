# Agents Documentation

This directory contains all specialized agents for the multi-agent customer support system.

## Overview

The system uses a **Supervisor Agent** (orchestrator) that routes requests to **Specialized Agents** via the A2A (Agent-to-Agent) protocol. Specialized agents use MCP tools to invoke Lambda functions.

## Architecture

```
Customer Request
    ↓
Supervisor Agent (AgentCore Runtime)
    ↓
Routes to Specialized Agents (A2A Protocol)
    ↓
Specialized Agents use MCP Tools (Lambda Functions)
    ↓
Results returned to Supervisor
    ↓
Supervisor compiles final response
```

## Available Agents

### 1. 🔵 SupervisorAgent (Main Orchestrator)

**Location**: AgentCore Runtime (deployed)  
**File**: `../agent.py`  
**Port**: N/A (AgentCore managed)  
**Lambda**: None (orchestrator only)

**What It Does:**
- Central orchestrator that routes requests to specialized agents
- Analyzes customer requests and determines intent
- Routes to appropriate specialized agents via A2A protocol
- Coordinates multi-agent workflows
- Manages session and memory (STM + LTM)
- Compiles responses from specialized agents

**Status**: ✅ **ESSENTIAL - Keep**

---

### 2. 🟡 SentimentAgent (Port 9001)

**File**: `sentiment_agent.py`  
**Lambda**: ✅ `sentiment_analysis`  
**MCP Tool**: ✅ `dev-customer-support-sentiment-analysis-target___sent`

**What It Does:**
- Analyzes customer messages for emotional tone
- Determines sentiment (POSITIVE, NEGATIVE, NEUTRAL, MIXED)
- Calculates sentiment confidence scores
- Assesses urgency level (low, medium, high, critical)
- Recommends escalation if needed

**How It Works:**
1. Supervisor routes emotional messages to SentimentAgent
2. SentimentAgent calls MCP tool `___sent`
3. Gateway invokes `sentiment_analysis` Lambda
4. Lambda uses Amazon Comprehend or Bedrock for analysis
5. Returns sentiment, score, confidence, escalation flags

**Status**: ✅ **ESSENTIAL - Keep**

---

### 3. 🟢 KnowledgeAgent (Port 9002)

**File**: `knowledge_agent.py`  
**Lambda**: ✅ `knowledge_search`  
**MCP Tool**: ✅ `dev-customer-support-knowledge-search-target___search`

**What It Does:**
- Searches S3 Vector knowledge base for relevant articles
- Finds solutions to customer questions
- Retrieves how-to guides and documentation
- Provides product/feature information

**How It Works:**
1. Supervisor routes information queries to KnowledgeAgent
2. KnowledgeAgent calls MCP tool `___search`
3. Gateway invokes `knowledge_search` Lambda
4. Lambda searches S3 Vector storage using embeddings
5. Returns relevant articles with scores

**Status**: ✅ **ESSENTIAL - Keep**

---

### 4. 🟠 TicketAgent (Port 9003)

**File**: `ticket_agent.py`  
**Lambda**: ✅ `ticket_management`  
**MCP Tool**: ✅ `dev-customer-support-ticket-management-target___ticket`

**What It Does:**
- Create new support tickets in DynamoDB
- Retrieve ticket information by ticket_id
- Update ticket status (open → in-progress → resolved → closed)
- List tickets by customer, status, or priority

**Operations:**
- `create`: Create new ticket
- `get`: Retrieve ticket by ID
- `update_status`: Update ticket status
- `list`: List tickets by customer/status/priority

**Status**: ✅ **ESSENTIAL - Keep**

---

### 5. 🔴 ResolutionAgent (Port 9005)

**File**: `resolution_agent.py`  
**Lambda**: None (uses LLM only)  
**MCP Tool**: None

**What It Does:**
- Generate personalized resolution responses
- Analyze ticket data, sentiment, and knowledge base results
- Determine resolution confidence and approach
- Create step-by-step solutions
- Escalate complex issues when needed

**How It Works:**
1. Supervisor routes to ResolutionAgent with context:
   - Sentiment analysis results
   - Knowledge base articles
   - Ticket information
   - Customer tier and preferences
2. ResolutionAgent uses LLM (Bedrock) to generate response
3. No tools needed - pure LLM generation
4. Returns personalized response to Supervisor

**Status**: ✅ **ESSENTIAL - Keep**

---

### 6. ⚫ EscalationAgent (Port 9006)

**File**: `escalation_agent.py`  
**Lambda**: ✅ ticket_management (via MCP)  
**MCP Tool**: ✅ `dev-customer-support-ticket-management-target___ticket`

**What It Does:**
- Evaluate if issue requires human support
- **AUTOMATICALLY create priority tickets** when escalation is determined
- Use actual ticket IDs as escalation references (stored in DynamoDB)
- Set response time expectations based on priority

**Escalation Criteria:**
- **ALWAYS escalate if**:
  * Customer explicitly requests human agent
  * NEGATIVE sentiment + high confidence (>0.8) + high urgency
  * Enterprise/Premium customer with negative sentiment
  * Security-related issues (breach, fraud, account compromise)
  * Billing disputes or payment issues

**Autonomous Capabilities:**
- ✅ Creates tickets automatically via MCP tool
- ✅ Maps escalation priority to ticket priority (critical/high/medium/low)
- ✅ Sets ticket status to "escalated"
- ✅ Uses actual ticket ID as escalation reference
- ✅ Stores escalation in DynamoDB for tracking

**Status**: ✅ **ESSENTIAL - Autonomous**

---


## Agent Summary

| Agent | Port | Lambda | MCP Tool | Status | Needed? |
|-------|------|--------|----------|--------|---------|
| SupervisorAgent | N/A | None | None | ✅ Working | ✅ **YES** |
| SentimentAgent | 9001 | ✅ sentiment_analysis | ✅ ___sent | ✅ Working | ✅ **YES** |
| KnowledgeAgent | 9002 | ✅ knowledge_search | ✅ ___search | ✅ Working | ✅ **YES** |
| TicketAgent | 9003 | ✅ ticket_management | ✅ ___ticket | ✅ Working | ✅ **YES** |
| ResolutionAgent | 9005 | None (LLM) | None | ✅ Working | ✅ **YES** |
| EscalationAgent | 9006 | ✅ ticket_management | ✅ ___ticket | ✅ Autonomous | ✅ **YES** |

## Communication Protocols

### A2A (Agent-to-Agent) Protocol

**Purpose**: Communication between Supervisor and Specialized Agents  
**Protocol**: HTTP REST API  
**Format**: JSON messages  
**Flow**: Supervisor → Specialized Agents

**Example Flow**:
```
Supervisor Agent
  ↓ (A2A HTTP Request)
  POST http://127.0.0.1:9002/message
  {
    "message": "Search for password reset instructions",
    "context": {...}
  }
  ↓
Knowledge Agent
  ↓ (Processes and calls MCP tool)
  ↓
Returns result to Supervisor
```

### MCP (Model Context Protocol)

**Purpose**: Communication between Specialized Agents and Lambda Functions  
**Protocol**: MCP over HTTP (via AgentCore Gateway)  
**Authentication**: Cognito JWT (Gateway) → AWS_IAM (Lambda)  
**Flow**: Specialized Agents → Gateway → Lambda Functions

**Example Flow**:
```
Knowledge Agent
  ↓ (MCP Tool Call)
  Tool: "dev-customer-support-knowledge-search-target___search"
  Arguments: {"query": "password reset"}
  ↓
AgentCore Gateway
  ↓ (Validates JWT, routes to Lambda)
  ↓
Knowledge Search Lambda
  ↓ (Searches S3 Vector)
  ↓
Returns results to Gateway → Agent
```

## Running Agents

### Same Container Approach (Current)

All specialized agents run in the **same Docker container** as the supervisor agent, making them accessible via `localhost` in AgentCore Runtime.

**Benefits:**
- ✅ No separate deployment needed
- ✅ Localhost access (same container network)
- ✅ Works automatically in AgentCore Runtime
- ✅ Simpler architecture
- ✅ Resource efficient

**How It Works:**
- Agents start automatically in background threads when supervisor initializes
- All agents accessible via `http://127.0.0.1:9001-9006`
- Supervisor discovers agents via A2A protocol

**Configuration:**
```python
# In agent.py
from shared.utils.agent_starter import start_all_agents_in_background

# Start all agents in background threads
threads = start_all_agents_in_background()
```

### Local Development

For local development, you can:

**Option 1**: Let supervisor start agents automatically (if in container)  
**Option 2**: Start agents separately:
```bash
python -m agents.sentiment_agent
python -m agents.knowledge_agent
python -m agents.ticket_agent
# etc.
```

**Option 3**: Disable background agents:
```bash
export DISABLE_BACKGROUND_AGENTS=true
```

## Typical Workflow Examples

### Example 1: "I am upset! How do I cancel my subscription?"

```
1. Customer Request
   ↓
2. SupervisorAgent
   - Analyzes request
   - Detects emotional language
   ↓
3. Routes to SentimentAgent (A2A)
   - SentimentAgent → MCP Tool → sentiment_analysis Lambda
   - Returns: NEGATIVE, high urgency, confidence 0.95
   ↓
4. Routes to EscalationAgent (A2A)
   - EscalationAgent creates escalation (LLM)
   - Returns: ESC-12345, priority: high, response time: 2 hours
   ↓
5. Routes to KnowledgeAgent (A2A)
   - KnowledgeAgent → MCP Tool → knowledge_search Lambda
   - Returns: Articles about subscription cancellation
   ↓
6. Routes to ResolutionAgent (A2A)
   - ResolutionAgent generates response (LLM)
   - Combines: sentiment acknowledgment + escalation info + cancellation steps
   ↓
7. Supervisor compiles final response
   ↓
8. Customer receives: 
   "I understand your frustration. I've escalated your issue (ESC-12345). 
    Here's how to cancel: [steps from knowledge base]"
```

### Example 2: "Create a ticket for password reset"

```
1. Customer Request
   ↓
2. SupervisorAgent
   - Analyzes request
   - Detects ticket creation need
   ↓
3. Routes to TicketAgent (A2A)
   - TicketAgent → MCP Tool → ticket_management Lambda
   - Lambda creates ticket in DynamoDB
   - Returns: TICKET-ABC123, status: open
   ↓
4. Routes to ResolutionAgent (A2A)
   - ResolutionAgent generates response (LLM)
   ↓
5. Supervisor compiles final response
   ↓
6. Customer receives: "Ticket TICKET-ABC123 created successfully"
```

## Testing

### Test Individual Agents

```bash
# Test SentimentAgent
curl -X POST http://127.0.0.1:9001/message \
  -H "Content-Type: application/json" \
  -d '{"message": "I am very frustrated!"}'

# Test KnowledgeAgent
curl -X POST http://127.0.0.1:9002/message \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I reset my password?"}'

# Test TicketAgent
curl -X POST http://127.0.0.1:9003/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Create a ticket for billing issue"}'
```

### Test Multi-Agent Flow

```bash
# Test through Supervisor
curl -X POST http://localhost:8081/invocations \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "I am upset! How do I cancel my subscription?",
    "session_id": "test-session-001"
  }'
```

## Recommendations

### ✅ Keep These Agents (6/7):
1. **SupervisorAgent** - Core orchestrator (essential)
2. **SentimentAgent** - Sentiment analysis (essential)
3. **KnowledgeAgent** - Knowledge base search (essential)
4. **TicketAgent** - Ticket management (essential)
5. **ResolutionAgent** - Response generation (essential)
6. **EscalationAgent** - Human escalation (useful)

### Total: 6 Agents (Supervisor + 5 Specialized)

## File Structure

```
agents/
├── __init__.py              # Agent imports
├── base.py                   # BaseAgent class
├── sentiment_agent.py        # SentimentAgent (Port 9001)
├── knowledge_agent.py        # KnowledgeAgent (Port 9002)
├── ticket_agent.py          # TicketAgent (Port 9003)
├── resolution_agent.py      # ResolutionAgent (Port 9005)
├── escalation_agent.py       # EscalationAgent (Port 9006)
└── README.md                # This file
```

## Additional Resources

- **Supervisor Agent**: See `../agent.py` for the main orchestrator
- **Lambda Functions**: See `../lambda/README.md` for Lambda documentation
- **Infrastructure**: See `../infrastructure/README.md` for deployment details
- **Main README**: See `../README.md` for overall project documentation

