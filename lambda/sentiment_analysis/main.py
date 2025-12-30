#!/usr/bin/env python3
"""
Sentiment Analysis Lambda Function
Analyzes customer sentiment using Amazon Comprehend or Bedrock (configurable)
"""

import json
import boto3
import os
from typing import Dict, Any
from datetime import datetime


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Lambda function to analyze customer sentiment using Amazon Comprehend or Bedrock
    """
    try:
        # Extract text from event
        # Gateway may pass input directly or wrapped in 'input' or 'body'
        # Also check for 'message_text' which Gateway might use
        text = None
        if 'text' in event:
            text = event['text']
        elif 'message_text' in event:
            text = event['message_text']
        elif isinstance(event.get('input'), dict):
            text = event['input'].get('text') or event['input'].get('message_text')
        elif isinstance(event.get('body'), str):
            try:
                body = json.loads(event['body'])
                text = body.get('text') or body.get('message_text')
            except:
                pass
        
        if not text:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Text is required', 'received_event': event})
            }
        
        # Try Comprehend first, fallback to Bedrock
        use_bedrock = os.environ.get('USE_BEDROCK_FOR_SENTIMENT', 'true').lower() == 'true'
        
        if use_bedrock:
            result = analyze_sentiment_with_bedrock(text)
        else:
            try:
                result = analyze_sentiment_with_comprehend(text)
            except Exception as comprehend_error:
                print(f"Comprehend failed, falling back to Bedrock: {comprehend_error}")
                result = analyze_sentiment_with_bedrock(text)
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Failed to analyze sentiment',
                'details': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
        }


def analyze_sentiment_with_comprehend(text: str) -> Dict[str, Any]:
    """Analyze sentiment using Amazon Comprehend"""
    comprehend = boto3.client('comprehend')
    
    # Analyze sentiment
    sentiment_response = comprehend.detect_sentiment(
        Text=text,
        LanguageCode='en'
    )
    
    sentiment = sentiment_response['Sentiment']
    scores = sentiment_response['SentimentScore']
    
    # Calculate normalized sentiment score (-1 to 1)
    if sentiment == 'POSITIVE':
        normalized_score = scores['Positive'] - 0.5
    elif sentiment == 'NEGATIVE':
        normalized_score = -(scores['Negative'] - 0.5)
    else:
        normalized_score = 0
    
    # Determine if escalation is required
    requires_escalation = normalized_score < -0.7
    requires_priority_increase = normalized_score < -0.3
    
    return {
        'sentiment': sentiment,
        'normalized_score': normalized_score,
        'confidence': max(scores.values()),
        'requires_escalation': requires_escalation,
        'requires_priority_increase': requires_priority_increase,
        'raw_scores': scores,
        'service_used': 'comprehend'
    }


def analyze_sentiment_with_bedrock(text: str) -> Dict[str, Any]:
    """Analyze sentiment using Amazon Bedrock Claude model"""
    
    bedrock = boto3.client('bedrock-runtime', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
    
    prompt = f"""Analyze the sentiment of this customer message and respond with ONLY a JSON object:

Customer message: "{text}"

Respond with this exact JSON format:
{{
    "sentiment": "POSITIVE|NEGATIVE|NEUTRAL|MIXED",
    "normalized_score": <number between -1.0 and 1.0>,
    "confidence": <number between 0.0 and 1.0>,
    "requires_escalation": <true/false>,
    "requires_priority_increase": <true/false>,
    "raw_scores": {{
        "Positive": <0.0-1.0>,
        "Negative": <0.0-1.0>,
        "Neutral": <0.0-1.0>,
        "Mixed": <0.0-1.0>
    }}
}}

Rules:
- normalized_score: -1.0 (very negative) to +1.0 (very positive)
- requires_escalation: true if normalized_score < -0.7
- requires_priority_increase: true if normalized_score < -0.3
- confidence: how confident you are in the sentiment classification
"""

    body = {
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 500,
        "anthropic_version": "bedrock-2023-05-31"
    }
    
    response = bedrock.invoke_model(
        modelId="anthropic.claude-3-haiku-20240307-v1:0",
        body=json.dumps(body)
    )
    
    response_body = json.loads(response['body'].read())
    content = response_body['content'][0]['text']
    
    # Parse JSON response from Claude
    try:
        sentiment_data = json.loads(content)
        sentiment_data['service_used'] = 'bedrock'
        return sentiment_data
    except json.JSONDecodeError:
        # Fallback if Claude doesn't return valid JSON
        return {
            "sentiment": "NEUTRAL",
            "normalized_score": 0.0,
            "confidence": 0.5,
            "requires_escalation": False,
            "requires_priority_increase": False,
            "raw_scores": {
                "Positive": 0.33,
                "Negative": 0.33,
                "Neutral": 0.34,
                "Mixed": 0.0
            },
            "service_used": "bedrock"
        }


# For local testing
if __name__ == "__main__":
    # Test with sample data
    test_cases = [
        "I am extremely frustrated with your service!",
        "Thank you for your help!",
        "I have a question about my account."
    ]
    
    for text in test_cases:
        result = lambda_handler({'text': text}, None)
        print(f"Text: {text}")
        print(f"Result: {result}")
        print("-" * 50)