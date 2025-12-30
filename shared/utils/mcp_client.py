import os
import logging
import boto3
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamablehttp_client

logger = logging.getLogger(__name__)


def _get_gateway_url_from_parameter_store(parameter_name: str, region: str = None) -> str:
    """Get Gateway URL from AWS Systems Manager Parameter Store"""
    try:
        session = boto3.Session(region_name=region or os.getenv("AWS_REGION", "us-east-1"))
        ssm_client = session.client("ssm")
        response = ssm_client.get_parameter(Name=parameter_name)
        gateway_url = response["Parameter"]["Value"]
        logger.info(f"Retrieved Gateway URL from Parameter Store: {parameter_name}")
        return gateway_url
    except Exception as e:
        logger.debug(f"Could not get Gateway URL from Parameter Store ({parameter_name}): {e}")
        return None


def _get_resource_prefix() -> str:
    """Get resource prefix from environment variables or derive from standard pattern"""
    resource_prefix = os.getenv("RESOURCE_PREFIX")
    if resource_prefix:
        return resource_prefix
    
    environment = os.getenv("ENVIRONMENT", "dev")
    project_name = os.getenv("PROJECT_NAME", "customer-support")
    return f"{environment}-{project_name}"


def _get_gateway_url() -> str:
    """Get Gateway URL from environment variable or Parameter Store"""
    # Try environment variable first (highest priority)
    gateway_url = os.getenv("AGENTCORE_GATEWAY_URL")
    
    # If not in environment, try Parameter Store
    if not gateway_url:
        resource_prefix = _get_resource_prefix()
        parameter_name = f"/{resource_prefix}/agentcore/gateway_url"
        gateway_url = _get_gateway_url_from_parameter_store(parameter_name)
    
    return gateway_url


def create_mcp_client() -> MCPClient:
    """
    Create an MCP client with Cognito authentication
    
    Gateway URL resolution:
    1. Environment variable AGENTCORE_GATEWAY_URL (highest priority)
    2. SSM Parameter Store: /{resource_prefix}/agentcore/gateway_url
    3. Fallback to localhost for development
    
    Authentication:
    - Cognito Bearer token (default)
    """
    gateway_url = _get_gateway_url()
    
    if not gateway_url:
        logger.info("No Gateway URL found, using local mock gateway")
        def create_mcp_transport():
            return streamablehttp_client("http://localhost:8000")
        return MCPClient(create_mcp_transport)
    
    # Use Cognito authentication (default)
    from .auth import TokenManager
    token_manager = TokenManager()
    token = token_manager.get_fresh_token()
    
    if token:
        logger.info("Using Cognito authentication for AgentCore Gateway")
        def create_mcp_transport():
            return streamablehttp_client(
                gateway_url,
                headers={"Authorization": f"Bearer {token}"}
            )
        return MCPClient(create_mcp_transport)
    else:
        logger.warning("Failed to get Cognito token, attempting connection without auth")
        def create_mcp_transport():
            return streamablehttp_client(gateway_url)
        return MCPClient(create_mcp_transport)