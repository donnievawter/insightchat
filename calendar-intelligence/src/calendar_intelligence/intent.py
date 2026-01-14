"""
Intent Detection - Determines what the user is asking about their calendar

Extracts meaning from natural language queries like:
- "What's on my calendar today?"
- "Do I have any meetings tomorrow?"
- "Show me the next 7 days"
"""

import re
from typing import Dict, Any, Optional
from datetime import datetime, timedelta


class IntentDetector:
    """Detects user intent from calendar-related queries."""
    
    # Word to number mapping for text numbers
    WORD_TO_NUM = {
        'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
    }
    
    @staticmethod
    def detect(query: str) -> Dict[str, Any]:
        """
        Analyze a query and determine the user's intent.
        
        Args:
            query: Natural language query from user
            
        Returns:
            Dictionary with:
            - type: Intent type (e.g., 'events_today', 'events_next_n_days')
            - timeframe: Human-readable timeframe
            - days: Number of days (for range queries)
            - search_term: Search term for filtering (optional)
        """
        message_lower = query.lower()
        
        # Check for "when is the next X" pattern
        next_event_pattern = re.search(r'when\s+is\s+(the|my)\s+next\s+(.+)', message_lower)
        if next_event_pattern:
            search_term = next_event_pattern.group(2).strip()
            return {
                'type': 'find_next_event',
                'timeframe': 'next 30 days',
                'days': 30,
                'search_term': search_term
            }
        
        # Check for "next N weeks"
        next_weeks_digit = re.search(r'next\s+(\d+)\s+weeks?', message_lower)
        next_weeks_word = re.search(r'next\s+(one|two|three|four|five|six|seven|eight|nine|ten)\s+weeks?', message_lower)
        
        if next_weeks_digit:
            weeks = int(next_weeks_digit.group(1))
            days = weeks * 7
            return {
                'type': 'events_next_n_days',
                'timeframe': f'next {weeks} week{"s" if weeks > 1 else ""}',
                'days': days
            }
        elif next_weeks_word:
            week_word = next_weeks_word.group(1)
            weeks = IntentDetector.WORD_TO_NUM.get(week_word, 1)
            days = weeks * 7
            return {
                'type': 'events_next_n_days',
                'timeframe': f'next {weeks} week{"s" if weeks > 1 else ""}',
                'days': days
            }
        
        # Check for "next N days"
        next_days_digit = re.search(r'next\s+(\d+)\s+days?', message_lower)
        next_days_word = re.search(r'next\s+(one|two|three|four|five|six|seven|eight|nine|ten)\s+days?', message_lower)
        
        if next_days_digit:
            days = int(next_days_digit.group(1))
            return {
                'type': 'events_next_n_days',
                'timeframe': f'next {days} day{"s" if days > 1 else ""}',
                'days': days
            }
        elif next_days_word:
            day_word = next_days_word.group(1)
            days = IntentDetector.WORD_TO_NUM.get(day_word, 1)
            return {
                'type': 'events_next_n_days',
                'timeframe': f'next {days} day{"s" if days > 1 else ""}',
                'days': days
            }
        
        # Check for "next month"
        if 'next month' in message_lower:
            return {
                'type': 'events_next_n_days',
                'timeframe': 'next month',
                'days': 30
            }
        
        # Check for "this week"
        if 'this week' in message_lower:
            return {
                'type': 'events_next_n_days',
                'timeframe': 'this week',
                'days': 7
            }
        
        # Check for "next week"
        if 'next week' in message_lower and 'weeks' not in message_lower:
            return {
                'type': 'events_next_n_days',
                'timeframe': 'next week',
                'days': 14
            }
        
        # Check for tomorrow
        if 'tomorrow' in message_lower:
            return {
                'type': 'events_tomorrow',
                'timeframe': 'tomorrow'
            }
        
        # Check for today
        if 'today' in message_lower or 'tonight' in message_lower:
            return {
                'type': 'events_today',
                'timeframe': 'today'
            }
        
        # Default to next 7 days
        return {
            'type': 'events_next_n_days',
            'timeframe': 'next 7 days',
            'days': 7
        }
    
    @staticmethod
    def can_handle(query: str) -> bool:
        """
        Determine if a query is calendar-related.
        
        Args:
            query: User's input message
            
        Returns:
            True if the query appears to be about calendars/events
        """
        message_lower = query.lower()
        
        # Primary calendar indicators
        primary_keywords = [
            'calendar', 'event', 'events', 'schedule', 'appointment', 'appointments',
            'meeting', 'meetings', 'agenda', 'today', 'tomorrow', 'tonight',
            'this week', 'next week', 'this month', 'next month'
        ]
        
        for keyword in primary_keywords:
            if keyword in message_lower:
                return True
        
        # Secondary keywords - only match if combined with calendar context
        if any(word in message_lower for word in ['when', 'what time', 'am i busy', 'free', 'available']):
            # Exclude if asking about documents/files
            if not any(word in message_lower for word in ['document', 'file', 'pdf', 'email', 'attachment']):
                return True
        
        # Match "when is the next" or "when is my next" patterns
        if re.search(r'when\s+is\s+(the|my)\s+next', message_lower):
            return True
        
        return False
