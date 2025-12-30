# Variables for S3 Module

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