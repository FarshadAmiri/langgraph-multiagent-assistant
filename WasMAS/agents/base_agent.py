"""Base agent class for all agents"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any
from ..utils.logger import get_logger


class BaseAgent(ABC):
    """Base class for all agents in the system"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(name)
    
    @abstractmethod
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's task
        
        Args:
            state: Current state containing task, input, etc.
            
        Returns:
            Updated state with output and sources
        """
        pass
    
    def _log_start(self, task: str):
        """Log agent start"""
        self.logger.info(f"[{self.name}] Starting task: {task[:100]}...")
    
    def _log_finish(self, result: str):
        """Log agent finish"""
        self.logger.info(f"[{self.name}] Finished. Result: {result[:100]}...")
    
    def _log_error(self, error: str):
        """Log agent error"""
        self.logger.error(f"[{self.name}] Error: {error}")
    
    def _create_output(
        self,
        output: str,
        sources: list = None,
        metadata: dict = None
    ) -> Dict[str, Any]:
        """Create standardized output format"""
        return {
            "output": output,
            "sources": sources or [],
            "timestamp": datetime.now().isoformat(),
            "agent": self.name,
            "metadata": metadata or {}
        }
