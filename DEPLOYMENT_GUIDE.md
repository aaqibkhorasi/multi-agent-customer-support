# Deployment Guide

Complete step-by-step guide for deploying the Multi-Agent Customer Support Platform to your AWS account.

## Prerequisites

Before starting, ensure you have:

1. **AWS Account** with appropriate permissions
2. **AWS CLI** installed and configured (`aws configure`)
3. **Terraform** >= 1.0 installed
4. **Python** 3.11+ installed
5. **AgentCore CLI** installed (`pip install bedrock-agentcore-starter-toolkit`)

## Step-by-Step Deployment

### Step 1: Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd multi-agent-customer-support

# Run the setup script
./setup.sh

# Activate virtual environment
source venv/bin/activate
```

**What `setup.sh` does:**
- Checks prerequisites (Python, AWS CLI, Terraform, AgentCore CLI)
- Creates virtual environment (`venv/`)
- Installs all Python dependencies from `requirements.txt`
- Creates `.env` file with default values

### Step 2: Configure AWS Credentials

```bash
# Configure AWS credentials (if not already done)
aws configure

# Enter your:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region (e.g., us-east-1)
# - Default output format (json)

# Verify AWS access
aws sts get-caller-identity
```

**Required AWS Permissions:**
- Bedrock (InvokeModel, CreateMemory, etc.)
- Lambda (CreateFunction, UpdateFunctionCode, etc.)
- DynamoDB (CreateTable, PutItem, etc.)
- S3 (CreateBucket, PutObject, etc.)
- Cognito (CreateUserPool, CreateUserPoolClient, etc.)
- IAM (CreateRole, AttachRolePolicy, etc.)
- SSM (PutParameter, GetParameter, etc.)
- AgentCore (CreateRuntime, CreateGateway, etc.)

### Step 3: Configure Terraform Variables

```bash
# Navigate to infrastructure directory
cd infrastructure/minimal

# Copy example variables file
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars with your values
# Required: aws_region, environment, project_name, admin_email
```

**Example `terraform.tfvars`:**
```hcl
aws_region = "us-east-1"
environment = "dev"
project_name = "customer-support"
admin_email = "your-email@company.com"
```

### Step 4: Deploy Infrastructure

```bash
# Initialize Terraform
terraform init

# Review what will be created
terraform plan

# Deploy infrastructure (this may take 10-15 minutes)
terraform apply

# Type 'yes' when prompted
```

**What gets deployed:**
- DynamoDB tables (tickets, customers, feedback)
- S3 buckets (knowledge base, vector storage)
- Lambda functions (sentiment_analysis, knowledge_search, ticket_management, knowledge_ingestion)
- Cognito User Pool (authentication)
- AgentCore Gateway (MCP Gateway for Lambda integration)
- IAM roles and policies
- SSM Parameter Store (for Gateway URL and Cognito credentials)

**Expected Output:**
- Gateway URL stored in SSM: `/dev-customer-support/agentcore-gateway-url`
- Cognito User Pool ID and Client ID
- DynamoDB table names
- S3 bucket names

### Step 5: Update Environment Configuration

```bash
# Return to project root
cd ../..

# Update .env file with Terraform outputs
./scripts/setup/update_env.sh
```

**What this does:**
- Reads Terraform outputs
- Updates `.env` file with:
  - Cognito configuration (User Pool ID, Client ID, Domain)
  - DynamoDB table names
  - S3 bucket names
  - Gateway URL (optional, read from SSM at runtime)

### Step 6: Initialize Knowledge Base

```bash
# Initialize S3 Vector knowledge base with sample articles
python scripts/deploy/initialize_s3_vectors.py
```

**What this does:**
- Creates S3 Vector indexes for knowledge base
- Ingests sample articles from `knowledge-base/sample-articles.json`
- Validates knowledge base setup

**Expected Output:**
- S3 Vector indexes created
- Sample articles ingested
- Knowledge base ready for queries

### Step 7: Deploy AgentCore

```bash
# Deploy the supervisor agent to AgentCore Runtime
./scripts/deploy/deploy_agentcore.sh
```

**What this does:**
- Checks AgentCore configuration (`.bedrock_agentcore.yaml`)
- Deploys supervisor agent to AgentCore Runtime
- Specialized agents start automatically in background threads (same container)
- Verifies deployment

**Expected Output:**
- Agent deployed: `customer_support_supervisor`
- Agent ARN: `arn:aws:bedrock-agentcore:...`
- Endpoint ready: `/invocations`

### Step 8: Verify Deployment

```bash
# Check agent status
agentcore status

# Test with a simple invocation
agentcore invoke '{"prompt": "How do I reset my password?", "session_id": "test-001"}'

# Or run test scripts
./tests/test_all_agents.sh
```

**Expected Output:**
- Agent status: `Ready`
- Test invocation returns response
- All agents respond correctly

## Post-Deployment Configuration

### Create Cognito Users (Optional)

```bash
# Create a test user in Cognito
aws cognito-idp admin-create-user \
  --user-pool-id <USER_POOL_ID> \
  --username testuser \
  --user-attributes Name=email,Value=test@example.com \
  --temporary-password TempPass123! \
  --message-action SUPPRESS

# Set permanent password
aws cognito-idp admin-set-user-password \
  --user-pool-id <USER_POOL_ID> \
  --username testuser \
  --password YourPassword123! \
  --permanent
```

### Access the UI

```bash
# Start Streamlit UI
streamlit run ui/ui.py

# Open browser to http://localhost:8501
# Sign in with Cognito credentials
```

## Troubleshooting

### Common Issues

1. **Terraform Apply Fails**
   - Check AWS credentials: `aws sts get-caller-identity`
   - Verify region is correct: `aws configure get region`
   - Check IAM permissions
   - Review Terraform error messages

2. **Lambda Deployment Fails**
   - Ensure Lambda function code exists in `lambda/` directories
   - Check `requirements.txt` for each Lambda
   - Verify IAM role has correct permissions

3. **AgentCore Deployment Fails**
   - Check `.bedrock_agentcore.yaml` exists
   - Verify AWS credentials have Bedrock permissions
   - Check AgentCore CLI is installed: `agentcore --version`

4. **Knowledge Base Initialization Fails**
   - Verify S3 Vector bucket exists
   - Check `.env` has `VECTOR_BUCKET_NAME`
   - Ensure AWS credentials have S3 permissions

5. **Agent Not Responding**
   - Check agent status: `agentcore status`
   - View logs: `agentcore logs`
   - Verify Gateway URL in SSM Parameter Store
   - Check CloudWatch logs for errors

### Getting Help

- Check CloudWatch Logs for detailed error messages
- Review Terraform outputs: `terraform output`
- Verify SSM Parameters: `aws ssm get-parameter --name /dev-customer-support/agentcore-gateway-url`
- Check agent logs: `agentcore logs`

## Cost Estimation

Approximate monthly costs (us-east-1, light usage):

- **DynamoDB**: $1-5 (pay-per-request)
- **Lambda**: $1-10 (based on invocations)
- **S3 Standard**: $1-5 (based on storage)
- **S3 Vector**: $10-50 (based on vector operations)
- **Cognito**: $0-5 (first 50,000 MAUs free)
- **CloudWatch Logs**: $1-5 (based on log volume)
- **AgentCore Runtime**: ~$50-200 (consumption-based)

**Total Estimated Cost**: $65-280/month for development environment

## Next Steps

After successful deployment:

1. **Test All Agents**: Run `./tests/test_all_agents.sh`
2. **Test Memory**: Run `python tests/test_session_memory_complete.py`
3. **Test UI**: Start UI and test authentication
4. **Add Knowledge Articles**: Use `python scripts/deploy/manage_knowledge_base.py`
5. **Monitor**: Set up CloudWatch alarms and dashboards
6. **Scale**: Adjust Lambda concurrency and DynamoDB capacity as needed

## Production Deployment

For production deployment:

1. **Update Environment**: Set `environment = "prod"` in `terraform.tfvars`
2. **Enable VPC**: Set `enable_vpc = true` (adds ~$45/month for NAT Gateway)
3. **Increase Log Retention**: Set `log_retention_days = 30` or higher
4. **Enable Monitoring**: Set up CloudWatch alarms and SNS notifications
5. **Review Security**: Enable encryption, VPC endpoints, and security groups
6. **Backup**: Set up DynamoDB backups and S3 versioning

## Cleanup

To remove all resources:

```bash
cd infrastructure/minimal
terraform destroy
```

**Warning**: This will delete all resources including data. Make sure to backup important data first.

