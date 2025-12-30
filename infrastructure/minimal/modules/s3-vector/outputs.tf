# Outputs for S3 Vector Module

# Vector Bucket Outputs
output "vector_bucket_name" {
  description = "Name of the S3 vector bucket"
  value       = aws_s3_bucket.vector.id
}

output "vector_bucket_arn" {
  description = "ARN of the S3 vector bucket"
  value       = aws_s3_bucket.vector.arn
}

output "vector_bucket_domain_name" {
  description = "Domain name of the S3 vector bucket"
  value       = aws_s3_bucket.vector.bucket_domain_name
}

output "vector_bucket_regional_domain_name" {
  description = "Regional domain name of the S3 vector bucket"
  value       = aws_s3_bucket.vector.bucket_regional_domain_name
}

# Vector Configuration Outputs
output "vector_dimensions" {
  description = "Number of vector dimensions configured"
  value       = var.vector_dimensions
}

output "similarity_algorithm" {
  description = "Similarity algorithm configured for vector search"
  value       = var.similarity_algorithm
}

# Vector Indexes Outputs
output "vector_indexes" {
  description = "Map of language codes to vector index configuration keys"
  value = {
    for lang in var.supported_languages : lang => aws_s3_object.vector_index_placeholders[lang].key
  }
}

output "vector_index_arns" {
  description = "Map of language codes to vector index object ARNs"
  value = {
    for lang in var.supported_languages : lang => "arn:aws:s3:::${aws_s3_bucket.vector.id}/${aws_s3_object.vector_index_placeholders[lang].key}"
  }
}

output "supported_languages" {
  description = "List of supported languages with vector indexes"
  value       = var.supported_languages
}