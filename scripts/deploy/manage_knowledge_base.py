#!/usr/bin/env python3
"""
Knowledge Base Management Script
Helps manage knowledge base content locally and sync with AWS
"""

import json
import boto3
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


class KnowledgeBaseManager:
    def __init__(self):
        self.s3 = boto3.client('s3')
        self.dynamodb = boto3.resource('dynamodb')
        self.bucket_name = os.environ.get('KNOWLEDGE_BASE_BUCKET', 'dev-customer-support-knowledge-base')
        self.table_name = os.environ.get('KNOWLEDGE_BASE_TABLE', 'dev-customer-support-knowledge-base')
        
    def add_article(self, article: Dict[str, Any]) -> str:
        """Add a new article to the knowledge base"""
        # Generate ID if not provided
        if 'id' not in article:
            import hashlib
            article['id'] = f"kb-{hashlib.md5(article['title'].encode()).hexdigest()[:8]}"
        
        # Add timestamps
        article['created_at'] = datetime.utcnow().isoformat()
        article['updated_at'] = datetime.utcnow().isoformat()
        
        # Store locally first
        self._save_article_locally(article)
        
        # Upload to S3
        self._upload_to_s3(article)
        
        print(f"✅ Added article: {article['title']} (ID: {article['id']})")
        return article['id']
    
    def update_article(self, article_id: str, updates: Dict[str, Any]) -> None:
        """Update an existing article"""
        # Load existing article
        article = self._load_article_locally(article_id)
        if not article:
            print(f"❌ Article {article_id} not found")
            return
        
        # Apply updates
        article.update(updates)
        article['updated_at'] = datetime.utcnow().isoformat()
        
        # Save locally
        self._save_article_locally(article)
        
        # Upload to S3
        self._upload_to_s3(article)
        
        print(f"✅ Updated article: {article['title']} (ID: {article_id})")
    
    def delete_article(self, article_id: str) -> None:
        """Delete an article from the knowledge base"""
        # Remove local file
        local_path = Path(f"knowledge-base/{article_id}.json")
        if local_path.exists():
            local_path.unlink()
        
        # Remove from S3
        try:
            self.s3.delete_object(
                Bucket=self.bucket_name,
                Key=f"knowledge-base/{article_id}.json"
            )
        except Exception as e:
            print(f"⚠️  Failed to delete from S3: {e}")
        
        print(f"✅ Deleted article: {article_id}")
    
    def list_articles(self) -> List[Dict[str, Any]]:
        """List all articles in the knowledge base"""
        articles = []
        kb_dir = Path("knowledge-base")
        
        if not kb_dir.exists():
            return articles
        
        for file_path in kb_dir.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    article = json.load(f)
                    articles.append(article)
            except Exception as e:
                print(f"⚠️  Failed to load {file_path}: {e}")
        
        return articles
    
    def sync_to_aws(self) -> None:
        """Sync all local articles to AWS"""
        articles = self.list_articles()
        
        for article in articles:
            try:
                self._upload_to_s3(article)
                print(f"✅ Synced: {article['title']}")
            except Exception as e:
                print(f"❌ Failed to sync {article['title']}: {e}")
        
        print(f"🚀 Synced {len(articles)} articles to AWS")
    
    def import_from_file(self, file_path: str) -> None:
        """Import articles from a JSON file"""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            articles = data
        elif isinstance(data, dict) and 'articles' in data:
            articles = data['articles']
        else:
            articles = [data]
        
        for article in articles:
            self.add_article(article)
        
        print(f"📥 Imported {len(articles)} articles from {file_path}")
    
    def export_to_file(self, file_path: str) -> None:
        """Export all articles to a JSON file"""
        articles = self.list_articles()
        
        with open(file_path, 'w') as f:
            json.dump(articles, f, indent=2)
        
        print(f"📤 Exported {len(articles)} articles to {file_path}")
    
    def _save_article_locally(self, article: Dict[str, Any]) -> None:
        """Save article to local file system"""
        kb_dir = Path("knowledge-base")
        kb_dir.mkdir(exist_ok=True)
        
        file_path = kb_dir / f"{article['id']}.json"
        with open(file_path, 'w') as f:
            json.dump(article, f, indent=2)
    
    def _load_article_locally(self, article_id: str) -> Dict[str, Any]:
        """Load article from local file system"""
        file_path = Path(f"knowledge-base/{article_id}.json")
        if not file_path.exists():
            return None
        
        with open(file_path, 'r') as f:
            return json.load(f)
    
    def _upload_to_s3(self, article: Dict[str, Any]) -> None:
        """Upload article to S3"""
        try:
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=f"knowledge-base/{article['id']}.json",
                Body=json.dumps(article, indent=2),
                ContentType='application/json'
            )
        except Exception as e:
            print(f"⚠️  Failed to upload to S3: {e}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python manage_knowledge_base.py <command> [args]")
        print("Commands:")
        print("  add <title> <content> [category] [tags]")
        print("  update <id> <field> <value>")
        print("  delete <id>")
        print("  list")
        print("  sync")
        print("  import <file>")
        print("  export <file>")
        return
    
    manager = KnowledgeBaseManager()
    command = sys.argv[1]
    
    if command == "add":
        if len(sys.argv) < 4:
            print("Usage: add <title> <content> [category] [tags]")
            return
        
        article = {
            'title': sys.argv[2],
            'content': sys.argv[3],
            'category': sys.argv[4] if len(sys.argv) > 4 else 'general',
            'tags': sys.argv[5].split(',') if len(sys.argv) > 5 else [],
            'difficulty': 'medium',
            'customer_tier': 'basic',
            'rating': 4.0,
            'view_count': 0
        }
        
        manager.add_article(article)
    
    elif command == "update":
        if len(sys.argv) < 5:
            print("Usage: update <id> <field> <value>")
            return
        
        article_id = sys.argv[2]
        field = sys.argv[3]
        value = sys.argv[4]
        
        # Try to parse as JSON for complex values
        try:
            value = json.loads(value)
        except:
            pass
        
        manager.update_article(article_id, {field: value})
    
    elif command == "delete":
        if len(sys.argv) < 3:
            print("Usage: delete <id>")
            return
        
        manager.delete_article(sys.argv[2])
    
    elif command == "list":
        articles = manager.list_articles()
        print(f"\n📚 Knowledge Base ({len(articles)} articles):")
        print("-" * 60)
        
        for article in articles:
            print(f"ID: {article['id']}")
            print(f"Title: {article['title']}")
            print(f"Category: {article.get('category', 'N/A')}")
            print(f"Updated: {article.get('updated_at', 'N/A')}")
            print("-" * 60)
    
    elif command == "sync":
        manager.sync_to_aws()
    
    elif command == "import":
        if len(sys.argv) < 3:
            print("Usage: import <file>")
            return
        
        manager.import_from_file(sys.argv[2])
    
    elif command == "export":
        if len(sys.argv) < 3:
            print("Usage: export <file>")
            return
        
        manager.export_to_file(sys.argv[2])
    
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()