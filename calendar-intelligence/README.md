# Calendar Intelligence

A reusable Python library for analyzing calendar events and queries across different data sources (ICS, Google Calendar, Nextcloud, etc.).

## Features

- 🔌 **Pluggable Data Sources**: Repository pattern allows easy switching between calendar providers
- 🧠 **Intent Detection**: Automatically understands queries like "what's on my calendar today?"
- 📊 **Structured Output**: Returns both raw data and formatted text for flexible consumption
- 🎯 **Application Agnostic**: Use in chat apps, voice assistants, dashboards, or CLIs

## Installation

Using `uv`:
```bash
# Install for development (editable mode)
cd calendar-intelligence
uv pip install -e .

# Install from another project
uv pip install ../calendar-intelligence
```

## Quick Start

```python
from calendar_intelligence import CalendarAnalyzer, IcsRepository

# Configure your calendar data source
repository = IcsRepository(api_url="https://ics.hlab.cam")

# Create analyzer
analyzer = CalendarAnalyzer(repository=repository)

# Analyze a query
result = await analyzer.analyze("What's on my calendar today?")

# Use the result
print(result['formatted_text'])  # Human-readable response
print(result['events'])          # Raw event data
print(result['metadata'])        # Event count, timeframe, etc.
```

## Response Structure

```python
{
    'success': True,
    'intent': {
        'type': 'events_today',
        'timeframe': 'today',
        'date_range': {'start': '2026-01-13', 'end': '2026-01-13'}
    },
    'events': [
        {
            'summary': 'Team Standup',
            'start': '2026-01-13 09:00',
            'end': '2026-01-13 09:30',
            'location': 'Zoom',
            'description': '...'
        }
    ],
    'formatted_text': 'You have 3 events today:\n\n**Team Standup**...',
    'metadata': {
        'event_count': 3,
        'data_source': 'ics',
        'endpoint': '/calendar/events/today'
    }
}
```

## Use Cases

### Chat Application
```python
result = await analyzer.analyze(user_query)
llm_context = result['formatted_text']
# Pass to LLM for conversational response
```

### Voice Assistant
```python
result = await analyzer.analyze(transcribed_voice)
await text_to_speech(result['formatted_text'])
```

### Dashboard Widget
```python
result = await analyzer.analyze("next 7 days")
render_calendar(result['events'])
```

### Analytics/Logging
```python
result = await analyzer.analyze("this month")
log_metrics(event_count=result['metadata']['event_count'])
```

## Adding New Data Sources

Implement the `CalendarRepository` interface:

```python
from calendar_intelligence.repositories import CalendarRepository
from datetime import datetime
from typing import List, Dict, Any

class GoogleCalendarRepository(CalendarRepository):
    def __init__(self, credentials_path: str):
        self.credentials = credentials_path
        # Initialize Google Calendar API client
    
    async def get_events_today(self) -> List[Dict[str, Any]]:
        # Fetch from Google Calendar API
        pass
    
    async def get_events_tomorrow(self) -> List[Dict[str, Any]]:
        # Fetch from Google Calendar API
        pass
    
    async def get_events_next_n_days(self, days: int) -> List[Dict[str, Any]]:
        # Fetch from Google Calendar API
        pass

# Use it
repository = GoogleCalendarRepository(credentials_path="./creds.json")
analyzer = CalendarAnalyzer(repository=repository)
```

## Architecture

```
calendar-intelligence/
├── src/
│   └── calendar_intelligence/
│       ├── __init__.py          # Public API exports
│       ├── analyzer.py          # Core analysis logic
│       ├── intent.py            # Query intent detection
│       ├── formatter.py         # Event formatting
│       └── repositories/
│           ├── __init__.py
│           ├── base.py          # Abstract interface
│           ├── ics.py           # ICS/iCal implementation
│           ├── google.py        # Google Calendar (future)
│           └── nextcloud.py     # Nextcloud (future)
```

## License

MIT
