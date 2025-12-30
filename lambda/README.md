# Lambda Functions Documentation

This directory contains all AWS Lambda functions used by the multi-agent customer support system.

## Overview

Lambda functions are exposed as **MCP (Model Context Protocol) tools** via the **AgentCore Gateway**. Specialized agents call these tools to perform operations like sentiment analysis, knowledge search, and ticket management.

## Architecture

```
Specialized Agent
    ↓ (MCP Tool Call)
AgentCore Gateway
    ↓ (AWS_IAM Authentication)
Lambda Function
    ↓ (AWS Service)
AWS Service (DynamoDB, S3, Comprehend, etc.)
```

## Available Lambda Functions

### 1. ✅ sentiment_analysis

**File**: `sentiment_analysis/main.py`  
**Used By**: SentimentAgent  
**MCP Tool**: `dev-customer-support-sentiment-analysis-target___sent`  
**Status**: ✅ **ACTIVE - Keep**

**Purpose:**
- Analyze customer sentiment and urgency
- Determine emotional tone (POSITIVE, NEGATIVE, NEUTRAL, MIXED)
- Calculate confidence scores
- Assess urgency levels

**Input:**
```json
{
  "text": "I am extremely frustrated with this service!"
}
```

**Output:**
```json
{
  "sentiment": "NEGATIVE",
  "score": 0.95,
  "confidence": 0.92,
  "urgency": "high",
  "requires_escalation": true
}
```

**AWS Services Used:**
- Amazon Comprehend (sentiment analysis)
- Amazon Bedrock (optional, for advanced analysis)

---

### 2. ✅ knowledge_search

**File**: `knowledge_search/main.py`  
**Used By**: KnowledgeAgent  
**MCP Tool**: `dev-customer-support-knowledge-search-target___search`  
**Status**: ✅ **ACTIVE - Keep**

**Purpose:**
- Search S3 Vector knowledge base for relevant articles
- Find solutions to customer questions
- Retrieve how-to guides and documentation

**Input:**
```json
{
  "query": "password reset",
  "category": "account",
  "max_results": 5,
  "language": "en"
}
```

**Output:**
```json
{
  "results": [
    {
      "title": "How to Reset Your Password",
      "content": "To reset your password...",
      "relevance_score": 0.92,
      "category": "account"
    }
  ],
  "total_results": 1
}
```

**AWS Services Used:**
- S3 Vector (knowledge base storage)
- Amazon Bedrock (embeddings)

---

### 3. ✅ ticket_management

**File**: `ticket_management/main.py`  
**Used By**: TicketAgent  
**MCP Tool**: `dev-customer-support-ticket-management-target___ticket`  
**Status**: ✅ **ACTIVE - Keep**

**Purpose:**
- CRUD operations for support tickets
- Create, retrieve, update, and list tickets
- Manage ticket lifecycle

**Operations:**

#### Create Ticket
**Input:**
```json
{
  "operation": "create",
  "data": {
    "user_id": "user123",
    "customer_email": "user@example.com",
    "subject": "Password Reset Issue",
    "description": "I cannot log in to my account",
    "category": "technical",
    "priority": "high"
  }
}
```

**Output:**
```json
{
  "status": "success",
  "ticket_id": "TICKET-ABC123",
  "message": "Ticket created successfully."
}
```

#### Get Ticket
**Input:**
```json
{
  "operation": "get",
  "data": {
    "ticket_id": "TICKET-ABC123"
  }
}
```

**Output:**
```json
{
  "status": "success",
  "ticket": {
    "ticket_id": "TICKET-ABC123",
    "status": "open",
    "priority": "high",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

#### Update Ticket Status
**Input:**
```json
{
  "operation": "update_status",
  "data": {
    "ticket_id": "TICKET-ABC123",
    "status": "resolved"
  }
}
```

**Output:**
```json
{
  "status": "success",
  "ticket": {
    "ticket_id": "TICKET-ABC123",
    "status": "resolved",
    "updated_at": "2024-01-15T11:00:00Z"
  }
}
```

#### List Tickets
**Input:**
```json
{
  "operation": "list",
  "data": {
    "filters": {
      "customer_email": "user@example.com",
      "status": "open"
    }
  }
}
```

**Output:**
```json
{
  "status": "success",
  "tickets": [...],
  "count": 3
}
```

**AWS Services Used:**
- DynamoDB (ticket storage)

---

### 4. ⚠️ knowledge_ingestion

**File**: `knowledge_ingestion/main.py`  
**Used By**: None (admin/maintenance function)  
**MCP Tool**: Not exposed (admin use only)  
**Status**: ⚠️ **ADMIN - Keep for maintenance**

**Purpose:**
- Ingest articles into knowledge base
- Update knowledge base content
- Manage article lifecycle

**When to Use:**
- Initial knowledge base setup
- Adding new articles
- Updating existing articles
- Bulk ingestion operations

**Note**: This function is not used by agents but is useful for knowledge base management.

---

## Lambda Function Summary

| Lambda Function | Used By | Status | Recommendation |
|----------------|---------|--------|----------------|
| `sentiment_analysis` | SentimentAgent | ✅ Active | **Keep** - Essential |
| `knowledge_search` | KnowledgeAgent | ✅ Active | **Keep** - Core functionality |
| `ticket_management` | TicketAgent | ✅ Active | **Keep** - Essential |
| `knowledge_ingestion` | None (admin) | ⚠️ Admin | **Keep** - Maintenance |

## Deployment

### Terraform Deployment

Lambda functions are deployed via Terraform:

```bash
cd infrastructure/minimal
terraform apply
```

**What Gets Deployed:**
- Lambda function code (packaged as ZIP)
- Lambda function URLs (for direct HTTP access)
- CloudWatch log groups
- IAM roles and policies
- Gateway targets (MCP tools)

### Manual Deployment

For local testing or manual deployment:

```bash
# Package Lambda function
cd lambda/sentiment_analysis
zip -r function.zip main.py requirements.txt

# Deploy via AWS CLI
aws lambda update-function-code \
  --function-name dev-customer-support-sentiment-analysis \
  --zip-file fileb://function.zip
```

## Testing

### Test via MCP Tool (Recommended)

```bash
# Test through AgentCore Gateway
# (Requires Cognito authentication)
curl -X POST https://your-gateway-url.amazonaws.com/tools/invoke \
  -H "Authorization: Bearer <cognito-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "dev-customer-support-sentiment-analysis-target___sent",
    "arguments": {"text": "I am very frustrated!"}
  }'
```

### Test via Lambda Function URL (Direct)

```bash
# Test sentiment_analysis directly
curl -X POST https://your-lambda-url.lambda-url.us-east-1.on.aws/ \
  -H "Content-Type: application/json" \
  -d '{"text": "I am very frustrated!"}'
```

### Test via Agent

```bash
# Test through Supervisor Agent
curl -X POST http://localhost:8081/invocations \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "I am very frustrated!",
    "session_id": "test-session-001"
  }'
```

## Environment Variables

Lambda functions use environment variables configured in Terraform:

```bash
# Common variables
TICKETS_TABLE=dev-customer-support-tickets
KNOWLEDGE_BASE_BUCKET=dev-customer-support-knowledge-base
VECTOR_BUCKET_NAME=dev-customer-support-vectors
AWS_REGION=us-east-1
```

## Monitoring

### CloudWatch Logs

Each Lambda function has a CloudWatch log group:

```bash
# View logs
aws logs tail /aws/lambda/dev-customer-support-sentiment-analysis --follow

# View logs for all functions
aws logs tail /aws/lambda/dev-customer-support-knowledge-search --follow
aws logs tail /aws/lambda/dev-customer-support-ticket-management --follow
```

### CloudWatch Metrics

Monitor Lambda performance:

```bash
# View metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=dev-customer-support-sentiment-analysis \
  --start-time 2024-01-15T00:00:00Z \
  --end-time 2024-01-15T23:59:59Z \
  --period 3600 \
  --statistics Sum
```

## Cost Analysis

### Estimated Monthly Costs (us-east-1, light usage)

- **sentiment_analysis**: $1-5 (based on invocations)
- **knowledge_search**: $1-5 (based on invocations)
- **ticket_management**: $1-5 (based on invocations)
- **knowledge_ingestion**: $0-1 (occasional usage)

**Total Estimated Cost**: $3-16/month for development environment

## Troubleshooting

### Common Issues

1. **Lambda Timeout**
   - Increase timeout in Terraform configuration
   - Check CloudWatch logs for errors
   - Optimize function code

2. **Permission Errors**
   - Verify IAM role has correct permissions
   - Check DynamoDB table access
   - Verify S3 bucket access

3. **MCP Tool Not Found**
   - Verify Gateway target is configured
   - Check Gateway logs
   - Verify Lambda function name matches

4. **Import Errors**
   - Ensure `requirements.txt` includes all dependencies
   - Check Lambda layer configuration
   - Verify Python runtime version

## File Structure

```
lambda/
├── sentiment_analysis/
│   ├── main.py              # Lambda handler
│   └── requirements.txt      # Dependencies
├── knowledge_search/
│   ├── main.py              # Lambda handler
│   └── requirements.txt      # Dependencies
├── ticket_management/
│   ├── main.py              # Lambda handler (handles create, get, update, list)
│   └── requirements.txt      # Dependencies
├── knowledge_ingestion/
│   └── main.py              # Lambda handler (admin/maintenance)
└── README.md                # This file
```

## Additional Resources

- **Infrastructure**: See `../infrastructure/README.md` for Terraform configuration
- **Agents**: See `../agents/README.md` for agent documentation
- **Gateway**: See `../infrastructure/README.md` for Gateway setup

