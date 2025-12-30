#!/usr/bin/env python3
"""
Test Long-Term Memory (LTM) across different sessions
Tests that information persists when session_id changes but user_id stays the same
"""

import subprocess
import json
import uuid
import time
import sys

def generate_session_id(prefix: str = "session") -> str:
    """Generate a session ID that meets AgentCore requirements (min 33 chars)"""
    return f"{prefix}-{uuid.uuid4()}"

def invoke_agent(prompt: str, session_id: str, user_id: str) -> dict:
    """Invoke agent using agentcore CLI with user_id for LTM"""
    payload = {
        "input": prompt,
        "user_id": user_id,
        "session_id": session_id,
        "context": {
            "user_id": user_id
        }
    }
    
    cmd = [
        "agentcore", "invoke",
        json.dumps(payload),
        "--session-id", session_id,
        "--user-id", user_id  # CRITICAL: This enables LTM
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            print(f"❌ Error: {result.stderr}")
            return None
        
        # Parse response - agentcore CLI outputs formatted text, need to extract JSON
        stdout = result.stdout
        
        # Try to find JSON in response
        if "Response:" in stdout:
            json_start = stdout.find("{")
            if json_start != -1:
                # Find the matching closing brace
                brace_count = 0
                json_end = json_start
                for i in range(json_start, len(stdout)):
                    if stdout[i] == '{':
                        brace_count += 1
                    elif stdout[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_end = i + 1
                            break
                
                json_str = stdout[json_start:json_end]
                try:
                    parsed = json.loads(json_str)
                    return parsed
                except Exception as e:
                    print(f"⚠️  JSON parse error: {e}")
                    print(f"   JSON string: {json_str[:200]}...")
        
        # Fallback: try to extract message from raw output
        if '"message"' in stdout:
            try:
                import re
                match = re.search(r'"message"\s*:\s*"([^"]*(?:\\.[^"]*)*)"', stdout, re.DOTALL)
                if match:
                    message = match.group(1).replace('\\n', '\n').replace('\\"', '"')
                    return {"message": message, "raw": stdout}
            except:
                pass
        
        return {"message": stdout, "raw": stdout}
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

def test_ltm():
    """Test Long-Term Memory across sessions"""
    print("🧪 Long-Term Memory (LTM) Cross-Session Test")
    print("=" * 70)
    
    # Use a consistent user_id across sessions
    user_id = f"test-user-{uuid.uuid4().hex[:8]}"
    print(f"\n📋 User ID: {user_id}")
    print("   (This will stay the same across different sessions)")
    
    # Session 1: Store information
    session_id_1 = generate_session_id("session-1")
    print(f"\n📋 Session 1 ID: {session_id_1}")
    print("=" * 70)
    
    print("\n🔹 Step 1: Store information in Session 1")
    print("-" * 70)
    prompt1 = "My name is John and my favorite color is blue. I prefer email notifications."
    print(f"Prompt: '{prompt1}'")
    
    response1 = invoke_agent(prompt1, session_id_1, user_id)
    if not response1:
        print("❌ Failed to get response")
        return False
    
    msg1 = response1.get('message', '') if isinstance(response1, dict) else str(response1)
    print(f"\n✅ Response:")
    print(f"   {msg1[:500]}...")
    print(f"\n📝 Full response keys: {list(response1.keys()) if isinstance(response1, dict) else 'N/A'}")
    
    time.sleep(3)
    
    # Session 2: Different session ID, same user_id - should remember
    session_id_2 = generate_session_id("session-2")
    print(f"\n📋 Session 2 ID: {session_id_2}")
    print("   (Different session, but same user_id)")
    print("=" * 70)
    
    print("\n🔹 Step 2: Query in Session 2 (should remember from Session 1)")
    print("-" * 70)
    prompt2 = "What is my name and what are my preferences?"
    print(f"Prompt: '{prompt2}'")
    print("Expected: Should remember 'John', 'blue', and 'email notifications'")
    
    response2 = invoke_agent(prompt2, session_id_2, user_id)
    if not response2:
        print("❌ Failed to get response")
        return False
    
    msg2 = response2.get('message', '') if isinstance(response2, dict) else str(response2)
    print(f"\n✅ Response:")
    print(f"   {msg2[:800]}...")
    print(f"\n📝 Full response keys: {list(response2.keys()) if isinstance(response2, dict) else 'N/A'}")
    
    # Check if LTM worked - look for specific details
    ltm_indicators = ['john', 'blue', 'email', 'notification', 'preference', 'favorite', 'color']
    found = [ind for ind in ltm_indicators if ind.lower() in msg2.lower()]
    
    # More detailed check
    has_john = 'john' in msg2.lower()
    has_blue = 'blue' in msg2.lower()
    has_email = 'email' in msg2.lower()
    
    print("\n" + "=" * 70)
    print("📊 LTM Test Results")
    print("=" * 70)
    
    print(f"\n🔍 LTM Details Check:")
    print(f"   Found 'john': {has_john}")
    print(f"   Found 'blue': {has_blue}")
    print(f"   Found 'email': {has_email}")
    print(f"   All indicators found: {', '.join(found)}")
    
    if found and (has_john or has_blue or has_email):
        print(f"\n✅ LTM WORKING! Found indicators: {', '.join(found)}")
        print("   The agent remembered information from Session 1 in Session 2!")
        print(f"   ✅ Same user_id: {user_id}")
        print(f"   ✅ Different session IDs: {session_id_1[:20]}... vs {session_id_2[:20]}...")
        return True
    else:
        print("\n❌ LTM NOT WORKING - Missing key details")
        print("   The agent did not remember specific information from Session 1")
        print(f"   ⚠️  Check:")
        print(f"      - user_id is being passed: {user_id}")
        print(f"      - --user-id flag is being used")
        print(f"      - AgentCore Runtime LTM is configured")
        print(f"      - System prompt includes LTM instructions")
        return False

if __name__ == "__main__":
    success = test_ltm()
    sys.exit(0 if success else 1)

