"""
Weather Tool - Integration with PyWeather API

This tool provides current weather conditions and forecasts by calling
the PyWeather API service.
"""

import re
from typing import Dict, Any, List
import requests
import logging
from .base_tool import BaseTool

logger = logging.getLogger(__name__)


class WeatherTool(BaseTool):
    """
    Tool for retrieving weather information from PyWeather API.
    
    Handles queries about:
    - Current temperature, conditions
    - Weather forecasts
    - Specific weather metrics (humidity, wind, pressure, etc.)
    """
    
    def __init__(self, api_url: str = None, timeout: int = 10, enabled: bool = True):
        """
        Initialize the weather tool.
        
        Args:
            api_url: Base URL for PyWeather API (e.g., http://localhost:8000)
            timeout: Request timeout in seconds
            enabled: Whether this tool is enabled
        """
        super().__init__(enabled=enabled, api_url=api_url, timeout=timeout)
        self.api_url = api_url.rstrip('/') if api_url else None
        self.timeout = timeout
        
    def get_intent_keywords(self) -> List[str]:
        """Keywords that suggest weather-related queries."""
        return [
            # Direct weather terms
            'weather', 'temperature', 'temp', 'forecast',
            'rain', 'raining', 'sunny', 'cloudy', 'snow', 'snowing',
            'wind', 'windy', 'humidity', 'humid',
            'hot', 'cold', 'warm', 'cool', 'freezing',
            
            # Weather metrics
            'degrees', 'fahrenheit', 'celsius',
            'precipitation', 'pressure', 'barometric',
            'uv', 'uv index', 'sunshine',
            
            # Weather questions
            'outside', 'outdoors',
            'umbrella', 'jacket', 'coat', 'shorts',
            'what.*like outside', 'how.*outside',
            
            # Tempest specific
            'tempest', 'station', 'sensor'
        ]
    
    def can_handle(self, query: str) -> bool:
        """
        Determine if this query is weather-related.
        
        Args:
            query: User's query string
            
        Returns:
            True if this appears to be a weather query
        """
        if not self.is_available():
            return False
        
        query_lower = query.lower()
        
        # Check for intent keywords
        keywords = self.get_intent_keywords()
        for keyword in keywords:
            # Use regex for pattern-based keywords
            if '.*' in keyword:
                if re.search(keyword, query_lower):
                    logger.info(f"Weather tool matched pattern: {keyword}")
                    return True
            # Direct string match for simple keywords
            elif keyword in query_lower:
                logger.info(f"Weather tool matched keyword: {keyword}")
                return True
        
        return False
    
    async def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Execute weather query against PyWeather API.
        
        Args:
            query: User's query string
            **kwargs: Additional parameters (unused)
            
        Returns:
            Dictionary with weather data or error information
        """
        if not self.is_available():
            return {
                'success': False,
                'error': 'Weather tool is not available or not configured',
                'data': None,
                'metadata': {'tool': 'weather'}
            }
        
        try:
            # Use the PyWeather /weather/query endpoint for natural language queries
            endpoint = f"{self.api_url}/weather/query"
            
            payload = {
                "prompt": query,
                "include_current": True,
                "include_forecast": True,
                "broadcast": False  # Don't broadcast to TTS
            }
            
            logger.info(f"Calling PyWeather API: {endpoint}")
            logger.debug(f"Payload: {payload}")
            
            response = requests.post(
                endpoint,
                json=payload,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"PyWeather API response received: {data.get('success', False)}")
            
            if data.get('success'):
                return {
                    'success': True,
                    'data': {
                        'response': data.get('response_text', ''),
                        'timestamp': data.get('timestamp', '')
                    },
                    'error': None,
                    'metadata': {
                        'tool': 'weather',
                        'api_url': self.api_url,
                        'includes_forecast': True,
                        'includes_current': True
                    }
                }
            else:
                return {
                    'success': False,
                    'error': data.get('message', 'Unknown error from weather API'),
                    'data': None,
                    'metadata': {'tool': 'weather'}
                }
            
        except requests.exceptions.Timeout:
            logger.error(f"Weather API timeout after {self.timeout}s")
            return {
                'success': False,
                'error': f'Weather API request timed out after {self.timeout} seconds',
                'data': None,
                'metadata': {'tool': 'weather'}
            }
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Cannot connect to weather API: {e}")
            return {
                'success': False,
                'error': f'Cannot connect to weather service at {self.api_url}',
                'data': None,
                'metadata': {'tool': 'weather'}
            }
        except requests.exceptions.HTTPError as e:
            logger.error(f"Weather API HTTP error: {e}")
            return {
                'success': False,
                'error': f'Weather API returned error: {response.status_code}',
                'data': None,
                'metadata': {'tool': 'weather'}
            }
        except Exception as e:
            logger.error(f"Unexpected error in weather tool: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'data': None,
                'metadata': {'tool': 'weather'}
            }
    
    def format_for_llm(self, result: Dict[str, Any]) -> str:
        """
        Format weather data for LLM context.
        
        Args:
            result: Result from execute()
            
        Returns:
            Formatted weather information for LLM
        """
        if not result.get('success'):
            return f"\n\n[Weather data unavailable: {result.get('error', 'Unknown error')}]"
        
        data = result.get('data', {})
        weather_response = data.get('response', '')
        timestamp = data.get('timestamp', '')
        
        # Format for LLM context
        formatted = f"""

---
WEATHER INFORMATION (from PyWeather):
{weather_response}

Timestamp: {timestamp}
---

Use the weather information above to answer the user's question about weather conditions.
"""
        return formatted
    
    def get_required_config(self) -> List[str]:
        """Required configuration keys for weather tool."""
        return ['api_url']
    
    def get_tool_description(self) -> str:
        """Get description of weather tool."""
        return "Weather tool - provides current conditions and forecasts from PyWeather API"
    
    async def health_check(self) -> bool:
        """
        Check if PyWeather API is reachable.
        
        Returns:
            True if the API is healthy
        """
        if not self.is_available():
            return False
        
        try:
            # Try to hit the status endpoint
            endpoint = f"{self.api_url}/weather/status"
            response = requests.get(endpoint, timeout=5)
            response.raise_for_status()
            
            # Check if we got a valid response
            data = response.json()
            logger.info(f"Weather API health check: {data}")
            return True
            
        except Exception as e:
            logger.warning(f"Weather API health check failed: {e}")
            return False
