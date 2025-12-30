#!/bin/bash
# End-to-end test script for all specialized agents
# Tests supervisor routing to each specialized agent

set -e

SESSION_ID="test-session-$(date +%s)"
echo "🧪 Testing Multi-Agent System End-to-End"
echo "=========================================="
echo "Session ID: $SESSION_ID"
echo ""

# Test 1: Sentiment Agent (should route to SentimentAgent)
echo "📋 Test 1: Sentiment Analysis"
echo "----------------------------"
echo "Prompt: 'I am extremely frustrated with this service! This is terrible!'"
echo ""
RESPONSE1=$(agentcore invoke "{\"prompt\": \"I am extremely frustrated with this service! This is terrible!\", \"session_id\": \"$SESSION_ID\"}" 2>&1)
echo "$RESPONSE1" | jq -r '.response // .content // .' 2>/dev/null || echo "$RESPONSE1"
echo ""
echo "✅ Expected: SentimentAgent should analyze sentiment (NEGATIVE, high urgency)"
echo ""

# Test 2: Knowledge Agent (should route to KnowledgeAgent)
echo "📋 Test 2: Knowledge Base Search"
echo "-------------------------------"
echo "Prompt: 'How do I reset my password?'"
echo ""
RESPONSE2=$(agentcore invoke "{\"prompt\": \"How do I reset my password?\", \"session_id\": \"$SESSION_ID\"}" 2>&1)
echo "$RESPONSE2" | jq -r '.response // .content // .' 2>/dev/null || echo "$RESPONSE2"
echo ""
echo "✅ Expected: KnowledgeAgent should search S3 vectors and provide answer"
echo ""

# Test 3: Ticket Agent (should route to TicketAgent)
echo "📋 Test 3: Ticket Management"
echo "---------------------------"
echo "Prompt: 'I need to create a support ticket for a billing issue'"
echo ""
RESPONSE3=$(agentcore invoke "{\"prompt\": \"I need to create a support ticket for a billing issue\", \"session_id\": \"$SESSION_ID\"}" 2>&1)
echo "$RESPONSE3" | jq -r '.response // .content // .' 2>/dev/null || echo "$RESPONSE3"
echo ""
echo "✅ Expected: TicketAgent should create ticket via Lambda"
echo ""

# Test 4: Resolution Agent (should route to ResolutionAgent)
echo "📋 Test 4: Personalized Resolution"
echo "----------------------------------"
echo "Prompt: 'Can you help me understand my subscription options?'"
echo ""
RESPONSE4=$(agentcore invoke "{\"prompt\": \"Can you help me understand my subscription options?\", \"session_id\": \"$SESSION_ID\"}" 2>&1)
echo "$RESPONSE4" | jq -r '.response // .content // .' 2>/dev/null || echo "$RESPONSE4"
echo ""
echo "✅ Expected: ResolutionAgent should provide personalized response"
echo ""

# Test 5: Escalation Agent (should route to EscalationAgent)
echo "📋 Test 5: Escalation to Human"
echo "------------------------------"
echo "Prompt: 'I need to speak to a human agent immediately! This is urgent!'"
echo ""
RESPONSE5=$(agentcore invoke "{\"prompt\": \"I need to speak to a human agent immediately! This is urgent!\", \"session_id\": \"$SESSION_ID\"}" 2>&1)
echo "$RESPONSE5" | jq -r '.response // .content // .' 2>/dev/null || echo "$RESPONSE5"
echo ""
echo "✅ Expected: EscalationAgent should handle human-in-the-loop escalation"
echo ""

# Test 6: Memory Test (Short-Term Memory)
echo "📋 Test 6: Short-Term Memory (STM)"
echo "----------------------------------"
echo "Step 1: Tell agent your name"
RESPONSE6A=$(agentcore invoke "{\"prompt\": \"My name is John Smith\", \"session_id\": \"$SESSION_ID\"}" 2>&1)
echo "$RESPONSE6A" | jq -r '.response // .content // .' 2>/dev/null || echo "$RESPONSE6A"
echo ""
echo "Step 2: Ask agent to recall your name"
RESPONSE6B=$(agentcore invoke "{\"prompt\": \"What is my name?\", \"session_id\": \"$SESSION_ID\"}" 2>&1)
echo "$RESPONSE6B" | jq -r '.response // .content // .' 2>/dev/null || echo "$RESPONSE6B"
echo ""
echo "✅ Expected: Agent should remember 'John Smith' from same session"
echo ""

# Test 7: Complex Multi-Agent Flow
echo "📋 Test 7: Complex Multi-Agent Flow"
echo "-----------------------------------"
echo "Prompt: 'I'm very upset about my billing. Can you search your knowledge base and create a ticket?'"
echo ""
RESPONSE7=$(agentcore invoke "{\"prompt\": \"I'm very upset about my billing. Can you search your knowledge base and create a ticket?\", \"session_id\": \"$SESSION_ID\"}" 2>&1)
echo "$RESPONSE7" | jq -r '.response // .content // .' 2>/dev/null || echo "$RESPONSE7"
echo ""
echo "✅ Expected: Multiple agents should collaborate (SentimentAgent + KnowledgeAgent + TicketAgent)"
echo ""

echo ""
echo "✅ All tests completed!"
echo "📊 Check CloudWatch logs for detailed agent routing:"
echo "   agentcore logs --follow"

