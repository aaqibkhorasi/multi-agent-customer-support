# S3 Vector Module for Customer Support Platform
# Manages S3 Vector buckets and indexes for knowledge base

# S3 Vector Bucket for knowledge base embeddings
resource "aws_s3_bucket" "vector" {
  bucket = "${var.resource_prefix}-vectors-${var.bucket_suffix}"

  tags = merge(var.common_tags, {
    Name        = "${var.resource_prefix}-vector-bucket"
    Description = "S3 Vector bucket for knowledge base embeddings"
    Purpose     = "vector-storage"
  })
}

# Block public access for vector bucket
resource "aws_s3_bucket_public_access_block" "vector" {
  bucket = aws_s3_bucket.vector.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Server-side encryption for vector bucket
resource "aws_s3_bucket_server_side_encryption_configuration" "vector" {
  bucket = aws_s3_bucket.vector.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# NOTE: S3 Vector is a conceptual feature for this demo
# In production, you would use Amazon OpenSearch Service with vector search
# or Amazon Bedrock Knowledge Bases for vector storage and search

# S3 Objects to simulate vector indexes for each language
resource "aws_s3_object" "vector_index_placeholders" {
  for_each = toset(var.supported_languages)
  
  bucket = aws_s3_bucket.vector.id
  key    = "indexes/knowledge-base-${each.value}/config.json"
  
  content = jsonencode({
    index_name           = "knowledge-base-${each.value}"
    language            = each.value
    dimensions          = var.vector_dimensions
    similarity_algorithm = var.similarity_algorithm
    created_at          = timestamp()
    
    # Metadata schema for filtering
    metadata_schema = {
      language = {
        type = "string"
        filterable = true
      }
      category = {
        type = "string"
        filterable = true
      }
      customer_tier = {
        type = "string"
        filterable = true
      }
      article_id = {
        type = "string"
        filterable = true
      }
      created_at = {
        type = "timestamp"
        filterable = true
      }
      updated_at = {
        type = "timestamp"
        filterable = true
      }
    }
  })

  content_type = "application/json"
  
  tags = merge(var.common_tags, {
    Name        = "${var.resource_prefix}-vector-index-${each.value}"
    Description = "Vector index configuration for ${each.value} language knowledge base"
    Language    = each.value
  })
}

# Lifecycle configuration for vector bucket
resource "aws_s3_bucket_lifecycle_configuration" "vector" {
  bucket = aws_s3_bucket.vector.id

  rule {
    id     = "vector_lifecycle"
    status = "Enabled"

    filter {
      prefix = ""
    }

    # Transition to IA after 30 days for cost optimization
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    # Transition to Glacier after 90 days for long-term storage
    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    # Delete after 365 days (adjust based on retention requirements)
    expiration {
      days = 365
    }
  }
}