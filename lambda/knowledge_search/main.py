#!/usr/bin/env python3
"""
Knowledge Search Lambda Function - S3 Vector Search
Uses native S3 vector storage and search capabilities
"""

import json
import os
import sys
import logging
from typing import Dict, Any
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
    from knowledge_search_service import KnowledgeSearchService
    from s3_vector_manager import S3VectorManager
    from embedding_service import EmbeddingService
except ImportError as e:
    logger.error(f"Import error: {e}")
    # Try alternative path
    try:
        from shared.utils.knowledge_search_service import KnowledgeSearchService
        from shared.utils.s3_vector_manager import S3VectorManager
        from shared.utils.embedding_service import EmbeddingService
    except ImportError as e2:
        logger.error(f"Alternative import error: {e2}")
        raise


def validate_search_input(event: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and sanitize search input parameters"""
    errors = []
    
    # Extract and validate query
    query = event.get('query', '').strip()
    if not query:
        errors.append('Query is required and cannot be empty')
    elif len(query) > 1000:
        errors.append('Query too long (max 1000 characters)')
    
    # Validate category
    category = event.get('category', '').strip()
    if category and len(category) > 100:
        errors.append('Category name too long (max 100 characters)')
    
    # Validate customer tier
    customer_tier = event.get('customer_tier', 'basic').strip().lower()
    valid_tiers = ['basic', 'premium', 'enterprise']
    if customer_tier not in valid_tiers:
        errors.append(f'Invalid customer tier. Must be one of: {valid_tiers}')
    
    # Validate language
    language = event.get('language', 'en').strip().lower()
    valid_languages = ['en', 'es', 'fr', 'de', 'ja']
    if language not in valid_languages:
        errors.append(f'Invalid language. Must be one of: {valid_languages}')
    
    # Validate max_results
    try:
        max_results = int(event.get('max_results', 5))
        if max_results < 1 or max_results > 50:
            errors.append('max_results must be between 1 and 50')
    except (ValueError, TypeError):
        errors.append('max_results must be a valid integer')
        max_results = 5
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'params': {
            'query': query,
            'category': category,
            'customer_tier': customer_tier,
            'language': language,
            'max_results': max_results
        }
    }


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Lambda function to search knowledge base using S3 vector storage
    """
    request_id = context.aws_request_id if context else 'local-test'
    logger.info(f"Processing search request {request_id}")
    
    try:
        # Validate input parameters
        validation = validate_search_input(event)
        if not validation['valid']:
            logger.warning(f"Invalid input parameters: {validation['errors']}")
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({
                    'error': 'Invalid input parameters',
                    'details': validation['errors'],
                    'timestamp': datetime.utcnow().isoformat(),
                    'request_id': request_id
                })
            }
        
        params = validation['params']
        logger.info(f"Search parameters: query='{params['query']}', category='{params['category']}', tier='{params['customer_tier']}', language='{params['language']}'")
        
        # Initialize search service with error handling
        try:
            search_service = KnowledgeSearchService()
        except Exception as e:
            logger.error(f"Failed to initialize search service: {e}")
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
        
        # Build filters - temporarily disable problematic filters
        filters = {
            'language': params['language']
        }
        
        # Only add category filter if provided (this works)
        if params['category']:
            filters['category'] = params['category']
        
        # Skip customer_tier filter for now due to S3 vector API limitations
        # TODO: Implement tier filtering in post-processing
        
        # Perform search with timeout handling
        try:
            search_results = search_service.search_knowledge_base(
                query=params['query'],
                filters=filters,
                max_results=params['max_results']
            )
        except Exception as e:
            logger.error(f"Search operation failed: {e}")
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({
                    'error': 'Search operation failed',
                    'details': str(e),
                    'query': params['query'],
                    'timestamp': datetime.utcnow().isoformat(),
                    'request_id': request_id
                })
            }
        
        # Check for search errors
        if search_results.get('error'):
            logger.error(f"Search failed: {search_results['error']}")
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({
                    'error': 'Search failed',
                    'details': search_results['error'],
                    'query': params['query'],
                    'timestamp': datetime.utcnow().isoformat(),
                    'request_id': request_id
                })
            }
        
        # Format results for compatibility with existing agents
        formatted_results = []
        for result in search_results['results']:
            # Apply customer tier filtering in post-processing
            result_tier = result.get('customer_tier', 'basic')
            tier_hierarchy = {'basic': 0, 'premium': 1, 'enterprise': 2}
            customer_level = tier_hierarchy.get(params['customer_tier'], 0)
            result_level = tier_hierarchy.get(result_tier, 0)
            
            # Only include results accessible to customer tier
            if result_level <= customer_level:
                formatted_result = {
                    'id': result['id'],
                    'title': result['title'],
                    'summary': result.get('summary', ''),
                    'content': result.get('summary', result['title']),  # Use summary as content preview
                    'category': result['category'],
                    'subcategory': result['subcategory'],
                    'tags': result['tags'],
                    'difficulty': result['difficulty'],
                    'rating': result['rating'],
                    'view_count': result['view_count'],
                    'last_updated': result['last_updated'],
                    'solution_type': result['solution_type'],
                    'relevance_score': result['relevance_score'],
                    'customer_tier': result['customer_tier']
                }
                formatted_results.append(formatted_result)
        
        # Return successful response
        response_body = {
            'query': params['query'],
            'category': params['category'],
            'results': formatted_results,
            'total_found': len(formatted_results),  # Update count after filtering
            'search_timestamp': search_results['search_timestamp'],
            'language': params['language'],
            'customer_tier': params['customer_tier'],
            'search_method': 's3_vector_native',
            'filters_applied': search_results['filters_applied'],
            'request_id': request_id
        }
        
        logger.info(f"Search completed successfully: {len(formatted_results)} results found")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps(response_body)
        }
        
    except Exception as e:
        logger.error(f"Unexpected error in lambda handler: {e}")
        error_response = {
            'error': 'Internal server error',
            'details': 'An unexpected error occurred while processing your request',
            'timestamp': datetime.utcnow().isoformat(),
            'query': event.get('query', ''),
            'search_method': 's3_vector_native',
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
        'query': 'how to reset my password',
        'category': 'account',
        'customer_tier': 'premium',
        'language': 'en',
        'max_results': 5
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))