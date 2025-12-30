# Outputs for DynamoDB Module

# Tickets Table Outputs
output "tickets_table_name" {
  description = "Name of the tickets DynamoDB table"
  value       = aws_dynamodb_table.tickets.name
}

output "tickets_table_arn" {
  description = "ARN of the tickets DynamoDB table"
  value       = aws_dynamodb_table.tickets.arn
}

output "tickets_table_id" {
  description = "ID of the tickets DynamoDB table"
  value       = aws_dynamodb_table.tickets.id
}

# Customers Table Outputs
output "customers_table_name" {
  description = "Name of the customers DynamoDB table"
  value       = aws_dynamodb_table.customers.name
}

output "customers_table_arn" {
  description = "ARN of the customers DynamoDB table"
  value       = aws_dynamodb_table.customers.arn
}

output "customers_table_id" {
  description = "ID of the customers DynamoDB table"
  value       = aws_dynamodb_table.customers.id
}

# Feedback Table Outputs
output "feedback_table_name" {
  description = "Name of the feedback DynamoDB table"
  value       = aws_dynamodb_table.feedback.name
}

output "feedback_table_arn" {
  description = "ARN of the feedback DynamoDB table"
  value       = aws_dynamodb_table.feedback.arn
}

output "feedback_table_id" {
  description = "ID of the feedback DynamoDB table"
  value       = aws_dynamodb_table.feedback.id
}

# All Table ARNs for IAM policies
output "all_table_arns" {
  description = "List of all DynamoDB table ARNs"
  value = [
    aws_dynamodb_table.tickets.arn,
    aws_dynamodb_table.customers.arn,
    aws_dynamodb_table.feedback.arn
  ]
}