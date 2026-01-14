"""
Event Formatter - Formats calendar events for display

Provides human-readable formatting of calendar events with support for:
- Single events vs event lists
- Different time contexts (today, tomorrow, next week, etc.)
- Time zones
- HTML cleanup in descriptions
"""

import re
import logging
from html import unescape
from typing import List, Dict, Any
from datetime import datetime
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)


class EventFormatter:
    """Formats calendar events into human-readable text."""
    
    def __init__(self, timezone: str = "America/Denver"):
        """
        Initialize the formatter.
        
        Args:
            timezone: IANA timezone name for displaying times
        """
        self.timezone = timezone
        self.local_tz = ZoneInfo(timezone)
    
    def format_events(
        self,
        events: List[Dict[str, Any]],
        timeframe: str,
        search_term: str = None
    ) -> str:
        """
        Format a list of events into a readable string.
        
        Args:
            events: List of event dictionaries
            timeframe: Description of timeframe (e.g., "today", "next 7 days")
            search_term: Optional search term used for filtering
            
        Returns:
            Formatted string suitable for display or TTS
        """
        if not events:
            return self._format_no_events(timeframe, search_term)
        
        if search_term:
            # For specific searches, show just the next matching event
            return self._format_next_event(events[0], search_term)
        
        # Format multiple events
        return self._format_event_list(events, timeframe)
    
    def _format_no_events(self, timeframe: str, search_term: str = None) -> str:
        """Format message when no events are found."""
        if search_term:
            return f"No events found matching '{search_term}' in the {timeframe}."
        
        if timeframe == 'today':
            return "You have no events scheduled for today."
        elif timeframe == 'tomorrow':
            return "You have no events scheduled for tomorrow."
        elif 'week' in timeframe:
            return f"You have no events scheduled for the {timeframe}."
        else:
            return f"You have no events in the {timeframe}."
    
    def _format_next_event(self, event: Dict[str, Any], search_term: str) -> str:
        """Format a single event (for 'when is next X' queries)."""
        summary = event.get('summary', 'Untitled Event')
        start = event.get('start', '')
        end = event.get('end', '')
        location = event.get('location', '')
        description = event.get('description', '')
        
        result = f"Your next '{search_term}' event:\n\n"
        result += f"📌 {summary}\n"
        
        # Format time
        if start:
            try:
                start_dt = datetime.strptime(start, '%Y-%m-%d %H:%M')
                start_dt = start_dt.replace(tzinfo=self.local_tz)
                
                # Show full date since this could be weeks away
                date_str = start_dt.strftime('%A, %B %-d, %Y')
                result += f"📅 {date_str}\n"
                
                if end:
                    end_dt = datetime.strptime(end, '%Y-%m-%d %H:%M')
                    end_dt = end_dt.replace(tzinfo=self.local_tz)
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
            clean_desc = self._clean_description(description)
            if clean_desc and len(clean_desc) < 200:
                result += f"\n{clean_desc}"
        
        return result
    
    def _format_event_list(self, events: List[Dict[str, Any]], timeframe: str) -> str:
        """Format multiple events into a list."""
        count = len(events)
        
        # Create header based on timeframe
        if timeframe == 'today':
            header = f"You have {count} event{'s' if count != 1 else ''} today:"
        elif timeframe == 'tomorrow':
            header = f"You have {count} event{'s' if count != 1 else ''} tomorrow:"
        elif 'week' in timeframe:
            header = f"You have {count} event{'s' if count != 1 else ''} {timeframe}:"
        else:
            header = f"You have {count} event{'s' if count != 1 else ''} in the {timeframe}:"
        
        event_lines = [header, ""]
        
        # Determine if we should show dates
        show_dates = timeframe not in ['today', 'tomorrow']
        
        for event in events:
            event_lines.extend(self._format_single_event(event, show_dates))
            event_lines.append("")  # Blank line between events
        
        return "\n".join(event_lines)
    
    def _format_single_event(self, event: Dict[str, Any], show_date: bool = True) -> List[str]:
        """Format a single event as a list of lines."""
        lines = []
        
        summary = event.get('summary', 'Untitled Event')
        start = event.get('start', '')
        end = event.get('end', '')
        location = event.get('location', '')
        description = event.get('description', '')
        
        lines.append(f"**{summary}**")
        
        # Format time - API returns times already in local timezone
        if start:
            try:
                start_dt = datetime.strptime(start, '%Y-%m-%d %H:%M')
                start_dt = start_dt.replace(tzinfo=self.local_tz)
                
                if show_date:
                    date_str = f"📅 {start_dt.strftime('%A, %b %-d')}"
                    lines.append(f"  {date_str}")
                
                if end:
                    end_dt = datetime.strptime(end, '%Y-%m-%d %H:%M')
                    end_dt = end_dt.replace(tzinfo=self.local_tz)
                    time_str = f"🕒 {start_dt.strftime('%-I:%M %p')} - {end_dt.strftime('%-I:%M %p %Z')}"
                else:
                    time_str = f"🕒 {start_dt.strftime('%-I:%M %p %Z')}"
                
                lines.append(f"  {time_str}")
            except Exception as e:
                logger.warning(f"Could not parse time '{start}': {e}")
                lines.append(f"  🕒 {start}")
        
        if location:
            lines.append(f"  📍 {location}")
        
        if description:
            # Extract Zoom links
            zoom_match = re.search(r'(https://[^\s]+zoom[^\s]+)', description)
            if zoom_match:
                zoom_url = zoom_match.group(1)
                lines.append(f"  🔗 Zoom: {zoom_url}")
            
            # Clean and include description if reasonable length
            clean_desc = self._clean_description(description)
            if clean_desc and len(clean_desc) < 500 and not clean_desc.startswith('Hi there'):
                desc = clean_desc[:200] + "..." if len(clean_desc) > 200 else clean_desc
                lines.append(f"  ℹ️ {desc}")
        
        return lines
    
    def _clean_description(self, description: str) -> str:
        """Remove HTML and clean up description text."""
        # Remove HTML tags
        clean = re.sub(r'<[^>]+>', '', description)
        # Decode HTML entities
        clean = unescape(clean)
        # Normalize whitespace
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean
