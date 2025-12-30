# Module Declarations for Customer Support Platform
# This file orchestrates all service modules

# IAM Module - Must be first as other modules depend on it
module "iam" {
  source = "./modules/iam"

  resource_prefix = local.resource_prefix
  common_tags     = local.common_tags

  # DynamoDB table ARNs for IAM policies
  dynamodb_table_arns = [
    module.dynamodb.tickets_table_arn,
    module.dynamodb.customers_table_arn,
    module.dynamodb.feedback_table_arn
  ]

  # S3 bucket ARNs for IAM policies
  knowledge_base_bucket_arn = module.s3.knowledge_base_bucket_arn
  vector_bucket_arn         = module.s3_vector.vector_bucket_arn

  # AWS region and account info
  aws_region     = data.aws_region.current.name
  aws_account_id = data.aws_caller_identity.current.account_id
}

# DynamoDB Module
module "dynamodb" {
  source = "./modules/dynamodb"

  resource_prefix = local.resource_prefix
  common_tags     = local.common_tags
  billing_mode    = var.dynamodb_billing_mode
}

# S3 Module for configuration storage
module "s3" {
  source = "./modules/s3"

  resource_prefix = local.resource_prefix
  common_tags     = local.common_tags
  bucket_suffix   = random_id.bucket_suffix.hex
}

# S3 Vector Module for knowledge base
module "s3_vector" {
  source = "./modules/s3-vector"

  resource_prefix      = local.resource_prefix
  common_tags          = local.common_tags
  bucket_suffix        = random_id.bucket_suffix.hex
  vector_dimensions    = var.vector_dimensions
  similarity_algorithm = var.vector_similarity_algorithm
  supported_languages  = var.supported_languages
}

# Lambda Module
module "lambda" {
  source = "./modules/lambda"

  resource_prefix           = local.resource_prefix
  common_tags               = local.common_tags
  lambda_execution_role_arn = module.iam.lambda_execution_role_arn

  # Lambda configuration
  runtime            = var.lambda_runtime
  timeout            = var.lambda_timeout
  memory_size        = var.lambda_memory_size
  log_retention_days = var.log_retention_days

  # Environment variables for Lambda functions
  environment_variables = {
    ENVIRONMENT           = var.environment
    VECTOR_BUCKET_NAME    = module.s3_vector.vector_bucket_name
    KNOWLEDGE_BASE_BUCKET = module.s3.knowledge_base_bucket_name
    TICKETS_TABLE         = module.dynamodb.tickets_table_name
    CUSTOMERS_TABLE       = module.dynamodb.customers_table_name
    FEEDBACK_TABLE        = module.dynamodb.feedback_table_name
  }
}

# Cognito Module
module "cognito" {
  source = "./modules/cognito"

  resource_prefix = local.resource_prefix
  common_tags     = local.common_tags
  admin_email     = var.admin_email
}

# AgentCore Gateway Module
module "agentcore_gateway" {
  source = "./modules/agentcore-gateway"

  resource_prefix = local.resource_prefix
  common_tags     = local.common_tags
  gateway_name    = "gateway" # Will result in: dev-customer-support-gateway

  # Cognito configuration for JWT authentication
  cognito_user_pool_id        = module.cognito.user_pool_id
  cognito_user_pool_client_id = module.cognito.user_pool_client_id
  # Use the full Cognito domain URL format
  cognito_domain = "${module.cognito.user_pool_domain}.auth.${data.aws_region.current.name}.amazoncognito.com"
  # M2M client ID for machine-to-machine authentication (created manually)
  m2m_client_id = "59cqlv3jaarlgc3d8snbsdpfd3"

  # Lambda function ARNs to expose as Gateway targets
  # Note: ticket_management Lambda will have 4 separate targets (one per tool)
  lambda_function_arns = [
    module.lambda.sentiment_analysis_function_arn,
    module.lambda.knowledge_search_function_arn,
    module.lambda.knowledge_ingestion_function_arn, # Admin function for ingesting articles into S3 vector
    module.lambda.ticket_management_function_arn    # Single Lambda with 4 tools
  ]

  aws_region     = data.aws_region.current.name
  aws_account_id = data.aws_caller_identity.current.account_id

  depends_on = [
    module.cognito,
    module.lambda
  ]
}

# SSM Parameter Store for AgentCore Gateway URL
# This allows the code to automatically read the Gateway URL without manual configuration
# Fully automated: Terraform creates it, code reads it at runtime
resource "aws_ssm_parameter" "agentcore_gateway_url" {
  name        = "/${local.resource_prefix}/agentcore/gateway_url"
  description = "AgentCore Gateway URL for MCP client connection (automatically set by Terraform)"
  type        = "String"
  value       = module.agentcore_gateway.gateway_url
  overwrite   = true

  tags = merge(
    local.common_tags,
    {
      Name = "${local.resource_prefix}-agentcore-gateway-url"
    }
  )

  depends_on = [module.agentcore_gateway]
}