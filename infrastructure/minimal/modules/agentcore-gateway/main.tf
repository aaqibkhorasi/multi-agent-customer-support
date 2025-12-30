# AgentCore Gateway Module
# Creates an AgentCore Gateway to expose Lambda functions as MCP tools

# Gateway IAM Role
resource "aws_iam_role" "gateway" {
  name = "${var.resource_prefix}-agentcore-gateway-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "bedrock-agentcore.amazonaws.com"
        }
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = var.aws_account_id
          }
          ArnLike = {
            "aws:SourceArn" = "arn:aws:bedrock-agentcore:${var.aws_region}:${var.aws_account_id}:*"
          }
        }
      }
    ]
  })

  tags = var.common_tags
}

# Gateway IAM Policy
resource "aws_iam_role_policy" "gateway" {
  name = "${var.resource_prefix}-agentcore-gateway-policy"
  role = aws_iam_role.gateway.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock-agentcore:*",
          "bedrock:*",
          "agent-credential-provider:*",
          "iam:PassRole",
          "secretsmanager:GetSecretValue",
          "lambda:InvokeFunction"
        ]
        Resource = "*"
      }
    ]
  })
}

# AgentCore Gateway
# Using Cognito JWT authentication
resource "aws_bedrockagentcore_gateway" "main" {
  name        = "${var.resource_prefix}-${var.gateway_name}"
  description = "AgentCore Gateway for Customer Support Multi-Agent System"

  role_arn        = aws_iam_role.gateway.arn
  authorizer_type = "CUSTOM_JWT"
  protocol_type   = "MCP"

  # Cognito JWT authorizer configuration
  # Use Cognito User Pool endpoint format: https://cognito-idp.{region}.amazonaws.com/{user_pool_id}
  # Allow both the main client and M2M client (if provided)
  authorizer_configuration {
    custom_jwt_authorizer {
      discovery_url = "https://cognito-idp.${var.aws_region}.amazonaws.com/${var.cognito_user_pool_id}/.well-known/openid-configuration"
      
      allowed_clients = concat(
        [var.cognito_user_pool_client_id],
        var.m2m_client_id != "" ? [var.m2m_client_id] : []
      )
    }
  }

  tags = var.common_tags

  depends_on = [aws_iam_role.gateway]
}

# Gateway Targets for Lambda Functions
# Map Lambda function names to their tool schemas
locals {
  lambda_tool_configs = {
    "sentiment_analysis" = {
      name        = "sent"
      description = "Analyze sentiment and emotion from customer messages using Amazon Comprehend"
      input_schema = jsonencode({
        type = "object"
        properties = {
          text = {
            type        = "string"
            description = "The text to analyze for sentiment"
          }
          language = {
            type        = "string"
            description = "Language code (optional, defaults to auto-detect)"
            default     = "auto"
          }
        }
        required = ["text"]
      })
    }
    "knowledge_search" = {
      name        = "search"
      description = "Search the knowledge base using S3 Vector search for relevant articles and solutions"
      input_schema = jsonencode({
        type = "object"
        properties = {
          query = {
            type        = "string"
            description = "Search query to find relevant knowledge base articles"
          }
          max_results = {
            type        = "integer"
            description = "Maximum number of results to return"
            default     = 5
          }
          language = {
            type        = "string"
            description = "Language code for search (en, es, fr, de, ja)"
            default     = "en"
          }
        }
        required = ["query"]
      })
    }
    "knowledge_ingestion" = {
      name        = "ingest"
      description = "Ingest or update knowledge base articles into S3 Vector storage"
      input_schema = jsonencode({
        type = "object"
        properties = {
          articles = {
            type        = "array"
            description = "Array of knowledge base articles to ingest"
            items = {
              type = "object"
              properties = {
                title       = { type = "string" }
                content     = { type = "string" }
                category    = { type = "string" }
                tags        = { type = "array", items = { type = "string" } }
                language    = { type = "string", default = "en" }
              }
              required = ["title", "content"]
            }
          }
        }
        required = ["articles"]
      })
    }
    "create_ticket" = {
      name        = "create_ticket"
      description = "Create a new support ticket in DynamoDB"
      input_schema = jsonencode({
        type = "object"
        properties = {
          user_id = {
            type        = "string"
            description = "User ID for ticket creation"
          }
          customer_email = {
            type        = "string"
            description = "Customer email address"
          }
          subject = {
            type        = "string"
            description = "Ticket subject/title"
          }
          description = {
            type        = "string"
            description = "Ticket description/question"
          }
          category = {
            type        = "string"
            description = "Ticket category: account, billing, technical, how-to, general"
            enum        = ["account", "billing", "technical", "how-to", "general"]
          }
          priority = {
            type        = "string"
            description = "Ticket priority: critical, high, medium, low"
            enum        = ["critical", "high", "medium", "low"]
          }
          status = {
            type        = "string"
            description = "Ticket status: open, in-progress, resolved, closed, escalated, cancelled"
            enum        = ["open", "in-progress", "resolved", "closed", "escalated", "cancelled"]
          }
        }
        required = []
      })
    }
    "get_ticket" = {
      name        = "get_ticket"
      description = "Retrieve a ticket by ticket_id from DynamoDB"
      input_schema = jsonencode({
        type = "object"
        properties = {
          ticket_id = {
            type        = "string"
            description = "Ticket ID to retrieve"
          }
        }
        required = ["ticket_id"]
      })
    }
    "update_ticket" = {
      name        = "update_ticket"
      description = "Update ticket status in DynamoDB"
      input_schema = jsonencode({
        type = "object"
        properties = {
          ticket_id = {
            type        = "string"
            description = "Ticket ID to update"
          }
          status = {
            type        = "string"
            description = "New ticket status: open, in-progress, resolved, closed, escalated, cancelled"
            enum        = ["open", "in-progress", "resolved", "closed", "escalated", "cancelled"]
          }
        }
        required = ["ticket_id", "status"]
      })
    }
    "list_tickets" = {
      name        = "list_tickets"
      description = "List tickets by customer_email, status, or priority from DynamoDB"
      input_schema = jsonencode({
        type = "object"
        properties = {
          customer_email = {
            type        = "string"
            description = "Filter by customer email address"
          }
          status = {
            type        = "string"
            description = "Filter by ticket status: open, in-progress, resolved, closed, escalated, cancelled"
            enum        = ["open", "in-progress", "resolved", "closed", "escalated", "cancelled"]
          }
          priority = {
            type        = "string"
            description = "Filter by ticket priority: critical, high, medium, low"
            enum        = ["critical", "high", "medium", "low"]
          }
          limit = {
            type        = "number"
            description = "Maximum number of tickets to return (default: 10)"
          }
        }
        required = []
      })
    }
  }
  
  # Create a map of Lambda ARN to normalized function name
  # Extract function name from ARN and remove prefix, normalize hyphens to underscores
  lambda_arn_to_name = {
    for arn in var.lambda_function_arns : arn => replace(replace(split(":", arn)[6], "${var.resource_prefix}-", ""), "-", "_")
  }
}

# Gateway Targets for Lambda Functions
# Most Lambdas have one target, but ticket_management has 4 targets (one per tool)
resource "aws_bedrockagentcore_gateway_target" "lambda_targets" {
  for_each = {
    for arn in var.lambda_function_arns : arn => local.lambda_arn_to_name[arn]
    if local.lambda_arn_to_name[arn] != "ticket_management"  # Exclude ticket_management, handled separately
  }

  gateway_identifier = aws_bedrockagentcore_gateway.main.gateway_id
  name              = "${var.resource_prefix}-${replace(each.value, "_", "-")}-target"

  target_configuration {
    mcp {
      lambda {
        lambda_arn = each.key
        
        tool_schema {
          inline_payload {
            name        = local.lambda_tool_configs[each.value].name
            description = local.lambda_tool_configs[each.value].description
            
            # Input schema for the tool
            # Gateway passes input as JSON object to Lambda
            # The input_schema block defines the structure
            input_schema {
              type = "object"
            }
          }
        }
      }
    }
  }

  # Credential provider configuration
  # For AWS_IAM authentication, use gateway_iam_role
  # This allows the Gateway to use its IAM role to invoke Lambda functions
  credential_provider_configuration {
    gateway_iam_role {
      # Gateway will use its IAM role (aws_iam_role.gateway) to invoke Lambda
      # No additional configuration needed for AWS_IAM authentication
    }
  }

  depends_on = [aws_bedrockagentcore_gateway.main]
}

# Special case: Create 4 separate Gateway targets for ticket_management Lambda
# Each target points to the same Lambda but exposes a different tool
locals {
  ticket_management_arn = [
    for arn in var.lambda_function_arns : arn
    if replace(replace(split(":", arn)[6], "${var.resource_prefix}-", ""), "-", "_") == "ticket_management"
  ][0]
  
  ticket_tools = ["create_ticket", "get_ticket", "update_ticket", "list_tickets"]
}

resource "aws_bedrockagentcore_gateway_target" "ticket_targets" {
  for_each = toset(local.ticket_tools)

  gateway_identifier = aws_bedrockagentcore_gateway.main.gateway_id
  # Shortened name to keep tool name under 64 chars (Bedrock limit)
  # Format: dev-cs-ticket-{operation}-target (cs = customer-support)
  name              = "dev-cs-ticket-${replace(each.value, "_", "-")}-target"

  target_configuration {
    mcp {
      lambda {
        lambda_arn = local.ticket_management_arn
        
        tool_schema {
          inline_payload {
            name        = local.lambda_tool_configs[each.value].name
            description = local.lambda_tool_configs[each.value].description
            
            # Input schema for the tool
            input_schema {
              type = "object"
            }
          }
        }
      }
    }
  }

  credential_provider_configuration {
    gateway_iam_role {
      # Gateway will use its IAM role to invoke Lambda
    }
  }

  depends_on = [aws_bedrockagentcore_gateway.main]
}

