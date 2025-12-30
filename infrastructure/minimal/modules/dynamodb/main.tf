# DynamoDB Module for Customer Support Platform
# Manages all DynamoDB tables and indexes

# Tickets Table
resource "aws_dynamodb_table" "tickets" {
  name           = "${var.resource_prefix}-tickets"
  billing_mode   = var.billing_mode
  hash_key       = "ticket_id"

  attribute {
    name = "ticket_id"
    type = "S"
  }

  attribute {
    name = "customer_email"
    type = "S"
  }

  attribute {
    name = "status"
    type = "S"
  }

  attribute {
    name = "created_at"
    type = "S"
  }

  attribute {
    name = "priority"
    type = "S"
  }

  # Global Secondary Index for customer queries
  global_secondary_index {
    name               = "customer-email-index"
    hash_key           = "customer_email"
    range_key          = "created_at"
    projection_type    = "ALL"
  }

  # Global Secondary Index for status-based queries
  global_secondary_index {
    name               = "status-index"
    hash_key           = "status"
    range_key          = "created_at"
    projection_type    = "ALL"
  }

  # Global Secondary Index for priority-based queries
  global_secondary_index {
    name               = "priority-index"
    hash_key           = "priority"
    range_key          = "created_at"
    projection_type    = "ALL"
  }

  # Point-in-time recovery
  point_in_time_recovery {
    enabled = true
  }

  # Server-side encryption
  server_side_encryption {
    enabled = true
  }

  tags = merge(var.common_tags, {
    Name        = "${var.resource_prefix}-tickets"
    Description = "Customer support tickets storage"
  })
}

# Customers Table
resource "aws_dynamodb_table" "customers" {
  name           = "${var.resource_prefix}-customers"
  billing_mode   = var.billing_mode
  hash_key       = "customer_id"

  attribute {
    name = "customer_id"
    type = "S"
  }

  attribute {
    name = "email"
    type = "S"
  }

  attribute {
    name = "customer_tier"
    type = "S"
  }

  # Global Secondary Index for email lookups
  global_secondary_index {
    name               = "email-index"
    hash_key           = "email"
    projection_type    = "ALL"
  }

  # Global Secondary Index for tier-based queries
  global_secondary_index {
    name               = "tier-index"
    hash_key           = "customer_tier"
    projection_type    = "ALL"
  }

  # Point-in-time recovery
  point_in_time_recovery {
    enabled = true
  }

  # Server-side encryption
  server_side_encryption {
    enabled = true
  }

  tags = merge(var.common_tags, {
    Name        = "${var.resource_prefix}-customers"
    Description = "Customer information and profiles"
  })
}

# Feedback Table
resource "aws_dynamodb_table" "feedback" {
  name           = "${var.resource_prefix}-feedback"
  billing_mode   = var.billing_mode
  hash_key       = "feedback_id"

  attribute {
    name = "feedback_id"
    type = "S"
  }

  attribute {
    name = "ticket_id"
    type = "S"
  }

  attribute {
    name = "created_at"
    type = "S"
  }

  # Global Secondary Index for ticket-based feedback queries
  global_secondary_index {
    name               = "ticket-feedback-index"
    hash_key           = "ticket_id"
    range_key          = "created_at"
    projection_type    = "ALL"
  }

  # Point-in-time recovery
  point_in_time_recovery {
    enabled = true
  }

  # Server-side encryption
  server_side_encryption {
    enabled = true
  }

  tags = merge(var.common_tags, {
    Name        = "${var.resource_prefix}-feedback"
    Description = "Customer feedback and satisfaction scores"
  })
}