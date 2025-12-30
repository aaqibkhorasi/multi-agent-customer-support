# Lambda Module for Customer Support Platform
# Manages all Lambda functions and their configurations

# Prepare Lambda packages with shared utilities
# Create staging directories that include both Lambda code and shared utilities
resource "null_resource" "prepare_lambda_packages" {
  for_each = toset(["sentiment_analysis", "knowledge_search", "knowledge_ingestion", "ticket_management"])
  
  triggers = {
    lambda_code_hash = filemd5("${path.root}/../../lambda/${each.value}/main.py")
    shared_utils_hash = join("", [
      for f in fileset("${path.root}/../../shared/utils", "*.py") : filemd5("${path.root}/../../shared/utils/${f}")
    ])
  }
  
  provisioner "local-exec" {
    command = <<-EOT
      set -e
      
      # Create staging directory (clean it first)
      rm -rf "${path.root}/lambda_packages/${each.value}"
      mkdir -p "${path.root}/lambda_packages/${each.value}"
      
      # Copy Lambda function code (excluding __pycache__)
      find "${path.root}/../../lambda/${each.value}" -type f -name "*.py" -o -name "requirements.txt" | while read file; do
        cp "$file" "${path.root}/lambda_packages/${each.value}/"
      done
      
      # Copy shared utilities directory structure
      mkdir -p "${path.root}/lambda_packages/${each.value}/shared/utils"
      find "${path.root}/../../shared/utils" -type f -name "*.py" | while read file; do
        cp "$file" "${path.root}/lambda_packages/${each.value}/shared/utils/"
      done
      
      # Ensure main.py is at the root
      if [ ! -f "${path.root}/lambda_packages/${each.value}/main.py" ]; then
        cp "${path.root}/../../lambda/${each.value}/main.py" "${path.root}/lambda_packages/${each.value}/main.py"
      fi
    EOT
  }
}

# Data source for Lambda deployment packages
data "archive_file" "lambda_packages" {
  for_each = toset(["sentiment_analysis", "knowledge_search", "knowledge_ingestion", "ticket_management"])
  
  type        = "zip"
  source_dir  = "${path.root}/lambda_packages/${each.value}"
  output_path = "${path.root}/lambda_packages/${each.value}.zip"
  
  depends_on = [null_resource.prepare_lambda_packages]
}

# CloudWatch Log Groups for Lambda functions
resource "aws_cloudwatch_log_group" "lambda_logs" {
  for_each = toset(["sentiment_analysis", "knowledge_search", "knowledge_ingestion", "ticket_management"])
  
  name              = "/aws/lambda/${var.resource_prefix}-${each.value}"
  retention_in_days = var.log_retention_days

  tags = merge(var.common_tags, {
    Name        = "${var.resource_prefix}-${each.value}-logs"
    Description = "CloudWatch logs for ${each.value} Lambda function"
  })
}

# Sentiment Analysis Lambda Function
resource "aws_lambda_function" "sentiment_analysis" {
  filename         = data.archive_file.lambda_packages["sentiment_analysis"].output_path
  function_name    = "${var.resource_prefix}-sentiment-analysis"
  role            = var.lambda_execution_role_arn
  handler         = "main.lambda_handler"
  runtime         = var.runtime
  timeout         = 900  # 15 minutes for all operations
  memory_size     = var.memory_size
  source_code_hash = data.archive_file.lambda_packages["sentiment_analysis"].output_base64sha256

  environment {
    variables = var.environment_variables
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda_logs["sentiment_analysis"]
  ]

  tags = merge(var.common_tags, {
    Name        = "${var.resource_prefix}-sentiment-analysis"
    Description = "Sentiment analysis using Amazon Comprehend and Bedrock"
    Purpose     = "sentiment-analysis"
  })
}

# Knowledge Search Lambda Function
resource "aws_lambda_function" "knowledge_search" {
  filename         = data.archive_file.lambda_packages["knowledge_search"].output_path
  function_name    = "${var.resource_prefix}-knowledge-search"
  role            = var.lambda_execution_role_arn
  handler         = "main.lambda_handler"
  runtime         = var.runtime
  timeout         = 900  # 15 minutes for all operations
  memory_size     = 512 # More memory for vector operations
  source_code_hash = data.archive_file.lambda_packages["knowledge_search"].output_base64sha256

  environment {
    variables = var.environment_variables
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda_logs["knowledge_search"]
  ]

  tags = merge(var.common_tags, {
    Name        = "${var.resource_prefix}-knowledge-search"
    Description = "S3 Vector-based knowledge base search"
    Purpose     = "knowledge-search"
  })
}

# Knowledge Ingestion Lambda Function
resource "aws_lambda_function" "knowledge_ingestion" {
  filename         = data.archive_file.lambda_packages["knowledge_ingestion"].output_path
  function_name    = "${var.resource_prefix}-knowledge-ingestion"
  role            = var.lambda_execution_role_arn
  handler         = "main.lambda_handler"
  runtime         = var.runtime
  timeout         = 900  # 15 minutes for all operations
  memory_size     = 1024 # More memory for embedding generation
  source_code_hash = data.archive_file.lambda_packages["knowledge_ingestion"].output_base64sha256

  environment {
    variables = var.environment_variables
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda_logs["knowledge_ingestion"]
  ]

  tags = merge(var.common_tags, {
    Name        = "${var.resource_prefix}-knowledge-ingestion"
    Description = "Knowledge base article ingestion and embedding generation"
    Purpose     = "knowledge-ingestion"
  })
}

# Ticket Management Lambda Function (handles all 4 operations via Gateway tool names)
resource "aws_lambda_function" "ticket_management" {
  filename         = data.archive_file.lambda_packages["ticket_management"].output_path
  function_name    = "${var.resource_prefix}-ticket-management"
  role            = var.lambda_execution_role_arn
  handler         = "main.lambda_handler"
  runtime         = var.runtime
  timeout         = 900  # 15 minutes for all operations
  memory_size     = var.memory_size
  source_code_hash = data.archive_file.lambda_packages["ticket_management"].output_base64sha256

  environment {
    variables = var.environment_variables
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda_logs["ticket_management"]
  ]

  tags = merge(var.common_tags, {
    Name        = "${var.resource_prefix}-ticket-management"
    Description = "Ticket management in DynamoDB"
    Purpose     = "ticket-management"
  })
}

# Lambda Function URLs (for direct HTTP access if needed)
resource "aws_lambda_function_url" "sentiment_analysis" {
  function_name      = aws_lambda_function.sentiment_analysis.function_name
  authorization_type = "AWS_IAM"

  cors {
    allow_credentials = false
    allow_origins     = ["*"]
    allow_methods     = ["POST"]
    allow_headers     = ["date", "keep-alive"]
    expose_headers    = ["date", "keep-alive"]
    max_age          = 86400
  }
}

resource "aws_lambda_function_url" "knowledge_search" {
  function_name      = aws_lambda_function.knowledge_search.function_name
  authorization_type = "AWS_IAM"

  cors {
    allow_credentials = false
    allow_origins     = ["*"]
    allow_methods     = ["POST"]
    allow_headers     = ["date", "keep-alive"]
    expose_headers    = ["date", "keep-alive"]
    max_age          = 86400
  }
}

resource "aws_lambda_function_url" "knowledge_ingestion" {
  function_name      = aws_lambda_function.knowledge_ingestion.function_name
  authorization_type = "AWS_IAM"

  cors {
    allow_credentials = false
    allow_origins     = ["*"]
    allow_methods     = ["POST"]
    allow_headers     = ["date", "keep-alive"]
    expose_headers    = ["date", "keep-alive"]
    max_age          = 86400
  }
}