#!/usr/bin/env python3
"""
Knowledge Ingestion Service
Handles ingestion of knowledge base articles into S3 vector storage
"""

import json
import os
import sys
from pathlib import Path
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


class KnowledgeIngestionService:
    """Service for ingesting knowledge base articles into S3 vector storage"""
    
    def __init__(self, vector_manager: S3VectorManager = None, embedding_service: EmbeddingService = None):
        self.vector_manager = vector_manager or S3VectorManager()
        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_ops = VectorOperations(self.vector_manager)
        
    def ingest_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest single knowledge base article"""
        try:
            # Validate required fields
            if not article.get('title') or not article.get('content'):
                raise ValueError("Article must have 'title' and 'content' fields")
            
            # Generate embedding for article content
            content_text = f"{article['title']} {article.get('summary', '')} {article['content']}"
            embedding = self.embedding_service.generate_embedding(content_text)
            
            # Prepare metadata (all values must be strings for S3 vectors)
            metadata = {
                'title': str(article['title']),
                'category': str(article.get('category', 'general')),
                'subcategory': str(article.get('subcategory', '')),
                'customer_tier': str(article.get('customer_tier', 'basic')),
                'language': str(article.get('language', 'en')),
                'tags': json.dumps(article.get('tags', [])),
                'difficulty': str(article.get('difficulty', 'medium')),
                'created_at': str(article.get('created_at', datetime.utcnow().isoformat())),
                'updated_at': str(datetime.utcnow().isoformat()),
                'content_length': str(len(article['content'])),
                'rating': str(article.get('rating', 0)),
                'view_count': str(article.get('view_count', 0)),
                'solution_type': str(article.get('solution_type', 'article')),
                'status': str(article.get('status', 'published'))
            }
            
            # Add summary if available
            if article.get('summary'):
                metadata['summary'] = str(article['summary'])
            
            # Determine vector index based on language
            language = article.get('language', 'en')
            index_name = f"knowledge-base-{language}"
            vector_key = article.get('id', f"article-{hash(article['title'])}")
            
            # Store vector in S3
            vectors = [{
                'vectorId': vector_key,
                'vector': embedding,
                'metadata': metadata
            }]
            
            response = self.vector_ops.put_vectors(
                index_name=index_name,
                vectors=vectors
            )
            
            return {
                'status': 'success',
                'article_id': vector_key,
                'index_name': index_name,
                'embedding_dimensions': len(embedding),
                'metadata_keys': list(metadata.keys()),
                'ingested_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'article_id': article.get('id', 'unknown'),
                'error': str(e),
                'failed_at': datetime.utcnow().isoformat()
            }
    
    def batch_ingest_articles(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Batch ingest multiple articles"""
        results = {
            'total_articles': len(articles),
            'successful': 0,
            'failed': 0,
            'errors': [],
            'successful_articles': [],
            'started_at': datetime.utcnow().isoformat()
        }
        
        print(f"🔄 Starting batch ingestion of {len(articles)} articles...")
        
        for i, article in enumerate(articles, 1):
            print(f"Processing article {i}/{len(articles)}: {article.get('title', 'Unknown')}")
            
            result = self.ingest_article(article)
            
            if result['status'] == 'success':
                results['successful'] += 1
                results['successful_articles'].append(result['article_id'])
            else:
                results['failed'] += 1
                results['errors'].append({
                    'article_id': result['article_id'],
                    'error': result['error']
                })
        
        results['completed_at'] = datetime.utcnow().isoformat()
        
        print(f"✅ Batch ingestion completed: {results['successful']} successful, {results['failed']} failed")
        
        return results
    
    def update_article(self, article_id: str, updated_article: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing article in vector store"""
        try:
            # Validate required fields
            if not updated_article.get('title') or not updated_article.get('content'):
                raise ValueError("Article must have 'title' and 'content' fields")
            
            # Generate new embedding
            content_text = f"{updated_article['title']} {updated_article.get('summary', '')} {updated_article['content']}"
            embedding = self.embedding_service.generate_embedding(content_text)
            
            # Update metadata
            metadata = {
                'title': str(updated_article['title']),
                'category': str(updated_article.get('category', 'general')),
                'subcategory': str(updated_article.get('subcategory', '')),
                'customer_tier': str(updated_article.get('customer_tier', 'basic')),
                'language': str(updated_article.get('language', 'en')),
                'tags': json.dumps(updated_article.get('tags', [])),
                'difficulty': str(updated_article.get('difficulty', 'medium')),
                'updated_at': str(datetime.utcnow().isoformat()),
                'content_length': str(len(updated_article['content'])),
                'rating': str(updated_article.get('rating', 0)),
                'view_count': str(updated_article.get('view_count', 0)),
                'solution_type': str(updated_article.get('solution_type', 'article')),
                'status': str(updated_article.get('status', 'published'))
            }
            
            # Add summary if available
            if updated_article.get('summary'):
                metadata['summary'] = str(updated_article['summary'])
            
            # Update vector
            language = updated_article.get('language', 'en')
            index_name = f"knowledge-base-{language}"
            
            response = self.vector_ops.update_vector(
                index_name=index_name,
                vector_id=article_id,
                embedding=embedding,
                metadata=metadata
            )
            
            return {
                'status': 'success',
                'article_id': article_id,
                'index_name': index_name,
                'updated_at': metadata['updated_at']
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'article_id': article_id,
                'error': str(e),
                'failed_at': datetime.utcnow().isoformat()
            }
    
    def delete_article(self, article_id: str, language: str = 'en') -> Dict[str, Any]:
        """Delete article from vector store"""
        try:
            index_name = f"knowledge-base-{language}"
            response = self.vector_ops.delete_vector(
                index_name=index_name,
                vector_id=article_id
            )
            
            return {
                'status': 'success',
                'article_id': article_id,
                'index_name': index_name,
                'deleted_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'article_id': article_id,
                'error': str(e),
                'failed_at': datetime.utcnow().isoformat()
            }
    
    def ingest_from_json_file(self, file_path: str) -> Dict[str, Any]:
        """Ingest articles from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            if isinstance(data, list):
                articles = data
            elif isinstance(data, dict) and 'articles' in data:
                articles = data['articles']
            else:
                articles = [data]
            
            print(f"📁 Loaded {len(articles)} articles from {file_path}")
            
            # Batch ingest articles
            results = self.batch_ingest_articles(articles)
            results['source_file'] = file_path
            
            return results
            
        except Exception as e:
            return {
                'status': 'error',
                'source_file': file_path,
                'error': str(e),
                'failed_at': datetime.utcnow().isoformat()
            }
    
    def migrate_from_existing_embeddings(self, embeddings_file_path: str) -> Dict[str, Any]:
        """Migrate from existing embeddings.json file to S3 vectors"""
        try:
            with open(embeddings_file_path, 'r', encoding='utf-8') as f:
                embeddings_data = json.load(f)
            
            articles = embeddings_data.get('articles', [])
            print(f"📁 Loaded {len(articles)} articles with embeddings from {embeddings_file_path}")
            
            results = {
                'total_articles': len(articles),
                'successful': 0,
                'failed': 0,
                'errors': [],
                'successful_articles': [],
                'started_at': datetime.utcnow().isoformat()
            }
            
            for i, article in enumerate(articles, 1):
                print(f"Migrating article {i}/{len(articles)}: {article.get('title', 'Unknown')}")
                
                try:
                    # Use existing embedding if available, otherwise generate new one
                    if 'embedding' in article and len(article['embedding']) == 1536:
                        embedding = article['embedding']
                        print(f"  Using existing embedding")
                    else:
                        content_text = f"{article['title']} {article.get('summary', '')} {article['content']}"
                        embedding = self.embedding_service.generate_embedding(content_text)
                        print(f"  Generated new embedding")
                    
                    # Prepare metadata
                    metadata = {
                        'title': str(article['title']),
                        'category': str(article.get('category', 'general')),
                        'subcategory': str(article.get('subcategory', '')),
                        'customer_tier': str(article.get('customer_tier', 'basic')),
                        'language': str(article.get('language', 'en')),
                        'tags': json.dumps(article.get('tags', [])),
                        'difficulty': str(article.get('difficulty', 'medium')),
                        'created_at': str(article.get('created_at', datetime.utcnow().isoformat())),
                        'updated_at': str(datetime.utcnow().isoformat()),
                        'content_length': str(len(article.get('content', ''))),
                        'rating': str(article.get('rating', 0)),
                        'view_count': str(article.get('view_count', 0)),
                        'solution_type': str(article.get('solution_type', 'article')),
                        'status': str(article.get('status', 'published'))
                    }
                    
                    if article.get('summary'):
                        metadata['summary'] = str(article['summary'])
                    
                    # Store in S3 vectors
                    language = article.get('language', 'en')
                    index_name = f"knowledge-base-{language}"
                    vector_key = article.get('id', f"article-{hash(article['title'])}")
                    
                    vectors = [{
                        'vectorId': vector_key,
                        'vector': embedding,
                        'metadata': metadata
                    }]
                    
                    self.vector_ops.put_vectors(index_name=index_name, vectors=vectors)
                    
                    results['successful'] += 1
                    results['successful_articles'].append(vector_key)
                    
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append({
                        'article_id': article.get('id', 'unknown'),
                        'error': str(e)
                    })
            
            results['completed_at'] = datetime.utcnow().isoformat()
            
            print(f"✅ Migration completed: {results['successful']} successful, {results['failed']} failed")
            
            return results
            
        except Exception as e:
            return {
                'status': 'error',
                'source_file': embeddings_file_path,
                'error': str(e),
                'failed_at': datetime.utcnow().isoformat()
            }


# For command line usage
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python knowledge_ingestion_service.py <command> [args]")
        print("Commands:")
        print("  ingest <json_file>     - Ingest articles from JSON file")
        print("  migrate <embeddings_file> - Migrate from existing embeddings.json")
        print("  test                   - Test with sample article")
        sys.exit(1)
    
    command = sys.argv[1]
    ingestion_service = KnowledgeIngestionService()
    
    if command == "ingest":
        if len(sys.argv) < 3:
            print("Please provide JSON file path")
            sys.exit(1)
        
        file_path = sys.argv[2]
        print(f"🚀 Starting ingestion from {file_path}")
        
        results = ingestion_service.ingest_from_json_file(file_path)
        
        if results.get('status') == 'error':
            print(f"❌ Ingestion failed: {results['error']}")
        else:
            print(f"✅ Ingestion completed:")
            print(f"  Total: {results['total_articles']}")
            print(f"  Successful: {results['successful']}")
            print(f"  Failed: {results['failed']}")
            
            if results['errors']:
                print(f"  Errors:")
                for error in results['errors']:
                    print(f"    - {error['article_id']}: {error['error']}")
    
    elif command == "migrate":
        if len(sys.argv) < 3:
            print("Please provide embeddings file path")
            sys.exit(1)
        
        file_path = sys.argv[2]
        print(f"🚀 Starting migration from {file_path}")
        
        results = ingestion_service.migrate_from_existing_embeddings(file_path)
        
        if results.get('status') == 'error':
            print(f"❌ Migration failed: {results['error']}")
        else:
            print(f"✅ Migration completed:")
            print(f"  Total: {results['total_articles']}")
            print(f"  Successful: {results['successful']}")
            print(f"  Failed: {results['failed']}")
    
    elif command == "test":
        print("🧪 Testing with sample article...")
        
        sample_article = {
            'id': 'test-001',
            'title': 'Test Article',
            'summary': 'This is a test article for S3 vector ingestion',
            'content': 'This is the content of the test article. It contains information about testing the S3 vector ingestion service.',
            'category': 'testing',
            'subcategory': 'ingestion',
            'tags': ['test', 'ingestion', 's3', 'vector'],
            'difficulty': 'easy',
            'customer_tier': 'basic',
            'language': 'en',
            'rating': 5,
            'view_count': 0,
            'solution_type': 'example'
        }
        
        result = ingestion_service.ingest_article(sample_article)
        
        if result['status'] == 'success':
            print(f"✅ Test successful:")
            print(f"  Article ID: {result['article_id']}")
            print(f"  Index: {result['index_name']}")
            print(f"  Embedding dimensions: {result['embedding_dimensions']}")
        else:
            print(f"❌ Test failed: {result['error']}")
    
    else:
        print(f"Unknown command: {command}")