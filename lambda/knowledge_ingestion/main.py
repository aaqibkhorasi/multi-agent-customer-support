#!/usr/bin/env python3
"""
Knowledge Base Ingestion Lambda Function - S3 Vector Storage
Ingests and updates knowledge base content using S3 vector storage
"""

import json
import os
import sys
import logging
from typing import Dict, Any, List
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the shared utils to the path
# In Lambda package, shared utils are at ./shared/utils relative to main.py
sys.path.append('/opt/python')
sys.path.append(os.path.join(os.path.dirname(__file__), 'shared', 'utils'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared', 'utils'))  # Fallback for local dev

try:
    from knowledge_ingestion_service import KnowledgeIngestionService
    from s3_vector_manager import S3VectorManager
    from embedding_service import EmbeddingService
except ImportError as e:
    logger.error(f"Import error: {e}")
    # Try alternative path
    try:
        from shared.utils.knowledge_ingestion_service import KnowledgeIngestionService
        from shared.utils.s3_vector_manager import S3VectorManager
        from shared.utils.embedding_service import EmbeddingService
    except ImportError as e2:
        logger.error(f"Alternative import error: {e2}")
        raise


def validate_article_data(article: Dict[str, Any]) -> Dict[str, Any]:
    """Validate article data for ingestion"""
    errors = []
    
    # Required fields
    if not article.get('title'):
        errors.append('Article title is required')
    elif len(article['title']) > 500:
        errors.append('Article title too long (max 500 characters)')
    
    if not article.get('content'):
        errors.append('Article content is required')
    elif len(article['content']) > 50000:
        errors.append('Article content too long (max 50,000 characters)')
    
    # Optional field validation
    if article.get('category') and len(article['category']) > 100:
        errors.append('Category name too long (max 100 characters)')
    
    if article.get('customer_tier'):
        valid_tiers = ['basic', 'premium', 'enterprise']
        if article['customer_tier'] not in valid_tiers:
            errors.append(f'Invalid customer tier. Must be one of: {valid_tiers}')
    
    if article.get('language'):
        valid_languages = ['en', 'es', 'fr', 'de', 'ja']
        if article['language'] not in valid_languages:
            errors.append(f'Invalid language. Must be one of: {valid_languages}')
    
    if article.get('difficulty'):
        valid_difficulties = ['easy', 'medium', 'hard']
        if article['difficulty'] not in valid_difficulties:
            errors.append(f'Invalid difficulty. Must be one of: {valid_difficulties}')
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Lambda function to ingest knowledge base content into S3 vector storage
    """
    request_id = context.aws_request_id if context else 'local-test'
    logger.info(f"Processing ingestion request {request_id}")
    
    try:
        # Initialize ingestion service with error handling
        try:
            ingestion_service = KnowledgeIngestionService()
        except Exception as e:
            logger.error(f"Failed to initialize ingestion service: {e}")
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({
                    'error': 'Service initialization failed',
                    'details': 'Unable to connect to vector storage service',
                    'timestamp': datetime.utcnow().isoformat(),
                    'request_id': request_id
                })
            }
        
        # Parse request body
        try:
            body = json.loads(event.get('body', '{}')) if event.get('body') else event
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in request body: {e}")
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({
                    'error': 'Invalid JSON in request body',
                    'details': str(e),
                    'timestamp': datetime.utcnow().isoformat(),
                    'request_id': request_id
                })
            }
        
        # Determine the action to perform
        action = body.get('action', 'ingest')
        logger.info(f"Processing action: {action}")
        
        if action == 'ingest':
            # Ingest single article
            article = body.get('article', {})
            if not article:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json'
                    },
                    'body': json.dumps({
                        'error': 'Article data is required for ingestion',
                        'timestamp': datetime.utcnow().isoformat(),
                        'request_id': request_id
                    })
                }
            
            # Validate article data
            validation = validate_article_data(article)
            if not validation['valid']:
                logger.warning(f"Invalid article data: {validation['errors']}")
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json'
                    },
                    'body': json.dumps({
                        'error': 'Invalid article data',
                        'details': validation['errors'],
                        'timestamp': datetime.utcnow().isoformat(),
                        'request_id': request_id
                    })
                }
            
            try:
                result = ingestion_service.ingest_article(article)
            except Exception as e:
                logger.error(f"Article ingestion failed: {e}")
                return {
                    'statusCode': 500,
                    'headers': {
                        'Content-Type': 'application/json'
                    },
                    'body': json.dumps({
                        'error': 'Article ingestion failed',
                        'details': str(e),
                        'timestamp': datetime.utcnow().isoformat(),
                        'request_id': request_id
                    })
                }
            
            if result['status'] == 'success':
                logger.info(f"Article ingested successfully: {result['article_id']}")
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json'
                    },
                    'body': json.dumps({
                        'message': 'Article ingested successfully',
                        'article_id': result['article_id'],
                        'index_name': result['index_name'],
                        'embedding_dimensions': result['embedding_dimensions'],
                        'ingested_at': result['ingested_at'],
                        'request_id': request_id
                    })
                }
            else:
                logger.error(f"Article ingestion failed: {result['error']}")
                return {
                    'statusCode': 500,
                    'headers': {
                        'Content-Type': 'application/json'
                    },
                    'body': json.dumps({
                        'error': 'Failed to ingest article',
                        'details': result['error'],
                        'article_id': result['article_id'],
                        'timestamp': datetime.utcnow().isoformat(),
                        'request_id': request_id
                    })
                }
        
        elif action == 'batch_ingest':
            # Batch ingest multiple articles
            articles = body.get('articles', [])
            if not articles:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json'
                    },
                    'body': json.dumps({
                        'error': 'Articles array is required for batch ingestion',
                        'timestamp': datetime.utcnow().isoformat(),
                        'request_id': request_id
                    })
                }
            
            if len(articles) > 100:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json'
                    },
                    'body': json.dumps({
                        'error': 'Too many articles for batch ingestion (max 100)',
                        'provided': len(articles),
                        'timestamp': datetime.utcnow().isoformat(),
                        'request_id': request_id
                    })
                }
            
            # Validate all articles first
            validation_errors = []
            for i, article in enumerate(articles):
                validation = validate_article_data(article)
                if not validation['valid']:
                    validation_errors.append({
                        'article_index': i,
                        'errors': validation['errors']
                    })
            
            if validation_errors:
                logger.warning(f"Invalid articles in batch: {len(validation_errors)} errors")
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json'
                    },
                    'body': json.dumps({
                        'error': 'Invalid articles in batch',
                        'validation_errors': validation_errors,
                        'timestamp': datetime.utcnow().isoformat(),
                        'request_id': request_id
                    })
                }
            
            try:
                result = ingestion_service.batch_ingest_articles(articles)
            except Exception as e:
                logger.error(f"Batch ingestion failed: {e}")
                return {
                    'statusCode': 500,
                    'headers': {
                        'Content-Type': 'application/json'
                    },
                    'body': json.dumps({
                        'error': 'Batch ingestion failed',
                        'details': str(e),
                        'timestamp': datetime.utcnow().isoformat(),
                        'request_id': request_id
                    })
                }
            
            logger.info(f"Batch ingestion completed: {result['successful']}/{result['total_articles']} successful")
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({
                    'message': 'Batch ingestion completed',
                    'total_articles': result['total_articles'],
                    'successful': result['successful'],
                    'failed': result['failed'],
                    'successful_articles': result['successful_articles'],
                    'errors': result['errors'],
                    'started_at': result['started_at'],
                    'completed_at': result['completed_at'],
                    'request_id': request_id
                })
            }
        
        elif action == 'update':
            # Update existing article
            article_id = body.get('article_id')
            updated_article = body.get('article', {})
            
            if not article_id or not updated_article:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json'
                    },
                    'body': json.dumps({
                        'error': 'Article ID and updated article data are required',
                        'timestamp': datetime.utcnow().isoformat(),
                        'request_id': request_id
                    })
                }
            
            # Validate updated article data
            validation = validate_article_data(updated_article)
            if not validation['valid']:
                logger.warning(f"Invalid updated article data: {validation['errors']}")
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json'
                    },
                    'body': json.dumps({
                        'error': 'Invalid updated article data',
                        'details': validation['errors'],
                        'timestamp': datetime.utcnow().isoformat(),
                        'request_id': request_id
                    })
                }
            
            try:
                result = ingestion_service.update_article(article_id, updated_article)
            except Exception as e:
                logger.error(f"Article update failed: {e}")
                return {
                    'statusCode': 500,
                    'headers': {
                        'Content-Type': 'application/json'
                    },
                    'body': json.dumps({
                        'error': 'Article update failed',
                        'details': str(e),
                        'article_id': article_id,
                        'timestamp': datetime.utcnow().isoformat(),
                        'request_id': request_id
                    })
                }
            
            if result['status'] == 'success':
                logger.info(f"Article updated successfully: {result['article_id']}")
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json'
                    },
                    'body': json.dumps({
                        'message': 'Article updated successfully',
                        'article_id': result['article_id'],
                        'index_name': result['index_name'],
                        'updated_at': result['updated_at'],
                        'request_id': request_id
                    })
                }
            else:
                logger.error(f"Article update failed: {result['error']}")
                return {
                    'statusCode': 500,
                    'headers': {
                        'Content-Type': 'application/json'
                    },
                    'body': json.dumps({
                        'error': 'Failed to update article',
                        'details': result['error'],
                        'article_id': result['article_id'],
                        'timestamp': datetime.utcnow().isoformat(),
                        'request_id': request_id
                    })
                }
        
        elif action == 'delete':
            # Delete article
            article_id = body.get('article_id')
            language = body.get('language', 'en')
            
            if not article_id:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json'
                    },
                    'body': json.dumps({
                        'error': 'Article ID is required for deletion',
                        'timestamp': datetime.utcnow().isoformat(),
                        'request_id': request_id
                    })
                }
            
            try:
                result = ingestion_service.delete_article(article_id, language)
            except Exception as e:
                logger.error(f"Article deletion failed: {e}")
                return {
                    'statusCode': 500,
                    'headers': {
                        'Content-Type': 'application/json'
                    },
                    'body': json.dumps({
                        'error': 'Article deletion failed',
                        'details': str(e),
                        'article_id': article_id,
                        'timestamp': datetime.utcnow().isoformat(),
                        'request_id': request_id
                    })
                }
            
            if result['status'] == 'success':
                logger.info(f"Article deleted successfully: {result['article_id']}")
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json'
                    },
                    'body': json.dumps({
                        'message': 'Article deleted successfully',
                        'article_id': result['article_id'],
                        'index_name': result['index_name'],
                        'deleted_at': result['deleted_at'],
                        'request_id': request_id
                    })
                }
            else:
                logger.error(f"Article deletion failed: {result['error']}")
                return {
                    'statusCode': 500,
                    'headers': {
                        'Content-Type': 'application/json'
                    },
                    'body': json.dumps({
                        'error': 'Failed to delete article',
                        'details': result['error'],
                        'article_id': result['article_id'],
                        'timestamp': datetime.utcnow().isoformat(),
                        'request_id': request_id
                    })
                }
        
        else:
            logger.warning(f"Unknown action requested: {action}")
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({
                    'error': f'Unknown action: {action}',
                    'supported_actions': ['ingest', 'batch_ingest', 'update', 'delete'],
                    'timestamp': datetime.utcnow().isoformat(),
                    'request_id': request_id
                })
            }
        
    except Exception as e:
        logger.error(f"Unexpected error in lambda handler: {e}")
        error_response = {
            'error': 'Internal server error',
            'details': 'An unexpected error occurred while processing your request',
            'timestamp': datetime.utcnow().isoformat(),
            'action': body.get('action', 'unknown') if 'body' in locals() else 'unknown',
            'request_id': request_id
        }
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps(error_response)
        }


# For local testing
if __name__ == "__main__":
    # Test with sample data
    test_event = {
        'action': 'ingest',
        'article': {
            'id': 'test-001',
            'title': 'Test Article for S3 Vector Storage',
            'summary': 'This is a test article for S3 vector ingestion',
            'content': 'This article demonstrates how to ingest knowledge base content into S3 vector storage using Amazon Bedrock Titan embeddings.',
            'category': 'testing',
            'subcategory': 'ingestion',
            'tags': ['test', 'ingestion', 's3', 'vector', 'bedrock'],
            'difficulty': 'easy',
            'customer_tier': 'basic',
            'language': 'en',
            'rating': 5,
            'view_count': 0,
            'solution_type': 'example',
            'status': 'published'
        }
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))