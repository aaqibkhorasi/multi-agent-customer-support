# Outputs for Customer Support Platform Infrastructure

# DynamoDB Outputs
output "dynamodb_tables" {
  description = "DynamoDB table names and ARNs"
  value = {
    tickets = {
      name = module.dynamodb.tickets_table_name
      arn  = module.dynamodb.tickets_table_arn
    }
    customers = {
      name = module.dynamodb.customers_table_name
      arn  = module.dynamodb.customers_table_arn
    }
    feedback = {
      name = module.dynamodb.feedback_table_name
      arn  = module.dynamodb.feedback_table_arn
    }
  }
}

# S3 Outputs
output "s3_buckets" {
  description = "S3 bucket information"
  value = {
    knowledge_base_bucket = {
      name = module.s3.knowledge_base_bucket_name
      arn  = module.s3.knowledge_base_bucket_arn
    }
    vector_bucket = {
      name = module.s3_vector.vector_bucket_name
      arn  = module.s3_vector.vector_bucket_arn
    }
  }
}

output "s3_vector_indexes" {
  description = "S3 vector indexes for different languages"
  value       = module.s3_vector.vector_indexes
}

# Lambda Outputs
output "lambda_functions" {
  description = "Lambda function information"
  value = {
    sentiment_analysis = {
      name = module.lambda.sentiment_analysis_function_name
      arn  = module.lambda.sentiment_analysis_function_arn
    }
    knowledge_search = {
      name = module.lambda.knowledge_search_function_name
      arn  = module.lambda.knowledge_search_function_arn
    }
    knowledge_ingestion = {
      name = module.lambda.knowledge_ingestion_function_name
      arn  = module.lambda.knowledge_ingestion_function_arn
    }
    ticket_management = {
      name = module.lambda.ticket_management_function_name
      arn  = module.lambda.ticket_management_function_arn
    }
  }
}

# IAM Outputs
output "iam_roles" {
  description = "IAM role information"
  value = {
    lambda_execution_role = {
      name = module.iam.lambda_execution_role_name
      arn  = module.iam.lambda_execution_role_arn
    }
    agentcore_execution_role = {
      name = module.iam.agentcore_execution_role_name
      arn  = module.iam.agentcore_execution_role_arn
    }
    agentcore_gateway_role = {
      name = module.agentcore_gateway.gateway_role_name
      arn  = module.agentcore_gateway.gateway_role_arn
    }
  }
}

# Cognito Outputs
output "cognito_user_pool" {
  description = "Cognito user pool information"
  value = {
    id        = module.cognito.user_pool_id
    arn       = module.cognito.user_pool_arn
    endpoint  = module.cognito.user_pool_endpoint
    client_id = module.cognito.user_pool_client_id
    domain    = module.cognito.user_pool_domain
  }
}

output "cognito_user_pool_domain" {
  description = "Cognito user pool domain"
  value = {
    value = module.cognito.user_pool_domain
    url   = "https://${module.cognito.user_pool_domain}.auth.${data.aws_region.current.name}.amazoncognito.com"
  }
}

# AgentCore Gateway Outputs
output "agentcore_gateway" {
  description = "AgentCore Gateway information"
  value = {
    id       = module.agentcore_gateway.gateway_id
    arn      = module.agentcore_gateway.gateway_arn
    url      = module.agentcore_gateway.gateway_url
    name     = module.agentcore_gateway.gateway_name
    role_arn = module.agentcore_gateway.gateway_role_arn
  }
}

# SSM Parameter Store Output
output "ssm_gateway_url_parameter" {
  description = "SSM Parameter Store name for Gateway URL"
  value       = aws_ssm_parameter.agentcore_gateway_url.name
}

# Environment Variables for Local Development
output "environment_variables" {
  description = "Environment variables for local development"
  value = {
    AWS_REGION            = var.aws_region
    ENVIRONMENT           = var.environment
    TICKETS_TABLE         = module.dynamodb.tickets_table_name
    CUSTOMERS_TABLE       = module.dynamodb.customers_table_name
    FEEDBACK_TABLE        = module.dynamodb.feedback_table_name
    KNOWLEDGE_BASE_BUCKET = module.s3.knowledge_base_bucket_name
    VECTOR_BUCKET_NAME    = module.s3_vector.vector_bucket_name
    COGNITO_USER_POOL_ID  = module.cognito.user_pool_id
    COGNITO_CLIENT_ID     = module.cognito.user_pool_client_id
    AGENTCORE_GATEWAY_URL = module.agentcore_gateway.gateway_url
  }
}

# Deployment Information
output "deployment_info" {
  description = "Deployment information and next steps"
  value = {
    region          = var.aws_region
    environment     = var.environment
    project_name    = var.project_name
    resource_prefix = local.resource_prefix
    deployment_time = timestamp()
    next_steps = [
      "1. Initialize S3 vectors: python scripts/initialize_s3_vectors.py",
      "2. Deploy AgentCore: agentcore deploy",
      "3. Start agents: python start_agents.py",
      "4. Test system: python test_multi_agent.py"
    ]
  }
}