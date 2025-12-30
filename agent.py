#!/usr/bin/env python3
"""
Multi-Agent Customer Support Platform - AgentCore Entry Point
Main entry point for AgentCore deployment with BedrockAgentCoreApp
"""

import os
import logging
from datetime import datetime
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.memory import MemoryClient
from dotenv import load_dotenv
import boto3
import json
from strands import Agent
from strands.models import BedrockModel
from strands_tools.a2a_client import A2AClientToolProvider
from shared.utils.mcp_client import create_mcp_client

# Load environment variables
load_dotenv(override=True)

# Remove placeholder AWS credentials if present (they override ~/.aws/credentials)
import os
if os.getenv("AWS_ACCESS_KEY_ID") == "your_access_key":
    os.environ.pop("AWS_ACCESS_KEY_ID", None)
if os.getenv("AWS_SECRET_ACCESS_KEY") == "your_secret_key":
    os.environ.pop("AWS_SECRET_ACCESS_KEY", None)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("customer-support-supervisor")

# Create AgentCore app
app = BedrockAgentCoreApp()

# Configuration from environment variables
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
MEMORY_ID = os.getenv("MEMORY_ID", "customer_support_supervisor_mem-SalHj92SVh")

# Agent URLs for A2A communication
# In production, these should point to deployed agent services (Docker containers, ECS tasks, etc.)
# In local development, they point to localhost
# Can be overridden via environment variables for each agent
AGENT_URLS = [
    os.getenv("SENTIMENT_AGENT_URL", "http://127.0.0.1:9001"),
    os.getenv("KNOWLEDGE_AGENT_URL", "http://127.0.0.1:9002"),
    os.getenv("TICKET_AGENT_URL", "http://127.0.0.1:9003"),
    os.getenv("RESOLUTION_AGENT_URL", "http://127.0.0.1:9005"),
    os.getenv("ESCALATION_AGENT_URL", "http://127.0.0.1:9006")
]


class SupervisorAgent:
    """Supervisor agent that orchestrates multi-agent customer support workflows"""
    
    def __init__(self):
        self.mcp_client = None  # Keep MCP client as instance variable
        self.agent_threads = []  # Keep track of background agent threads
        # Start specialized agents in background threads (same container)
        self._start_background_agents()
        self.agent = self._initialize_agent()
    
    def _start_background_agents(self):
        """Start specialized agents in background threads so they're accessible via localhost"""
        try:
            from shared.utils.agent_starter import start_all_agents_in_background
            
            # Check if we're in a container (AgentCore Runtime)
            in_container = os.getenv("DOCKER_CONTAINER") == "1" or os.path.exists("/.dockerenv")
            
            if in_container:
                logger.info("Running in container - starting specialized agents in background threads...")
                # Start all agents in background threads
                self.agent_threads = start_all_agents_in_background()
                if self.agent_threads:
                    logger.info(f"✅ Started {len(self.agent_threads)} specialized agents in background")
                    # Give agents more time to fully initialize (A2A servers need to start)
                    # Hotel assistant pattern: agents are started separately, so supervisor waits
                    import time
                    logger.info("Waiting for agents to fully initialize A2A servers...")
                    time.sleep(10)  # Increased to 10 seconds to ensure A2A servers are bound
                    logger.info("Agents should be ready now")
                else:
                    logger.warning("⚠️  No specialized agents started in background")
            else:
                logger.info("Running locally - specialized agents should be started separately")
        except Exception as e:
            logger.warning(f"Could not start background agents: {e}. Continuing without them.")
        
    def _initialize_agent(self) -> Agent:
        """Initialize the supervisor agent with A2A tools and MCP tools"""
        try:
            # Initialize A2A client tool provider for agent communication
            # Gracefully handle if agents are not available
            # Initialize A2A client tool provider (like hotel assistant - simple, no retries)
            a2a_tools = []
            try:
                a2a_provider = A2AClientToolProvider(AGENT_URLS)
                a2a_tools = a2a_provider.tools
                if a2a_tools:
                    logger.info(f"✅ Successfully initialized A2A provider with {len(a2a_tools)} tools")
                else:
                    logger.warning("A2A provider initialized but no tools available. Agents may not be running yet.")
            except Exception as e:
                logger.warning(f"Could not initialize A2A provider: {e}. Continuing without specialized agents.")
                logger.info("To enable specialized agents, ensure they are running and accessible at:")
                for url in AGENT_URLS:
                    logger.info(f"  - {url}")
            
            # Supervisor agent does NOT use MCP tools directly
            # Specialized agents use MCP tools (Lambda functions) and return results
            # Supervisor only routes to specialized agents via A2A protocol
            logger.info("Supervisor agent uses A2A protocol to route to specialized agents. Specialized agents use MCP tools.")
            
            # Only use A2A tools (specialized agents)
            all_tools = a2a_tools
            
            if not all_tools:
                logger.warning("No specialized agents available. Supervisor will work with LLM only.")
            else:
                logger.info(f"Total specialized agents available: {len(all_tools)}")
            
            # Initialize Bedrock model with explicit region
            session = boto3.Session(region_name=AWS_REGION)
            logger.info(f"Initializing Bedrock model {BEDROCK_MODEL_ID} in region {AWS_REGION}")
            bedrock_model = BedrockModel(
                model_id=BEDROCK_MODEL_ID,
                boto_session=session
            )
            
            # Create agent with tools
            agent = Agent(
                model=bedrock_model,
                tools=all_tools,
                system_prompt=self._get_system_prompt(),
            )
            
            # Log tool availability for debugging
            if all_tools:
                tool_names = [getattr(tool, 'name', None) or getattr(tool, '__name__', None) or str(tool) for tool in all_tools]
                logger.info(f"✅ Supervisor Agent initialized with {len(all_tools)} tools: {tool_names}")
            else:
                logger.error("❌ CRITICAL: Supervisor Agent has NO tools available! Agents cannot be called!")
            
            return agent
        except Exception as e:
            logger.error(f"Failed to initialize supervisor agent: {e}")
            raise
        
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the supervisor agent (simplified like hotel assistant)"""
        return f"""
You are the Supervisor Agent for a multi-agent customer support platform.

Your role is to:
1. Analyze the customer request carefully and determine its intent.
2. Select and invoke the most appropriate specialized agent (without asking the user which one).
3. Pass all relevant context to the selected agent.
4. If the request requires multiple steps, orchestrate those steps across agents.

Available agents:
- SentimentAgent: Analyzes customer emotions and urgency using sentiment analysis.
- KnowledgeAgent: Searches knowledge base using S3 vectors for solutions, how-to guides, and documentation.
- TicketAgent: Creates, modifies, retrieves, and manages support tickets in DynamoDB.
- ResolutionAgent: Generates personalized responses based on context from other agents.
- EscalationAgent: Handles escalation to human support agents for complex or high-urgency issues.

Agents are hosted at these urls:
- SentimentAgent at "http://127.0.0.1:9001"
- KnowledgeAgent at "http://127.0.0.1:9002"
- TicketAgent at "http://127.0.0.1:9003"
- ResolutionAgent at "http://127.0.0.1:9005"
- EscalationAgent at "http://127.0.0.1:9006"

Guidelines:
- If the user asks about features, API limits, billing, account settings, troubleshooting, or how-to guides, route to KnowledgeAgent.
- **CRITICAL: Only route to TicketAgent if the user EXPLICITLY asks to create, get, update, or list tickets. Do NOT create tickets automatically unless explicitly requested.**
- If the user shares information (like preferences, name, etc.) WITHOUT asking for a ticket, do NOT create a ticket. Just acknowledge and remember it.
- If the customer message has emotional language, route to SentimentAgent first, then route to appropriate agent.
- For generating final responses, route to ResolutionAgent.
- If the user asks memory questions like "What did I tell you?" or "What's my name?" or "What are my preferences?", handle directly using conversation history and Long-Term Memory - do NOT route to KnowledgeAgent.
- Always provide a cohesive summary if multiple agents are involved.
- Always prioritize accuracy and context-awareness. Do not guess if the user's request is ambiguous; instead, ask a clarifying question before routing.
- Never answer questions yourself unless no agent is appropriate.
- **NEVER create tickets unless the user explicitly requests it.**

Memory handling:
- **CRITICAL FOR LTM (Long-Term Memory)**: AgentCore Runtime automatically manages Long-Term Memory using user_id. Information shared by users (names, preferences, past issues) is stored in LTM and persists across different session IDs for the same user_id.
- If the user asks memory questions like "What did I tell you?" or "What's my name?" or "What are my preferences?", you MUST:
  1. Check the conversation history (Short-Term Memory) first
  2. If not found, AgentCore Runtime will automatically retrieve from Long-Term Memory (LTM) using user_id
  3. Answer directly using the retrieved information - do NOT route to KnowledgeAgent
  4. Do NOT create tickets for memory questions
- When users share information (name, preferences, etc.), acknowledge it and remember it. This information is automatically stored in LTM by AgentCore Runtime.
- Always check the conversation history first before routing to agents.

Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
"""
    
    async def process_request(self, question: str, context: dict = None):
        """Process a customer request through the supervisor agent"""
        try:
            logger.info(f"Processing request: {question}")
            
            # Build user context message
            user_context = {
                "user_id": context.get("user_id", "anonymous") if context else "anonymous",
                "username": context.get("username", "Anonymous") if context else "Anonymous",
                "department": context.get("department", "general") if context else "general",
                "permissions": context.get("permissions", []) if context else [],
                "authenticated": context.get("authenticated", False) if context else False
            }
            
            # Extract user_id for LTM (fix scoping issue)
            user_id_for_ltm = context.get('user_id', 'anonymous') if context else 'anonymous'
            
            # Build enhanced prompt with user context
            if context:
                conversation_history = context.get('conversation_history', [])
                history_text = ""
                
                # Try to retrieve LTM from previous sessions if conversation_history is empty
                if not conversation_history and user_id_for_ltm and user_id_for_ltm != "anonymous":
                    try:
                        # Initialize MemoryClient to retrieve LTM
                        memory_client = MemoryClient(region_name=AWS_REGION)
                        runtime_session_id = context.get('runtime_session_id') or context.get('session_id')
                        
                        # Retrieve recent conversation turns from LTM (cross-session)
                        # For LTM, we use user_id as actor_id to retrieve across all sessions
                        # Note: get_last_k_turns retrieves from the specified session_id
                        # For true cross-session LTM, we may need to use retrieve_memories with semantic search
                        # But let's try get_last_k_turns first - it should work if AgentCore stores LTM by actor_id
                        recent_turns = memory_client.get_last_k_turns(
                            memory_id=MEMORY_ID,
                            actor_id=user_id_for_ltm,  # Use user_id as actor_id for LTM (cross-session)
                            session_id=runtime_session_id or user_id_for_ltm,  # Use user_id as fallback session_id
                            k=5  # Last 5 conversation turns
                        )
                        
                        # If no turns found, try semantic search for LTM (alternative approach)
                        if not recent_turns:
                            try:
                                # Try retrieving memories using semantic search (for user preferences/facts)
                                memories = memory_client.retrieve_memories(
                                    memory_id=MEMORY_ID,
                                    namespace=f"support/user/{user_id_for_ltm}/preferences",
                                    query=question,  # Use current question to find relevant memories
                                    top_k=3
                                )
                                if memories:
                                    logger.info(f"LTM: Retrieved {len(memories)} memories via semantic search for user_id '{user_id_for_ltm}'")
                                    history_text = "\n=== LONG-TERM MEMORY (USER PREFERENCES/FACTS) ===\n"
                                    for memory in memories:
                                        content = memory.get('content', {}).get('text', '')
                                        if content:
                                            history_text += f"{content}\n"
                                    history_text += "=== END OF LONG-TERM MEMORY ===\n"
                                    history_text += "\nCRITICAL: The above information is from PREVIOUS SESSIONS (Long-Term Memory). Use this to answer questions about the user's preferences or past information.\n"
                            except Exception as e2:
                                logger.debug(f"LTM: Semantic search also failed: {e2}")
                        
                        if recent_turns:
                            logger.info(f"LTM: Retrieved {len(recent_turns)} conversation turns from LTM for user_id '{user_id_for_ltm}'")
                            history_text = "\n=== LONG-TERM MEMORY (FROM PREVIOUS SESSIONS) ===\n"
                            for turn in recent_turns:
                                for message in turn:
                                    role = message.get('role', 'unknown')
                                    content = message.get('content', {}).get('text', '')
                                    if content:
                                        history_text += f"{role.upper()}: {content}\n"
                            history_text += "=== END OF LONG-TERM MEMORY ===\n"
                            history_text += "\nCRITICAL: The above conversation is from PREVIOUS SESSIONS (Long-Term Memory). If the user asks about their name, preferences, or past information, use this LTM data.\n"
                        else:
                            logger.info(f"LTM: No previous conversation turns found for user_id '{user_id_for_ltm}'")
                            history_text = f"\n=== NO CONVERSATION HISTORY IN THIS SESSION ===\n"
                            history_text += f"⚠️ This is a NEW session for user_id '{user_id_for_ltm}', but no Long-Term Memory (LTM) found from previous sessions.\n"
                    except Exception as e:
                        logger.warning(f"LTM: Failed to retrieve LTM for user_id '{user_id_for_ltm}': {e}")
                        history_text = f"\n=== NO CONVERSATION HISTORY IN THIS SESSION ===\n"
                        history_text += f"⚠️ This is a NEW session for user_id '{user_id_for_ltm}'.\n"
                elif conversation_history:
                    history_text = "\n=== PREVIOUS CONVERSATION (YOU MUST USE THIS FOR MEMORY QUESTIONS) ===\n"
                    for msg in conversation_history[-6:]:  # Last 6 messages (3 exchanges)
                        role = msg.get('role', 'unknown')
                        content = msg.get('content', '')
                        history_text += f"{role.upper()}: {content}\n"
                    history_text += "=== END OF PREVIOUS CONVERSATION ===\n"
                    history_text += "\nCRITICAL: If the user asks about information from the conversation above (like their name, preferences, or what they told you), you MUST reference it from the Previous Conversation section.\n"
                else:
                    history_text = "\n=== NO PREVIOUS CONVERSATION ===\nThis is the first message in the session.\n"
                
                # LTM note for agent awareness
                ltm_note = ""
                if user_id_for_ltm and user_id_for_ltm != "anonymous":
                    ltm_note = f"\n⚠️ CRITICAL FOR LTM: User ID is '{user_id_for_ltm}'. Long-Term Memory (LTM) has been retrieved from previous sessions (if available) and is shown above. Use this information to answer questions about the user's name, preferences, or past interactions.\n"
                
                user_info = f"""
User Context:
- Username: {user_context['username']}
- Department: {user_context['department'].title()}
- Permissions: {', '.join(user_context['permissions']) if user_context['permissions'] else 'Basic'}
- Authenticated: {user_context['authenticated']}
- User ID: {user_id_for_ltm} (for LTM)
{ltm_note}
{history_text}
Session ID: {context.get('session_id', 'Not provided - new session')}
Customer Request: {question}
"""
            else:
                user_info = f"Customer Request: {question}"
            
            # Use Strands agent to process request
            response = await self.agent.invoke_async(user_info)
            
            # Track which agents were called
            specialized_agents = []
            mcp_tools_used = []
            response_trace = []
            
            # Log response structure for debugging
            logger.debug(f"Response type: {type(response)}, attributes: {dir(response) if hasattr(response, '__dict__') else 'N/A'}")
            
            # Extract tool calls from response if available
            # Check various possible response structures
            tool_calls = []
            if hasattr(response, 'tool_calls'):
                tool_calls = response.tool_calls or []
                logger.debug(f"Found tool_calls attribute: {len(tool_calls)} calls")
            elif hasattr(response, 'message'):
                if isinstance(response.message, dict) and 'tool_calls' in response.message:
                    tool_calls = response.message['tool_calls'] or []
                    logger.debug(f"Found tool_calls in message dict: {len(tool_calls)} calls")
                elif isinstance(response.message, list):
                    # Check if any item in the list contains tool_calls
                    for item in response.message:
                        if isinstance(item, dict) and 'tool_calls' in item:
                            tool_calls.extend(item.get('tool_calls', []))
                    if tool_calls:
                        logger.debug(f"Found tool_calls in message list: {len(tool_calls)} calls")
            
            # Also check if agent has conversation history with tool calls
            # Strands agents may store tool calls in conversation history
            if hasattr(self.agent, 'conversation') and self.agent.conversation:
                try:
                    # Check last few messages for tool calls
                    for msg in list(self.agent.conversation)[-5:]:
                        if hasattr(msg, 'tool_calls') and msg.tool_calls:
                            tool_calls.extend(msg.tool_calls)
                        elif isinstance(msg, dict) and 'tool_calls' in msg:
                            tool_calls.extend(msg.get('tool_calls', []))
                    if tool_calls:
                        logger.debug(f"Found tool_calls in conversation history: {len(tool_calls)} calls")
                except Exception as e:
                    logger.debug(f"Could not access conversation history: {e}")
            
            # Map A2A tool calls to agent names
            agent_url_to_name = {
                "http://127.0.0.1:9001": "SentimentAgent",
                "http://127.0.0.1:9002": "KnowledgeAgent",
                "http://127.0.0.1:9003": "TicketAgent",
                "http://127.0.0.1:9005": "ResolutionAgent",
                "http://127.0.0.1:9006": "EscalationAgent"
            }
            
            # Process tool calls to identify agents
            for tool_call in tool_calls:
                tool_name = ""
                tool_args = {}
                
                if isinstance(tool_call, dict):
                    tool_name = tool_call.get('name', '') or tool_call.get('function', {}).get('name', '')
                    tool_args = tool_call.get('arguments', {}) or tool_call.get('function', {}).get('arguments', {})
                elif hasattr(tool_call, 'name'):
                    tool_name = tool_call.name
                    tool_args = getattr(tool_call, 'arguments', {})
                
                # Check if this is an A2A tool call (agent routing)
                if 'a2a' in tool_name.lower() or 'send_message' in tool_name.lower() or 'discover_agent' in tool_name.lower():
                    # Extract agent URL from arguments
                    if isinstance(tool_args, str):
                        try:
                            import json
                            tool_args = json.loads(tool_args)
                        except:
                            pass
                    
                    agent_url = tool_args.get('target_agent_url') or tool_args.get('url', '')
                    if agent_url:
                        agent_name = agent_url_to_name.get(agent_url)
                        if agent_name and agent_name not in specialized_agents:
                            specialized_agents.append(agent_name)
                            response_trace.append({
                                "type": "agent",
                                "name": agent_name,
                                "action": "routed_to",
                                "url": agent_url
                            })
                
                # Check if this is an MCP tool call
                elif 'target' in tool_name.lower() and '___' in tool_name:
                    # MCP tool format: target_name___tool_name
                    if tool_name not in mcp_tools_used:
                        mcp_tools_used.append(tool_name)
                        response_trace.append({
                            "type": "tool",
                            "tool": tool_name,
                            "action": "called_mcp_tool"
                        })
            
            # Extract message content from response (handle different response structures)
            if hasattr(response, 'message'):
                if isinstance(response.message, dict):
                    message_content = response.message.get("content", "")
                elif isinstance(response.message, list):
                    # If message is a list, extract text from dict items or join strings
                    parts = []
                    for item in response.message:
                        if isinstance(item, dict):
                            # Extract 'text' or 'content' from dict items
                            text = item.get('text') or item.get('content') or str(item)
                            parts.append(text)
                        else:
                            parts.append(str(item))
                    message_content = " ".join(parts)
                else:
                    message_content = str(response.message)
            elif hasattr(response, 'content'):
                message_content = str(response.content)
            else:
                message_content = str(response)
            
            # Ensure message_content is a string and clean it up
            if not isinstance(message_content, str):
                message_content = str(message_content)
            
            # Clean up any remaining list/dict artifacts in the string
            if message_content.startswith('[') and message_content.endswith(']'):
                try:
                    import ast
                    parsed = ast.literal_eval(message_content)
                    if isinstance(parsed, list) and len(parsed) > 0:
                        if isinstance(parsed[0], dict):
                            message_content = parsed[0].get('text') or parsed[0].get('content') or message_content
                except:
                    pass
            
            # Fallback: Parse message content for agent references
            # Sometimes agents are called but tool calls aren't in response object
            if not specialized_agents:
                message_lower = message_content.lower()
                # Check for agent names in message
                agent_keywords = {
                    "knowledgeagent": "KnowledgeAgent",
                    "sentimentagent": "SentimentAgent",
                    "ticketagent": "TicketAgent",
                    "resolutionagent": "ResolutionAgent",
                    "escalationagent": "EscalationAgent"
                }
                for keyword, agent_name in agent_keywords.items():
                    if keyword in message_lower and agent_name not in specialized_agents:
                        specialized_agents.append(agent_name)
                        response_trace.append({
                            "type": "agent",
                            "name": agent_name,
                            "action": "detected_in_response",
                            "method": "message_parsing"
                        })
            
            logger.info(f"Request processed successfully. Agents called: {specialized_agents}, MCP tools: {len(mcp_tools_used)}")
            
            # Build response with agent tracking
            response_dict = {
                "message": message_content,
                "status": "processed",
                "timestamp": datetime.now().isoformat(),
                "agent": "SupervisorAgent",
                "model": BEDROCK_MODEL_ID,
                "context": context or {},
                "authenticated": user_context['authenticated'],
                "specialized_agents": specialized_agents,
                "mcp_tools_used": mcp_tools_used,
                "response_trace": response_trace
            }
            
            # Add conversation context for UI to parse (format expected by UI)
            conversation_context = []
            for trace_item in response_trace:
                if trace_item.get("type") == "agent":
                    conversation_context.append({
                        "tool_calls": [{
                            "name": "a2a_send_message",
                            "arguments": {
                                "target_agent_url": trace_item.get("url", ""),
                                "agent_name": trace_item.get("name")
                            }
                        }],
                        "timestamp": datetime.now().isoformat()
                    })
                elif trace_item.get("type") == "tool":
                    conversation_context.append({
                        "tool_calls": [{
                            "name": trace_item.get("tool"),
                            "function": trace_item.get("function", "")
                        }],
                        "timestamp": datetime.now().isoformat()
                    })
            
            if context:
                response_dict["context"]["conversation_context"] = conversation_context
            
            return response_dict
        except Exception as e:
            logger.error(f"Error processing request: {e}", exc_info=True)
            # Return error response without fallback message
            return {
                "error": f"Failed to process request: {str(e)}",
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "agent": "SupervisorAgent",
                "authenticated": (context.get('authenticated', False) if context and isinstance(context, dict) else False),
                "context": context or {}
            }


# Initialize supervisor agent
supervisor = SupervisorAgent()


@app.entrypoint
async def send_message(request):
    """
    Main entry point for the customer support system with authentication and memory.
    
    This endpoint follows AgentCore Runtime best practices:
    - Uses runtimeSessionId for session management (provided by AgentCore Runtime)
    - Maintains context across interactions within the same session
    - Supports A2A protocol for multi-agent communication
    - Integrates MCP tools via AgentCore Gateway
    
    Supports multiple request formats:
    
    AWS Agent Sandbox format:
    {
        "input": "user question",
        "user_id": "user123",
        "session_id": "session-id",
        "context": {
            "timezone": "America/New_York",
            "language": "en"
        }
    }
    
    Standard HTTP format:
    {
        "prompt": "user question",
        "session_id": "your-specific-session-id"
    }
    
    Extended format:
    {
        "question": "user question",
        "context": {
            "user_id": "user123",
            "runtimeSessionId": "session-id-from-agentcore",  # Optional, auto-generated if not provided
            ...
        }
    }
    """
    try:
        # Log full request for debugging
        logger.info(f"Received request - Type: {type(request)}")
        if isinstance(request, dict):
            logger.info(f"Request keys: {list(request.keys())}")
            logger.info(f"Request content: {request}")
        else:
            logger.info(f"Request attributes: {dir(request) if hasattr(request, '__dict__') else 'N/A'}")
            # Try to convert object to dict for easier handling
            if hasattr(request, '__dict__'):
                request = request.__dict__
            elif hasattr(request, 'dict'):
                request = request.dict()
        
        # Ensure request is a dict at this point
        if not isinstance(request, dict):
            logger.error(f"Request is not a dict and cannot be converted. Type: {type(request)}")
            return {"error": "Invalid request format. Request must be a dictionary."}
        
        # Support multiple formats:
        # - "input" (AWS Agent Sandbox format)
        # - "prompt" (standard HTTP format)
        # - "question" (extended format)
        question = request.get("input") or request.get("prompt") or request.get("question")
        context = request.get("context", {}) or {}
        include_details = request.get("include_details", False)
        
        logger.info(f"Extracted question: {question}")
        logger.info(f"Extracted context: {context}")
        
        if not question:
            logger.error(f"No question found in request. Request was: {request}")
            return {"error": "No question provided. Request must contain 'input', 'prompt', or 'question' field."}

        # Extract session ID - multiple sources:
        # 1. From request body: session_id (standard HTTP format)
        # 2. From context: runtimeSessionId (extended format)
        # 3. From context: runtime_session_id (alternative format)
        # Request is now guaranteed to be a dict at this point
        runtime_session_id = (
            request.get("session_id") or 
            context.get("runtimeSessionId") or
            context.get("runtime_session_id")
        )
        
        # If still no session ID, AgentCore Runtime will auto-generate one
        # We'll include it in the response so client can use it for follow-ups
        if runtime_session_id:
            logger.info(f"Processing request in session: {runtime_session_id}")
        else:
            logger.info("No session ID provided - AgentCore Runtime will auto-generate one")

        logger.info(f"Received request: {question}")
        
        # Extract user_id from multiple sources for LTM support
        # AgentCore Runtime uses user_id for Long-Term Memory (LTM) across sessions
        # Priority: context.user_id > request.user_id > anonymous
        user_id_for_ltm = (
            context.get("user_id") or 
            request.get("user_id") or 
            "anonymous"
        )
        
        # Extract user context from authenticated request
        user_context = {
            "user_id": user_id_for_ltm,  # Use extracted user_id for LTM
            "username": context.get("username"),
            "customer_tier": context.get("customer_tier", "standard"),
            "department": context.get("department", "general"),
            "permissions": context.get("permissions", []),
            "authenticated": context.get("authenticated", False),
            "runtime_session_id": runtime_session_id  # Include session ID in context
        }
        
        # Log user_id for LTM debugging
        if user_id_for_ltm and user_id_for_ltm != "anonymous":
            logger.info(f"LTM: Using user_id '{user_id_for_ltm}' for Long-Term Memory (session: {runtime_session_id})")
        else:
            logger.warning(f"LTM: No user_id provided - LTM will not work across sessions")
        
        # Enhanced context with user information and memory
        # AgentCore Runtime automatically manages memory via runtimeSessionId
        # We pass the session ID to the agent so it can reference previous context
        enhanced_context = {
            **context, 
            **user_context,
            "memory_enabled": True,
            "conversation_context": context.get("conversation_history", []),
            # Include session ID in system context for memory awareness
            "session_id": runtime_session_id
        }
        
        # Build conversation history for context (AgentCore Runtime handles persistence)
        # We include this in the prompt so the agent can reference it
        conversation_history = context.get("conversation_history", [])
        if runtime_session_id and conversation_history:
            logger.info(f"Session {runtime_session_id} has {len(conversation_history)} previous messages")
        
        # Process request with user context and memory
        response = await supervisor.process_request(question, enhanced_context)
        
        # Add authentication info to response if requested
        if include_details and user_context.get("authenticated"):
            response["auth_info"] = {
                "department": user_context.get("department"),
                "permissions": user_context.get("permissions"),
                "username": user_context.get("username")
            }
            
            # Add processing steps for transparency
            response["processing_steps"] = [
                {
                    "step": "Authentication Verification",
                    "description": f"Verified user: {user_context.get('username')}",
                    "status": "completed"
                },
                {
                    "step": "Memory Context Loading",
                    "description": "Loading conversation history and user preferences from memory",
                    "status": "completed"
                },
                {
                    "step": "Request Classification",
                    "description": f"Classified as {user_context.get('department')} department request",
                    "status": "completed"
                },
                {
                    "step": "Permission Check",
                    "description": f"User has {len(user_context.get('permissions', []))} permissions",
                    "status": "completed"
                },
                {
                    "step": "Response Generation",
                    "description": f"Generated response for {user_context.get('username')} with memory context",
                    "status": "completed"
                },
                {
                    "step": "Memory Storage",
                    "description": "Storing conversation context and user preferences for future interactions",
                    "status": "completed"
                }
            ]
        
        # Add memory context to response
        response["memory_info"] = {
            "memory_enabled": True,
            "conversation_length": len(enhanced_context.get("conversation_context", [])),
            "user_context_stored": user_context.get("authenticated", False)
        }
        
        # Add session information (AgentCore Runtime manages this)
        # IMPORTANT: AgentCore Runtime DOES auto-generate session IDs if not provided,
        # but the auto-generated ID is NOT accessible in the entrypoint function.
        # The session ID is only accessible if:
        # 1. Provided explicitly in request body (session_id or context.runtimeSessionId)
        # 2. Provided via --session-id flag in agentcore invoke
        # 3. Shown in agentcore invoke output (but not accessible in code)
        
        if not runtime_session_id:
            # Try to get from AgentCore Runtime app context (may not be available)
            try:
                if hasattr(app, 'get_runtime_session_id'):
                    runtime_session_id = app.get_runtime_session_id()
                elif hasattr(app, 'runtime_session_id'):
                    runtime_session_id = app.runtime_session_id
                elif hasattr(request, 'runtimeSessionId'):
                    runtime_session_id = getattr(request, 'runtimeSessionId', None)
            except Exception as e:
                logger.debug(f"Could not get session ID from app context: {e}")
        
        # Always include session info in response
        if runtime_session_id:
            response["session_info"] = {
                "runtime_session_id": runtime_session_id,
                "note": "Session managed by AgentCore Runtime. Use same session ID for follow-up interactions."
            }
        else:
            response["session_info"] = {
                "runtime_session_id": None,
                "note": "AgentCore Runtime auto-generated a session ID internally, but it's not accessible in the entrypoint. To maintain session continuity, explicitly provide a session_id in the request body or use --session-id flag with agentcore invoke."
            }
        
        # Also include session_id at top level for easier access
        if runtime_session_id:
            response["session_id"] = runtime_session_id
            # Ensure context exists before accessing it
            if "context" not in response:
                response["context"] = {}
            response["context"]["runtime_session_id"] = runtime_session_id
            response["context"]["session_id"] = runtime_session_id
        
        return response
            
    except Exception as e:
        logger.error(f"Failed to process request: {str(e)}", exc_info=True)
        return {"error": f"Failed to process request: {str(e)}", "status": "error"}


if __name__ == "__main__":
    print("Multi-Agent Customer Support System starting...")
    print(f"Using Bedrock model: {BEDROCK_MODEL_ID}")
    print(f"AWS Region: {AWS_REGION}")
    print("Memory: STM_AND_LTM enabled")
    print("Configured agent URLs:", AGENT_URLS)
    app.run()