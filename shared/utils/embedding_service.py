#!/usr/bin/env python3
"""
Embedding Service
Generates vector embeddings using Amazon Bedrock Titan
"""

import boto3
import json
import time
from typing import List, Dict, Any
from datetime import datetime


class EmbeddingService:
    """Service for generating vector embeddings using Amazon Bedrock Titan"""
    
    def __init__(self, region_name: str = 'us-east-1'):
        self.bedrock_client = boto3.client('bedrock-runtime', region_name=region_name)
        self.model_id = "amazon.titan-embed-text-v1"
        self.region_name = region_name
        
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using Amazon Bedrock Titan"""
        try:
            body = {
                "inputText": text
            }
            
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body)
            )
            
            response_body = json.loads(response['body'].read())
            embedding = response_body['embedding']
            
            # Validate embedding dimensions
            if len(embedding) != 1536:
                raise ValueError(f"Invalid embedding dimensions: {len(embedding)}, expected 1536")
            
            return embedding
            
        except Exception as e:
            print(f"❌ Failed to generate embedding: {e}")
            raise
    
    def generate_batch_embeddings(self, texts: List[str], batch_size: int = 25) -> List[List[float]]:
        """Generate embeddings for multiple texts in batches"""
        embeddings = []
        total_texts = len(texts)
        
        print(f"🔄 Generating embeddings for {total_texts} texts...")
        
        for i in range(0, total_texts, batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = []
            
            print(f"Processing batch {i//batch_size + 1}/{(total_texts + batch_size - 1)//batch_size}")
            
            for j, text in enumerate(batch):
                try:
                    embedding = self.generate_embedding(text)
                    batch_embeddings.append(embedding)
                    
                    # Progress indicator
                    if (j + 1) % 5 == 0:
                        print(f"  Generated {j + 1}/{len(batch)} embeddings in current batch")
                        
                except Exception as e:
                    print(f"❌ Failed to generate embedding for text: {text[:50]}... Error: {e}")
                    # Use zero vector as fallback
                    batch_embeddings.append([0.0] * 1536)
            
            embeddings.extend(batch_embeddings)
            
            # Rate limiting to avoid throttling
            if i + batch_size < total_texts:
                time.sleep(0.1)
        
        print(f"✅ Generated {len(embeddings)} embeddings")
        return embeddings
    
    def validate_embedding(self, embedding: List[float]) -> bool:
        """Validate embedding format and dimensions"""
        if not isinstance(embedding, list):
            return False
        
        if len(embedding) != 1536:
            return False
        
        # Check if all elements are numbers
        try:
            for value in embedding:
                float(value)
        except (TypeError, ValueError):
            return False
        
        return True
    
    def get_embedding_stats(self, embedding: List[float]) -> Dict[str, Any]:
        """Get statistics about an embedding vector"""
        if not self.validate_embedding(embedding):
            raise ValueError("Invalid embedding format")
        
        import numpy as np
        
        arr = np.array(embedding)
        
        return {
            'dimensions': len(embedding),
            'mean': float(np.mean(arr)),
            'std': float(np.std(arr)),
            'min': float(np.min(arr)),
            'max': float(np.max(arr)),
            'norm': float(np.linalg.norm(arr)),
            'non_zero_count': int(np.count_nonzero(arr)),
            'zero_count': int(len(embedding) - np.count_nonzero(arr))
        }
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        if not (self.validate_embedding(embedding1) and self.validate_embedding(embedding2)):
            raise ValueError("Invalid embedding format")
        
        import numpy as np
        
        # Convert to numpy arrays
        a = np.array(embedding1)
        b = np.array(embedding2)
        
        # Calculate cosine similarity
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        similarity = dot_product / (norm_a * norm_b)
        return float(similarity)


# For testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python embedding_service.py <command> [args]")
        print("Commands:")
        print("  test <text>     - Generate embedding for text")
        print("  batch <file>    - Generate embeddings for texts in file (one per line)")
        print("  compare <text1> <text2> - Compare similarity between two texts")
        sys.exit(1)
    
    command = sys.argv[1]
    embedding_service = EmbeddingService()
    
    if command == "test":
        if len(sys.argv) < 3:
            print("Please provide text to embed")
            sys.exit(1)
        
        text = sys.argv[2]
        print(f"🔄 Generating embedding for: '{text}'")
        
        try:
            embedding = embedding_service.generate_embedding(text)
            stats = embedding_service.get_embedding_stats(embedding)
            
            print(f"✅ Generated embedding with {len(embedding)} dimensions")
            print(f"📊 Stats: mean={stats['mean']:.4f}, std={stats['std']:.4f}, norm={stats['norm']:.4f}")
            print(f"First 10 values: {embedding[:10]}")
            
        except Exception as e:
            print(f"❌ Failed: {e}")
    
    elif command == "batch":
        if len(sys.argv) < 3:
            print("Please provide file path")
            sys.exit(1)
        
        file_path = sys.argv[2]
        
        try:
            with open(file_path, 'r') as f:
                texts = [line.strip() for line in f if line.strip()]
            
            print(f"📁 Loaded {len(texts)} texts from {file_path}")
            embeddings = embedding_service.generate_batch_embeddings(texts)
            
            print(f"✅ Generated {len(embeddings)} embeddings")
            
            # Save embeddings
            output_file = file_path.replace('.txt', '_embeddings.json')
            with open(output_file, 'w') as f:
                json.dump({
                    'texts': texts,
                    'embeddings': embeddings,
                    'generated_at': datetime.utcnow().isoformat(),
                    'model': embedding_service.model_id
                }, f, indent=2)
            
            print(f"💾 Saved embeddings to {output_file}")
            
        except Exception as e:
            print(f"❌ Failed: {e}")
    
    elif command == "compare":
        if len(sys.argv) < 4:
            print("Please provide two texts to compare")
            sys.exit(1)
        
        text1 = sys.argv[2]
        text2 = sys.argv[3]
        
        try:
            print(f"🔄 Comparing texts:")
            print(f"Text 1: '{text1}'")
            print(f"Text 2: '{text2}'")
            
            embedding1 = embedding_service.generate_embedding(text1)
            embedding2 = embedding_service.generate_embedding(text2)
            
            similarity = embedding_service.calculate_similarity(embedding1, embedding2)
            
            print(f"✅ Similarity score: {similarity:.4f}")
            
            if similarity > 0.8:
                print("🟢 Very similar")
            elif similarity > 0.6:
                print("🟡 Moderately similar")
            elif similarity > 0.4:
                print("🟠 Somewhat similar")
            else:
                print("🔴 Not very similar")
                
        except Exception as e:
            print(f"❌ Failed: {e}")
    
    else:
        print(f"Unknown command: {command}")