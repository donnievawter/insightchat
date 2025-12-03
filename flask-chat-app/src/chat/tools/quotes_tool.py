"""
Quotes Tool - Integration with RSS Quotes API

This tool provides inspirational quotes and content from RSS feeds.
Currently a placeholder - implement based on your RSS quotes API structure.
"""

from typing import Dict, Any, List
import requests
import logging
from .base_tool import BaseTool

logger = logging.getLogger(__name__)


class QuotesTool(BaseTool):
    """
    Tool for retrieving quotes from RSS feeds.
    
    This is a template implementation. Customize based on your
    RSS quotes API structure.
    """
    
    def __init__(self, api_url: str = None, timeout: int = 10, enabled: bool = True):
        """
        Initialize the quotes tool.
        
        Args:
            api_url: Base URL for RSS Quotes API
            timeout: Request timeout in seconds
            enabled: Whether this tool is enabled
        """
        super().__init__(enabled=enabled, api_url=api_url, timeout=timeout)
        self.api_url = api_url.rstrip('/') if api_url else None
        self.timeout = timeout
        
    def get_intent_keywords(self) -> List[str]:
        """Keywords that suggest quote-related queries."""
        return [
            'quote', 'quotes', 'quotation',
            'saying', 'proverb', 'wisdom',
            'inspiration', 'inspire', 'motivate', 'motivation',
            'famous saying', 'who said',
            'rss', 'feed', 'article'
        ]
    
    def can_handle(self, query: str) -> bool:
        """
        Determine if this query is quote-related.
        
        Args:
            query: User's query string
            
        Returns:
            True if this appears to be a quote query
        """
        if not self.is_available():
            return False
        
        query_lower = query.lower()
        
        # Check for intent keywords
        keywords = self.get_intent_keywords()
        for keyword in keywords:
            if keyword in query_lower:
                logger.info(f"Quotes tool matched keyword: {keyword}")
                return True
        
        return False
    
    async def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Execute quotes query against RSS Quotes API.
        
        NOTE: This is a placeholder implementation. Update based on your
        actual RSS quotes API structure.
        
        Args:
            query: User's query string
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with quote data or error information
        """
        if not self.is_available():
            return {
                'success': False,
                'error': 'Quotes tool is not available or not configured',
                'data': None,
                'metadata': {'tool': 'quotes'}
            }
        
        try:
            # Example implementation - customize for your API
            # Assuming your API has an endpoint like /api/quotes or /api/search
            endpoint = f"{self.api_url}/api/quotes"
            
            # Example: search for quotes matching the query
            params = {
                'query': query,
                'limit': 5  # Get a few relevant quotes
            }
            
            logger.info(f"Calling Quotes API: {endpoint}")
            logger.debug(f"Params: {params}")
            
            response = requests.get(
                endpoint,
                params=params,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Quotes API response received")
            
            # Adapt this based on your API's response structure
            quotes = data.get('quotes', [])
            
            if quotes:
                return {
                    'success': True,
                    'data': {
                        'quotes': quotes,
                        'count': len(quotes)
                    },
                    'error': None,
                    'metadata': {
                        'tool': 'quotes',
                        'api_url': self.api_url
                    }
                }
            else:
                return {
                    'success': False,
                    'error': 'No quotes found matching the query',
                    'data': None,
                    'metadata': {'tool': 'quotes'}
                }
            
        except requests.exceptions.Timeout:
            logger.error(f"Quotes API timeout after {self.timeout}s")
            return {
                'success': False,
                'error': f'Quotes API request timed out after {self.timeout} seconds',
                'data': None,
                'metadata': {'tool': 'quotes'}
            }
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Cannot connect to quotes API: {e}")
            return {
                'success': False,
                'error': f'Cannot connect to quotes service at {self.api_url}',
                'data': None,
                'metadata': {'tool': 'quotes'}
            }
        except requests.exceptions.HTTPError as e:
            logger.error(f"Quotes API HTTP error: {e}")
            return {
                'success': False,
                'error': f'Quotes API returned error: {response.status_code}',
                'data': None,
                'metadata': {'tool': 'quotes'}
            }
        except Exception as e:
            logger.error(f"Unexpected error in quotes tool: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'data': None,
                'metadata': {'tool': 'quotes'}
            }
    
    def format_for_llm(self, result: Dict[str, Any]) -> str:
        """
        Format quotes data for LLM context.
        
        Args:
            result: Result from execute()
            
        Returns:
            Formatted quotes for LLM
        """
        if not result.get('success'):
            return f"\n\n[Quotes unavailable: {result.get('error', 'Unknown error')}]"
        
        data = result.get('data', {})
        quotes = data.get('quotes', [])
        
        if not quotes:
            return "\n\n[No quotes found]"
        
        # Format quotes for LLM context
        formatted = "\n\n---\nRELEVANT QUOTES:\n"
        
        for i, quote in enumerate(quotes, 1):
            # Adapt this based on your quote structure
            # Example assumes: {'text': '...', 'author': '...', 'source': '...'}
            text = quote.get('text', quote.get('content', ''))
            author = quote.get('author', 'Unknown')
            source = quote.get('source', '')
            
            formatted += f"\n{i}. \"{text}\"\n   - {author}"
            if source:
                formatted += f" ({source})"
            formatted += "\n"
        
        formatted += "\n---\n\nUse the quotes above to help answer the user's question.\n"
        return formatted
    
    def get_required_config(self) -> List[str]:
        """Required configuration keys for quotes tool."""
        return ['api_url']
    
    def get_tool_description(self) -> str:
        """Get description of quotes tool."""
        return "Quotes tool - provides inspirational quotes and content from RSS feeds"
    
    async def health_check(self) -> bool:
        """
        Check if Quotes API is reachable.
        
        Returns:
            True if the API is healthy
        """
        if not self.is_available():
            return False
        
        try:
            # Try to hit a health or status endpoint
            # Adjust based on your API structure
            endpoint = f"{self.api_url}/health"
            response = requests.get(endpoint, timeout=5)
            response.raise_for_status()
            return True
            
        except Exception as e:
            logger.warning(f"Quotes API health check failed: {e}")
            return False
