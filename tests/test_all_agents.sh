#!/bin/bash

echo "🧪 Testing All Agents - Comprehensive Test Suite"
echo "================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Function to run test and check for agent mentions
run_test() {
    local test_name="$1"
    local prompt="$2"
    local session_id="$3"
    local expected_agent="$4"
    
    echo -e "${YELLOW}📋 Test: $test_name${NC}"
    echo "Prompt: $prompt"
    echo "Session: $session_id"
    echo ""
    
    # Run the test
    response=$(agentcore invoke "{\"prompt\": \"$prompt\", \"session_id\": \"$session_id\"}" 2>&1)
    echo "$response" | head -20
    
    # Check if expected agent is mentioned (case insensitive)
    if echo "$response" | grep -qi "$expected_agent"; then
        echo -e "${GREEN}✅ PASS: $test_name - $expected_agent detected${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL: $test_name - $expected_agent not detected${NC}"
        ((FAILED++))
    fi
    
    echo ""
    echo "---"
    echo ""
    sleep 2
}

# Test 1: KnowledgeAgent - Password Reset
run_test "KnowledgeAgent - Password Reset" \
    "How do I reset my password?" \
    "test-kb-001" \
    "KnowledgeAgent"

# Test 2: KnowledgeAgent - Billing Query
run_test "KnowledgeAgent - Billing Query" \
    "help me understand the bill" \
    "test-kb-002" \
    "KnowledgeAgent"

# Test 3: SentimentAgent - Negative Sentiment
run_test "SentimentAgent - Negative Sentiment" \
    "I am extremely frustrated with this service!" \
    "test-sent-001" \
    "SentimentAgent"

# Test 4: TicketAgent - Create Ticket
run_test "TicketAgent - Create Ticket" \
    "I have issues with accessing my client information and getting 505 error, Can you create a ticket for it" \
    "test-ticket-001" \
    "TicketAgent"

# Test 5: EscalationAgent - Security Issue
run_test "EscalationAgent - Security Issue" \
    "I am very upset! I need to speak to a human agent immediately! This is a security issue with my account!" \
    "test-escalation-001" \
    "EscalationAgent"

# Test 6: Memory - Short-Term Memory (STM)
echo -e "${YELLOW}📋 Test: Memory - Short-Term Memory (STM)${NC}"
echo "Step 1: Store information"
agentcore invoke '{"prompt": "My name is Sarah Johnson and I am a data scientist", "session_id": "test-mem-stm-001"}' 2>&1 | head -10
echo ""
sleep 2

echo "Step 2: Recall information (same session)"
response=$(agentcore invoke '{"prompt": "What is my name?", "session_id": "test-mem-stm-001"}' 2>&1)
echo "$response" | head -10

if echo "$response" | grep -qi "Sarah\|Johnson"; then
    echo -e "${GREEN}✅ PASS: Memory STM - Name recalled${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL: Memory STM - Name not recalled${NC}"
    ((FAILED++))
fi
echo ""
echo "---"
echo ""
sleep 2

# Test 7: Multi-Agent Workflow - Complex Request
run_test "Multi-Agent Workflow - Complex Request" \
    "I am very upset! How do I cancel my subscription? Also create a ticket for billing dispute." \
    "test-multi-001" \
    "SentimentAgent\|KnowledgeAgent\|TicketAgent"

# Test 8: ResolutionAgent - Personalized Response
run_test "ResolutionAgent - Personalized Response" \
    "I need help with my account settings" \
    "test-resolution-001" \
    "ResolutionAgent"

# Test 9: TicketAgent - Get Ticket Status
run_test "TicketAgent - Get Ticket Status" \
    "Can you provide me the ticket number from my previous ticket?" \
    "test-ticket-002" \
    "TicketAgent"

# Test 10: KnowledgeAgent - API Limits
run_test "KnowledgeAgent - API Limits" \
    "What are the API rate limits for my account?" \
    "test-kb-003" \
    "KnowledgeAgent"

# Summary
echo ""
echo "================================================"
echo "📊 Test Summary"
echo "================================================"
echo -e "${GREEN}✅ Passed: $PASSED${NC}"
echo -e "${RED}❌ Failed: $FAILED${NC}"
echo "Total: $((PASSED + FAILED))"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}⚠️  Some tests failed. Please review the output above.${NC}"
    exit 1
fi
