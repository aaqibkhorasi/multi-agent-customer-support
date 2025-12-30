import os
import requests
import logging
import boto3
from typing import Optional

logger = logging.getLogger(__name__)

def _get_ssm_parameter(parameter_name: str, region: str = None, decrypt: bool = False) -> Optional[str]:
    """Get parameter from SSM Parameter Store"""
    try:
        session = boto3.Session(region_name=region or os.getenv("AWS_REGION", "us-east-1"))
        ssm_client = session.client("ssm")
        response = ssm_client.get_parameter(Name=parameter_name, WithDecryption=decrypt)
        return response["Parameter"]["Value"]
    except Exception as e:
        logger.debug(f"Could not get SSM parameter {parameter_name}: {e}")
        return None

def _get_resource_prefix() -> str:
    """Get resource prefix from environment variables or derive from standard pattern"""
    resource_prefix = os.getenv("RESOURCE_PREFIX")
    if resource_prefix:
        return resource_prefix
    
    environment = os.getenv("ENVIRONMENT", "dev")
    project_name = os.getenv("PROJECT_NAME", "customer-support")
    return f"{environment}-{project_name}"

class TokenManager:
    """Manages Cognito authentication tokens for AgentCore gateway access"""
    
    def __init__(self):
        # Try environment variables first, then SSM Parameter Store
        resource_prefix = _get_resource_prefix()
        region = os.getenv("AWS_REGION", "us-east-1")
        
        # Get Cognito domain URL
        self.cognito_domain_url = (
            os.getenv("COGNITO_DOMAIN_URL") or
            _get_ssm_parameter(f"/{resource_prefix}/agentcore/cognito_domain_url", region)
        )
        
        # Get M2M client ID
        self.client_id = (
            os.getenv("USER_POOL_CLIENT_ID") or 
            os.getenv("COGNITO_CLIENT_ID") or
            _get_ssm_parameter(f"/{resource_prefix}/agentcore/user_pool_client_id", region)
        )
        
        # Get M2M client secret (from SSM SecureString or env var)
        self.client_secret = (
            os.getenv("USER_POOL_CLIENT_SECRET") or 
            os.getenv("COGNITO_CLIENT_SECRET") or
            _get_ssm_parameter(f"/{resource_prefix}/agentcore/user_pool_client_secret", region, decrypt=True)
        )
        
        self.user_pool_id = os.getenv("USER_POOL_ID") or os.getenv("COGNITO_USER_POOL_ID")
        
        # Get resource server ID
        resource_server_id = (
            os.getenv("AGENTCORE_RESOURCE_SERVER_ID") or
            _get_ssm_parameter(f"/{resource_prefix}/agentcore/resource_server_id", region) or
            "agentcore-gateway"
        )
        self.scope_string = f"{resource_server_id}/gateway:read {resource_server_id}/gateway:write"

    def get_fresh_token(self) -> Optional[str]:
        """Get a fresh access token from Cognito"""
        try:
            # If no Cognito config, return None (for local development)
            if not self.cognito_domain_url or not self.client_id:
                logger.warning("No Cognito configuration found, skipping authentication")
                return None
                
            url = f"{self.cognito_domain_url}/oauth2/token"

            # Build request data
            data = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "scope": self.scope_string,
            }
            
            # Add client_secret only if it exists (some clients don't have secrets)
            if self.client_secret:
                data["client_secret"] = self.client_secret

            response = requests.post(
                url,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data=data,
            )
            response.raise_for_status()
            token = response.json()["access_token"]
            logger.info("Successfully obtained fresh token from Cognito")
            return token
        except requests.exceptions.RequestException as err:
            logger.error(f"Failed to get token: {str(err)}")
            if hasattr(err, 'response') and err.response is not None:
                logger.error(f"Response: {err.response.text}")
            return None