"""
Simple Streamlit UI for testing the Multi-Agent Customer Support System
Supports session ID management for memory testing and Cognito authentication
"""

import streamlit as st
import json
import requests
import os
import subprocess
import shutil
import boto3
import uuid
import re
import logging
from datetime import datetime
from typing import Optional, Dict
try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False

# Setup logging
logger = logging.getLogger(__name__)

def generate_session_id(prefix: str = "session") -> str:
    """Generate a session ID that meets AgentCore requirements (min 33 chars)"""
    return f"{prefix}-{uuid.uuid4()}"

# Page configuration
st.set_page_config(
    page_title="Customer Support Agent",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_info" not in st.session_state:
    st.session_state.user_info = {}
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "show_auth" not in st.session_state:
    st.session_state.show_auth = False
if "id_token" not in st.session_state:
    st.session_state.id_token = None
if "cognito_config" not in st.session_state:
    st.session_state.cognito_config = {}
# CRITICAL FOR LTM: Store persistent user_id that survives session changes
if "persistent_user_id" not in st.session_state:
    # Generate a unique user_id for this browser session (persists across session ID changes)
    import uuid
    st.session_state.persistent_user_id = f"ui-user-{uuid.uuid4().hex[:8]}"

# Get AgentCore endpoint from environment or use default
# Options:
# 1. Use agentcore CLI (recommended for local): Set to "cli"
# 2. Use local HTTP endpoint: "http://localhost:8080/invocations"
# 3. Use AWS AgentCore Runtime: Set to runtime ARN or endpoint URL
AGENTCORE_MODE = os.getenv("AGENTCORE_MODE", "cli")  # "cli", "local", or "aws"
AGENTCORE_ENDPOINT = os.getenv("AGENTCORE_ENDPOINT", "")

# Default Cognito Configuration (from Terraform outputs)
# These are the actual values from your deployed infrastructure
DEFAULT_COGNITO_CONFIG = {
    "user_pool_id": "us-east-1_il7Myy5fw",
    "client_id": "29st43m8gdd3vj7ave165ukkah",
    "region": "us-east-1",
    "domain": "dev-customer-support-auth-xo726ktv.auth.us-east-1.amazoncognito.com",
}

def get_cognito_config() -> Dict:
    """Get Cognito configuration from multiple sources with fallback to defaults"""
    # If already cached, return it
    if st.session_state.cognito_config and st.session_state.cognito_config.get("user_pool_id"):
        return st.session_state.cognito_config
    
    # Start with defaults
    config = DEFAULT_COGNITO_CONFIG.copy()
    
    # Try environment variables first (override defaults)
    if os.getenv("COGNITO_USER_POOL_ID"):
        config["user_pool_id"] = os.getenv("COGNITO_USER_POOL_ID")
    if os.getenv("COGNITO_CLIENT_ID"):
        config["client_id"] = os.getenv("COGNITO_CLIENT_ID")
    if os.getenv("AWS_REGION"):
        config["region"] = os.getenv("AWS_REGION")
    if os.getenv("COGNITO_DOMAIN_URL"):
        config["domain"] = os.getenv("COGNITO_DOMAIN_URL")
    
    # Try to get from Terraform outputs (if terraform is available)
    if not config.get("user_pool_id") or not config.get("client_id"):
        try:
            import subprocess
            import json
            
            terraform_dir = os.path.join(os.path.dirname(__file__), "infrastructure", "minimal")
            if os.path.exists(terraform_dir):
                result = subprocess.run(
                    ["terraform", "output", "-json", "cognito_user_pool"],
                    cwd=terraform_dir,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    terraform_output = json.loads(result.stdout)
                    if terraform_output.get("id"):
                        config["user_pool_id"] = terraform_output["id"]
                    if terraform_output.get("client_id"):
                        config["client_id"] = terraform_output["client_id"]
                    if terraform_output.get("domain"):
                        config["domain"] = terraform_output["domain"]
        except:
            pass  # Terraform not available or failed, use defaults
    
    # Try SSM Parameter Store as fallback
    if not config.get("user_pool_id") or not config.get("client_id"):
        try:
            ssm = boto3.client("ssm", region_name=config["region"])
            resource_prefix = os.getenv("RESOURCE_PREFIX", "dev-customer-support")
            
            try:
                config["user_pool_id"] = ssm.get_parameter(
                    Name=f"/{resource_prefix}/cognito/user_pool_id"
                )["Parameter"]["Value"]
            except:
                pass
            
            try:
                config["client_id"] = ssm.get_parameter(
                    Name=f"/{resource_prefix}/cognito/client_id"
                )["Parameter"]["Value"]
            except:
                pass
        except:
            pass  # SSM not available, use defaults
    
    # Set domain if not set
    if not config.get("domain") and config.get("user_pool_id"):
        try:
            # Extract domain from user pool ID
            pool_id_parts = config["user_pool_id"].split("_")
            if len(pool_id_parts) > 1:
                config["domain"] = f"{pool_id_parts[1].lower()}.auth.{config['region']}.amazoncognito.com"
        except:
            pass
    
    # Cache the config
    st.session_state.cognito_config = config
    return config

def authenticate_with_cognito(username: str, password: str, config: Dict) -> Optional[Dict]:
    """Authenticate user with Cognito"""
    try:
        cognito_client = boto3.client('cognito-idp', region_name=config["region"])
        
        response = cognito_client.initiate_auth(
            AuthFlow='USER_PASSWORD_AUTH',
            ClientId=config["client_id"],
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )
        
        # Check if there's a challenge (e.g., NEW_PASSWORD_REQUIRED)
        if 'ChallengeName' in response:
            challenge_name = response.get('ChallengeName')
            if challenge_name == 'NEW_PASSWORD_REQUIRED':
                # User needs to set a new password
                return {
                    "error": "New password required",
                    "error_code": "NewPasswordRequired",
                    "challenge_name": challenge_name,
                    "session": response.get('Session'),
                    "details": "Your account requires a password change. Please set a new password first using AWS CLI or Cognito console."
                }
            else:
                return {
                    "error": f"Authentication challenge required: {challenge_name}",
                    "error_code": "ChallengeRequired",
                    "challenge_name": challenge_name,
                    "details": f"Please complete the {challenge_name} challenge."
                }
        
        # Check for AuthenticationResult
        auth_result = response.get('AuthenticationResult', {})
        if not auth_result:
            return {
                "error": "No authentication result received",
                "error_code": "NoAuthResult",
                "details": "The authentication response did not contain an authentication result."
            }
        
        return {
            "access_token": auth_result.get('AccessToken'),
            "id_token": auth_result.get('IdToken'),
            "refresh_token": auth_result.get('RefreshToken'),
            "expires_in": auth_result.get('ExpiresIn', 3600)
        }
    except Exception as e:
        # Get detailed error information
        error_code = "Unknown"
        error_msg = str(e)
        
        # Try to extract error code and message from boto3 exception
        if hasattr(e, 'response'):
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_msg = e.response.get('Error', {}).get('Message', str(e))
        
        # Map common Cognito errors to user-friendly messages
        if "NotAuthorizedException" in error_code or "NotAuthorizedException" in error_msg:
            return {"error": "Invalid username or password", "error_code": error_code, "details": error_msg}
        elif "UserNotFoundException" in error_code or "UserNotFoundException" in error_msg:
            return {"error": "User not found. Please check your username.", "error_code": error_code, "details": error_msg}
        elif "UserNotConfirmedException" in error_code or "UserNotConfirmedException" in error_msg:
            return {"error": "User account not confirmed. Please check your email for verification code.", "error_code": error_code, "details": error_msg}
        elif "InvalidParameterException" in error_code:
            return {"error": f"Invalid configuration: {error_msg}", "error_code": error_code, "details": error_msg}
        elif "ResourceNotFoundException" in error_code:
            return {"error": "Cognito user pool or client not found. Please check your configuration.", "error_code": error_code, "details": error_msg}
        else:
            return {"error": f"Authentication failed: {error_msg}", "error_code": error_code, "details": error_msg}

def decode_token(token: str) -> Optional[Dict]:
    """Decode JWT token"""
    if not JWT_AVAILABLE:
        return None
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded
    except:
        return None

def get_user_info_from_token(id_token: str) -> Dict:
    """Extract user information from ID token"""
    decoded = decode_token(id_token)
    if not decoded:
        return {}
    
    return {
        "username": decoded.get("cognito:username") or decoded.get("sub"),
        "email": decoded.get("email"),
        "email_verified": decoded.get("email_verified", False),
        "user_id": decoded.get("sub"),
        "groups": decoded.get("cognito:groups", []),
        "custom:department": decoded.get("custom:department", "general"),
    }

def invoke_agent(message: str, session_id: str, user_id: str = None, access_token: str = None) -> dict:
    """Invoke the AgentCore agent"""
    try:
        # Use authenticated user_id if available, otherwise use persistent user_id for LTM
        if not user_id:
            # Priority: authenticated user_id > persistent_user_id > default
            user_id = (
                st.session_state.user_info.get("user_id") or 
                st.session_state.user_info.get("username") or 
                st.session_state.get("persistent_user_id") or 
                "ui-user"
            )
        
        payload = {
            "input": message,
            "user_id": user_id,
            "session_id": session_id
        }
        
        # Build context with user info and conversation history
        context = {}
        
        # Add user context if authenticated
        if st.session_state.authenticated and st.session_state.user_info:
            context.update({
                "user_id": st.session_state.user_info.get("user_id") or user_id,  # CRITICAL: Must be in context for LTM
                "username": st.session_state.user_info.get("username"),
                "department": st.session_state.user_info.get("custom:department", "general"),
                "authenticated": True,
                "email": st.session_state.user_info.get("email"),
            })
        else:
            # Even if not authenticated, include user_id in context for LTM
            # This ensures LTM works even without authentication
            context["user_id"] = user_id
        
        # CRITICAL: Add conversation history for memory context
        # AgentCore Runtime manages memory via session_id, but we also pass explicit history
        # This ensures the agent has immediate access to previous messages
        if st.session_state.conversation_history:
            context["conversation_history"] = st.session_state.conversation_history
            context["runtimeSessionId"] = session_id  # Explicitly set for AgentCore
        
        # Add context to payload if we have any
        if context:
            payload["context"] = context
        
        # Option 1: Use agentcore CLI (recommended)
        if AGENTCORE_MODE == "cli" or not AGENTCORE_ENDPOINT:
            # Check if agentcore is available
            if not shutil.which("agentcore"):
                return {
                    "error": "AgentCore CLI not found",
                    "message": "Please install agentcore CLI or use local/aws mode"
                }
            
            # Use agentcore invoke command
            # For LTM (Long-Term Memory), user_id must be passed as a flag
            # Same user_id with different session_id should retrieve LTM
            cmd = [
                "agentcore", "invoke",
                json.dumps(payload),
                "--session-id", session_id
            ]
            
            # CRITICAL FOR LTM: Add --user-id flag for Long-Term Memory support
            # AgentCore Runtime uses user_id for LTM across different sessions
            # Always add --user-id flag (even for "ui-user") so LTM works across session changes
            if user_id:
                cmd.extend(["--user-id", user_id])
                logger.debug(f"LTM: Adding --user-id flag: {user_id} (for cross-session memory)")
            else:
                # Fallback: use persistent user_id from session_state
                persistent_user_id = st.session_state.get("persistent_user_id")
                if persistent_user_id:
                    cmd.extend(["--user-id", persistent_user_id])
                    logger.debug(f"LTM: Using persistent user_id: {persistent_user_id}")
            
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=120  # Increased timeout for agent processing (2 minutes)
                )
            except subprocess.TimeoutExpired:
                return {"error": "Timeout", "message": "Agent invocation timed out after 120 seconds. The agent may be processing a complex request or waiting for specialized agents."}
            
            if result.returncode != 0:
                # Check for session ID validation error
                error_output = result.stderr or result.stdout or ""
                if "Invalid length for parameter runtimeSessionId" in error_output or "valid min length: 33" in error_output:
                    return {
                        "error": "Session ID too short",
                        "message": "Session ID must be at least 33 characters. Please use a longer session ID.",
                        "stdout": result.stdout,
                        "stderr": result.stderr
                    }
                
                return {
                    "error": "AgentCore CLI error",
                    "message": result.stderr or "Failed to invoke agent",
                    "stdout": result.stdout
                }
            
            # Parse response
            try:
                # agentcore invoke outputs formatted text with JSON response
                stdout_text = result.stdout
                
                # Find "Response:" marker
                if "Response:" in stdout_text:
                    response_idx = stdout_text.find("Response:")
                    after_response = stdout_text[response_idx:]
                    
                    # Find the first { after Response:
                    json_start = after_response.find("{")
                    if json_start != -1:
                        json_candidate = after_response[json_start:]
                        
                        # Properly extract JSON by counting braces (handles newlines in strings)
                        brace_count = 0
                        in_string = False
                        escape_next = False
                        json_end = -1
                        
                        for i, char in enumerate(json_candidate):
                            if escape_next:
                                escape_next = False
                                continue
                            
                            if char == '\\':
                                escape_next = True
                                continue
                            
                            if char == '"' and not escape_next:
                                in_string = not in_string
                                continue
                            
                            if not in_string:
                                if char == '{':
                                    brace_count += 1
                                elif char == '}':
                                    brace_count -= 1
                                    if brace_count == 0:
                                        json_end = i + 1
                                        break
                        
                        if json_end > 0:
                            json_str = json_candidate[:json_end]
                            
                            # Fix invalid control characters (newlines in strings)
                            # Replace unescaped newlines within string values with \n
                            # This is a workaround for JSON that has literal newlines
                            fixed_json = []
                            in_string = False
                            escape_next = False
                            
                            i = 0
                            while i < len(json_str):
                                char = json_str[i]
                                
                                if escape_next:
                                    fixed_json.append(char)
                                    escape_next = False
                                    i += 1
                                    continue
                                
                                if char == '\\':
                                    fixed_json.append(char)
                                    escape_next = True
                                    i += 1
                                    continue
                                
                                if char == '"':
                                    in_string = not in_string
                                    fixed_json.append(char)
                                    i += 1
                                    continue
                                
                                if in_string and char == '\n':
                                    # Replace literal newline with escaped newline
                                    fixed_json.append('\\n')
                                elif in_string and char == '\r':
                                    # Replace literal carriage return
                                    fixed_json.append('\\r')
                                elif in_string and ord(char) < 32 and char not in ['\t']:
                                    # Replace other control characters
                                    fixed_json.append(f'\\u{ord(char):04x}')
                                else:
                                    fixed_json.append(char)
                                
                                i += 1
                            
                            json_str = ''.join(fixed_json)
                            parsed_response = json.loads(json_str)
                            
                            # Ensure we have a valid response structure
                            if isinstance(parsed_response, dict):
                                return parsed_response
                
                # Fallback: Try simple extraction
                response_text = stdout_text.strip()
                if "Response:" in response_text:
                    json_start = response_text.find("{")
                    if json_start != -1:
                        json_end = response_text.rfind("}")
                        if json_end != -1 and json_end > json_start:
                            response_text = response_text[json_start:json_end + 1]
                
                # Try to parse
                parsed_response = json.loads(response_text)
                
                if isinstance(parsed_response, dict):
                    return parsed_response
                else:
                    return {
                        "message": str(parsed_response),
                        "raw_output": result.stdout
                    }
                    
            except json.JSONDecodeError as e:
                # If JSON parsing fails, try to extract message field manually
                error_msg = "Failed to parse response"
                if "Invalid length for parameter runtimeSessionId" in result.stdout:
                    error_msg = "Session ID must be at least 33 characters"
                
                # Try to extract message from raw output as fallback
                raw_output = result.stdout
                if "Response:" in raw_output and '"message"' in raw_output:
                    try:
                        # Find message field and extract its value
                        msg_pattern = r'"message"\s*:\s*"([^"]*(?:\\.[^"]*)*)"'
                        match = re.search(msg_pattern, raw_output, re.DOTALL)
                        if match:
                            extracted_msg = match.group(1).replace('\\n', '\n').replace('\\"', '"')
                            return {
                                "message": extracted_msg,
                                "raw_output": raw_output,
                                "note": "Extracted from response (full parsing failed)"
                            }
                    except:
                        pass
                
                return {
                    "error": "Response parsing error",
                    "message": error_msg,
                    "raw_output": result.stdout,
                    "parse_error": str(e)
                }
        
        # Option 2: Local HTTP endpoint
        elif AGENTCORE_MODE == "local" or "localhost" in AGENTCORE_ENDPOINT or "127.0.0.1" in AGENTCORE_ENDPOINT:
            endpoint = AGENTCORE_ENDPOINT or "http://localhost:8080/invocations"
            response = requests.post(endpoint, json=payload, timeout=120)  # Increased timeout for agent processing
            response.raise_for_status()
            return response.json()
        
        # Option 3: AWS AgentCore Runtime (requires AWS credentials)
        else:
            import boto3
            from botocore.auth import SigV4Auth
            from botocore.awsrequest import AWSRequest
            
            # Use runtime ARN or endpoint URL
            if not AGENTCORE_ENDPOINT:
                # Default runtime ARN
                runtime_arn = "arn:aws:bedrock-agentcore:us-east-1:060476965572:runtime/customer_support_supervisor-GIa7fv2B6G"
                endpoint = f"https://bedrock-agentcore-runtime.us-east-1.amazonaws.com/runtime/{runtime_arn.split('/')[-1]}/runtime-endpoint/DEFAULT/invocations"
            else:
                endpoint = AGENTCORE_ENDPOINT
            
            session = boto3.Session()
            credentials = session.get_credentials()
            
            request = AWSRequest(
                method='POST',
                url=endpoint,
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'}
            )
            
            SigV4Auth(credentials, 'bedrock-agentcore', 'us-east-1').add_auth(request)
            
            response = requests.post(
                request.url,
                data=request.data,
                headers=dict(request.headers),
                timeout=120  # Increased timeout for agent processing
            )
            
            response.raise_for_status()
            return response.json()
            
    except Exception as e:
        return {"error": str(e), "message": f"Failed to invoke agent: {str(e)}"}

# Sidebar for authentication and session management
with st.sidebar:
    # Authentication section
    st.header("🔐 Authentication")
    
    if st.session_state.authenticated:
        st.success("✅ Authenticated")
        with st.expander("👤 User Info"):
            st.json(st.session_state.user_info)
        
        if st.button("🚪 Sign Out"):
            st.session_state.authenticated = False
            st.session_state.user_info = {}
            st.session_state.access_token = None
            st.rerun()
        
        if st.button("🔑 Go to Auth Page"):
            st.session_state.show_auth = True
            st.rerun()
    else:
        st.info("Not authenticated")
        if st.button("🔐 Sign In"):
            st.session_state.show_auth = True
            st.rerun()
    
    st.divider()
    
    st.header("🔧 Session Management")
    
    # Session ID input
    default_session_id = st.session_state.session_id or generate_session_id()
    new_session_id = st.text_input(
        "Session ID",
        value=default_session_id,
        help="Change this to test memory across different sessions. Same session ID = same memory context. Must be at least 33 characters."
    )
    
    # Validate session ID length
    if new_session_id and len(new_session_id) < 33:
        st.warning(f"⚠️ Session ID must be at least 33 characters (current: {len(new_session_id)}). Generating new one...")
        if st.button("🔄 Generate Valid Session ID"):
            new_session_id = generate_session_id()
            st.session_state.session_id = new_session_id
            st.session_state.conversation_history = []
            st.rerun()
    
    if st.button("🔄 Update Session ID"):
        # Validate before updating
        if len(new_session_id) >= 33:
            st.session_state.session_id = new_session_id
            st.session_state.conversation_history = []
            st.rerun()
        else:
            st.error(f"❌ Session ID must be at least 33 characters (current: {len(new_session_id)})")
    
    st.divider()
    
    # Current session info
    st.subheader("📊 Current Session")
    st.text(f"Session ID: {st.session_state.session_id or 'Not set'}")
    st.text(f"Messages: {len(st.session_state.messages)}")
    
    st.divider()
    
    # Memory testing guide
    st.subheader("🧠 Memory Testing")
    
    # Show current user_id for LTM debugging
    current_user_id = (
        st.session_state.user_info.get("user_id") or 
        st.session_state.user_info.get("username") or 
        st.session_state.get("persistent_user_id") or 
        "ui-user"
    )
    st.info(f"**Current User ID for LTM:** `{current_user_id}`\n\nThis ID persists across session changes. Keep it the same to test LTM.")
    
    st.markdown("""
    **Short-Term Memory (STM):**
    - Use the same session ID
    - Agent remembers context within the session
    
    **Long-Term Memory (LTM):**
    - Use the same user_id (shown above)
    - Change session ID
    - Agent remembers across sessions
    - ⚠️ **Important:** The user_id above must stay the same when you change session ID
    """)
    
    st.divider()
    
    # Clear conversation
    if st.button("🗑️ Clear Conversation"):
        st.session_state.messages = []
        st.session_state.conversation_history = []
        st.rerun()
    
    st.divider()
    
    # Available Agents and Tools
    st.header("🤖 Available Agents")
    with st.expander("📋 Agent List", expanded=True):
        agents_info = {
            "🔵 SupervisorAgent": "Main orchestrator - routes to specialized agents",
            "🟢 KnowledgeAgent": "Searches knowledge base using S3 vectors",
            "🟡 SentimentAgent": "Analyzes customer emotions and urgency",
            "🟠 TicketAgent": "Manages support tickets",
            "🔴 ResolutionAgent": "Generates personalized responses",
            "⚫ EscalationAgent": "Handles human-in-the-loop escalation"
        }
        for agent, desc in agents_info.items():
            st.markdown(f"**{agent}**")
            st.caption(desc)
    
    st.divider()
    
    # Available MCP Tools
    st.header("🔧 Available MCP Tools")
    with st.expander("📋 MCP Tools List", expanded=False):
        mcp_tools_info = {
            "dev-customer-support-sentiment-analysis-target___sent": "Sentiment analysis using Amazon Comprehend",
            "dev-customer-support-knowledge-search-target___search": "Knowledge base search using S3 vectors",
            "dev-customer-support-ticket-management-target___ticket": "Manage support tickets (create, get, update, list)"
        }
        for tool, desc in mcp_tools_info.items():
            st.markdown(f"**`{tool}`**")
            st.caption(desc)
    
    st.divider()
    
    # Configuration
    st.subheader("⚙️ Configuration")
    mode = st.selectbox(
        "Invocation Mode",
        options=["cli", "local", "aws"],
        index=0 if AGENTCORE_MODE == "cli" else (1 if AGENTCORE_MODE == "local" else 2),
        help="cli: Use agentcore CLI (recommended), local: HTTP endpoint, aws: AWS Runtime"
    )
    if mode != AGENTCORE_MODE:
        os.environ["AGENTCORE_MODE"] = mode
        st.info("Mode updated. Restart the app to apply changes.")
    
    if mode in ["local", "aws"]:
        endpoint = st.text_input(
            "AgentCore Endpoint",
            value=AGENTCORE_ENDPOINT or "",
            help="AgentCore Runtime endpoint URL (leave empty for defaults)"
        )
        if endpoint != AGENTCORE_ENDPOINT:
            os.environ["AGENTCORE_ENDPOINT"] = endpoint
            st.info("Endpoint updated. Restart the app to apply changes.")

# Check if we should show auth page or chat page
if st.session_state.get("show_auth", False):
    # Authentication page
    st.title("🔐 Customer Support - Authentication")
    
    config = get_cognito_config()
    
    if st.session_state.authenticated and st.session_state.access_token:
        st.success("✅ You are authenticated!")
        
        with st.expander("👤 User Information"):
            user_info = st.session_state.user_info
            st.json(user_info)
            
            if "id_token" in st.session_state and st.session_state.id_token and JWT_AVAILABLE:
                token_info = decode_token(st.session_state.id_token)
                if token_info:
                    st.subheader("Token Information")
                    st.json({
                        "expires_at": datetime.fromtimestamp(token_info.get("exp", 0)).isoformat() if token_info.get("exp") else "N/A",
                        "issued_at": datetime.fromtimestamp(token_info.get("iat", 0)).isoformat() if token_info.get("iat") else "N/A",
                        "issuer": token_info.get("iss"),
                        "audience": token_info.get("aud"),
                    })
        
        st.info("💡 You can now use the Chat page with authenticated requests.")
    
    else:
        st.markdown("### Sign In")
        
        # Show current configuration (read-only, for reference)
        with st.expander("📋 Current Configuration (Auto-detected)", expanded=False):
            st.json({
                "User Pool ID": config.get("user_pool_id", "Not configured"),
                "Client ID": config.get("client_id", "Not configured"),
                "Region": config.get("region", "Not configured"),
                "Domain": config.get("domain", "Not configured"),
            })
            st.caption("💡 Configuration is automatically loaded from defaults, environment variables, or Terraform outputs.")
        
        # Check if we have valid configuration
        if not config.get("client_id") or not config.get("user_pool_id"):
            st.warning("⚠️ Cognito configuration incomplete. Please configure manually:")
            
            with st.expander("⚙️ Manual Configuration"):
                manual_user_pool_id = st.text_input(
                    "User Pool ID", 
                    value=config.get("user_pool_id", ""),
                    help="Enter your Cognito User Pool ID"
                )
                manual_client_id = st.text_input(
                    "Client ID", 
                    value=config.get("client_id", ""),
                    help="Enter your Cognito Client ID"
                )
                manual_region = st.text_input(
                    "AWS Region", 
                    value=config.get("region", "us-east-1"),
                    help="Enter your AWS Region"
                )
                
                if st.button("💾 Save Configuration"):
                    if manual_user_pool_id and manual_client_id:
                        st.session_state.cognito_config = {
                            "user_pool_id": manual_user_pool_id,
                            "client_id": manual_client_id,
                            "region": manual_region,
                        }
                        config = st.session_state.cognito_config
                        st.success("✅ Configuration saved!")
                        st.rerun()
                    else:
                        st.error("Please enter both User Pool ID and Client ID")
        else:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Sign In", use_container_width=True)
                
                if submit:
                    if not username or not password:
                        st.error("Please enter both username and password")
                    else:
                        with st.spinner("Authenticating..."):
                            auth_result = authenticate_with_cognito(username, password, config)
                            
                            if auth_result and auth_result.get("access_token"):
                                st.session_state.authenticated = True
                                st.session_state.access_token = auth_result["access_token"]
                                st.session_state.id_token = auth_result.get("id_token")
                                
                                if auth_result.get("id_token"):
                                    st.session_state.user_info = get_user_info_from_token(auth_result["id_token"])
                                
                                st.success("✅ Authentication successful!")
                                st.session_state.show_auth = False
                                st.rerun()
                            elif auth_result and auth_result.get("error"):
                                error_msg = auth_result['error']
                                error_code = auth_result.get('error_code', '')
                                details = auth_result.get('details', '')
                                
                                st.error(f"❌ {error_msg}")
                                
                                # Show detailed error in expander for debugging
                                if details and error_code:
                                    with st.expander("🔍 Error Details (for debugging)"):
                                        st.code(f"Error Code: {error_code}\nDetails: {details}")
                                        
                                        # Provide helpful suggestions based on error
                                        if "UserNotFoundException" in error_code:
                                            st.info("💡 **Tip:** Create a user first using AWS CLI:\n```bash\naws cognito-idp admin-create-user \\\n  --user-pool-id " + config.get('user_pool_id', 'YOUR_USER_POOL_ID') + " \\\n  --username your-username \\\n  --user-attributes Name=email,Value=your-email@example.com \\\n  --temporary-password TempPass123! \\\n  --message-action SUPPRESS\n```")
                                        elif "NotAuthorizedException" in error_code:
                                            st.info("💡 **Tip:** Make sure you're using the correct password. If this is a new user, you may need to set a permanent password first.")
                                        elif "ResourceNotFoundException" in error_code:
                                            st.info("💡 **Tip:** Verify your Cognito User Pool ID and Client ID are correct.")
                            else:
                                st.error("❌ Authentication failed. Please check your credentials.")
            
            st.divider()
            
            with st.expander("📝 New User? Register Here"):
                st.info("To create a new user account, use AWS CLI:")
                st.code("""
aws cognito-idp admin-create-user \\
  --user-pool-id YOUR_USER_POOL_ID \\
  --username newuser \\
  --user-attributes Name=email,Value=newuser@example.com \\
  --temporary-password TempPass123! \\
  --message-action SUPPRESS

aws cognito-idp admin-set-user-password \\
  --user-pool-id YOUR_USER_POOL_ID \\
  --username newuser \\
  --password NewPass123! \\
  --permanent
                """)
            
            with st.expander("⚙️ Current Configuration"):
                st.json(config)

else:
    # Main chat interface
    st.title("🤖 Customer Support Agent")
    st.markdown("**Multi-Agent System with Memory Management**")

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Show metadata if available
            if "metadata" in message:
                with st.expander("📋 Response Details"):
                    st.json(message["metadata"])

    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Ensure session ID is set and valid (at least 33 characters)
        if not st.session_state.session_id:
            st.session_state.session_id = new_session_id or generate_session_id()
        elif len(st.session_state.session_id) < 33:
            # Regenerate if too short
            st.session_state.session_id = generate_session_id()
        
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Show thinking indicator
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Invoke agent
                # CRITICAL FOR LTM: Use persistent user_id that survives session changes
                user_id = None
                if st.session_state.authenticated and st.session_state.user_info:
                    user_id = st.session_state.user_info.get("user_id") or st.session_state.user_info.get("username")
                else:
                    # For unauthenticated users, use persistent_user_id so LTM works across sessions
                    user_id = st.session_state.get("persistent_user_id")
                
                response = invoke_agent(
                    message=prompt,
                    session_id=st.session_state.session_id,
                    user_id=user_id or st.session_state.get("persistent_user_id", "ui-user"),
                    access_token=st.session_state.access_token if st.session_state.authenticated else None
                )
                
                # Extract response message
                if "error" in response:
                    message_content = f"❌ Error: {response.get('message', response.get('error', 'Unknown error'))}"
                    metadata = response
                    specialized_agents = []
                else:
                    message_content = response.get("message", response.get("response", "No response received"))
                    
                    # Extract agent information
                    primary_agent = response.get("agent", "Unknown")
                    model = response.get("model", "N/A")
                    context = response.get("context", {})
                    
                    # Extract detailed agent and tool usage from conversation context
                    specialized_agents = []
                    mcp_tools_used = []
                    response_trace = []  # Track the response generation flow
                    conversation_context = context.get("conversation_context", [])
                    
                    # Look for agent routing in conversation context
                    for entry in conversation_context:
                        if isinstance(entry, dict):
                            # Check for tool calls that indicate agent routing
                            tool_calls = entry.get("tool_calls", [])
                            for tool_call in tool_calls:
                                tool_name = tool_call.get("name", "")
                                # A2A tool calls - agent routing
                                if "a2a" in tool_name.lower() or "send_message" in tool_name.lower():
                                    # Try to extract agent name from arguments
                                    args = tool_call.get("arguments", {})
                                    if isinstance(args, str):
                                        try:
                                            args = json.loads(args)
                                        except:
                                            pass
                                    agent_name = args.get("agent_name") if isinstance(args, dict) else None
                                    if agent_name and agent_name not in specialized_agents:
                                        specialized_agents.append(agent_name)
                                        response_trace.append({
                                            "type": "agent",
                                            "name": agent_name,
                                            "action": "routed_to",
                                            "timestamp": entry.get("timestamp", "N/A")
                                        })
                                
                                # MCP tool calls - Lambda function calls
                                elif "___" in tool_name:
                                    # Extract tool name and target
                                    parts = tool_name.split("___")
                                    if len(parts) >= 2:
                                        target_name = parts[0]
                                        tool_function = parts[1]
                                        
                                        # Track MCP tool usage
                                        if tool_name not in mcp_tools_used:
                                            mcp_tools_used.append(tool_name)
                                        
                                        # Extract agent type from target name
                                        agent_mapping = {
                                            "knowledge": "KnowledgeAgent",
                                            "sentiment": "SentimentAgent",
                                            "ticket": "TicketAgent",
                                            "escalation": "EscalationAgent"
                                        }
                                        
                                        for key, agent_name in agent_mapping.items():
                                            if key in target_name.lower():
                                                if agent_name not in specialized_agents:
                                                    specialized_agents.append(agent_name)
                                                response_trace.append({
                                                    "type": "tool",
                                                    "agent": agent_name,
                                                    "tool": tool_name,
                                                    "function": tool_function,
                                                    "action": "called_mcp_tool",
                                                    "timestamp": entry.get("timestamp", "N/A")
                                                })
                                                break
                    
                    metadata = {
                        "session_id": response.get("session_id"),
                        "runtime_session_id": context.get("runtime_session_id"),
                        "memory_info": response.get("memory_info", {}),
                        "status": response.get("status"),
                        "primary_agent": primary_agent,
                        "model": model,
                        "specialized_agents": specialized_agents,
                        "mcp_tools_used": mcp_tools_used,
                        "response_trace": response_trace,
                        "user_tier": response.get("user_tier", "N/A"),
                        "authenticated": response.get("authenticated", False)
                    }
                
                # Display agent routing information
                if "error" not in response:
                    # Agent badges with colors
                    agent_badges = {
                        "SupervisorAgent": ("🔵", "Supervisor"),
                        "KnowledgeAgent": ("🟢", "Knowledge"),
                        "SentimentAgent": ("🟡", "Sentiment"),
                        "TicketAgent": ("🟠", "Ticket"),
                        "ResolutionAgent": ("🔴", "Resolution"),
                        "EscalationAgent": ("⚫", "Escalation")
                    }
                    
                    # Show primary agent
                    primary_agent = metadata.get("primary_agent", "Unknown")
                    badge_emoji, badge_name = agent_badges.get(primary_agent, ("⚪", primary_agent))
                    
                    # Create agent routing display
                    agent_info_html = f"""
                    <div style="background-color: #f0f2f6; padding: 10px; border-radius: 8px; margin-bottom: 10px;">
                        <strong>{badge_emoji} Primary Agent: {primary_agent}</strong>
                    """
                    
                    # Show specialized agents if any
                    specialized_agents = metadata.get("specialized_agents", [])
                    if specialized_agents:
                        agent_info_html += f"<br><strong>🔀 Routed to Specialized Agents:</strong><br>"
                        for agent in specialized_agents:
                            agent_emoji, agent_name = agent_badges.get(agent, ("⚪", agent))
                            agent_info_html += f"&nbsp;&nbsp;&nbsp;{agent_emoji} {agent}<br>"
                    else:
                        agent_info_html += "<br><em>No specialized agents called (handled directly by Supervisor)</em>"
                    
                    agent_info_html += "</div>"
                    st.markdown(agent_info_html, unsafe_allow_html=True)
                
                # Display response
                st.markdown(message_content)
                
                # Show metadata with agent routing info
                with st.expander("📋 Response Details"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("🤖 Agent Information")
                        agent_info = {
                            "Primary Agent": metadata.get("primary_agent", "N/A"),
                            "Model": metadata.get("model", "N/A"),
                            "Status": metadata.get("status", "N/A")
                        }
                        specialized_agents_list = metadata.get("specialized_agents", [])
                        if specialized_agents_list:
                            agent_info["Specialized Agents"] = specialized_agents_list
                        st.json(agent_info)
                        
                        # MCP Tools Used
                        mcp_tools = metadata.get("mcp_tools_used", [])
                        if mcp_tools:
                            st.subheader("🔧 MCP Tools Used")
                            for tool in mcp_tools:
                                st.code(tool, language=None)
                    
                    with col2:
                        st.subheader("💾 Session & Memory")
                        st.json({
                            "Session ID": metadata.get("session_id", "N/A"),
                            "Runtime Session ID": metadata.get("runtime_session_id", "N/A"),
                            "Memory Enabled": metadata.get("memory_info", {}).get("memory_enabled", False),
                            "User Tier": metadata.get("user_tier", "N/A")
                        })
                    
                    # Response Trace - Show the flow
                    response_trace = metadata.get("response_trace", [])
                    if response_trace:
                        st.subheader("🔍 Response Generation Trace")
                        st.markdown("**Flow of agents and tools used to generate this response:**")
                        
                        trace_html = "<div style='background-color: #f0f2f6; padding: 15px; border-radius: 8px; margin-top: 10px;'>"
                        for i, step in enumerate(response_trace, 1):
                            if step.get("type") == "agent":
                                trace_html += f"""
                                <div style='margin-bottom: 10px; padding: 10px; background-color: white; border-left: 4px solid #4CAF50; border-radius: 4px;'>
                                    <strong>Step {i}: Agent Routing</strong><br>
                                    <span style='color: #666;'>→ Routed to <strong>{step.get('name', 'Unknown')}</strong></span>
                                </div>
                                """
                            elif step.get("type") == "tool":
                                trace_html += f"""
                                <div style='margin-bottom: 10px; padding: 10px; background-color: white; border-left: 4px solid #2196F3; border-radius: 4px;'>
                                    <strong>Step {i}: MCP Tool Call</strong><br>
                                    <span style='color: #666;'>→ <strong>{step.get('agent', 'Unknown')}</strong> called tool:</span><br>
                                    <code style='background-color: #f5f5f5; padding: 2px 6px; border-radius: 3px;'>{step.get('tool', 'Unknown')}</code>
                                </div>
                                """
                        trace_html += "</div>"
                        st.markdown(trace_html, unsafe_allow_html=True)
                    else:
                        st.subheader("🔍 Response Generation Trace")
                        st.info("No detailed trace available. Response was handled directly by SupervisorAgent.")
                    
                    st.subheader("📊 Full Response Metadata")
                    st.json(metadata)
                
                # Add to conversation history
                st.session_state.conversation_history.append({
                    "role": "user",
                    "content": prompt
                })
                st.session_state.conversation_history.append({
                    "role": "assistant",
                    "content": message_content
                })
                
                # Add assistant message to chat
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": message_content,
                    "metadata": metadata
                })

    # Footer
    st.divider()
    st.markdown("""
    **💡 Tips for Memory Testing:**
    - **Same Session ID**: Test short-term memory (STM) - agent remembers within the conversation
    - **Different Session ID, Same User**: Test long-term memory (LTM) - agent remembers across sessions
    - **New User**: Start fresh with no memory context
    """)

