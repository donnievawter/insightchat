"""
Tool Router - Orchestrates external API tool invocations

This module detects user intent and routes queries to appropriate tools
(weather, quotes, etc.) before falling back to standard RAG+LLM processing.
"""

import os
import logging
from typing import Dict, Any, List, Optional, Tuple
import asyncio

from .tools.weather_tool import WeatherTool
from .tools.quotes_tool import QuotesTool
from .tools.calendar_tool import CalendarTool

logger = logging.getLogger(__name__)


class ToolRouter:
    """
    Manages tool registration and routing based on query intent.
    
    The router:
    1. Maintains a registry of available tools
    2. Detects which tools can handle a query
    3. Executes tools and formats results for the LLM
    4. Provides fallback to standard RAG+LLM flow
    """
    
    def __init__(self):
        """Initialize the tool router with configured tools."""
        self.tools = []
        self._initialize_tools()
        
    def _initialize_tools(self):
        """
        Initialize tools based on environment configuration.
        
        Tools are only enabled if:
        1. TOOL_<NAME>_ENABLED is True in config
        2. Required configuration is present (e.g., API URL)
        """
        # Weather Tool
        weather_enabled = os.getenv('TOOL_WEATHER_ENABLED', 'false').lower() == 'true'
        weather_url = os.getenv('TOOL_WEATHER_API_URL', '')
        weather_timeout = int(os.getenv('TOOL_WEATHER_TIMEOUT', '10'))
        
        if weather_enabled and weather_url:
            try:
                weather_tool = WeatherTool(
                    api_url=weather_url,
                    timeout=weather_timeout,
                    enabled=True
                )
                self.tools.append(weather_tool)
                logger.info(f"✓ Weather tool registered: {weather_url}")
            except Exception as e:
                logger.error(f"Failed to initialize weather tool: {e}")
        elif weather_enabled:
            logger.warning("Weather tool enabled but TOOL_WEATHER_API_URL not configured")
        else:
            logger.debug("Weather tool disabled in configuration")
        
        # Quotes Tool
        quotes_enabled = os.getenv('TOOL_QUOTES_ENABLED', 'false').lower() == 'true'
        quotes_url = os.getenv('TOOL_QUOTES_API_URL', '')
        quotes_timeout = int(os.getenv('TOOL_QUOTES_TIMEOUT', '10'))
        
        if quotes_enabled and quotes_url:
            try:
                quotes_tool = QuotesTool(
                    api_url=quotes_url,
                    timeout=quotes_timeout,
                    enabled=True
                )
                self.tools.append(quotes_tool)
                logger.info(f"✓ Quotes tool registered: {quotes_url}")
            except Exception as e:
                logger.error(f"Failed to initialize quotes tool: {e}")
        elif quotes_enabled:
            logger.warning("Quotes tool enabled but TOOL_QUOTES_API_URL not configured")
        else:
            logger.debug("Quotes tool disabled in configuration")
        
        # Calendar Tool
        calendar_enabled = os.getenv('TOOL_CALENDAR_ENABLED', 'false').lower() == 'true'
        calendar_url = os.getenv('TOOL_CALENDAR_API_URL', '')
        calendar_timeout = int(os.getenv('TOOL_CALENDAR_TIMEOUT', '10'))
        
        if calendar_enabled and calendar_url:
            try:
                calendar_tool = CalendarTool(
                    api_url=calendar_url,
                    timeout=calendar_timeout,
                    enabled=True
                )
                self.tools.append(calendar_tool)
                logger.info(f"✓ Calendar tool registered: {calendar_url}")
            except Exception as e:
                logger.error(f"Failed to initialize calendar tool: {e}")
        elif calendar_enabled:
            logger.warning("Calendar tool enabled but TOOL_CALENDAR_API_URL not configured")
        else:
            logger.debug("Calendar tool disabled in configuration")
        
        # Add more tools here as needed...
        
        logger.info(f"Tool router initialized with {len(self.tools)} active tools")
    
    def get_active_tools(self) -> List[str]:
        """
        Get list of active tool names.
        
        Returns:
            List of tool names that are currently active
        """
        return [tool.name for tool in self.tools if tool.is_available()]
    
    async def route_query(self, query: str) -> Tuple[List[Dict[str, Any]], str]:
        """
        Analyze query and invoke appropriate tools.
        
        Args:
            query: User's query string
            
        Returns:
            Tuple of (tool_results, formatted_context)
            - tool_results: List of tool execution results
            - formatted_context: Formatted string to inject into LLM context
        """
        tool_results = []
        context_parts = []
        
        # Find tools that can handle this query
        matching_tools = [tool for tool in self.tools if tool.can_handle(query)]
        
        if not matching_tools:
            logger.debug(f"No tools matched query: {query[:100]}")
            return [], ""
        
        logger.info(f"Query matched {len(matching_tools)} tools: {[t.name for t in matching_tools]}")
        
        # Execute matching tools (can be parallelized for efficiency)
        for tool in matching_tools:
            try:
                logger.info(f"Executing {tool.name} tool...")
                result = await tool.execute(query)
                tool_results.append(result)
                
                # Format result for LLM context
                formatted = tool.format_for_llm(result)
                if formatted:
                    context_parts.append(formatted)
                    
                if result.get('success'):
                    logger.info(f"✓ {tool.name} tool executed successfully")
                else:
                    logger.warning(f"✗ {tool.name} tool failed: {result.get('error')}")
                    
            except Exception as e:
                logger.error(f"Error executing {tool.name} tool: {e}", exc_info=True)
                tool_results.append({
                    'success': False,
                    'error': str(e),
                    'data': None,
                    'metadata': {'tool': tool.name}
                })
        
        # Combine all tool contexts
        combined_context = "\n".join(context_parts) if context_parts else ""
        
        return tool_results, combined_context
    
    async def health_check_all(self) -> Dict[str, bool]:
        """
        Check health of all registered tools.
        
        Returns:
            Dictionary mapping tool names to health status
        """
        health_status = {}
        
        for tool in self.tools:
            try:
                is_healthy = await tool.health_check()
                health_status[tool.name] = is_healthy
            except Exception as e:
                logger.error(f"Health check failed for {tool.name}: {e}")
                health_status[tool.name] = False
        
        return health_status
    
    def get_tool_info(self) -> List[Dict[str, Any]]:
        """
        Get information about all registered tools.
        
        Returns:
            List of dictionaries with tool information
        """
        tool_info = []
        
        for tool in self.tools:
            info = {
                'name': tool.name,
                'description': tool.get_tool_description(),
                'enabled': tool.enabled,
                'available': tool.is_available(),
                'keywords': tool.get_intent_keywords()[:10]  # Sample keywords
            }
            tool_info.append(info)
        
        return tool_info


# Global router instance
_router_instance = None


def get_tool_router() -> ToolRouter:
    """
    Get the global tool router instance (singleton pattern).
    
    Returns:
        ToolRouter instance
    """
    global _router_instance
    
    if _router_instance is None:
        _router_instance = ToolRouter()
    
    return _router_instance


def reset_tool_router():
    """
    Reset the global tool router (useful for testing or config reload).
    """
    global _router_instance
    _router_instance = None
    logger.info("Tool router reset")
