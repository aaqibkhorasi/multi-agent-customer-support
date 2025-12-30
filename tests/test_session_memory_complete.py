#!/usr/bin/env python3
"""
Complete session memory test with conversation history tracking
Tests multi-turn conversations with proper context retention
"""

import requests
import json
import time
import sys

AGENT_URL = "http://localhost:8081/invocations"

def send_message(question: str, session_id: str, conversation_history: list = None, context: dict = None):
    """Send a message to the agent with a session ID and conversation history"""
    payload = {
        "question": question,
        "context": {
            **(context or {}),
            "runtimeSessionId": session_id,
            "conversation_history": conversation_history or []
        }
    }
    
    try:
        response = requests.post(AGENT_URL, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                print(f"   Response: {e.response.text[:200]}")
            except:
                pass
        return None

def test_session_memory():
    """Test session memory with multiple turns and conversation history"""
    print("🧪 Complete Session Memory Test")
    print("=" * 70)
    
    # Create a unique session ID
    session_id = f"test-session-{int(time.time())}"
    print(f"\n📋 Session ID: {session_id}")
    print(f"   Agent URL: {AGENT_URL}\n")
    
    conversation_history = []
    
    # Test 1: First message
    print("=" * 70)
    print("Test 1: Initial Message (Establishing Context)")
    print("=" * 70)
    question1 = "My name is John and I need help with password reset"
    print(f"Question: '{question1}'")
    
    response1 = send_message(
        question1,
        session_id,
        conversation_history,
        {"user_id": "john_doe", "customer_tier": "premium"}
    )
    
    if not response1:
        print("❌ Failed to get response")
        return False
    
    print(f"\n✅ Status: {response1.get('status', 'N/A')}")
    msg1 = response1.get('message', '')
    print(f"📝 Response ({len(msg1)} chars):")
    print("-" * 70)
    print(msg1[:500] + ("..." if len(msg1) > 500 else ""))
    print("-" * 70)
    
    # Add to conversation history
    conversation_history.append({
        "role": "user",
        "content": question1
    })
    conversation_history.append({
        "role": "assistant",
        "content": msg1
    })
    
    memory_info1 = response1.get('memory_info', {})
    print(f"\n💾 Memory Info:")
    print(f"   Enabled: {memory_info1.get('memory_enabled', False)}")
    print(f"   Conversation Length: {len(conversation_history)} messages")
    
    time.sleep(2)
    
    # Test 2: Follow-up that should reference previous context
    print("\n" + "=" * 70)
    print("Test 2: Follow-up Message (Should Remember Name & Issue)")
    print("=" * 70)
    question2 = "What was my issue again?"
    print(f"Question: '{question2}'")
    print(f"Conversation History: {len(conversation_history)} messages")
    print("Expected: Should remember the name 'John' and password reset issue")
    
    response2 = send_message(
        question2,
        session_id,  # Same session ID
        conversation_history,  # Pass conversation history
        {"user_id": "john_doe", "customer_tier": "premium"}
    )
    
    if not response2:
        print("❌ Failed to get response")
        return False
    
    print(f"\n✅ Status: {response2.get('status', 'N/A')}")
    msg2 = response2.get('message', '')
    print(f"📝 Response ({len(msg2)} chars):")
    print("-" * 70)
    print(msg2[:600] + ("..." if len(msg2) > 600 else ""))
    print("-" * 70)
    
    # Add to conversation history
    conversation_history.append({
        "role": "user",
        "content": question2
    })
    conversation_history.append({
        "role": "assistant",
        "content": msg2
    })
    
    memory_info2 = response2.get('memory_info', {})
    print(f"\n💾 Memory Info:")
    print(f"   Enabled: {memory_info2.get('memory_enabled', False)}")
    print(f"   Conversation Length: {len(conversation_history)} messages")
    
    # Check if memory retained context
    context_indicators = ['john', 'password', 'reset', 'previous', 'earlier', 'mentioned', 'you said', 'your issue']
    found = [ind for ind in context_indicators if ind.lower() in msg2.lower()]
    if found:
        print(f"\n✅ Context retention detected!")
        print(f"   Keywords: {', '.join(found[:5])}")
        print("   The agent remembered the previous conversation!")
        context_retained = True
    else:
        print("\n⚠️  No clear context indicators found")
        print("   The agent may not be using session memory")
        context_retained = False
    
    time.sleep(2)
    
    # Test 3: Another follow-up
    print("\n" + "=" * 70)
    print("Test 3: Third Follow-up (Should Remember Full Context)")
    print("=" * 70)
    question3 = "Can you remind me of the steps?"
    print(f"Question: '{question3}'")
    print(f"Conversation History: {len(conversation_history)} messages")
    print("Expected: Should remember password reset steps from first message")
    
    response3 = send_message(
        question3,
        session_id,  # Same session ID
        conversation_history,  # Pass full conversation history
        {"user_id": "john_doe", "customer_tier": "premium"}
    )
    
    if not response3:
        print("❌ Failed to get response")
        return False
    
    print(f"\n✅ Status: {response3.get('status', 'N/A')}")
    msg3 = response3.get('message', '')
    print(f"📝 Response ({len(msg3)} chars):")
    print("-" * 70)
    print(msg3[:600] + ("..." if len(msg3) > 600 else ""))
    print("-" * 70)
    
    # Add to conversation history
    conversation_history.append({
        "role": "user",
        "content": question3
    })
    conversation_history.append({
        "role": "assistant",
        "content": msg3
    })
    
    memory_info3 = response3.get('memory_info', {})
    print(f"\n💾 Memory Info:")
    print(f"   Enabled: {memory_info3.get('memory_enabled', False)}")
    print(f"   Conversation Length: {len(conversation_history)} messages")
    
    # Check for step-by-step content
    step_indicators = ['step', '1.', '2.', '3.', 'first', 'then', 'next', 'finally']
    found_steps = [ind for ind in step_indicators if ind.lower() in msg3.lower()]
    if found_steps:
        print(f"\n✅ Steps provided!")
        print(f"   Indicators: {', '.join(found_steps[:5])}")
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Session Memory Test Summary")
    print("=" * 70)
    
    all_responses = [response1, response2, response3]
    all_success = all(r.get('status') == 'processed' for r in all_responses if r)
    
    if all_success:
        print("✅ All messages processed successfully")
        print(f"✅ Same session ID used: {session_id}")
        print(f"✅ Conversation history tracked: {len(conversation_history)} messages")
        
        if context_retained:
            print("✅ Context retention: WORKING")
            print("   The agent remembers previous conversation turns")
        else:
            print("⚠️  Context retention: May need improvement")
            print("   Consider enhancing conversation history format")
        
        print("\n🎉 Session memory test completed!")
        print("\n💡 Note: AgentCore Runtime with STM_ONLY memory mode")
        print("   automatically maintains session state. Conversation history")
        print("   is passed explicitly to ensure context is available.")
        return True
    else:
        print("❌ Some messages failed")
        return False

if __name__ == "__main__":
    success = test_session_memory()
    sys.exit(0 if success else 1)

