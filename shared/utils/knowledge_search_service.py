#!/usr/bin/env python3
"""
Knowledge Search Service
Handles semantic search of knowledge base using S3 vector storage
"""

import json
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional

# Import our custom services
try:
    from .s3_vector_manager import S3VectorManager, VectorOperations
    from .embedding_service import EmbeddingService
except ImportError:
    # Fallback for direct execution
    from s3_vector_manager import S3VectorManager, VectorOperations
    from embedding_service import EmbeddingService


class KnowledgeSearchService:
    """Service for searching knowledge base using S3 vector storage"""
    
    def __init__(self, vector_manager: S3VectorManager = None, embedding_service: EmbeddingService = None):
        self.vector_manager = vector_manager or S3VectorManager()
        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_ops = VectorOperations(self.vector_manager)
        
    def search_knowledge_base(self, query: str, filters: Optional[Dict] = None, 
                            max_results: int = 5) -> Dict[str, Any]:
        """Search knowledge base using S3 vector query_vectors API"""
        try:
            # Generate query embedding
            query_embedding = self.embedding_service.generate_embedding(query)
            
            # Determine search language and index
            language = filters.get('language', 'en') if filters else 'en'
            index_name = f"knowledge-base-{language}"
            
            # Build query filter for customer tier access control
            query_filter = self._build_query_filter(filters) if filters else None
            
            # Perform vector search using query_vectors API
            search_response = self.vector_ops.query_vectors(
                index_name=index_name,
                query_vector=query_embedding,
                top_k=max_results,
                query_filter=query_filter
            )
            
            # Process search results
            results = []
            for vector_result in search_response.get('vectors', []):
                metadata = vector_result.get('metadata', {})
                
                result = {
                    'id': vector_result['key'],
                    'title': metadata.get('title', ''),
                    'summary': metadata.get('summary', ''),
                    'category': metadata.get('category', ''),
                    'subcategory': metadata.get('subcategory', ''),
                    'customer_tier': metadata.get('customer_tier', 'basic'),
                    'language': metadata.get('language', 'en'),
                    'tags': json.loads(metadata.get('tags', '[]')),
                    'difficulty': metadata.get('difficulty', 'medium'),
                    'rating': float(metadata.get('rating', 0)),
                    'view_count': int(metadata.get('view_count', 0)),
                    'solution_type': metadata.get('solution_type', 'article'),
                    'status': metadata.get('status', 'published'),
                    'relevance_score': 1.0 - vector_result.get('distance', 0.0),  # Convert distance to similarity
                    'last_updated': metadata.get('updated_at', ''),
                    'created_at': metadata.get('created_at', '')
                }
                
                results.append(result)
            
            return {
                'query': query,
                'results': results,
                'total_found': len(results),
                'search_timestamp': datetime.utcnow().isoformat(),
                'language': language,
                'search_method': 's3_vector_query_vectors',
                'filters_applied': filters or {}
            }
            
        except Exception as e:
            return {
                'query': query,
                'results': [],
                'total_found': 0,
                'error': str(e),
                'search_timestamp': datetime.utcnow().isoformat(),
                'search_method': 's3_vector_query_vectors',
                'filters_applied': filters or {}
            }
    
    def _build_query_filter(self, filters: Dict) -> Dict:
        """Build query filter for S3 vector search"""
        query_filter = {}
        
        # Try simpler filter format - just the field name and value
        if 'customer_tier' in filters:
            query_filter['customer_tier'] = filters['customer_tier']
        
        if 'category' in filters:
            query_filter['category'] = filters['category']
        
        if 'difficulty' in filters:
            query_filter['difficulty'] = filters['difficulty']
        
        if 'status' in filters:
            query_filter['status'] = filters['status']
        
        return query_filter
    
    def multi_language_search(self, query: str, languages: List[str], 
                            filters: Optional[Dict] = None, max_results: int = 5) -> Dict[str, Any]:
        """Search across multiple language indexes"""
        all_results = []
        search_details = []
        
        for language in languages:
            lang_filters = filters.copy() if filters else {}
            lang_filters['language'] = language
            
            search_result = self.search_knowledge_base(
                query=query,
                filters=lang_filters,
                max_results=max_results
            )
            
            all_results.extend(search_result['results'])
            search_details.append({
                'language': language,
                'results_count': len(search_result['results']),
                'error': search_result.get('error')
            })
        
        # Sort all results by relevance score
        all_results.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return {
            'query': query,
            'results': all_results[:max_results],
            'total_found': len(all_results),
            'languages_searched': languages,
            'search_details': search_details,
            'search_timestamp': datetime.utcnow().isoformat(),
            'search_method': 's3_vector_multi_language',
            'filters_applied': filters or {}
        }
    
    def search_by_category(self, query: str, category: str, customer_tier: str = 'basic', 
                          language: str = 'en', max_results: int = 5) -> Dict[str, Any]:
        """Search within a specific category"""
        filters = {
            'category': category,
            'customer_tier': customer_tier,
            'language': language
        }
        
        return self.search_knowledge_base(
            query=query,
            filters=filters,
            max_results=max_results
        )
    
    def search_similar_articles(self, article_id: str, language: str = 'en', 
                              max_results: int = 5) -> Dict[str, Any]:
        """Find articles similar to a given article"""
        try:
            # Get the original article's vector
            index_name = f"knowledge-base-{language}"
            article_vector = self.vector_ops.get_vector(index_name, article_id)
            
            if not article_vector or 'Vector' not in article_vector:
                raise ValueError(f"Article {article_id} not found")
            
            # Use the article's vector as query vector
            search_response = self.vector_ops.query_vectors(
                index_name=index_name,
                query_vector=article_vector['data']['float32'],
                top_k=max_results + 1  # +1 to exclude the original article
            )
            
            # Process results and exclude the original article
            results = []
            for vector_result in search_response.get('vectors', []):
                if vector_result['key'] != article_id:  # Exclude original article
                    metadata = vector_result.get('metadata', {})
                    
                    result = {
                        'id': vector_result['key'],
                        'title': metadata.get('title', ''),
                        'summary': metadata.get('summary', ''),
                        'category': metadata.get('category', ''),
                        'subcategory': metadata.get('subcategory', ''),
                        'customer_tier': metadata.get('customer_tier', 'basic'),
                        'language': metadata.get('language', 'en'),
                        'tags': json.loads(metadata.get('tags', '[]')),
                        'difficulty': metadata.get('difficulty', 'medium'),
                        'rating': float(metadata.get('rating', 0)),
                        'view_count': int(metadata.get('view_count', 0)),
                        'solution_type': metadata.get('solution_type', 'article'),
                        'relevance_score': 1.0 - vector_result.get('distance', 0.0),
                        'last_updated': metadata.get('updated_at', '')
                    }
                    
                    results.append(result)
                    
                    if len(results) >= max_results:
                        break
            
            return {
                'reference_article_id': article_id,
                'results': results,
                'total_found': len(results),
                'search_timestamp': datetime.utcnow().isoformat(),
                'language': language,
                'search_method': 's3_vector_similarity'
            }
            
        except Exception as e:
            return {
                'reference_article_id': article_id,
                'results': [],
                'total_found': 0,
                'error': str(e),
                'search_timestamp': datetime.utcnow().isoformat(),
                'search_method': 's3_vector_similarity'
            }
    
    def get_article_by_id(self, article_id: str, language: str = 'en') -> Dict[str, Any]:
        """Get a specific article by ID"""
        try:
            index_name = f"knowledge-base-{language}"
            vector_result = self.vector_ops.get_vector(index_name, article_id)
            
            if not vector_result:
                return {
                    'article_id': article_id,
                    'found': False,
                    'error': 'Article not found'
                }
            
            metadata = vector_result.get('metadata', {})
            
            article = {
                'id': article_id,
                'title': metadata.get('title', ''),
                'summary': metadata.get('summary', ''),
                'category': metadata.get('category', ''),
                'subcategory': metadata.get('subcategory', ''),
                'customer_tier': metadata.get('customer_tier', 'basic'),
                'language': metadata.get('language', 'en'),
                'tags': json.loads(metadata.get('tags', '[]')),
                'difficulty': metadata.get('difficulty', 'medium'),
                'rating': float(metadata.get('rating', 0)),
                'view_count': int(metadata.get('view_count', 0)),
                'solution_type': metadata.get('solution_type', 'article'),
                'status': metadata.get('status', 'published'),
                'content_length': int(metadata.get('content_length', 0)),
                'last_updated': metadata.get('updated_at', ''),
                'created_at': metadata.get('created_at', ''),
                'found': True
            }
            
            return article
            
        except Exception as e:
            return {
                'article_id': article_id,
                'found': False,
                'error': str(e)
            }


# For command line usage
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python knowledge_search_service.py <command> [args]")
        print("Commands:")
        print("  search <query>                    - Search knowledge base")
        print("  search <query> --category <cat>   - Search within category")
        print("  search <query> --tier <tier>      - Search for specific customer tier")
        print("  similar <article_id>              - Find similar articles")
        print("  get <article_id>                  - Get article by ID")
        sys.exit(1)
    
    command = sys.argv[1]
    search_service = KnowledgeSearchService()
    
    if command == "search":
        if len(sys.argv) < 3:
            print("Please provide search query")
            sys.exit(1)
        
        query = sys.argv[2]
        filters = {}
        
        # Parse additional arguments
        i = 3
        while i < len(sys.argv):
            if sys.argv[i] == "--category" and i + 1 < len(sys.argv):
                filters['category'] = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--tier" and i + 1 < len(sys.argv):
                filters['customer_tier'] = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--language" and i + 1 < len(sys.argv):
                filters['language'] = sys.argv[i + 1]
                i += 2
            else:
                i += 1
        
        print(f"🔍 Searching for: '{query}'")
        if filters:
            print(f"📋 Filters: {filters}")
        
        results = search_service.search_knowledge_base(query, filters, max_results=5)
        
        if results.get('error'):
            print(f"❌ Search failed: {results['error']}")
        else:
            print(f"✅ Found {results['total_found']} results:")
            
            for i, result in enumerate(results['results'], 1):
                print(f"\n{i}. {result['title']}")
                print(f"   Category: {result['category']}")
                print(f"   Relevance: {result['relevance_score']:.3f}")
                print(f"   Tier: {result['customer_tier']}")
                if result['summary']:
                    print(f"   Summary: {result['summary']}")
    
    elif command == "similar":
        if len(sys.argv) < 3:
            print("Please provide article ID")
            sys.exit(1)
        
        article_id = sys.argv[2]
        language = sys.argv[3] if len(sys.argv) > 3 else 'en'
        
        print(f"🔍 Finding articles similar to: {article_id}")
        
        results = search_service.search_similar_articles(article_id, language, max_results=5)
        
        if results.get('error'):
            print(f"❌ Search failed: {results['error']}")
        else:
            print(f"✅ Found {results['total_found']} similar articles:")
            
            for i, result in enumerate(results['results'], 1):
                print(f"\n{i}. {result['title']}")
                print(f"   Category: {result['category']}")
                print(f"   Similarity: {result['relevance_score']:.3f}")
    
    elif command == "get":
        if len(sys.argv) < 3:
            print("Please provide article ID")
            sys.exit(1)
        
        article_id = sys.argv[2]
        language = sys.argv[3] if len(sys.argv) > 3 else 'en'
        
        print(f"📄 Getting article: {article_id}")
        
        article = search_service.get_article_by_id(article_id, language)
        
        if not article['found']:
            print(f"❌ Article not found: {article.get('error', 'Unknown error')}")
        else:
            print(f"✅ Article found:")
            print(f"   Title: {article['title']}")
            print(f"   Category: {article['category']}")
            print(f"   Tier: {article['customer_tier']}")
            print(f"   Rating: {article['rating']}")
            print(f"   Views: {article['view_count']}")
            print(f"   Updated: {article['last_updated']}")
            if article['summary']:
                print(f"   Summary: {article['summary']}")
    
    else:
        print(f"Unknown command: {command}")