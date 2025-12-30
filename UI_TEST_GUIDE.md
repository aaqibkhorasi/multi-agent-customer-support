# UI Test Guide - Comprehensive Agent & Memory Testing

## 🚀 Starting the UI

The UI is running at: **http://localhost:8501**

If it's not running, start it with:
```bash
cd /Users/aaqibkhorasi/Documents/Projects/multi-agent-customer-support
streamlit run ui/ui.py
```

---

## 📋 Test Prompts by Agent

### 1. 🟢 KnowledgeAgent Tests

**Purpose**: Search knowledge base for answers

#### Test 1: Password Reset
```
How do I reset my password?
```

**Expected**: Should search knowledge base and return password reset instructions

#### Test 2: Account Management
```
How can I update my email address?
```

**Expected**: Should find relevant knowledge base articles

#### Test 3: Billing Questions
```
What payment methods do you accept?
```

**Expected**: Should search and return payment information

#### Test 4: Technical Support
```
How do I enable two-factor authentication?
```

**Expected**: Should find security/authentication articles

---

### 2. 🟡 SentimentAgent Tests

**Purpose**: Analyze customer sentiment and urgency

#### Test 1: Negative Sentiment (High Urgency)
```
I am extremely frustrated with this service! Nothing works and I want a refund immediately!
```

**Expected**: 
- Sentiment: NEGATIVE
- Urgency: HIGH or CRITICAL
- Should route to EscalationAgent

#### Test 2: Positive Sentiment
```
Thank you so much! Your service is amazing and I love it!
```

**Expected**:
- Sentiment: POSITIVE
- Urgency: LOW
- Should route to ResolutionAgent for acknowledgment

#### Test 3: Mixed Sentiment
```
The product is good but the customer service response time is too slow
```

**Expected**:
- Sentiment: MIXED
- Should identify both positive and negative aspects

#### Test 4: Neutral Query
```
What are your business hours?
```

**Expected**:
- Sentiment: NEUTRAL
- Should route to KnowledgeAgent

---

### 3. 🔵 TicketAgent Tests

**Purpose**: Create, retrieve, update, and list support tickets

#### Test 1: Create High Priority Ticket
```
Create a high priority ticket for billing issue: My payment was charged twice
```

**Expected**:
- Creates ticket in DynamoDB
- Returns ticket ID (e.g., TICKET-XXXXX)
- Status: open
- Priority: high
- Category: billing

#### Test 2: Create Technical Ticket
```
I need help with login issues. Create a ticket for me.
```

**Expected**:
- Creates ticket with category: technical
- Subject: Login Issues
- Status: open

#### Test 3: Get Ticket Status
```
What is the status of ticket TICKET-853CD290?
```

**Expected**:
- Retrieves ticket from DynamoDB
- Returns ticket details (status, priority, subject, etc.)

#### Test 4: Update Ticket
```
Update ticket TICKET-853CD290 to resolved status
```

**Expected**:
- Updates ticket status to "resolved"
- Returns confirmation

#### Test 5: List Tickets
```
Show me all my open tickets
```

**Expected**:
- Lists all tickets (or tickets for current user)
- Shows ticket IDs, subjects, statuses

---

### 4. 🟣 ResolutionAgent Tests

**Purpose**: Generate personalized responses and resolutions

#### Test 1: Simple Resolution
```
I forgot my password
```

**Expected**:
- Routes to KnowledgeAgent first
- Then ResolutionAgent provides personalized response
- Includes steps to reset password

#### Test 2: Account Issue
```
My account is locked
```

**Expected**:
- Creates ticket (TicketAgent)
- Provides resolution steps
- Personalized response

#### Test 3: Feature Request
```
I want to request a new feature
```

**Expected**:
- Creates ticket
- Provides acknowledgment
- Personalized response

---

### 5. 🔴 EscalationAgent Tests

**Purpose**: Handle high-urgency escalations

#### Test 1: High Urgency Escalation
```
This is urgent! I need immediate help with a critical billing issue!
```

**Expected**:
- SentimentAgent detects HIGH urgency
- Routes to EscalationAgent
- EscalationAgent creates high-priority ticket
- Provides escalation acknowledgment

#### Test 2: Frustrated Customer
```
I've been waiting for 3 days and no one has responded! This is unacceptable!
```

**Expected**:
- SentimentAgent detects NEGATIVE + HIGH urgency
- Routes to EscalationAgent
- Creates ticket with high priority
- Provides escalation response

---

## 🧠 Memory Testing

### Short-Term Memory (STM) Tests

**How it works**: STM remembers context within the same session (same session_id)

#### Test 1: Context Continuity
**Session 1** (Use same session ID):
```
Message 1: My name is John and I work in the IT department
```

**Wait for response, then:**
```
Message 2: What did I tell you about myself?
```

**Expected**: Should remember "John" and "IT department"

#### Test 2: Follow-up Questions
**Session 1**:
```
Message 1: I have a billing question
```

**Wait for response, then:**
```
Message 2: Can you help me with that?
```

**Expected**: Should remember the billing question context

#### Test 3: Multi-turn Conversation
**Session 1**:
```
Message 1: Create a ticket for login issues
Message 2: What's the ticket ID?
Message 3: Update that ticket to in-progress
```

**Expected**: Should remember the ticket ID across messages

---

### Long-Term Memory (LTM) Tests

**How it works**: LTM remembers context across different sessions (same user_id)

#### Test 1: Cross-Session Memory
**Session 1** (user_id: "test-user-123"):
```
Message: My favorite color is blue and I prefer email notifications
```

**Wait, then start NEW Session 2** (same user_id: "test-user-123"):
```
Message: What are my preferences?
```

**Expected**: Should remember "blue" and "email notifications" from previous session

#### Test 2: User Profile Memory
**Session 1** (user_id: "john-doe"):
```
Message: I'm a premium customer and I use the mobile app
```

**Session 2** (same user_id: "john-doe", different session_id):
```
Message: What type of customer am I?
```

**Expected**: Should remember "premium customer" and "mobile app"

#### Test 3: Persistent Preferences
**Session 1** (user_id: "user-456"):
```
Message: I always prefer phone support over chat
```

**Session 2** (same user_id: "user-456"):
```
Message: How should I contact support?
```

**Expected**: Should remember preference for phone support

---

## 🔄 Multi-Agent Workflow Tests

### Test 1: Complete Support Flow
```
I'm very frustrated because I can't log in and I've been trying for hours!
```

**Expected Flow**:
1. SentimentAgent → Detects NEGATIVE + HIGH urgency
2. EscalationAgent → Creates high-priority ticket
3. KnowledgeAgent → Searches for login troubleshooting
4. ResolutionAgent → Provides personalized resolution

### Test 2: Knowledge + Ticket Creation
```
I need help with password reset and want to track this issue
```

**Expected Flow**:
1. KnowledgeAgent → Searches password reset info
2. TicketAgent → Creates ticket for tracking
3. ResolutionAgent → Provides complete response

### Test 3: Sentiment Analysis + Escalation
```
This service is terrible! I want to cancel immediately!
```

**Expected Flow**:
1. SentimentAgent → Detects NEGATIVE sentiment
2. EscalationAgent → Handles escalation
3. TicketAgent → Creates cancellation ticket

---

## 📊 Testing Checklist

### Agent Functionality
- [ ] KnowledgeAgent: Searches knowledge base correctly
- [ ] SentimentAgent: Detects sentiment and urgency
- [ ] TicketAgent: Creates tickets in DynamoDB
- [ ] TicketAgent: Retrieves ticket by ID
- [ ] TicketAgent: Updates ticket status
- [ ] TicketAgent: Lists tickets
- [ ] ResolutionAgent: Provides personalized responses
- [ ] EscalationAgent: Handles high-urgency issues

### Memory Functionality
- [ ] STM: Remembers context within same session
- [ ] STM: Follow-up questions work correctly
- [ ] LTM: Remembers across different sessions (same user_id)
- [ ] LTM: User preferences persist

### Multi-Agent Coordination
- [ ] Supervisor routes to correct agents
- [ ] Agents coordinate workflows
- [ ] Responses are compiled correctly

### UI Functionality
- [ ] Authentication works
- [ ] Session ID management works
- [ ] User ID is passed for LTM
- [ ] Response display is correct
- [ ] Agent routing info is visible

---

## 🎯 Quick Test Sequence

Run these in order to test everything quickly:

1. **Knowledge Test**:
   ```
   How do I reset my password?
   ```

2. **Sentiment Test**:
   ```
   I am extremely frustrated with this service!
   ```

3. **Ticket Creation**:
   ```
   Create a high priority ticket for billing issue: duplicate charge
   ```

4. **STM Test** (same session):
   ```
   What ticket did I just create?
   ```

5. **Ticket Retrieval**:
   ```
   What is the status of ticket TICKET-853CD290?
   ```

6. **Multi-Agent Flow**:
   ```
   I need help with login and want to track this as a ticket
   ```

---

## 🔍 Verification Steps

### After Each Test:

1. **Check Response**: Does it make sense?
2. **Check Agent Routing**: Expand "Response Details" to see which agents were used
3. **Check Tools**: Verify MCP tools were called (Lambda invocations)
4. **Check DynamoDB** (for tickets):
   ```bash
   aws dynamodb scan --table-name dev-customer-support-tickets --region us-east-1 --limit 5
   ```
5. **Check CloudWatch Logs** (for Lambda invocations):
   ```bash
   aws logs tail /aws/lambda/dev-customer-support-ticket-management --follow
   ```

---

## 🐛 Troubleshooting

### UI Not Loading
- Check if Streamlit is installed: `pip install streamlit`
- Check if port 8501 is available
- Check console for errors

### Agents Not Responding
- Verify AgentCore Runtime is deployed: `agentcore list-runtimes`
- Check CloudWatch logs for agent errors
- Verify agents are starting in background threads

### Memory Not Working
- Ensure session_id is set (UUID format, 33+ chars)
- For LTM: Ensure user_id is set (from Cognito authentication)
- Check AgentCore Memory is configured

### Tickets Not Creating
- Check DynamoDB table exists
- Verify Lambda function is deployed
- Check Lambda logs for errors
- Verify Gateway targets are configured

---

## 📝 Notes

- **Session ID**: Use UUID format (auto-generated by UI)
- **User ID**: Comes from Cognito authentication (for LTM)
- **Response Time**: First request may take 30-60 seconds (cold start)
- **Timeout**: UI timeout is set to 120 seconds

---

## 🎉 Success Criteria

✅ All agents respond correctly  
✅ Tickets are created in DynamoDB  
✅ STM remembers context within session  
✅ LTM remembers across sessions (with same user_id)  
✅ Multi-agent workflows coordinate properly  
✅ UI displays responses correctly  

Happy Testing! 🚀

