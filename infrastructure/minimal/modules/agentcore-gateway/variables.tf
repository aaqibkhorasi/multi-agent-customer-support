# Variables for AgentCore Gateway Module

variable "resource_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "gateway_name" {
  description = "Name of the AgentCore Gateway"
  type        = string
  default     = "customer-support-gateway"
}

variable "cognito_user_pool_id" {
  description = "Cognito User Pool ID for JWT authentication"
  type        = string
}

variable "cognito_user_pool_client_id" {
  description = "Cognito User Pool Client ID for JWT authentication"
  type        = string
}

variable "cognito_domain" {
  description = "Cognito domain URL for JWT discovery (deprecated, use cognito_user_pool_id instead)"
  type        = string
  default     = ""
}

variable "m2m_client_id" {
  description = "Optional M2M client ID for machine-to-machine authentication"
  type        = string
  default     = ""
}

variable "lambda_function_arns" {
  description = "List of Lambda function ARNs to expose as Gateway targets"
  type        = list(string)
  default     = []
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "aws_account_id" {
  description = "AWS account ID"
  type        = string
}

