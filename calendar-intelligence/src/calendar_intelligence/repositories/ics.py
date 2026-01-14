"""
ICS Calendar Repository

Implements CalendarRepository for ICS/iCal-based calendar services
(like ics.hlab.cam or any other ICS API endpoint).
"""

import logging
from typing import List, Dict, Any
import requests

from .base import CalendarRepository

logger = logging.getLogger(__name__)


class IcsRepository(CalendarRepository):
    """
    Repository for ICS-based calendar APIs.
    
    Compatible with APIs that provide endpoints like:
    - /calendar/events/today
    - /calendar/events/tomorrow
    - /calendar/events/next/{days}
    - /calendar/health
    """
    
    def __init__(self, api_url: str, timeout: int = 10):
        """
        Initialize the ICS repository.
        
        Args:
            api_url: Base URL for the ICS API (e.g., https://ics.hlab.cam)
            timeout: Request timeout in seconds
        """
        self.api_url = api_url.rstrip('/')
        self.timeout = timeout
        
    async def get_events_today(self) -> List[Dict[str, Any]]:
        """Fetch today's events from the ICS API."""
        return await self._fetch_events('/calendar/events/today')
    
    async def get_events_tomorrow(self) -> List[Dict[str, Any]]:
        """Fetch tomorrow's events from the ICS API."""
        return await self._fetch_events('/calendar/events/tomorrow')
    
    async def get_events_next_n_days(self, days: int) -> List[Dict[str, Any]]:
        """Fetch events for the next N days from the ICS API."""
        return await self._fetch_events(f'/calendar/events/next/{days}')
    
    async def get_health(self) -> Dict[str, Any]:
        """Check ICS API health status."""
        try:
            url = f"{self.api_url}/calendar/health"
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"ICS API health check failed: {e}")
            return {'status': 'unhealthy', 'error': str(e)}
    
    async def _fetch_events(self, endpoint: str) -> List[Dict[str, Any]]:
        """
        Internal method to fetch events from a specific endpoint.
        
        Args:
            endpoint: API endpoint path (e.g., '/calendar/events/today')
            
        Returns:
            List of event dictionaries
            
        Raises:
            requests.exceptions.RequestException: If API call fails
        """
        url = f"{self.api_url}{endpoint}"
        logger.info(f"Fetching events from ICS API: {url}")
        
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            events = data.get('events', [])
            logger.info(f"Retrieved {len(events)} events from {endpoint}")
            return events
            
        except requests.exceptions.Timeout:
            logger.error(f"ICS API timeout after {self.timeout}s for {endpoint}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"ICS API error for {endpoint}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching from {endpoint}: {e}", exc_info=True)
            raise
