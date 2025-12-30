# Outputs for AgentCore Gateway Module

output "gateway_id" {
  description = "ID of the AgentCore Gateway"
  value       = aws_bedrockagentcore_gateway.main.gateway_id
}

output "gateway_arn" {
  description = "ARN of the AgentCore Gateway"
  value       = aws_bedrockagentcore_gateway.main.gateway_arn
}

output "gateway_url" {
  description = "URL of the AgentCore Gateway"
  value       = aws_bedrockagentcore_gateway.main.gateway_url
}

output "gateway_name" {
  description = "Name of the AgentCore Gateway"
  value       = aws_bedrockagentcore_gateway.main.name
}

output "gateway_role_arn" {
  description = "ARN of the Gateway IAM role"
  value       = aws_iam_role.gateway.arn
}

output "gateway_role_name" {
  description = "Name of the Gateway IAM role"
  value       = aws_iam_role.gateway.name
}

# Target outputs
output "target_ids" {
  description = "Map of target IDs by Lambda function ARN"
  value = {
    for arn, target in aws_bedrockagentcore_gateway_target.lambda_targets : arn => target.target_id
  }
}

