"""
Base Repository Interface for Calendar Data Sources

Defines the abstract interface that all calendar repositories must implement.
This allows the CalendarAnalyzer to work with any calendar provider (ICS, Google, Nextcloud, etc.)
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime


class CalendarRepository(ABC):
    """
    Abstract base class for calendar data sources.
    
    Implementations should:
    1. Handle authentication/connection to their specific calendar provider
    2. Fetch events in the required formats
    3. Return events in a standardized structure
    4. Handle errors gracefully
    """
    
    @abstractmethod
    async def get_events_today(self) -> List[Dict[str, Any]]:
        """
        Fetch all events for today.
        
        Returns:
            List of event dictionaries with keys:
            - summary: str (event title)
            - start: str (YYYY-MM-DD HH:MM format)
            - end: str (YYYY-MM-DD HH:MM format)
            - location: str (optional)
            - description: str (optional)
        """
        pass
    
    @abstractmethod
    async def get_events_tomorrow(self) -> List[Dict[str, Any]]:
        """
        Fetch all events for tomorrow.
        
        Returns:
            List of event dictionaries (same structure as get_events_today)
        """
        pass
    
    @abstractmethod
    async def get_events_next_n_days(self, days: int) -> List[Dict[str, Any]]:
        """
        Fetch all events for the next N days.
        
        Args:
            days: Number of days to fetch (e.g., 7 for next week, 30 for next month)
            
        Returns:
            List of event dictionaries (same structure as get_events_today)
        """
        pass
    
    @abstractmethod
    async def get_health(self) -> Dict[str, Any]:
        """
        Check if the calendar service is available.
        
        Returns:
            Dictionary with 'status' key (e.g., {'status': 'healthy'})
        """
        pass
    
    def get_source_name(self) -> str:
        """
        Get the name of this calendar source.
        
        Returns:
            Name identifier (e.g., 'ics', 'google', 'nextcloud')
        """
        return self.__class__.__name__.replace('Repository', '').lower()
