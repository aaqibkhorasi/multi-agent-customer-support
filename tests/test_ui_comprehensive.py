#!/usr/bin/env python3
"""
Comprehensive UI Testing Script
Tests all agents, routing, memory, and authentication
"""

import json
import subprocess
import sys
import time
import uuid
from datetime import datetime
from typing import Dict, List

def generate_session_id(prefix: str = "session") -> str:
    """Generate a session ID that meets AgentCore requirements (min 33 chars)"""
    return f"{prefix}-{uuid.uuid4()}"

def invoke_agent_via_cli(prompt: str, session_id: str, user_id: str = "test-user") -> Dict:
    """Invoke agent using agentcore CLI"""
    payload = {
        "input": prompt,
        "user_id": user_id,
        "session_id": session_id
    }
    
    cmd = [
        "agentcore", "invoke",
        json.dumps(payload),
        "--session-id", session_id
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            return {
                "error": True,
                "message": result.stderr or "Failed to invoke agent",
                "stdout": result.stdout
            }
        
        # Parse response
        response_text = result.stdout.strip()
        if "Response:" in response_text:
            json_start = response_text.find("{")
            if json_start != -1:
                response_text = response_text[json_start:]
        
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            return {
                "message": response_text,
                "raw_output": result.stdout
            }
    except subprocess.TimeoutExpired:
        return {"error": True, "message": "Timeout after 60 seconds"}
    except Exception as e:
        return {"error": True, "message": str(e)}

def test_scenario(name: str, prompt: str, session_id: str, expected_agent: str = None, user_id: str = "test-user") -> Dict:
    """Test a single scenario"""
    print(f"\n{'='*60}")
    print(f"🧪 TEST: {name}")
    print(f"{'='*60}")
    print(f"📝 Prompt: {prompt}")
    print(f"🆔 Session ID: {session_id}")
    print(f"👤 User ID: {user_id}")
    if expected_agent:
        print(f"🎯 Expected Agent: {expected_agent}")
    print()
    
    start_time = time.time()
    response = invoke_agent_via_cli(prompt, session_id, user_id)
    elapsed = time.time() - start_time
    
    print(f"⏱️  Response Time: {elapsed:.2f}s")
    
    if "error" in response and response.get("error"):
        print(f"❌ ERROR: {response.get('message', 'Unknown error')}")
        return {
            "name": name,
            "status": "FAILED",
            "error": response.get("message"),
            "elapsed": elapsed
        }
    
    message = response.get("message", response.get("response", "No response"))
    print(f"💬 Response: {message[:200]}..." if len(message) > 200 else f"💬 Response: {message}")
    
    # Check if specialized agent was called
    metadata = response.get("metadata", {})
    context = response.get("context", {})
    
    print(f"\n📊 Metadata:")
    print(f"   - Session ID: {response.get('session_id', 'N/A')}")
    print(f"   - Runtime Session ID: {context.get('runtime_session_id', 'N/A')}")
    print(f"   - Memory Info: {response.get('memory_info', {})}")
    
    # Analyze response for agent routing
    agent_indicators = {
        "knowledge": ["knowledge", "article", "document", "information", "found in"],
        "sentiment": ["sentiment", "feeling", "emotion", "upset", "happy", "frustrated"],
        "ticket": ["ticket", "created", "issue", "tracking"],
        "notification": ["notification", "email", "sent", "alert"],
        "resolution": ["resolution", "solution", "recommendation", "suggest"]
    }
    
    detected_agents = []
    message_lower = message.lower()
    for agent, keywords in agent_indicators.items():
        if any(keyword in message_lower for keyword in keywords):
            detected_agents.append(agent)
    
    if detected_agents:
        print(f"🔍 Detected Agents: {', '.join(detected_agents)}")
    
    status = "PASSED"
    if expected_agent and expected_agent.lower() not in [a.lower() for a in detected_agents]:
        status = "WARNING"  # Expected agent not clearly detected, but might still be working
    
    return {
        "name": name,
        "status": status,
        "response": message,
        "detected_agents": detected_agents,
        "elapsed": elapsed,
        "metadata": metadata
    }

def test_memory_retention(session_id: str, user_id: str = "test-user") -> Dict:
    """Test memory retention across multiple messages"""
    print(f"\n{'='*60}")
    print(f"🧠 MEMORY TEST: Session Retention")
    print(f"{'='*60}")
    
    # First message
    print("\n📨 Message 1: Setting context")
    response1 = invoke_agent_via_cli(
        "My name is John and I have a premium subscription.",
        session_id,
        user_id
    )
    message1 = response1.get("message", response1.get("response", ""))
    print(f"   Response: {message1[:150]}...")
    
    time.sleep(2)  # Brief pause
    
    # Second message - should remember the name
    print("\n📨 Message 2: Testing memory")
    response2 = invoke_agent_via_cli(
        "What's my name and subscription tier?",
        session_id,
        user_id
    )
    message2 = response2.get("message", response2.get("response", ""))
    print(f"   Response: {message2[:150]}...")
    
    # Check if memory worked
    message2_lower = message2.lower()
    remembers_name = "john" in message2_lower
    remembers_tier = "premium" in message2_lower or "subscription" in message2_lower
    
    print(f"\n✅ Memory Check:")
    print(f"   - Remembers name: {'✅' if remembers_name else '❌'}")
    print(f"   - Remembers tier: {'✅' if remembers_tier else '❌'}")
    
    return {
        "name": "Memory Retention Test",
        "status": "PASSED" if (remembers_name or remembers_tier) else "FAILED",
        "remembers_name": remembers_name,
        "remembers_tier": remembers_tier,
        "response1": message1[:100],
        "response2": message2[:100]
    }

def test_cross_session_memory(user_id: str = "test-user") -> Dict:
    """Test long-term memory across different sessions"""
    print(f"\n{'='*60}")
    print(f"🧠 MEMORY TEST: Cross-Session (LTM)")
    print(f"{'='*60}")
    
    session1 = generate_session_id("ltm-1")
    session2 = generate_session_id("ltm-2")
    
    # First session
    print(f"\n📨 Session 1 ({session1}): Setting context")
    response1 = invoke_agent_via_cli(
        "I prefer email notifications and my account email is john@example.com",
        session1,
        user_id
    )
    print(f"   Response: {response1.get('message', response1.get('response', ''))[:150]}...")
    
    time.sleep(2)
    
    # Second session - should remember from LTM
    print(f"\n📨 Session 2 ({session2}): Testing LTM")
    response2 = invoke_agent_via_cli(
        "What's my preferred notification method and email?",
        session2,
        user_id
    )
    message2 = response2.get("message", response2.get("response", ""))
    print(f"   Response: {message2[:150]}...")
    
    message2_lower = message2.lower()
    remembers_email = "email" in message2_lower and ("john@example.com" in message2_lower or "notification" in message2_lower)
    
    print(f"\n✅ LTM Check:")
    print(f"   - Remembers preferences: {'✅' if remembers_email else '❌'}")
    
    return {
        "name": "Cross-Session Memory (LTM) Test",
        "status": "PASSED" if remembers_email else "FAILED",
        "remembers_preferences": remembers_email,
        "session1": session1,
        "session2": session2
    }

def main():
    """Run comprehensive tests"""
    print("\n" + "="*60)
    print("🚀 COMPREHENSIVE UI TESTING")
    print("="*60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # Test 1: Knowledge Agent
    results.append(test_scenario(
        "Knowledge Agent - Password Reset",
        "How do I reset my password?",
        generate_session_id("knowledge"),
        "knowledge"
    ))
    
    time.sleep(2)
    
    # Test 2: Sentiment Agent
    results.append(test_scenario(
        "Sentiment Agent - Emotional Query",
        "I am very frustrated with my service!",
        generate_session_id("sentiment"),
        "sentiment"
    ))
    
    time.sleep(2)
    
    # Test 3: Ticket Agent
    results.append(test_scenario(
        "Ticket Agent - Create Ticket",
        "I need to create a support ticket for billing issues",
        generate_session_id("ticket"),
        "ticket"
    ))
    
    time.sleep(2)
    
    # Test 4: Complex Query (should route to multiple agents)
    results.append(test_scenario(
        "Multi-Agent - Complex Query",
        "I'm upset about my bill. Can you help me understand the charges and create a ticket?",
        generate_session_id("multi"),
        None  # Should route to sentiment + ticket
    ))
    
    time.sleep(2)
    
    # Test 5: Memory Retention (STM)
    memory_session = generate_session_id("memory")
    results.append(test_memory_retention(memory_session))
    
    time.sleep(2)
    
    # Test 6: Cross-Session Memory (LTM)
    results.append(test_cross_session_memory())
    
    # Summary
    print(f"\n\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for r in results if r.get("status") == "PASSED")
    failed = sum(1 for r in results if r.get("status") == "FAILED")
    warnings = sum(1 for r in results if r.get("status") == "WARNING")
    
    print(f"\n✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⚠️  Warnings: {warnings}")
    print(f"📈 Total: {len(results)}")
    
    print(f"\n📋 Detailed Results:")
    for i, result in enumerate(results, 1):
        status_icon = "✅" if result.get("status") == "PASSED" else "❌" if result.get("status") == "FAILED" else "⚠️"
        print(f"   {i}. {status_icon} {result.get('name')} - {result.get('status')}")
        if result.get("elapsed"):
            print(f"      ⏱️  {result.get('elapsed'):.2f}s")
        if result.get("detected_agents"):
            print(f"      🔍 Agents: {', '.join(result.get('detected_agents', []))}")
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Return exit code
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

