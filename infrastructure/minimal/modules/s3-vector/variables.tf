# Variables for S3 Vector Module

variable "resource_prefix" {
  description = "Prefix for resource naming"
  type        = string
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "bucket_suffix" {
  description = "Random suffix for bucket naming to ensure uniqueness"
  type        = string
}

variable "vector_dimensions" {
  description = "Number of dimensions for vector embeddings"
  type        = number
  default     = 1536
  
  validation {
    condition     = var.vector_dimensions > 0 && var.vector_dimensions <= 2048
    error_message = "Vector dimensions must be between 1 and 2048."
  }
}

variable "similarity_algorithm" {
  description = "Similarity algorithm for vector search"
  type        = string
  default     = "cosine"
  
  validation {
    condition     = contains(["cosine", "euclidean", "dot_product"], var.similarity_algorithm)
    error_message = "Similarity algorithm must be one of: cosine, euclidean, dot_product."
  }
}

variable "supported_languages" {
  description = "List of supported languages for knowledge base indexes"
  type        = list(string)
  default     = ["en", "es", "fr", "de", "ja"]
  
  validation {
    condition     = length(var.supported_languages) > 0
    error_message = "At least one language must be supported."
  }
}