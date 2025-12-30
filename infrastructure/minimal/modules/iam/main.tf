# IAM Module for Customer Support Platform
# Manages all IAM roles, policies, and permissions

# Lambda Execution Role
resource "aws_iam_role" "lambda_execution" {
  name = "${var.resource_prefix}-lambda-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = var.common_tags
}

# Lambda Basic Execution Policy
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Custom Lambda Policy for Application Resources
resource "aws_iam_role_policy" "lambda_application_policy" {
  name = "${var.resource_prefix}-lambda-application-policy"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # CloudWatch Logs
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:${var.aws_account_id}:*"
      },
      
      # DynamoDB Access
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:BatchGetItem",
          "dynamodb:BatchWriteItem"
        ]
        Resource = concat(
          var.dynamodb_table_arns,
          [for arn in var.dynamodb_table_arns : "${arn}/index/*"]
        )
      },
      
      # S3 Configuration Bucket Access
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${var.knowledge_base_bucket_arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = var.knowledge_base_bucket_arn
      },
      
      # S3 Vector Operations
      # S3 vectors uses ARN format: arn:aws:s3vectors:region:account-id:bucket/bucket-name/index/index-name
      # We use "*" to allow all S3 vector resources since the exact index ARN is dynamic
      {
        Effect = "Allow"
        Action = [
          "s3vectors:CreateVectorBucket",
          "s3vectors:CreateVectorIndex",
          "s3vectors:PutVectors",
          "s3vectors:GetVector",
          "s3vectors:GetVectors",
          "s3vectors:UpdateVector",
          "s3vectors:DeleteVector",
          "s3vectors:QueryVectors",
          "s3vectors:ListVectors",
          "s3vectors:DescribeVectorBucket",
          "s3vectors:DescribeVectorIndex"
        ]
        Resource = "*"
      },
      
      # Amazon Comprehend for Sentiment Analysis
      {
        Effect = "Allow"
        Action = [
          "comprehend:DetectSentiment",
          "comprehend:DetectEntities",
          "comprehend:ClassifyDocument",
          "comprehend:DetectLanguage"
        ]
        Resource = "*"
      },
      
      # Amazon Bedrock for AI Models
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = [
          "arn:aws:bedrock:${var.aws_region}::foundation-model/amazon.titan-text-lite-v1",
          "arn:aws:bedrock:${var.aws_region}::foundation-model/amazon.titan-embed-text-v1",
          "arn:aws:bedrock:${var.aws_region}::foundation-model/amazon.titan-embed-text-v2:0",
          "arn:aws:bedrock:${var.aws_region}::foundation-model/anthropic.claude-3-haiku-20240307-v1:0",
          "arn:aws:bedrock:${var.aws_region}::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
        ]
      }
    ]
  })
}

# AgentCore Runtime Execution Role
resource "aws_iam_role" "agentcore_execution" {
  name = "${var.resource_prefix}-agentcore-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "bedrock-agentcore.amazonaws.com"
        }
      }
    ]
  })

  tags = var.common_tags
}

# AgentCore Basic Execution Policy
resource "aws_iam_role_policy_attachment" "agentcore_basic_execution" {
  role       = aws_iam_role.agentcore_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Custom AgentCore Policy for Application Resources
resource "aws_iam_role_policy" "agentcore_application_policy" {
  name = "${var.resource_prefix}-agentcore-application-policy"
  role = aws_iam_role.agentcore_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # CloudWatch Logs
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:${var.aws_account_id}:*"
      },
      
      # DynamoDB Access
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:BatchGetItem",
          "dynamodb:BatchWriteItem"
        ]
        Resource = concat(
          var.dynamodb_table_arns,
          [for arn in var.dynamodb_table_arns : "${arn}/index/*"]
        )
      },
      
      # S3 Configuration Bucket Access
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${var.knowledge_base_bucket_arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = var.knowledge_base_bucket_arn
      },
      
      # S3 Vector Operations
      # S3 vectors uses ARN format: arn:aws:s3vectors:region:account-id:bucket/bucket-name/index/index-name
      # We use "*" to allow all S3 vector resources since the exact index ARN is dynamic
      {
        Effect = "Allow"
        Action = [
          "s3vectors:CreateVectorBucket",
          "s3vectors:CreateVectorIndex",
          "s3vectors:PutVectors",
          "s3vectors:GetVector",
          "s3vectors:GetVectors",
          "s3vectors:UpdateVector",
          "s3vectors:DeleteVector",
          "s3vectors:QueryVectors",
          "s3vectors:ListVectors",
          "s3vectors:DescribeVectorBucket",
          "s3vectors:DescribeVectorIndex"
        ]
        Resource = "*"
      },
      
      # Amazon Bedrock for AI Models
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = [
          "arn:aws:bedrock:${var.aws_region}::foundation-model/anthropic.claude-3-haiku-20240307-v1:0",
          "arn:aws:bedrock:${var.aws_region}::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0",
          "arn:aws:bedrock:${var.aws_region}::foundation-model/anthropic.claude-3-opus-20240229-v1:0"
        ]
      },
      
      # Lambda Invoke (for MCP tools)
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          "arn:aws:lambda:${var.aws_region}:${var.aws_account_id}:function:${var.resource_prefix}-*"
        ]
      },
      
      # ECR Access (for container image pull)
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer"
        ]
        Resource = "*"
      },
      
      # SSM Parameter Store Access (for Gateway URL configuration)
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters"
        ]
        Resource = "arn:aws:ssm:${var.aws_region}:${var.aws_account_id}:parameter/${var.resource_prefix}/agentcore/*"
      },
      # X-Ray Tracing (Optional - for observability)
      {
        Effect = "Allow"
        Action = [
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords"
        ]
        Resource = "*"
      }
    ]
  })
}