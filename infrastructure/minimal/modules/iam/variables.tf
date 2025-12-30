# IAM Module Variables

variable "resource_prefix" {
  description = "Prefix for resource naming"
  type        = string
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
}

variable "dynamodb_table_arns" {
  description = "List of DynamoDB table ARNs for IAM policies"
  type        = list(string)
}

variable "knowledge_base_bucket_arn" {
  description = "S3 knowledge base bucket ARN"
  type        = string
}

variable "vector_bucket_arn" {
  description = "S3 vector bucket ARN"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "aws_account_id" {
  description = "AWS account ID"
  type        = string
}