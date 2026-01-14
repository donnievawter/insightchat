"""
Calendar Analyzer - Main orchestration of calendar intelligence

Combines intent detection, data fetching, and formatting to provide
calendar analysis capabilities to any application.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from .intent import IntentDetector
from .formatter import EventFormatter
from .repositories.base import CalendarRepository

logger = logging.getLogger(__name__)


class CalendarAnalyzer:
    """
    Main calendar intelligence service.
    
    Orchestrates:
    1. Query intent detection
    2. Data fetching from repository
    3. Event formatting for consumption
    
    Usage:
        repository = IcsRepository(api_url="https://ics.hlab.cam")
        analyzer = CalendarAnalyzer(repository=repository)
        result = await analyzer.analyze("What's on my calendar today?")
    """
    
    def __init__(
        self,
        repository: CalendarRepository,
        timezone: str = "America/Denver",
        enabled: bool = True
    ):
        """
        Initialize the analyzer.
        
        Args:
            repository: Calendar data source implementation
            timezone: IANA timezone for displaying event times
            enabled: Whether the analyzer is enabled
        """
        self.repository = repository
        self.enabled = enabled
        self.intent_detector = IntentDetector()
        self.formatter = EventFormatter(timezone=timezone)
        self.timezone = timezone
    
    def can_handle(self, query: str) -> bool:
        """
        Determine if this analyzer should handle the query.
        
        Args:
            query: User's natural language query
            
        Returns:
            True if the query appears to be calendar-related
        """
        if not self.enabled:
            return False
        
        return self.intent_detector.can_handle(query)
    
    async def analyze(self, query: str) -> Dict[str, Any]:
        """
        Analyze a calendar-related query.
        
        Args:
            query: Natural language query about calendar/events
            
        Returns:
            Dictionary with:
            - success: bool
            - intent: Detected intent details
            - events: List of event dictionaries
            - formatted_text: Human-readable text response
            - metadata: Additional info (event_count, data_source, etc.)
            - error: Error message (if success=False)
        """
        if not self.enabled:
            return {
                'success': False,
                'error': 'Calendar analyzer is disabled'
            }
        
        try:
            # Detect user intent
            intent = self.intent_detector.detect(query)
            logger.info(f"Detected intent: {intent}")
            
            # Fetch events based on intent
            events = await self._fetch_events_for_intent(intent)
            
            # Filter events if search term present
            if 'search_term' in intent and intent['search_term']:
                events = self._filter_events(events, intent['search_term'])
            
            # Format events for display
            formatted_text = self.formatter.format_events(
                events=events,
                timeframe=intent.get('timeframe', 'upcoming'),
                search_term=intent.get('search_term')
            )
            
            # Calculate date range for metadata
            date_range = self._calculate_date_range(intent)
            
            return {
                'success': True,
                'intent': {
                    **intent,
                    'date_range': date_range
                },
                'events': events,
                'formatted_text': formatted_text,
                'metadata': {
                    'event_count': len(events),
                    'data_source': self.repository.get_source_name(),
                    'timezone': self.timezone
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing calendar query: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Calendar analysis failed: {str(e)}',
                'metadata': {
                    'data_source': self.repository.get_source_name()
                }
            }
    
    async def check_health(self) -> Dict[str, Any]:
        """
        Check if the calendar service is healthy.
        
        Returns:
            Health status dictionary
        """
        try:
            health = await self.repository.get_health()
            return {
                'success': True,
                'data': health,
                'formatted_text': f"Calendar service status: {health.get('status', 'unknown')}"
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _fetch_events_for_intent(self, intent: Dict[str, Any]) -> list:
        """
        Fetch events from repository based on detected intent.
        
        Args:
            intent: Intent dictionary from IntentDetector
            
        Returns:
            List of event dictionaries
        """
        intent_type = intent.get('type')
        
        if intent_type == 'events_today':
            return await self.repository.get_events_today()
        
        elif intent_type == 'events_tomorrow':
            return await self.repository.get_events_tomorrow()
        
        elif intent_type in ['events_next_n_days', 'find_next_event']:
            days = intent.get('days', 7)
            return await self.repository.get_events_next_n_days(days)
        
        else:
            # Default to next 7 days
            logger.warning(f"Unknown intent type '{intent_type}', defaulting to next 7 days")
            return await self.repository.get_events_next_n_days(7)
    
    def _filter_events(self, events: list, search_term: str) -> list:
        """
        Filter events by search term.
        
        Args:
            events: List of event dictionaries
            search_term: Term to search for in event summaries
            
        Returns:
            Filtered list of matching events
        """
        if not search_term:
            return events
        
        search_lower = search_term.lower()
        return [
            event for event in events
            if search_lower in event.get('summary', '').lower()
        ]
    
    def _calculate_date_range(self, intent: Dict[str, Any]) -> Dict[str, str]:
        """
        Calculate the date range for the intent.
        
        Args:
            intent: Intent dictionary
            
        Returns:
            Dictionary with 'start' and 'end' date strings (YYYY-MM-DD)
        """
        today = datetime.now().date()
        intent_type = intent.get('type')
        
        if intent_type == 'events_today':
            return {
                'start': today.strftime('%Y-%m-%d'),
                'end': today.strftime('%Y-%m-%d')
            }
        
        elif intent_type == 'events_tomorrow':
            tomorrow = today + timedelta(days=1)
            return {
                'start': tomorrow.strftime('%Y-%m-%d'),
                'end': tomorrow.strftime('%Y-%m-%d')
            }
        
        elif intent_type in ['events_next_n_days', 'find_next_event']:
            days = intent.get('days', 7)
            end_date = today + timedelta(days=days)
            return {
                'start': today.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d')
            }
        
        else:
            # Default to next 7 days
            end_date = today + timedelta(days=7)
            return {
                'start': today.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d')
            }
