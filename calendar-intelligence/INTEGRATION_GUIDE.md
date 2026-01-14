# Calendar Intelligence - Integration Guide

## Quick Start: Using in Another Application

### Step 1: Install the Library

From your new application directory:

```bash
# Option A: Local development (recommended during development)
cd /path/to/your-voice-app
uv pip install -e /opt/dockerapps/insightchat/calendar-intelligence

# Option B: If calendar-intelligence is in a sibling directory
uv pip install -e ../calendar-intelligence

# Option C: From Git (when you move it to its own repo)
uv pip install git+https://github.com/yourusername/calendar-intelligence.git
```

### Step 2: Basic Integration

```python
# your_app/calendar_handler.py
from calendar_intelligence import CalendarAnalyzer, IcsRepository

# Initialize once (e.g., at app startup)
repository = IcsRepository(
    api_url="https://ics.hlab.cam",
    timeout=10
)

analyzer = CalendarAnalyzer(
    repository=repository,
    timezone="America/Denver",  # Your local timezone
    enabled=True
)

# Use it to analyze queries
async def handle_calendar_query(user_query: str):
    # Check if it's calendar-related
    if not analyzer.can_handle(user_query):
        return None  # Not a calendar query
    
    # Analyze the query
    result = await analyzer.analyze(user_query)
    
    if result['success']:
        # You now have:
        # - result['formatted_text']: Ready for display/TTS
        # - result['events']: Raw event data for processing
        # - result['metadata']: Event count, timezone, etc.
        return result
    else:
        # Handle error
        return {'error': result['error']}
```

### Step 3: Use the Results

Different applications use the results differently:

**Voice App (Text-to-Speech)**
```python
result = await analyzer.analyze(transcribed_text)
if result['success']:
    # Use pre-formatted text directly - no LLM needed!
    await text_to_speech(result['formatted_text'])
```

**Chat App (LLM Context)**
```python
result = await analyzer.analyze(user_message)
if result['success']:
    # Pass to LLM as context
    llm_response = await llm.generate(
        user_query=user_message,
        context=result['formatted_text']
    )
```

**Dashboard (UI Rendering)**
```python
result = await analyzer.analyze("next 7 days")
if result['success']:
    # Use raw event data
    for event in result['events']:
        render_event_card(
            title=event['summary'],
            time=event['start'],
            location=event.get('location')
        )
```

## Application Structure Examples

### Voice Assistant Application

```
voice-assistant/
├── main.py
├── handlers/
│   ├── calendar_handler.py    # Uses calendar-intelligence
│   ├── weather_handler.py
│   └── general_handler.py
├── tts/
│   └── synthesizer.py
└── requirements.txt            # Add: -e ../calendar-intelligence
```

**handlers/calendar_handler.py**:
```python
from calendar_intelligence import CalendarAnalyzer, IcsRepository
import os

class CalendarHandler:
    def __init__(self):
        repo = IcsRepository(api_url=os.getenv('ICS_API_URL'))
        self.analyzer = CalendarAnalyzer(
            repository=repo,
            timezone=os.getenv('TIMEZONE', 'America/Denver')
        )
    
    def can_handle(self, transcription: str) -> bool:
        return self.analyzer.can_handle(transcription)
    
    async def handle(self, transcription: str) -> str:
        result = await self.analyzer.analyze(transcription)
        if result['success']:
            return result['formatted_text']
        else:
            return f"Sorry, I couldn't access your calendar: {result['error']}"
```

**main.py**:
```python
from handlers.calendar_handler import CalendarHandler
from tts.synthesizer import speak

calendar_handler = CalendarHandler()

async def process_voice_command(transcription: str):
    if calendar_handler.can_handle(transcription):
        response = await calendar_handler.handle(transcription)
        await speak(response)
        return
    
    # Try other handlers...
```

### CLI Tool

```
cal-cli/
├── cal.py                      # Main CLI script
└── requirements.txt            # Add: -e ../calendar-intelligence
```

**cal.py**:
```python
#!/usr/bin/env python3
import asyncio
import sys
import os
from calendar_intelligence import CalendarAnalyzer, IcsRepository

async def main():
    if len(sys.argv) < 2:
        print("Usage: cal <query>")
        print("Examples: cal today | cal 'next week' | cal 'when is my next meeting'")
        sys.exit(1)
    
    query = ' '.join(sys.argv[1:])
    
    repo = IcsRepository(api_url=os.getenv('ICS_API_URL', 'https://ics.hlab.cam'))
    analyzer = CalendarAnalyzer(repository=repo)
    
    result = await analyzer.analyze(query)
    
    if result['success']:
        print(result['formatted_text'])
        print(f"\n📊 Total: {result['metadata']['event_count']} events")
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
```

Make it executable:
```bash
chmod +x cal.py
./cal.py today
```

### Web API / FastAPI

```
calendar-api/
├── main.py
├── routers/
│   └── calendar.py             # Uses calendar-intelligence
└── requirements.txt            # Add: -e ../calendar-intelligence
```

**routers/calendar.py**:
```python
from fastapi import APIRouter, HTTPException
from calendar_intelligence import CalendarAnalyzer, IcsRepository
import os

router = APIRouter()

# Initialize once
repo = IcsRepository(api_url=os.getenv('ICS_API_URL'))
analyzer = CalendarAnalyzer(repository=repo)

@router.get("/calendar/analyze")
async def analyze_query(q: str):
    """
    Analyze a calendar query.
    Query param: q (e.g., "today", "next week", "when is my next meeting")
    """
    result = await analyzer.analyze(q)
    
    if not result['success']:
        raise HTTPException(status_code=500, detail=result['error'])
    
    return {
        "query": q,
        "formatted_response": result['formatted_text'],
        "events": result['events'],
        "metadata": result['metadata']
    }

@router.get("/calendar/events/today")
async def get_today():
    result = await analyzer.analyze("today")
    if not result['success']:
        raise HTTPException(status_code=500, detail=result['error'])
    return result['events']
```

## Environment Variables

Create a `.env` file in your application:

```bash
# Calendar Intelligence Configuration
ICS_API_URL=https://ics.hlab.cam
TIMEZONE=America/Denver
CALENDAR_TIMEOUT=10
```

Load in your app:
```python
from dotenv import load_dotenv
load_dotenv()
```

## Dependency Management

### Using uv (Recommended)

**pyproject.toml**:
```toml
[project]
dependencies = [
    "calendar-intelligence @ file:///opt/dockerapps/insightchat/calendar-intelligence",
    # Or when published: "calendar-intelligence>=0.1.0",
]
```

Or simply:
```bash
uv pip install -e /opt/dockerapps/insightchat/calendar-intelligence
```

### Using pip

**requirements.txt**:
```
-e /opt/dockerapps/insightchat/calendar-intelligence
# Or: -e ../calendar-intelligence
```

## Testing Your Integration

Create a test script:

```python
# test_calendar_integration.py
import asyncio
from calendar_intelligence import CalendarAnalyzer, IcsRepository

async def test():
    repo = IcsRepository(api_url="https://ics.hlab.cam")
    analyzer = CalendarAnalyzer(repository=repo)
    
    # Test intent detection
    assert analyzer.can_handle("what's on my calendar today?")
    assert not analyzer.can_handle("what's the weather?")
    
    # Test analysis
    result = await analyzer.analyze("today")
    assert result['success']
    assert 'formatted_text' in result
    assert 'events' in result
    
    print("✅ All tests passed!")

asyncio.run(test())
```

## Docker Integration

If your application runs in Docker:

**Dockerfile**:
```dockerfile
FROM python:3.11

WORKDIR /app

# Copy calendar-intelligence library
COPY calendar-intelligence /opt/calendar-intelligence

# Install it
RUN pip install -e /opt/calendar-intelligence

# Copy and install your app
COPY . /app
RUN pip install -r requirements.txt

CMD ["python", "main.py"]
```

**docker-compose.yml**:
```yaml
services:
  voice-app:
    build: .
    environment:
      - ICS_API_URL=https://ics.hlab.cam
      - TIMEZONE=America/Denver
    volumes:
      - ../calendar-intelligence:/opt/calendar-intelligence:ro
```

## Switching Calendar Sources

If you want to use Google Calendar instead of ICS:

```python
# Create a new repository (you'd need to implement this)
from calendar_intelligence.repositories import CalendarRepository

class GoogleCalendarRepository(CalendarRepository):
    def __init__(self, credentials_path: str):
        # Your Google Calendar setup
        pass
    
    async def get_events_today(self):
        # Call Google Calendar API
        pass
    
    # Implement other required methods...

# Use it (rest of your app stays the same!)
repo = GoogleCalendarRepository(credentials_path="./creds.json")
analyzer = CalendarAnalyzer(repository=repo)
```

## Common Patterns

### Singleton Pattern (One Analyzer Per App)

```python
# calendar_service.py
from calendar_intelligence import CalendarAnalyzer, IcsRepository
import os

_analyzer = None

def get_analyzer() -> CalendarAnalyzer:
    global _analyzer
    if _analyzer is None:
        repo = IcsRepository(api_url=os.getenv('ICS_API_URL'))
        _analyzer = CalendarAnalyzer(repository=repo)
    return _analyzer

# Use everywhere:
from calendar_service import get_analyzer

analyzer = get_analyzer()
result = await analyzer.analyze(query)
```

### Dependency Injection (FastAPI Example)

```python
from fastapi import Depends
from calendar_intelligence import CalendarAnalyzer, IcsRepository

def get_calendar_analyzer():
    repo = IcsRepository(api_url=os.getenv('ICS_API_URL'))
    return CalendarAnalyzer(repository=repo)

@app.get("/calendar")
async def get_calendar(
    q: str,
    analyzer: CalendarAnalyzer = Depends(get_calendar_analyzer)
):
    return await analyzer.analyze(q)
```

## Troubleshooting

**Import Error**:
```bash
# Make sure it's installed
uv pip list | grep calendar-intelligence

# Reinstall if needed
uv pip install -e /opt/dockerapps/insightchat/calendar-intelligence --force-reinstall
```

**API Connection Issues**:
```python
# Check health
result = await analyzer.check_health()
print(result)
```

**Debug Mode**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now you'll see all internal log messages
result = await analyzer.analyze("today")
```

## Summary

1. **Install**: `uv pip install -e /path/to/calendar-intelligence`
2. **Import**: `from calendar_intelligence import CalendarAnalyzer, IcsRepository`
3. **Initialize**: Create repository → Create analyzer
4. **Use**: `result = await analyzer.analyze(query)`
5. **Consume**: Use `result['formatted_text']` or `result['events']` based on your needs

The library handles all the complexity - you just provide the query and decide what to do with the results!
