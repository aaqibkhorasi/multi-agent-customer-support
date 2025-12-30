# Outputs for Cognito Module

# User Pool Outputs
output "user_pool_id" {
  description = "ID of the Cognito user pool"
  value       = aws_cognito_user_pool.main.id
}

output "user_pool_arn" {
  description = "ARN of the Cognito user pool"
  value       = aws_cognito_user_pool.main.arn
}

output "user_pool_endpoint" {
  description = "Endpoint of the Cognito user pool"
  value       = aws_cognito_user_pool.main.endpoint
}

output "user_pool_name" {
  description = "Name of the Cognito user pool"
  value       = aws_cognito_user_pool.main.name
}

# User Pool Client Outputs
output "user_pool_client_id" {
  description = "ID of the Cognito user pool client"
  value       = aws_cognito_user_pool_client.main.id
}

output "user_pool_client_name" {
  description = "Name of the Cognito user pool client"
  value       = aws_cognito_user_pool_client.main.name
}

# User Pool Domain Outputs
output "user_pool_domain" {
  description = "Domain of the Cognito user pool"
  value       = aws_cognito_user_pool_domain.main.domain
}

output "user_pool_domain_cloudfront_distribution_arn" {
  description = "CloudFront distribution ARN for the user pool domain"
  value       = aws_cognito_user_pool_domain.main.cloudfront_distribution_arn
}

# Identity Pool Outputs
output "identity_pool_id" {
  description = "ID of the Cognito identity pool"
  value       = aws_cognito_identity_pool.main.id
}

output "identity_pool_arn" {
  description = "ARN of the Cognito identity pool"
  value       = aws_cognito_identity_pool.main.arn
}

# IAM Role Outputs
output "authenticated_role_arn" {
  description = "ARN of the authenticated user IAM role"
  value       = aws_iam_role.authenticated.arn
}

output "authenticated_role_name" {
  description = "Name of the authenticated user IAM role"
  value       = aws_iam_role.authenticated.name
}

# Admin User Outputs
output "admin_username" {
  description = "Username of the admin user"
  value       = aws_cognito_user.admin.username
}

# Resource Server Outputs
# Note: Resource server is created manually, identifier is "agentcore-gateway"
output "resource_server_id" {
  description = "Identifier of the Cognito resource server (created manually)"
  value       = "agentcore-gateway"
}

# Authentication Configuration for Applications
output "auth_config" {
  description = "Authentication configuration for client applications"
  value = {
    user_pool_id        = aws_cognito_user_pool.main.id
    user_pool_client_id = aws_cognito_user_pool_client.main.id
    identity_pool_id    = aws_cognito_identity_pool.main.id
    domain             = aws_cognito_user_pool_domain.main.domain
    region             = data.aws_region.current.name
    resource_server_id = "agentcore-gateway"
  }
}

# Data source for current region
data "aws_region" "current" {}