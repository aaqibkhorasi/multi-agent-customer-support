# Outputs for Lambda Module

# Sentiment Analysis Function Outputs
output "sentiment_analysis_function_name" {
  description = "Name of the sentiment analysis Lambda function"
  value       = aws_lambda_function.sentiment_analysis.function_name
}

output "sentiment_analysis_function_arn" {
  description = "ARN of the sentiment analysis Lambda function"
  value       = aws_lambda_function.sentiment_analysis.arn
}

output "sentiment_analysis_function_url" {
  description = "Function URL of the sentiment analysis Lambda"
  value       = aws_lambda_function_url.sentiment_analysis.function_url
}

# Knowledge Search Function Outputs
output "knowledge_search_function_name" {
  description = "Name of the knowledge search Lambda function"
  value       = aws_lambda_function.knowledge_search.function_name
}

output "knowledge_search_function_arn" {
  description = "ARN of the knowledge search Lambda function"
  value       = aws_lambda_function.knowledge_search.arn
}

output "knowledge_search_function_url" {
  description = "Function URL of the knowledge search Lambda"
  value       = aws_lambda_function_url.knowledge_search.function_url
}

# Knowledge Ingestion Function Outputs
output "knowledge_ingestion_function_name" {
  description = "Name of the knowledge ingestion Lambda function"
  value       = aws_lambda_function.knowledge_ingestion.function_name
}

output "knowledge_ingestion_function_arn" {
  description = "ARN of the knowledge ingestion Lambda function"
  value       = aws_lambda_function.knowledge_ingestion.arn
}

output "knowledge_ingestion_function_url" {
  description = "Function URL of the knowledge ingestion Lambda"
  value       = aws_lambda_function_url.knowledge_ingestion.function_url
}

# Ticket Management Function Outputs
output "ticket_management_function_name" {
  description = "Name of the ticket management Lambda function"
  value       = aws_lambda_function.ticket_management.function_name
}

output "ticket_management_function_arn" {
  description = "ARN of the ticket management Lambda function"
  value       = aws_lambda_function.ticket_management.arn
}

# All Function Information
output "all_functions" {
  description = "Map of all Lambda functions with their details"
  value = {
    sentiment_analysis = {
      name = aws_lambda_function.sentiment_analysis.function_name
      arn  = aws_lambda_function.sentiment_analysis.arn
      url  = aws_lambda_function_url.sentiment_analysis.function_url
    }
    knowledge_search = {
      name = aws_lambda_function.knowledge_search.function_name
      arn  = aws_lambda_function.knowledge_search.arn
      url  = aws_lambda_function_url.knowledge_search.function_url
    }
    knowledge_ingestion = {
      name = aws_lambda_function.knowledge_ingestion.function_name
      arn  = aws_lambda_function.knowledge_ingestion.arn
      url  = aws_lambda_function_url.knowledge_ingestion.function_url
    }
    ticket_management = {
      name = aws_lambda_function.ticket_management.function_name
      arn  = aws_lambda_function.ticket_management.arn
    }
  }
}

# CloudWatch Log Groups
output "log_groups" {
  description = "CloudWatch log group names for Lambda functions"
  value = {
    for name, log_group in aws_cloudwatch_log_group.lambda_logs : name => log_group.name
  }
}