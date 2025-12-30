#!/usr/bin/env python3
"""
Check Bedrock model access and help enable models if needed
"""

import boto3
import json
import sys

def check_bedrock_access():
    """Check if Bedrock models are accessible"""
    print("🔍 Checking Bedrock Model Access")
    print("=" * 70)
    
    try:
        session = boto3.Session(region_name='us-east-1')
        bedrock = session.client('bedrock', region_name='us-east-1')
        
        # List available models
        response = bedrock.list_foundation_models()
        models = response.get('modelSummaries', [])
        
        print(f"\n✅ Found {len(models)} foundation models")
        
        # Check for Anthropic Claude models
        anthropic_models = [m for m in models if 'anthropic' in m.get('modelId', '').lower()]
        print(f"✅ Found {len(anthropic_models)} Anthropic models")
        
        # Check specific model
        target_model = "anthropic.claude-3-haiku-20240307-v1:0"
        model_found = any(target_model in m.get('modelId', '') for m in models)
        
        if model_found:
            print(f"\n✅ Model {target_model} is available")
        else:
            print(f"\n⚠️  Model {target_model} not found")
            print("   Available Anthropic models:")
            for m in anthropic_models[:5]:
                print(f"     - {m.get('modelId')}")
        
        # Try to test model access
        print(f"\n🧪 Testing model access...")
        bedrock_runtime = session.client('bedrock-runtime', region_name='us-east-1')
        
        # Try a simple test invoke
        try:
            test_payload = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 10,
                "messages": [
                    {"role": "user", "content": "Hi"}
                ]
            }
            
            response = bedrock_runtime.invoke_model(
                modelId=target_model,
                body=json.dumps(test_payload),
                contentType="application/json"
            )
            print(f"✅ Model access test: SUCCESS!")
            print("   The model is enabled and accessible")
            return True
            
        except bedrock_runtime.exceptions.ValidationException as e:
            print(f"⚠️  Validation error (might be payload format): {e}")
            return False
        except bedrock_runtime.exceptions.AccessDeniedException as e:
            print(f"❌ Access Denied: {e}")
            print("\n💡 Solution:")
            print("   1. Go to AWS Console > Bedrock > Model access")
            print(f"   2. Enable: {target_model}")
            print("   3. Wait a few minutes for activation")
            return False
        except Exception as e:
            error_code = getattr(e, 'response', {}).get('Error', {}).get('Code', 'Unknown')
            if 'UnrecognizedClientException' in str(e) or error_code == 'UnrecognizedClientException':
                print(f"❌ UnrecognizedClientException: {e}")
                print("\n💡 This usually means:")
                print("   • The model isn't enabled in your AWS account")
                print("   • Or credentials don't have bedrock:InvokeModel permission")
                print("\n🔧 Fix:")
                print("   1. AWS Console > Bedrock > Model access")
                print(f"   2. Enable: Anthropic Claude 3 Haiku")
                print("   3. Restart agentcore dev")
            else:
                print(f"❌ Error: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking Bedrock: {e}")
        return False

if __name__ == "__main__":
    success = check_bedrock_access()
    sys.exit(0 if success else 1)

