# S3 Module for Customer Support Platform
# Manages S3 buckets for knowledge base and file storage

# Knowledge Base Bucket for articles and content
resource "aws_s3_bucket" "knowledge_base" {
  bucket = "${var.resource_prefix}-knowledge-base-${var.bucket_suffix}"

  tags = merge(var.common_tags, {
    Name        = "${var.resource_prefix}-knowledge-base-bucket"
    Description = "Knowledge base storage for articles and content"
    Purpose     = "knowledge_base"
  })
}

# Block public access for knowledge base bucket
resource "aws_s3_bucket_public_access_block" "knowledge_base" {
  bucket = aws_s3_bucket.knowledge_base.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Enable versioning for knowledge base bucket
resource "aws_s3_bucket_versioning" "knowledge_base" {
  bucket = aws_s3_bucket.knowledge_base.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Server-side encryption for knowledge base bucket
resource "aws_s3_bucket_server_side_encryption_configuration" "knowledge_base" {
  bucket = aws_s3_bucket.knowledge_base.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# Lifecycle configuration for knowledge base bucket
resource "aws_s3_bucket_lifecycle_configuration" "knowledge_base" {
  bucket = aws_s3_bucket.knowledge_base.id

  rule {
    id     = "knowledge_base_lifecycle"
    status = "Enabled"

    filter {
      prefix = ""
    }

    # Keep current versions for 90 days (longer for knowledge base)
    expiration {
      days = 90
    }

    # Keep non-current versions for 60 days (must be greater than transition days)
    noncurrent_version_expiration {
      noncurrent_days = 60
    }

    # Transition to IA after 30 days
    noncurrent_version_transition {
      noncurrent_days = 30
      storage_class   = "STANDARD_IA"
    }
  }
}