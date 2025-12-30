# Customer Support Platform - Terraform Infrastructure

This directory contains the Terraform infrastructure code for the Customer Support Platform, organized in a professional modular structure.

## Architecture Overview

The infrastructure is organized into the following modules:

- **IAM Module** (`modules/iam/`) - Manages all IAM roles, policies, and permissions
- **DynamoDB Module** (`modules/dynamodb/`) - Manages DynamoDB tables for tickets, customers, and feedback
- **S3 Module** (`modules/s3/`) - Manages S3 buckets for configuration storage
- **S3 Vector Module** (`modules/s3-vector/`) - Manages S3 Vector buckets and indexes for knowledge base
- **Lambda Module** (`modules/lambda/`) - Manages all Lambda functions and their configurations
- **Cognito Module** (`modules/cognito/`) - Manages user authentication and authorization
- **AgentCore Gateway Module** (`modules/agentcore-gateway/`) - Manages AgentCore Gateway for MCP tool integration

## File Structure

```
infrastructure/minimal/
├── main.tf                 # Entry point and provider configuration
├── variables.tf            # Input variables with validation
├── outputs.tf             # Output values for all modules
├── modules.tf             # Module orchestration and dependencies
├── terraform.tfvars      # Environment-specific values
├── lambda_packages/       # Generated Lambda deployment packages
└── modules/
    ├── iam/
    │   ├── main.tf        # IAM roles and policies
    │   ├── variables.tf   # IAM module variables
    │   └── outputs.tf     # IAM module outputs
    ├── dynamodb/
    │   ├── main.tf        # DynamoDB tables and indexes
    │   ├── variables.tf   # DynamoDB module variables
    │   └── outputs.tf     # DynamoDB module outputs
    ├── s3/
    │   ├── main.tf        # S3 buckets for configuration
    │   ├── variables.tf   # S3 module variables
    │   └── outputs.tf     # S3 module outputs
    ├── s3-vector/
    │   ├── main.tf        # S3 Vector buckets and indexes
    │   ├── variables.tf   # S3 Vector module variables
    │   └── outputs.tf     # S3 Vector module outputs
    ├── lambda/
    │   ├── main.tf        # Lambda functions and configurations
    │   ├── variables.tf   # Lambda module variables
    │   └── outputs.tf     # Lambda module outputs
    └── cognito/
        ├── main.tf        # Cognito user pools and identity pools
        ├── variables.tf   # Cognito module variables
        └── outputs.tf     # Cognito module outputs
```

## Key Features

### Professional Structure
- **Modular Design**: Each service is isolated in its own module with clear interfaces
- **Dependency Management**: Proper module dependencies and data flow
- **Consistent Naming**: Standardized resource naming across all modules
- **Comprehensive Tagging**: Common tags applied to all resources for cost tracking

### Security Best Practices
- **Least Privilege**: IAM policies follow principle of least privilege
- **Encryption**: All data encrypted at rest and in transit
- **Access Control**: Proper S3 bucket policies and public access blocking
- **Authentication**: Cognito-based authentication with advanced security features

### Cost Optimization
- **Pay-per-Request**: DynamoDB configured for pay-per-request billing
- **Lifecycle Policies**: S3 lifecycle rules for cost-effective storage
- **Right-sizing**: Lambda functions sized appropriately for their workloads
- **Log Retention**: CloudWatch logs with configurable retention periods

### Scalability
- **Auto-scaling**: DynamoDB and Lambda scale automatically
- **Multi-language Support**: S3 Vector indexes for multiple languages
- **Flexible Configuration**: Environment-based configuration system

## Deployment

### Prerequisites
1. AWS CLI configured with appropriate credentials
2. Terraform >= 1.0 installed
3. Lambda function code available in `../../lambda/` directories

### Steps

1. **Initialize Terraform**:
   ```bash
   terraform init
   ```

2. **Configure Variables**:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your values
   ```

3. **Plan Deployment**:
   ```bash
   terraform plan
   ```

4. **Deploy Infrastructure**:
   ```bash
   terraform apply
   ```

5. **Initialize S3 Vectors**:
   ```bash
   cd ../..
   python scripts/initialize_s3_vectors.py
   ```

### Configuration Variables

Key variables to configure in `terraform.tfvars`:

```hcl
aws_region    = "us-east-1"
environment   = "dev"
project_name  = "customer-support"
admin_email   = "admin@yourcompany.com"
```

## Module Dependencies

The modules have the following dependency order:

1. **IAM Module** - Must be deployed first (other modules depend on IAM roles)
2. **DynamoDB Module** - Independent, can be deployed in parallel with S3 modules
3. **S3 Module** - Independent, provides configuration storage
4. **S3 Vector Module** - Independent, provides vector storage for knowledge base
5. **Lambda Module** - Depends on IAM, DynamoDB, and S3 modules
6. **Cognito Module** - Independent, provides authentication

## Outputs

After deployment, the following key outputs are available:

- **DynamoDB Table Names**: For application configuration
- **S3 Bucket Names**: For file storage and vector operations
- **Lambda Function URLs**: For direct HTTP access
- **Cognito Configuration**: For client application setup
- **Environment Variables**: Ready-to-use configuration for local development

## Maintenance

### Adding New Resources
1. Add resources to the appropriate module's `main.tf`
2. Add any new variables to the module's `variables.tf`
3. Add outputs to the module's `outputs.tf`
4. Update the root `modules.tf` if new module inputs are needed

### Updating Configurations
1. Modify variables in `terraform.tfvars`
2. Run `terraform plan` to review changes
3. Run `terraform apply` to deploy changes

### Monitoring
- CloudWatch logs are automatically created for all Lambda functions
- DynamoDB metrics are available in CloudWatch
- S3 access logs can be enabled if needed

## Troubleshooting

### Common Issues

1. **Lambda Package Not Found**:
   - Ensure Lambda function code exists in `../../lambda/<function_name>/`
   - Check that `main.py` exists in each Lambda directory

2. **S3 Bucket Name Conflicts**:
   - Bucket names include random suffix for uniqueness
   - If conflicts occur, run `terraform apply` again

3. **IAM Permission Errors**:
   - Ensure AWS credentials have sufficient permissions
   - Check that all required AWS services are available in the region

4. **Module Dependency Errors**:
   - Terraform automatically handles dependencies
   - If issues occur, try `terraform refresh` followed by `terraform apply`

## Cost Estimation

Approximate monthly costs (us-east-1, light usage):

- **DynamoDB**: $1-5 (pay-per-request)
- **Lambda**: $1-10 (based on invocations)
- **S3 Standard**: $1-5 (based on storage)
- **S3 Vector**: $10-50 (based on vector operations)
- **Cognito**: $0-5 (first 50,000 MAUs free)
- **CloudWatch Logs**: $1-5 (based on log volume)

**Total Estimated Cost**: $15-80/month for development environment

## Security Considerations

- All S3 buckets have public access blocked
- DynamoDB tables use encryption at rest
- Lambda functions have minimal required permissions
- Cognito enforces strong password policies
- CloudWatch logs have configurable retention
- IAM roles follow least privilege principle

## AgentCore Gateway

The **AgentCore Gateway** exposes Lambda functions as MCP (Model Context Protocol) tools that can be used by the AgentCore Runtime.

### Gateway Configuration

**Approach**: Terraform (Recommended) ✅

**What Gets Deployed:**
- Gateway with Cognito JWT authentication
- Gateway targets for each Lambda function
- Gateway URL stored in SSM Parameter Store
- AgentCore Runtime reads Gateway URL from SSM at runtime

**Gateway Targets:**
- `sentiment_analysis` → `___sent` tool
- `knowledge_search` → `___search` tool
- `ticket_management` → `___ticket` tool

**Authentication:**
- **Gateway**: Cognito JWT (OAuth 2.0)
- **Lambda**: AWS_IAM (via Gateway IAM role)

### Gateway URL

After deployment, the Gateway URL is stored in SSM Parameter Store:
- Parameter: `/dev-customer-support/agentcore-gateway-url`
- Automatically read by AgentCore Runtime

## Cognito Authentication

### User Pool Configuration

- **OAuth 2.0**: Enabled for AgentCore Gateway
- **JWT Tokens**: ID tokens and access tokens
- **Resource Server**: Custom scopes for API access
- **M2M Client**: Machine-to-machine authentication

### Getting Access Tokens

**Option 1: AWS CLI**
```bash
aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id <client-id> \
  --auth-parameters USERNAME=username,PASSWORD=password
```

**Option 2: Cognito Hosted UI**
- Navigate to: `https://<cognito-domain>.auth.<region>.amazoncognito.com`
- Sign in and get tokens from callback URL

### Using Tokens with Gateway

```bash
curl -X POST https://<gateway-url>/tools/invoke \
  -H "Authorization: Bearer <access-token>" \
  -H "Content-Type: application/json" \
  -d '{"tool": "...", "arguments": {...}}'
```

## Bedrock Configuration

### Model Access

Ensure your AWS credentials have permissions to access Bedrock:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "arn:aws:bedrock:*::foundation-model/*"
    }
  ]
}
```

### Model Configuration

Default model: `anthropic.claude-3-haiku-20240307-v1:0`

Configured in:
- `.bedrock_agentcore.yaml` (AgentCore)
- Environment variables (Lambda functions)

## Next Steps

After infrastructure deployment:

1. Initialize S3 vectors with sample data
2. Deploy AgentCore configuration
3. Start specialized agents
4. Test the complete system
5. Configure monitoring and alerting