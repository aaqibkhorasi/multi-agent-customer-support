"""
Utility to start specialized agents in the same container as the supervisor
This allows agents to be discovered via localhost in AgentCore Runtime
"""

import os
import threading
import logging
import time
from typing import List, Optional

logger = logging.getLogger(__name__)

# Agent configurations
AGENT_CONFIGS = {
    "sentiment": {
        "port": 9001,
        "name": "SentimentAgent",
        "module": "agents.sentiment_agent"
    },
    "knowledge": {
        "port": 9002,
        "name": "KnowledgeAgent",
        "module": "agents.knowledge_agent"
    },
    "ticket": {
        "port": 9003,
        "name": "TicketAgent",
        "module": "agents.ticket_agent"
    },
    "resolution": {
        "port": 9005,
        "name": "ResolutionAgent",
        "module": "agents.resolution_agent"
    },
    "escalation": {
        "port": 9006,
        "name": "EscalationAgent",
        "module": "agents.escalation_agent"
    }
}


def start_agent_in_thread(agent_name: str, config: dict) -> Optional[threading.Thread]:
    """Start a specialized agent in a background thread"""
    try:
        logger.info(f"Starting {config['name']} on port {config['port']} in background thread...")
        
        # Import the agent class
        module_name = config['module']
        agent_class_name = config['name']
        
        # Dynamic import based on agent name
        if agent_name == "sentiment":
            from agents.sentiment_agent import SentimentAgent
            agent_class = SentimentAgent
        elif agent_name == "knowledge":
            from agents.knowledge_agent import KnowledgeAgent
            agent_class = KnowledgeAgent
        elif agent_name == "ticket":
            from agents.ticket_agent import TicketAgent
            agent_class = TicketAgent
        elif agent_name == "resolution":
            from agents.resolution_agent import ResolutionAgent
            agent_class = ResolutionAgent
        elif agent_name == "escalation":
            from agents.escalation_agent import EscalationAgent
            agent_class = EscalationAgent
        else:
            logger.error(f"Unknown agent: {agent_name}")
            return None
        
        # Create agent instance (agents set their own ports in __init__)
        agent_instance = agent_class()
        
        # Start agent in a daemon thread (dies when main thread dies)
        def run_agent():
            try:
                agent_instance.serve(host="0.0.0.0")
            except Exception as e:
                logger.error(f"Error running {config['name']}: {e}")
        
        thread = threading.Thread(target=run_agent, daemon=True, name=f"{config['name']}-thread")
        thread.start()
        
        # Give the agent a moment to start
        time.sleep(0.5)
        
        logger.info(f"✅ {config['name']} started in background thread")
        return thread
        
    except Exception as e:
        logger.error(f"Failed to start {config['name']}: {e}", exc_info=True)
        return None


def start_all_agents_in_background(enabled_agents: Optional[List[str]] = None) -> List[threading.Thread]:
    """
    Start all specialized agents in background threads
    
    Args:
        enabled_agents: List of agent names to start (e.g., ["sentiment", "knowledge"])
                        If None, starts all agents
    
    Returns:
        List of started threads
    """
    threads = []
    
    # Check if we should start agents (can be disabled via environment variable)
    if os.getenv("DISABLE_BACKGROUND_AGENTS", "false").lower() == "true":
        logger.info("Background agents disabled via DISABLE_BACKGROUND_AGENTS environment variable")
        return threads
    
    # Determine which agents to start
    agents_to_start = enabled_agents if enabled_agents else list(AGENT_CONFIGS.keys())
    
    logger.info(f"Starting {len(agents_to_start)} specialized agents in background threads...")
    
    for agent_name in agents_to_start:
        if agent_name not in AGENT_CONFIGS:
            logger.warning(f"Unknown agent name: {agent_name}, skipping")
            continue
        
        config = AGENT_CONFIGS[agent_name]
        thread = start_agent_in_thread(agent_name, config)
        
        if thread:
            threads.append(thread)
            # Small delay between starts
            time.sleep(0.3)
    
    if threads:
        logger.info(f"✅ Started {len(threads)} agents in background. They will be accessible via localhost.")
        # Give all agents a moment to fully initialize
        time.sleep(1)
    else:
        logger.warning("⚠️  No agents were started in background")
    
    return threads

