"""
Calendar Tool - Integration with Calendar API

This tool provides access to calendar events by calling the calendar API service.
"""

import re
import os
from typing import Dict, Any, List
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
import logging
from .base_tool import BaseTool
from ..config import LOCAL_TIMEZONE

logger = logging.getLogger(__name__)


class CalendarTool(BaseTool):
    """
    Tool for retrieving calendar events from the calendar API.
    
    Handles queries about:
    - All events
    - Today's events
    - Tomorrow's events
    - Events in the next N days
    - Calendar health status
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
        self.api_url = api_url.rstrip('/') if api_url else None
        self.timeout = timeout
        
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
        
        Args:
            query: The user's input message
            
        Returns:
            bool: True if message contains calendar-related keywords
        """
        if not self.enabled or not self.api_url:
            return False
            
        message_lower = query.lower()
        
        # Primary calendar indicators - if any of these are present, it's definitely a calendar query
        primary_keywords = [
            'calendar', 'event', 'events', 'schedule', 'appointment', 'appointments',
            'meeting', 'meetings', 'agenda', 'today', 'tomorrow', 'tonight',
            'this week', 'next week', 'this month', 'next month'
        ]
        
        for keyword in primary_keywords:
            if keyword in message_lower:
                return True
        
        # Secondary keywords - only match if combined with calendar context
        # Check if query is asking about time/scheduling (not documents)
        if any(word in message_lower for word in ['when', 'what time', 'am i busy', 'free', 'available']):
            # Exclude if asking about documents/files
            if not any(word in message_lower for word in ['document', 'file', 'pdf', 'email', 'attachment']):
                return True
        
        # Match "when is the next" or "when is my next" patterns
        if re.search(r'when\s+is\s+(the|my)\s+next', message_lower):
            return True
        
        return False
    
    def _determine_endpoint(self, user_message: str) -> tuple[str, Dict[str, Any]]:
        """
        Determine which calendar endpoint to call based on the message.
        
        Returns:
            tuple: (endpoint_path, params_dict)
        """
        message_lower = user_message.lower()
        
        # Check for "when is the next X" or "when is my next X" pattern
        # Return next 30 days of events - LLM will filter based on search term
        next_event_pattern = re.search(r'when\s+is\s+(the|my)\s+next', message_lower)
        if next_event_pattern:
            return '/calendar/events/next/30', {}
        
        # Word to number mapping for text numbers
        word_to_num = {
            'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
        }
        
        # Check for "next N weeks" (with number or word)
        next_weeks_digit = re.search(r'next\s+(\d+)\s+weeks?', message_lower)
        next_weeks_word = re.search(r'next\s+(one|two|three|four|five|six|seven|eight|nine|ten)\s+weeks?', message_lower)
        
        if next_weeks_digit:
            weeks = int(next_weeks_digit.group(1))
            days = weeks * 7
            return f'/calendar/events/next/{days}', {}
        elif next_weeks_word:
            week_word = next_weeks_word.group(1)
            weeks = word_to_num.get(week_word, 1)
            days = weeks * 7
            return f'/calendar/events/next/{days}', {}
        
        # Check for "next N days" (with number or word)
        next_days_digit = re.search(r'next\s+(\d+)\s+days?', message_lower)
        next_days_word = re.search(r'next\s+(one|two|three|four|five|six|seven|eight|nine|ten)\s+days?', message_lower)
        
        if next_days_digit:
            days = next_days_digit.group(1)
            return f'/calendar/events/next/{days}', {}
        elif next_days_word:
            day_word = next_days_word.group(1)
            days = word_to_num.get(day_word, 1)
            return f'/calendar/events/next/{days}', {}
        
        # Check for "next month"
        if 'next month' in message_lower:
            return f'/calendar/events/next/30', {}
        
        # Check for "this week"
        if 'this week' in message_lower:
            return '/calendar/events/next/7', {}
        
        # Check for "next week" (singular - just one week from now)
        if 'next week' in message_lower and 'weeks' not in message_lower:
            return '/calendar/events/next/14', {}
        
        # Check for tomorrow
        if 'tomorrow' in message_lower:
            return '/calendar/events/tomorrow', {}
        
        # Check for today
        if 'today' in message_lower or 'tonight' in message_lower:
            return '/calendar/events/today', {}
        
        # Default to next 7 days (includes recurring events)
        # This is better than /calendar/events which doesn't expand recurring events
        return '/calendar/events/next/7', {}
    
    async def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Execute the calendar tool to fetch events.
        
        Args:
            query: The user's query
            **kwargs: Additional parameters
            
        Returns:
            Dict with 'success', 'data', and optional 'error' keys
        """
        if not self.enabled:
            return {
                'success': False,
                'error': 'Calendar tool is disabled'
            }
        
        if not self.api_url:
            return {
                'success': False,
                'error': 'Calendar API URL not configured'
            }
        
        try:
            # Determine which endpoint to call
            endpoint, params = self._determine_endpoint(query)
            url = f"{self.api_url}{endpoint}"
            
            logger.info(f"Calling calendar API: {url}")
            
            # Make the API request
            response = requests.get(
                url,
                params=params,
                timeout=self.timeout
            )
            
            # Store search term for filtering if present
            search_term = params.get('search')
            
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Calendar API response from {endpoint}: {data}")
            
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
            
        except requests.exceptions.Timeout:
            logger.error(f"Calendar API timeout after {self.timeout}s")
            return {
                'success': False,
                'error': f'Calendar API request timed out after {self.timeout} seconds',
                'metadata': {'tool': self.name}
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Calendar API error: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to fetch calendar data: {str(e)}',
                'metadata': {'tool': self.name}
            }
        except Exception as e:
            logger.error(f"Unexpected error in calendar tool: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'metadata': {'tool': self.name}
            }
    
    def _format_health_response(self, data: Dict[str, Any]) -> str:
        """Format health check response."""
        status = data.get('status', 'unknown')
        return f"Calendar API Status: {status}"
    
    def _format_next_event_response(self, data: Dict[str, Any], search_term: str, original_query: str) -> str:
        """
        Format response for 'when is the next X' queries.
        Filters events by search term and returns the first match.
        
        Args:
            data: API response data with events
            search_term: Term to search for in event summaries
            original_query: Original user query
            
        Returns:
            Formatted string with the next matching event
        """
        from html import unescape
        
        events = data.get('events', [])
        
        if not events:
            return f"No events found in the next 30 days matching '{search_term}'."
        
        # Filter events by search term (case-insensitive)
        matching_events = [
            event for event in events
            if search_term.lower() in event.get('summary', '').lower()
        ]
        
        if not matching_events:
            return f"No events found in the next 30 days matching '{search_term}'."
        
        # Get the first (next) matching event
        event = matching_events[0]
        summary = event.get('summary', 'Untitled Event')
        start = event.get('start', '')
        end = event.get('end', '')
        location = event.get('location', '')
        description = event.get('description', '')
        
        # Format the response
        result = f"Your next '{search_term}' event:\n\n"
        result += f"📌 {summary}\n"
        
        # Format time
        if start:
            try:
                local_tz = ZoneInfo(LOCAL_TIMEZONE)
                start_dt = datetime.strptime(start, '%Y-%m-%d %H:%M')
                start_dt = start_dt.replace(tzinfo=local_tz)
                
                # Show full date since this could be weeks away
                date_str = start_dt.strftime('%A, %B %-d, %Y')
                result += f"📅 {date_str}\n"
                
                if end:
                    end_dt = datetime.strptime(end, '%Y-%m-%d %H:%M')
                    end_dt = end_dt.replace(tzinfo=local_tz)
                    time_str = f"{start_dt.strftime('%-I:%M %p')} - {end_dt.strftime('%-I:%M %p %Z')}"
                else:
                    time_str = start_dt.strftime('%-I:%M %p %Z')
                
                result += f"🕒 {time_str}\n"
            except Exception as e:
                logger.warning(f"Could not parse time '{start}': {e}")
                result += f"🕒 {start}\n"
        
        if location:
            result += f"📍 {location}\n"
        
        if description:
            # Clean HTML tags and decode entities
            clean_desc = re.sub(r'<[^>]+>', '', description)
            clean_desc = unescape(clean_desc).strip()
            if clean_desc and len(clean_desc) < 200:
                result += f"\n{clean_desc}"
        
        return result
    
    def _format_events_response(self, data: Dict[str, Any], endpoint: str) -> str:
        """
        Format calendar events into a readable response.
        
        Args:
            data: API response data
            endpoint: The endpoint that was called
            
        Returns:
            Formatted string response
        """
        import re
        from html import unescape
        
        events = data.get('events', [])
        
        if not events:
            if 'today' in endpoint:
                return "You have no events scheduled for today."
            elif 'tomorrow' in endpoint:
                return "You have no events scheduled for tomorrow."
            elif 'next/7' in endpoint:
                return "You have no events scheduled for the next week."
            elif 'next' in endpoint:
                return "You have no upcoming events."
            else:
                return "No events found."
        
        # Determine time context for header based on endpoint
        if 'today' in endpoint:
            header = f"You have {len(events)} event(s) today:"
        elif 'tomorrow' in endpoint:
            header = f"You have {len(events)} event(s) tomorrow:"
        elif 'next/7' in endpoint:
            header = f"You have {len(events)} event(s) in the next week:"
        elif 'next/14' in endpoint:
            header = f"You have {len(events)} event(s) in the next 2 weeks:"
        elif 'next/30' in endpoint:
            header = f"You have {len(events)} event(s) in the next month:"
        elif 'next' in endpoint:
            # Extract days from endpoint like /next/21
            days_match = re.search(r'next/(\d+)', endpoint)
            if days_match:
                days = days_match.group(1)
                header = f"You have {len(events)} event(s) in the next {days} days:"
            else:
                header = f"You have {len(events)} upcoming event(s):"
        else:
            header = f"Found {len(events)} event(s):"
        
        # Format each event
        event_lines = [header, ""]
        
        for event in events:
            summary = event.get('summary', 'Untitled Event')
            start = event.get('start', '')
            end = event.get('end', '')
            location = event.get('location', '')
            description = event.get('description', '')
            
            # Format time - API returns times already in local timezone
            time_str = ""
            date_str = ""
            if start:
                try:
                    # Use configured local timezone for display
                    local_tz = ZoneInfo(LOCAL_TIMEZONE)
                    
                    # Parse start time (format: "2025-12-03 21:00")
                    # Note: API already returns times in local timezone, no conversion needed
                    start_dt = datetime.strptime(start, '%Y-%m-%d %H:%M')
                    start_dt = start_dt.replace(tzinfo=local_tz)
                    
                    # Determine if we need to show the date
                    # For today/tomorrow endpoints, date is implied
                    # For multi-day views, always show date
                    show_date = 'today' not in endpoint and 'tomorrow' not in endpoint
                    
                    if show_date:
                        # Show day of week and date: "Monday, Dec 9"
                        date_str = f"📅 {start_dt.strftime('%A, %b %-d')}"
                    
                    if end:
                        # Parse end time (also already in local timezone)
                        end_dt = datetime.strptime(end, '%Y-%m-%d %H:%M')
                        end_dt = end_dt.replace(tzinfo=local_tz)
                        
                        # Format: "10:00 AM - 11:00 AM MST"
                        time_str = f"🕒 {start_dt.strftime('%-I:%M %p')} - {end_dt.strftime('%-I:%M %p %Z')}"
                    else:
                        time_str = f"🕒 {start_dt.strftime('%-I:%M %p %Z')}"
                except Exception as e:
                    logger.warning(f"Could not parse time '{start}': {e}")
                    # Fallback to original format
                    start_parts = start.split(' ')
                    if len(start_parts) == 2:
                        date_str = f"📅 {start_parts[0]}"
                        time_str = f"🕒 {start_parts[1]}"
                    else:
                        time_str = f"🕒 {start}"
            
            event_lines.append(f"**{summary}**")
            if date_str:
                event_lines.append(f"  {date_str}")
            if time_str:
                event_lines.append(f"  {time_str}")
            if location:
                event_lines.append(f"  📍 {location}")
            if description:
                # Clean HTML from description
                desc_clean = re.sub(r'<[^>]+>', '', description)  # Remove HTML tags
                desc_clean = unescape(desc_clean)  # Unescape HTML entities
                desc_clean = re.sub(r'\s+', ' ', desc_clean).strip()  # Normalize whitespace
                
                # Extract key info (like Zoom links)
                zoom_match = re.search(r'(https://[^\s]+zoom[^\s]+)', description)
                if zoom_match:
                    zoom_url = zoom_match.group(1)
                    event_lines.append(f"  🔗 Zoom: {zoom_url}")
                
                # Only include description if it's not too long and not just HTML
                if desc_clean and len(desc_clean) < 500 and not desc_clean.startswith('Hi there'):
                    desc = desc_clean[:200] + "..." if len(desc_clean) > 200 else desc_clean
                    event_lines.append(f"  ℹ️ {desc}")
            event_lines.append("")  # Blank line between events
        
        return "\n".join(event_lines)
    
    def format_for_llm(self, result: Dict[str, Any]) -> str:
        """
        Format the calendar result for the LLM.
        
        Uses the pre-formatted response if available, otherwise falls back to base implementation.
        """
        if not result.get('success'):
            return f"[Calendar tool error: {result.get('error', 'Unknown error')}]"
        
        # Use the formatted_response if available
        formatted = result.get('formatted_response', '')
        if formatted:
            return f"[Calendar Information]\n{formatted}"
        
        # Fallback to default
        return super().format_for_llm(result)
    
    def get_tool_description(self) -> str:
        """Return description of this tool for LLM context."""
        return """Calendar Tool: Retrieves calendar events and schedules.
        
Available endpoints:
- All events: /calendar/events
- Today's events: /calendar/events/today
- Tomorrow's events: /calendar/events/tomorrow
- Next N days: /calendar/events/next/{days}
- Health check: /calendar/health

Use this tool when users ask about:
- Their schedule or calendar
- Events today, tomorrow, or upcoming
- Meetings or appointments
- What's on their agenda

Examples:
- "What's on my calendar today?"
- "Do I have any meetings tomorrow?"
- "Show me my events for the next 7 days"
"""
