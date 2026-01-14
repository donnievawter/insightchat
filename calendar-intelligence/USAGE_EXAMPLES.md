# Calendar Intelligence - Usage Examples

This document shows how to integrate `calendar-intelligence` into different types of applications.

## Installation

```bash
# Install with uv (recommended)
cd calendar-intelligence
uv pip install -e .

# Or from another project directory
uv pip install -e ../calendar-intelligence
```

## Configuration

The library supports multiple calendar data sources through the Repository pattern:

### ICS/iCal Repository (Current)
```python
from calendar_intelligence import CalendarAnalyzer, IcsRepository

repository = IcsRepository(
    api_url="https://ics.hlab.cam",
    timeout=10
)

analyzer = CalendarAnalyzer(
    repository=repository,
    timezone="America/Denver",  # IANA timezone
    enabled=True
)
```

### Future: Google Calendar Repository
```python
from calendar_intelligence import CalendarAnalyzer
from calendar_intelligence.repositories import GoogleCalendarRepository

repository = GoogleCalendarRepository(
    credentials_path="./credentials.json"
)

analyzer = CalendarAnalyzer(repository=repository)
```

## Use Case 1: Chat Application (Current InsightChat)

The chat app uses the library through a tool wrapper that integrates with the LLM:

```python
# flask-chat-app/src/chat/tools/calendar_tool.py
from calendar_intelligence import CalendarAnalyzer, IcsRepository
from .base_tool import BaseTool

class CalendarTool(BaseTool):
    def __init__(self, api_url: str, timeout: int = 10, enabled: bool = True):
        super().__init__(enabled=enabled)
        
        # Initialize the library
        repository = IcsRepository(api_url=api_url, timeout=timeout)
        self.analyzer = CalendarAnalyzer(
            repository=repository,
            timezone="America/Denver",
            enabled=enabled
        )
    
    def can_handle(self, query: str) -> bool:
        """Check if query is calendar-related"""
        return self.analyzer.can_handle(query)
    
    async def execute(self, query: str, **kwargs):
        """Fetch and analyze calendar events"""
        result = await self.analyzer.analyze(query)
        
        # Adapt response format for chat app
        return {
            'success': result['success'],
            'formatted_response': result['formatted_text'],
            'data': result.get('events', []),
            'metadata': result['metadata']
        }

# In your routes.py or handler
calendar_tool = CalendarTool(
    api_url=os.getenv('TOOL_CALENDAR_API_URL'),
    enabled=True
)

if calendar_tool.can_handle(user_message):
    result = await calendar_tool.execute(user_message)
    # Pass result['formatted_response'] to LLM as context
    llm_response = generate_llm_response(
        user_query=user_message,
        context=result['formatted_response']
    )
```

## Use Case 2: Voice Assistant Application

Voice applications can use the library directly for text-to-speech responses:

```python
# voice-app/calendar_handler.py
from calendar_intelligence import CalendarAnalyzer, IcsRepository
import asyncio

class VoiceCalendarHandler:
    def __init__(self, ics_api_url: str):
        repository = IcsRepository(api_url=ics_api_url)
        self.analyzer = CalendarAnalyzer(
            repository=repository,
            timezone="America/Denver"
        )
    
    async def handle_voice_query(self, transcribed_text: str):
        """
        Handle a voice query about calendar.
        
        Returns text ready for TTS (no LLM needed!)
        """
        # Check if it's calendar-related
        if not self.analyzer.can_handle(transcribed_text):
            return None  # Let other handlers deal with it
        
        # Analyze the query
        result = await self.analyzer.analyze(transcribed_text)
        
        if result['success']:
            # Return formatted text directly to TTS
            return result['formatted_text']
        else:
            return f"Sorry, I had trouble accessing your calendar: {result['error']}"

# Usage
async def main():
    handler = VoiceCalendarHandler(ics_api_url="https://ics.hlab.cam")
    
    # User speaks: "What's on my calendar today?"
    transcription = "What's on my calendar today?"
    
    response = await handler.handle_voice_query(transcription)
    
    if response:
        # Send to text-to-speech
        await text_to_speech(response)
        # Output: "You have 3 events today: Team Standup at 9:00 AM..."
```

## Use Case 3: Dashboard/Widget Application

Web dashboards can use the raw event data for rendering:

```python
# dashboard-app/widgets/calendar_widget.py
from calendar_intelligence import CalendarAnalyzer, IcsRepository
from fastapi import FastAPI
from datetime import datetime

app = FastAPI()

# Initialize once at startup
repository = IcsRepository(api_url="https://ics.hlab.cam")
analyzer = CalendarAnalyzer(repository=repository)

@app.get("/api/calendar/today")
async def get_today_events():
    """API endpoint for calendar widget"""
    result = await analyzer.analyze("today's events")
    
    if not result['success']:
        return {"error": result['error']}, 500
    
    # Return structured data for frontend rendering
    return {
        "events": [
            {
                "title": event['summary'],
                "start": event['start'],
                "end": event['end'],
                "location": event.get('location'),
                "description": event.get('description')
            }
            for event in result['events']
        ],
        "count": result['metadata']['event_count'],
        "date_range": result['intent']['date_range']
    }

# Frontend JavaScript would then render this as a calendar widget
```

## Use Case 4: CLI Tool

Command-line tools can use both formatted text and raw data:

```python
#!/usr/bin/env python3
# cal-cli.py - Command-line calendar tool

import asyncio
import sys
from calendar_intelligence import CalendarAnalyzer, IcsRepository

async def main():
    if len(sys.argv) < 2:
        print("Usage: cal-cli <query>")
        print("Examples:")
        print("  cal-cli today")
        print("  cal-cli 'next week'")
        print("  cal-cli 'when is my next dentist appointment'")
        sys.exit(1)
    
    query = ' '.join(sys.argv[1:])
    
    # Initialize analyzer
    repository = IcsRepository(api_url="https://ics.hlab.cam")
    analyzer = CalendarAnalyzer(repository=repository)
    
    # Analyze query
    result = await analyzer.analyze(query)
    
    if result['success']:
        # Print formatted text (already nicely formatted!)
        print(result['formatted_text'])
        print(f"\n📊 Total: {result['metadata']['event_count']} events")
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
```

Usage:
```bash
$ python cal-cli.py today
You have 3 events today:

**Team Standup**
  🕒 9:00 AM - 9:30 AM MST
  📍 Zoom

**Client Meeting**
  🕒 2:00 PM - 3:00 PM MST
  📍 Conference Room A

**Code Review**
  🕒 4:00 PM - 5:00 PM MST

📊 Total: 3 events
```

## Use Case 5: Slack Bot

Slack bots can use the library to respond to calendar queries:

```python
# slack-bot/calendar_commands.py
from slack_bolt.async_app import AsyncApp
from calendar_intelligence import CalendarAnalyzer, IcsRepository

app = AsyncApp(token=os.environ["SLACK_BOT_TOKEN"])

# Initialize analyzer
repository = IcsRepository(api_url=os.environ["ICS_API_URL"])
analyzer = CalendarAnalyzer(repository=repository)

@app.command("/calendar")
async def handle_calendar_command(ack, command, say):
    await ack()
    
    query = command['text'] or "today"
    result = await analyzer.analyze(query)
    
    if result['success']:
        # Post formatted response to Slack
        await say(result['formatted_text'])
    else:
        await say(f"❌ Error: {result['error']}")

# User types: /calendar today
# Bot responds with formatted event list
```

## Use Case 6: Analytics/Logging Service

Services can track calendar usage patterns:

```python
# analytics-service/calendar_tracker.py
from calendar_intelligence import CalendarAnalyzer, IcsRepository
import logging
from datetime import datetime

class CalendarAnalytics:
    def __init__(self, ics_api_url: str, db_connection):
        repository = IcsRepository(api_url=ics_api_url)
        self.analyzer = CalendarAnalyzer(repository=repository)
        self.db = db_connection
    
    async def track_daily_events(self):
        """Run daily to track meeting patterns"""
        result = await self.analyzer.analyze("today")
        
        if result['success']:
            # Log to database
            self.db.insert({
                'date': datetime.now().date(),
                'event_count': result['metadata']['event_count'],
                'events': result['events']
            })
            
            # Calculate metrics
            total_duration = self._calculate_total_duration(result['events'])
            meeting_count = len([e for e in result['events'] if 'meeting' in e['summary'].lower()])
            
            logging.info(f"Daily stats: {meeting_count} meetings, {total_duration} hours scheduled")
```

## Advanced: Custom Repository

Create a repository for your calendar system:

```python
# my_custom_repository.py
from calendar_intelligence.repositories import CalendarRepository
from typing import List, Dict, Any
import requests

class MyCustomCalendarRepository(CalendarRepository):
    """Repository for your custom calendar API"""
    
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
    
    async def get_events_today(self) -> List[Dict[str, Any]]:
        return self._fetch("/events/today")
    
    async def get_events_tomorrow(self) -> List[Dict[str, Any]]:
        return self._fetch("/events/tomorrow")
    
    async def get_events_next_n_days(self, days: int) -> List[Dict[str, Any]]:
        return self._fetch(f"/events/range?days={days}")
    
    async def get_health(self) -> Dict[str, Any]:
        response = requests.get(f"{self.base_url}/health")
        return response.json()
    
    def _fetch(self, endpoint: str) -> List[Dict[str, Any]]:
        """Your custom API call logic"""
        response = requests.get(
            f"{self.base_url}{endpoint}",
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        response.raise_for_status()
        
        # Transform your API response to standard format
        data = response.json()
        return [
            {
                'summary': event['title'],
                'start': event['start_time'],
                'end': event['end_time'],
                'location': event.get('venue'),
                'description': event.get('notes')
            }
            for event in data['items']
        ]

# Use it
repository = MyCustomCalendarRepository(
    api_key="your-key",
    base_url="https://api.mycalendar.com"
)
analyzer = CalendarAnalyzer(repository=repository)
```

## Testing

```python
# test_calendar_integration.py
import pytest
from calendar_intelligence import CalendarAnalyzer, IcsRepository

@pytest.mark.asyncio
async def test_today_events():
    repository = IcsRepository(api_url="https://ics.hlab.cam")
    analyzer = CalendarAnalyzer(repository=repository)
    
    result = await analyzer.analyze("what's on my calendar today?")
    
    assert result['success']
    assert 'events' in result
    assert 'formatted_text' in result
    assert result['intent']['type'] == 'events_today'
```

## Environment Variables

Typical configuration:

```bash
# .env
CALENDAR_API_URL=https://ics.hlab.cam
CALENDAR_TIMEOUT=10
CALENDAR_TIMEZONE=America/Denver
CALENDAR_ENABLED=true
```

## Summary

The `calendar-intelligence` library provides:

1. **Flexible Integration**: Works with any Python application
2. **No LLM Required**: Pre-formatted responses ready for display/TTS
3. **Pluggable Data Sources**: Swap calendar providers without changing app code
4. **Structured Output**: Raw data + formatted text for different use cases
5. **Intent Detection**: Understands natural language queries automatically

Each application decides:
- Whether to use formatted text directly (voice, CLI) or pass to LLM (chat)
- How to render the data (text, UI widgets, Slack messages)
- Which repository to use (ICS, Google, Nextcloud, custom)
