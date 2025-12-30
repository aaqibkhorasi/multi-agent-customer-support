# 🚀 Quick Test Prompts - Copy & Paste Ready

## UI is Running at: http://localhost:8501

---

## 📋 Test Prompts (Copy & Paste)

### 🟢 KnowledgeAgent Tests

```
How do I reset my password?
```

```
How can I update my email address?
```

```
What payment methods do you accept?
```

```
How do I enable two-factor authentication?
```

---

### 🟡 SentimentAgent Tests

```
I am extremely frustrated with this service! Nothing works and I want a refund immediately!
```

```
Thank you so much! Your service is amazing and I love it!
```

```
The product is good but the customer service response time is too slow
```

```
What are your business hours?
```

---

### 🔵 TicketAgent Tests

```
Create a high priority ticket for billing issue: My payment was charged twice
```

```
I need help with login issues. Create a ticket for me.
```

```
What is the status of ticket TICKET-853CD290?
```

```
Update ticket TICKET-853CD290 to resolved status
```

```
Show me all my open tickets
```

---

### 🟣 ResolutionAgent Tests

```
I forgot my password
```

```
My account is locked
```

```
I want to request a new feature
```

---

### 🔴 EscalationAgent Tests

```
This is urgent! I need immediate help with a critical billing issue!
```

```
I've been waiting for 3 days and no one has responded! This is unacceptable!
```

---

## 🧠 Memory Tests

### STM (Short-Term Memory) - Same Session

**Step 1:**
```
My name is John and I work in the IT department
```

**Step 2 (wait for response, then):**
```
What did I tell you about myself?
```

**Step 3:**
```
I have a billing question
```

**Step 4 (wait for response, then):**
```
Can you help me with that?
```

---

### LTM (Long-Term Memory) - Cross Session

**Session 1** (Note the user_id from authentication):
```
My favorite color is blue and I prefer email notifications
```

**Start NEW Session 2** (same user_id, different session_id):
```
What are my preferences?
```

---

## 🔄 Multi-Agent Workflow Tests

```
I'm very frustrated because I can't log in and I've been trying for hours!
```

```
I need help with password reset and want to track this issue
```

```
This service is terrible! I want to cancel immediately!
```

---

## ⚡ Quick 5-Minute Test Sequence

Run these in order:

1. **Knowledge**:
   ```
   How do I reset my password?
   ```

2. **Sentiment**:
   ```
   I am extremely frustrated with this service!
   ```

3. **Ticket Creation**:
   ```
   Create a high priority ticket for billing issue: duplicate charge
   ```

4. **STM Memory** (same session):
   ```
   What ticket did I just create?
   ```

5. **Multi-Agent**:
   ```
   I need help with login and want to track this as a ticket
   ```

---

## ✅ Verification Commands

### Check Tickets in DynamoDB:
```bash
aws dynamodb scan --table-name dev-customer-support-tickets --region us-east-1 --limit 5
```

### Check Lambda Logs:
```bash
aws logs tail /aws/lambda/dev-customer-support-ticket-management --follow
```

### Check Agent Logs:
```bash
aws logs tail /aws/bedrock-agentcore/runtimes/customer_support_supervisor-GIa7fv2B6G-DEFAULT --follow
```

---

## 🎯 Expected Results

- ✅ **KnowledgeAgent**: Returns relevant answers from knowledge base
- ✅ **SentimentAgent**: Detects sentiment (POSITIVE/NEGATIVE/NEUTRAL/MIXED) and urgency
- ✅ **TicketAgent**: Creates tickets in DynamoDB, returns ticket IDs
- ✅ **ResolutionAgent**: Provides personalized, helpful responses
- ✅ **EscalationAgent**: Handles high-urgency issues with escalation
- ✅ **STM**: Remembers context within same session
- ✅ **LTM**: Remembers preferences across sessions (same user_id)

---

**Happy Testing! 🚀**

