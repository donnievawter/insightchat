"""
Base Tool - Abstract base class for all external API tools

This module provides the foundation for integrating external APIs into InsightChat.
Each tool can provide specialized data that enhances the LLM's responses.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class BaseTool(ABC):
    """
    Abstract base class for all tools.
    
    Each tool should:
    1. Implement intent detection (which queries it can handle)
    2. Provide an execute method that calls the external API
    3. Return structured data that the LLM can use
    """
    
    def __init__(self, enabled: bool = True, **config):
        """
        Initialize the tool with configuration.
        
        Args:
            enabled: Whether this tool is enabled
            **config: Tool-specific configuration parameters
        """
        self.enabled = enabled
        self.config = config
        self.name = self.__class__.__name__.replace('Tool', '').lower()
        
    @abstractmethod
    def get_intent_keywords(self) -> List[str]:
        """
        Return a list of keywords/phrases that indicate this tool should be used.
        
        Returns:
            List of keywords that suggest this tool is relevant
        """
        pass
    
    @abstractmethod
    def can_handle(self, query: str) -> bool:
        """
        Determine if this tool can handle the given query.
        
        Args:
            query: User's query string
            
        Returns:
            True if this tool should be invoked for this query
        """
        pass
    
    @abstractmethod
    async def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool and return results.
        
        Args:
            query: User's query string
            **kwargs: Additional parameters
            
        Returns:
            Dictionary containing:
                - success: bool - Whether the tool executed successfully
                - data: Any - The tool's response data
                - error: str - Error message if success is False
                - metadata: Dict - Additional metadata about the execution
        """
        pass
    
    def format_for_llm(self, result: Dict[str, Any]) -> str:
        """
        Format the tool's result for inclusion in the LLM prompt.
        
        Args:
            result: Result dictionary from execute()
            
        Returns:
            Formatted string to include in LLM context
        """
        if not result.get('success'):
            return f"[{self.name} tool error: {result.get('error', 'Unknown error')}]"
        
        data = result.get('data', {})
        return f"[{self.name} tool response: {data}]"
    
    def is_available(self) -> bool:
        """
        Check if the tool is available and properly configured.
        
        Returns:
            True if the tool can be used
        """
        if not self.enabled:
            logger.debug(f"{self.name} tool is disabled")
            return False
        
        # Check required configuration
        required_config = self.get_required_config()
        for key in required_config:
            if key not in self.config or not self.config[key]:
                logger.warning(f"{self.name} tool missing required config: {key}")
                return False
        
        return True
    
    def get_required_config(self) -> List[str]:
        """
        Return list of required configuration keys.
        
        Override this in subclasses to specify required config.
        
        Returns:
            List of required configuration key names
        """
        return []
    
    def get_tool_description(self) -> str:
        """
        Get a human-readable description of what this tool does.
        
        Returns:
            Description string for documentation/logging
        """
        return f"{self.name} tool"
    
    async def health_check(self) -> bool:
        """
        Perform a health check on the tool's external service.
        
        Returns:
            True if the service is healthy and reachable
        """
        return self.is_available()
