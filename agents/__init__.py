"""
Multi-Agent Customer Support Platform - Agent Modules
"""

from .base import BaseAgent
from .sentiment_agent import SentimentAgent
from .knowledge_agent import KnowledgeAgent
from .ticket_agent import TicketAgent
from .resolution_agent import ResolutionAgent
from .escalation_agent import EscalationAgent

__all__ = [
    "BaseAgent",
    "SentimentAgent", 
    "KnowledgeAgent",
    "TicketAgent",
    "ResolutionAgent",
    "EscalationAgent"
]