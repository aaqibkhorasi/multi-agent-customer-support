#!/usr/bin/env python3
"""
S3 Vector Manager
Manages S3 vector buckets and indexes for knowledge base storage
"""

import boto3
import json
import os
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from botocore.exceptions import ClientError, BotoCoreError, NoCredentialsError, PartialCredentialsError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class S3VectorManager:
    """Manager for S3 vector buckets and indexes"""
    
    def __init__(self, region_name: str = 'us-east-1'):
        try:
            self.s3vectors_client = boto3.client('s3vectors', region_name=region_name)
            self.bedrock_client = boto3.client('bedrock-runtime', region_name=region_name)
            self.bucket_name = os.environ.get('VECTOR_BUCKET_NAME', 'dev-customer-support-knowledge-vectors')
            self.region_name = region_name
            logger.info(f"Initialized S3VectorManager with bucket: {self.bucket_name}")
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise ValueError("AWS credentials not configured. Please set up AWS credentials.")
        except PartialCredentialsError:
            logger.error("Incomplete AWS credentials")
            raise ValueError("Incomplete AWS credentials. Please check your AWS configuration.")
        except Exception as e:
            logger.error(f"Failed to initialize S3VectorManager: {e}")
            raise
        
    def validate_bucket_name(self, bucket_name: str) -> bool:
        """Validate bucket name according to S3 vectors requirements"""
        if not bucket_name:
            logger.error("Bucket name is empty")
            return False
        if len(bucket_name) < 3 or len(bucket_name) > 63:
            logger.error(f"Bucket name length invalid: {len(bucket_name)} (must be 3-63 characters)")
            return False
        if not bucket_name.islower():
            logger.error("Bucket name must be lowercase")
            return False
        if not all(c.isalnum() or c == '-' for c in bucket_name):
            logger.error("Bucket name contains invalid characters (only alphanumeric and hyphens allowed)")
            return False
        if bucket_name.startswith('-') or bucket_name.endswith('-'):
            logger.error("Bucket name cannot start or end with hyphen")
            return False
        return True

    def create_vector_bucket(self) -> Dict[str, Any]:
        """Create S3 vector bucket with proper configuration"""
        try:
            # Validate bucket name
            if not self.validate_bucket_name(self.bucket_name):
                raise ValueError(f"Invalid bucket name: {self.bucket_name}. Must be 3-63 characters, lowercase, alphanumeric + hyphens only")
            
            logger.info(f"Creating vector bucket: {self.bucket_name}")
            response = self.s3vectors_client.create_vector_bucket(
                vectorBucketName=self.bucket_name,
                encryptionConfiguration={
                    'sseType': 'AES256'
                },
                tags={
                    'Environment': os.environ.get('ENVIRONMENT', 'dev'),
                    'Project': 'customer-support',
                    'Component': 'knowledge-base'
                }
            )
            logger.info(f"Successfully created vector bucket: {self.bucket_name}")
            print(f"✅ Created vector bucket: {self.bucket_name}")
            return response
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            if error_code == 'ConflictException':
                logger.info(f"Vector bucket {self.bucket_name} already exists")
                print(f"ℹ️  Vector bucket {self.bucket_name} already exists")
                return {'status': 'exists', 'vectorBucketName': self.bucket_name}
            elif error_code == 'ValidationException':
                logger.error(f"Invalid bucket configuration: {error_message}")
                raise ValueError(f"Invalid bucket configuration: {error_message}")
            elif error_code == 'AccessDeniedException':
                logger.error(f"Access denied creating bucket: {error_message}")
                raise PermissionError(f"Access denied creating bucket: {error_message}")
            elif error_code == 'ServiceQuotaExceededException':
                logger.error(f"Service quota exceeded: {error_message}")
                raise RuntimeError(f"Service quota exceeded: {error_message}")
            elif error_code == 'ThrottlingException':
                logger.warning(f"Request throttled, retrying: {error_message}")
                time.sleep(2)
                return self.create_vector_bucket()  # Retry once
            else:
                logger.error(f"Failed to create vector bucket: {error_code} - {error_message}")
                print(f"❌ Failed to create vector bucket: {error_code} - {error_message}")
                raise RuntimeError(f"Failed to create vector bucket: {error_code} - {error_message}")
        except BotoCoreError as e:
            logger.error(f"AWS service error creating bucket: {e}")
            raise RuntimeError(f"AWS service error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error creating vector bucket: {e}")
            print(f"❌ Failed to create vector bucket: {e}")
            raise
    
    def create_vector_index(self, index_name: str, language: str = 'en') -> Dict[str, Any]:
        """Create vector index for organizing vectors by language/category"""
        try:
            # Create index without metadata configuration for simplicity
            # All metadata will be filterable by default
            response = self.s3vectors_client.create_index(
                vectorBucketName=self.bucket_name,
                indexName=index_name,
                dataType='float32',
                dimension=1536,  # Titan embedding dimensions
                distanceMetric='cosine',
                tags={
                    'Language': language,
                    'Environment': os.environ.get('ENVIRONMENT', 'dev'),
                    'Project': 'customer-support'
                }
            )
            print(f"✅ Created vector index: {index_name}")
            return response
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ConflictException':
                print(f"ℹ️  Vector index {index_name} already exists")
                return {'status': 'exists', 'indexName': index_name}
            elif error_code == 'ValidationException':
                raise ValueError(f"Invalid index configuration: {e}")
            elif error_code == 'AccessDeniedException':
                raise PermissionError(f"Access denied creating index: {e}")
            else:
                print(f"❌ Failed to create vector index {index_name}: {e}")
                raise
        except Exception as e:
            print(f"❌ Failed to create vector index {index_name}: {e}")
            raise
    
    def bucket_exists(self) -> bool:
        """Check if vector bucket exists"""
        try:
            self.s3vectors_client.get_vector_bucket(vectorBucketName=self.bucket_name)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                return False
            else:
                raise
    
    def index_exists(self, index_name: str) -> bool:
        """Check if vector index exists"""
        try:
            self.s3vectors_client.get_index(
                vectorBucketName=self.bucket_name,
                indexName=index_name
            )
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                return False
            else:
                raise
    
    def initialize_infrastructure(self) -> Dict[str, Any]:
        """Initialize vector bucket and indexes if they don't exist"""
        results = {
            'bucket_created': False,
            'indexes_created': [],
            'errors': []
        }
        
        # Create bucket if it doesn't exist
        try:
            if not self.bucket_exists():
                self.create_vector_bucket()
                results['bucket_created'] = True
                # Wait for bucket to be ready
                time.sleep(2)
            else:
                print(f"ℹ️  Vector bucket {self.bucket_name} already exists")
        except Exception as e:
            results['errors'].append(f"Bucket creation failed: {str(e)}")
            return results
        
        # Create indexes for supported languages
        supported_languages = ['en', 'es', 'fr', 'de', 'ja']
        
        for language in supported_languages:
            index_name = f"knowledge-base-{language}"
            
            try:
                if not self.index_exists(index_name):
                    self.create_vector_index(index_name, language)
                    results['indexes_created'].append(index_name)
                    # Small delay between index creations
                    time.sleep(1)
                else:
                    print(f"ℹ️  Vector index {index_name} already exists")
            except Exception as e:
                results['errors'].append(f"Index {index_name} creation failed: {str(e)}")
        
        return results
    
    def get_bucket_info(self) -> Dict[str, Any]:
        """Get information about the vector bucket"""
        try:
            response = self.s3vectors_client.get_vector_bucket(vectorBucketName=self.bucket_name)
            return response
        except Exception as e:
            print(f"Failed to get bucket info: {e}")
            raise
    
    def get_index_info(self, index_name: str) -> Dict[str, Any]:
        """Get information about a specific vector index"""
        try:
            response = self.s3vectors_client.get_index(
                vectorBucketName=self.bucket_name,
                indexName=index_name
            )
            return response
        except Exception as e:
            print(f"Failed to get index info for {index_name}: {e}")
            raise

    def list_vector_indexes(self) -> List[str]:
        """List all vector indexes in the bucket"""
        try:
            response = self.s3vectors_client.list_indexes(vectorBucketName=self.bucket_name)
            return [index['indexName'] for index in response.get('indexes', [])]
        except Exception as e:
            print(f"Failed to list vector indexes: {e}")
            raise


class VectorOperations:
    """Operations for vector CRUD and search"""
    
    def __init__(self, vector_manager: S3VectorManager):
        self.vector_manager = vector_manager
        
    def put_vectors(self, index_name: str, vectors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Store multiple vectors with metadata in S3 vector index"""
        try:
            # Validate vectors format
            for vector in vectors:
                if 'vectorId' not in vector or 'vector' not in vector:
                    raise ValueError("Each vector must have 'vectorId' and 'vector' fields")
                if len(vector['vector']) != 1536:
                    raise ValueError(f"Vector must have 1536 dimensions, got {len(vector['vector'])}")
            
            # Convert to S3 vectors API format
            s3_vectors = []
            for vector in vectors:
                s3_vector = {
                    'key': vector['vectorId'],
                    'data': {'float32': vector['vector']},
                    'metadata': vector.get('metadata', {})
                }
                s3_vectors.append(s3_vector)
            
            response = self.vector_manager.s3vectors_client.put_vectors(
                vectorBucketName=self.vector_manager.bucket_name,
                indexName=index_name,
                vectors=s3_vectors
            )
            print(f"✅ Stored {len(vectors)} vectors in {index_name}")
            return response
        except Exception as e:
            print(f"❌ Failed to put vectors in {index_name}: {e}")
            raise
    
    def put_single_vector(self, index_name: str, vector_id: str, 
                         embedding: List[float], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Store single vector with metadata in S3 vector index"""
        vectors = [{
            'vectorId': vector_id,
            'vector': embedding,
            'metadata': metadata
        }]
        return self.put_vectors(index_name, vectors)
    
    def query_vectors(self, index_name: str, query_vector: List[float], 
                     top_k: int = 5, query_filter: Optional[Dict] = None) -> Dict[str, Any]:
        """Search vectors using native S3 vector query_vectors API"""
        try:
            # Validate query vector
            if len(query_vector) != 1536:
                raise ValueError(f"Query vector must have 1536 dimensions, got {len(query_vector)}")
            
            query_params = {
                'vectorBucketName': self.vector_manager.bucket_name,
                'indexName': index_name,
                'queryVector': {'float32': query_vector},
                'topK': top_k,
                'returnMetadata': True,
                'returnDistance': True
            }
            
            # Add metadata filters if provided
            if query_filter:
                query_params['filter'] = query_filter
            
            response = self.vector_manager.s3vectors_client.query_vectors(**query_params)
            print(f"✅ Queried {len(response.get('vectors', []))} vectors from {index_name}")
            return response
        except Exception as e:
            print(f"❌ Failed to query vectors in {index_name}: {e}")
            raise
    
    def update_vector(self, index_name: str, vector_id: str, 
                     embedding: List[float], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing vector with new embedding and metadata"""
        try:
            # Validate embedding
            if len(embedding) != 1536:
                raise ValueError(f"Embedding must have 1536 dimensions, got {len(embedding)}")
            
            # Use put_vectors to update (S3 vectors doesn't have separate update method)
            vectors = [{
                'key': vector_id,
                'data': {'float32': embedding},
                'metadata': metadata
            }]
            
            response = self.vector_manager.s3vectors_client.put_vectors(
                vectorBucketName=self.vector_manager.bucket_name,
                indexName=index_name,
                vectors=vectors
            )
            print(f"✅ Updated vector {vector_id} in {index_name}")
            return response
        except Exception as e:
            print(f"❌ Failed to update vector {vector_id}: {e}")
            raise
    
    def delete_vector(self, index_name: str, vector_id: str) -> Dict[str, Any]:
        """Delete vector from S3 vector index"""
        try:
            response = self.vector_manager.s3vectors_client.delete_vectors(
                vectorBucketName=self.vector_manager.bucket_name,
                indexName=index_name,
                keys=[vector_id]
            )
            print(f"✅ Deleted vector {vector_id} from {index_name}")
            return response
        except Exception as e:
            print(f"❌ Failed to delete vector {vector_id}: {e}")
            raise
    
    def get_vector(self, index_name: str, vector_id: str) -> Dict[str, Any]:
        """Get specific vector by ID"""
        try:
            response = self.vector_manager.s3vectors_client.get_vectors(
                vectorBucketName=self.vector_manager.bucket_name,
                indexName=index_name,
                keys=[vector_id],
                returnMetadata=True
            )
            vectors = response.get('vectors', [])
            if vectors:
                return vectors[0]
            else:
                return None
        except Exception as e:
            print(f"❌ Failed to get vector {vector_id}: {e}")
            raise
    
    def list_vectors(self, index_name: str, max_results: int = 100) -> Dict[str, Any]:
        """List vectors in an index"""
        try:
            response = self.vector_manager.s3vectors_client.list_vectors(
                vectorBucketName=self.vector_manager.bucket_name,
                indexName=index_name,
                maxResults=max_results,
                returnMetadata=True
            )
            return response
        except Exception as e:
            print(f"❌ Failed to list vectors in {index_name}: {e}")
            raise


# For testing and initialization
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python s3_vector_manager.py <command>")
        print("Commands:")
        print("  init     - Initialize vector bucket and indexes")
        print("  info     - Get bucket information")
        print("  list     - List vector indexes")
        sys.exit(1)
    
    command = sys.argv[1]
    vector_manager = S3VectorManager()
    
    if command == "init":
        print("🚀 Initializing S3 vector infrastructure...")
        results = vector_manager.initialize_infrastructure()
        
        print(f"\n📊 Results:")
        print(f"Bucket created: {results['bucket_created']}")
        print(f"Indexes created: {len(results['indexes_created'])}")
        
        if results['indexes_created']:
            for index in results['indexes_created']:
                print(f"  - {index}")
        
        if results['errors']:
            print(f"\n❌ Errors:")
            for error in results['errors']:
                print(f"  - {error}")
        else:
            print("\n✅ Infrastructure initialization completed successfully!")
    
    elif command == "info":
        print("📋 Getting bucket information...")
        info = vector_manager.get_bucket_info()
        print(json.dumps(info, indent=2, default=str))
    
    elif command == "list":
        print("📋 Listing vector indexes...")
        indexes = vector_manager.list_vector_indexes()
        print(f"Found {len(indexes)} indexes:")
        for index in indexes:
            print(f"  - {index}")
    
    else:
        print(f"Unknown command: {command}")