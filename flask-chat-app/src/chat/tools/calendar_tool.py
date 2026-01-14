"""
Calendar Tool - Integration with Calendar API

This tool provides access to calendar events using the calendar-intelligence library.
Now acts as a thin wrapper around CalendarAnalyzer for integration with the chat application.
"""

import logging
from typing import Dict, Any, List
from .base_tool import BaseTool
from ..config import LOCAL_TIMEZONE

# Import the calendar-intelligence library
from calendar_intelligence import CalendarAnalyzer, IcsRepository

logger = logging.getLogger(__name__)


class CalendarTool(BaseTool):
    """
    Tool for retrieving calendar events from the calendar API.
    
    Now uses the calendar-intelligence library for all calendar logic,
    making it a thin integration layer for the chat application.
    """
    
    def __init__(self, api_url: str = None, timeout: int = 10, enabled: bool = True):
        """
        Initialize the calendar tool.
        
        Args:
            api_url: Base URL for Calendar API (e.g., https://ics.hlab.cam)
            timeout: Request timeout in seconds
            enabled: Whether this tool is enabled
        """
        super().__init__(enabled=enabled, api_url=api_url, timeout=timeout)
        
        # Initialize the calendar-intelligence library
        if api_url:
            repository = IcsRepository(api_url=api_url, timeout=timeout)
            self.analyzer = CalendarAnalyzer(
                repository=repository,
                timezone=LOCAL_TIMEZONE,
                enabled=enabled
            )
        else:
            self.analyzer = None
        
    def get_intent_keywords(self) -> List[str]:
        """Keywords that suggest calendar-related queries."""
        return [
            # Direct calendar terms
            'calendar', 'event', 'events', 'schedule', 'appointment', 'appointments',
            'meeting', 'meetings', 'agenda',
            
            # Time references
            'today', 'tomorrow', 'tonight', 'this week', 'next week', 'this month', 'next month',
            'upcoming', 'later', 'soon', 'coming up',
            
            # Questions
            'when', 'what time', 'do i have', 'am i busy', 'free', 'available',
            "what's on", "what's scheduled", "what's coming",
            
            # Actions
            'show me', 'check', 'list', 'tell me about', 'remind me'
        ]
    
    def can_handle(self, query: str) -> bool:
        """
        Determine if this tool should handle the message.
        
        Delegates to the calendar-intelligence library's intent detector.
        
        Args:
            query: The user's input message
            
        Returns:
            bool: True if message contains calendar-related keywords
        """
        if not self.enabled or not self.analyzer:
            return False
        
        return self.analyzer.can_handle(query)
    
    
    async def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Execute the calendar tool to fetch and analyze events.
        
        Delegates to the calendar-intelligence library's analyzer.
        
        Args:
            query: The user's query
            **kwargs: Additional parameters
            
        Returns:
            Dict with 'success', 'data', 'formatted_response', and metadata
        """
        if not self.enabled:
            return {
                'success': False,
                'error': 'Calendar tool is disabled'
            }
        
        if not self.analyzer:
            return {
                'success': False,
                'error': 'Calendar analyzer not configured (API URL required)'
            }
        
        try:
            # Use the calendar-intelligence library to analyze the query
            result = await self.analyzer.analyze(query)
            
            if not result['success']:
                return result
            
            # Adapt the library's response format to match what the chat app expects
            return {
                'success': True,
                'data': {
                    'events': result['events'],
                    'intent': result['intent']
                },
                'formatted_response': result['formatted_text'],
                'metadata': {
                    'tool': self.name,
                    **result['metadata']
                }
            }
            
        except Exception as e:
            logger.error(f"Unexpected error in calendar tool: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'metadata': {'tool': self.name}
            }
            
            # Format the response
            if endpoint == '/calendar/health':
                return {
                    'success': True,
                    'data': data,
                    'formatted_response': self._format_health_response(data),
                    'metadata': {
                        'tool': self.name,
                        'endpoint': endpoint
                    }
                }
            else:
                # Format all events - LLM will filter based on the query
                formatted_response = self._format_events_response(data, endpoint)
                
                return {
                    'success': True,
                    'data': data,
                    'formatted_response': formatted_response,
                    'metadata': {
                        'tool': self.name,
                        'endpoint': endpoint,
                        'event_count': len(data.get('events', []))
                    }
                }
    
    def format_for_llm(self, result: Dict[str, Any]) -> str:
        """
        Format the calendar result for the LLM.
        
        Uses the formatted_response from the library.
        """
        if not result.get('success'):
            return f"[Calendar tool error: {result.get('error', 'Unknown error')}]"
        
        # Use the formatted_response from the analyzer
        formatted = result.get('formatted_response', '')
        if formatted:
            return f"[Calendar Information]\n{formatted}"
        
        # Fallback to default
        return super().format_for_llm(result)
    
    def get_tool_description(self) -> str:
        """Return description of this tool for LLM context."""
        return """Calendar Tool: Retrieves calendar events and schedules.
        
Uses calendar-intelligence library to understand queries about:
- Today's/tomorrow's events
- Events in the next N days/weeks/months
- Finding specific events by name

Examples:
- "What's on my calendar today?"
- "Do I have any meetings tomorrow?"
- "Show me my events for the next 7 days"
- "When is my next dentist appointment?"
"""

