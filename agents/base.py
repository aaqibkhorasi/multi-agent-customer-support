#!/usr/bin/env python3
"""
Base Agent class for the Multi-Agent Customer Support Platform
Uses Strands Agents with A2A protocol
"""

import os
import sys
import logging
import boto3
from abc import ABC, abstractmethod
from strands import Agent
from strands.models import BedrockModel
from strands.multiagent.a2a import A2AServer

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.utils.mcp_client import create_mcp_client

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all customer support agents using Strands A2A protocol"""

    def __init__(self, port: str):
        self.port = port
        self.mcp_client = None  # Will be set in serve() method
        self.agent = self._create_agent()

    def _create_agent(self) -> Agent:
        """Create the agent with MCP tools (hotel assistant pattern - tools list)"""
        try:
            # Create Bedrock model
            aws_region = os.getenv("AWS_REGION", "us-east-1")
            bedrock_model_id = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
            
            # Initialize AWS session for Bedrock
            session = boto3.Session(region_name=aws_region)
            
            model = BedrockModel(
                model_id=bedrock_model_id,
                boto_session=session
            )
            
            logger.info(f"Using Bedrock model: {bedrock_model_id} in region: {aws_region}")

            # Load MCP tools (hotel assistant pattern - load in _create_agent)
            mcp_client = create_mcp_client()
            mcp_tools = []
            
            try:
                with mcp_client:
                    mcp_tools = mcp_client.list_tools_sync()
                    tool_names = []
                    for tool in mcp_tools:
                        tool_name = getattr(tool, 'name', None) or getattr(tool, 'tool_name', None) or str(tool)
                        tool_names.append(tool_name)
                    logger.info(f"✅ {self.get_agent_name()} loaded {len(mcp_tools)} MCP tools during creation: {tool_names}")
            except Exception as mcp_error:
                logger.warning(f"Could not load MCP tools during agent creation for {self.get_agent_name()}: {mcp_error}. Will retry in serve().")
                mcp_tools = []

            # Create agent WITH tools list (hotel assistant pattern)
            # Store MCP client reference for serve() method
            self.mcp_client = mcp_client
            agent = Agent(
                model,
                name=self.get_agent_name(),
                description=self.get_agent_description(),
                system_prompt=self.get_system_prompt(),
                tools=mcp_tools,  # Pass tools list, not client
            )

            return agent
        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            raise

    @abstractmethod
    def get_agent_name(self) -> str:
        """Get the agent name"""
        pass

    @abstractmethod
    def get_agent_description(self) -> str:
        """Get the agent description"""
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for the agent"""
        pass

    def serve(self, host: str = "0.0.0.0"):
        """
        Start the A2A server for this agent.
        Uses the same MCP client instance from _create_agent() to ensure tools are properly bound.
        Based on A2A-Multi-Agents-AgentCore pattern: run server within MCP client context.
        """
        try:
            # Reuse the MCP client from _create_agent() to ensure tools are bound to the same client
            # If not set, create a new one (shouldn't happen, but safety check)
            if not self.mcp_client:
                logger.warning(f"MCP client not set for {self.get_agent_name()}, creating new one")
                self.mcp_client = create_mcp_client()

            # Run A2A server within MCP client context
            # This ensures the MCP client session remains active during the entire server lifecycle
            # Tools loaded from list_tools_sync() need the client to be active when they execute
            with self.mcp_client:
                # Reload tools while client is open to ensure they're bound to the active client
                mcp_tools = self.mcp_client.list_tools_sync()
                tool_names = []
                for tool in mcp_tools:
                    tool_name = getattr(tool, 'name', None) or getattr(tool, 'tool_name', None) or str(tool)
                    tool_names.append(tool_name)
                logger.info(f"✅ {self.get_agent_name()} refreshed {len(mcp_tools)} MCP tools in serve(): {tool_names}")

                # Update agent tools with tools bound to the active MCP client
                self.agent.tools = mcp_tools

                # Create and serve A2A server within MCP context
                # The 'with self.mcp_client:' context keeps the client open for tool execution
                # This matches the A2A-Multi-Agents-AgentCore pattern where server runs within context
                a2a_server = A2AServer(self.agent, port=self.port)
                logger.info(f"🚀 Starting {self.get_agent_name()} on {host}:{self.port}")
                logger.info(f"📋 MCP client context is active - tools should be able to execute")
                a2a_server.serve(host=host, port=int(self.port))
        except KeyboardInterrupt:
            logger.info(f"{self.get_agent_name()} shutting down...")
        except Exception as e:
            logger.error(f"{self.get_agent_name()} error: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise