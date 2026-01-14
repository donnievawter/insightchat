# Calendar Intelligence Library - Migration Summary

## What We Built

Created a reusable Python library called **calendar-intelligence** that extracts calendar analysis logic from your chat application, making it available to other applications (voice apps, CLIs, dashboards, etc.).

## Architecture

### Repository Pattern (Pluggable Data Sources)

```
CalendarAnalyzer
    ↓ uses
CalendarRepository (interface)
    ↓ implemented by
├── IcsRepository (current: ics.hlab.cam)
├── GoogleCalendarRepository (future)
└── NextcloudRepository (future)
```

**Key Benefit**: Switch calendar providers without changing application code.

### Package Structure

```
calendar-intelligence/
├── pyproject.toml                    # uv package config
├── README.md                         # Package documentation
├── USAGE_EXAMPLES.md                 # Integration examples
├── test_library.py                   # Quick test script
└── src/
    └── calendar_intelligence/
        ├── __init__.py              # Public API exports
        ├── analyzer.py              # Main orchestrator
        ├── intent.py                # Query understanding
        ├── formatter.py             # Event formatting
        └── repositories/
            ├── __init__.py
            ├── base.py             # Abstract interface
            └── ics.py              # ICS implementation
```

## What the Library Does

1. **Intent Detection**: Understands queries like "tomorrow", "next week", "when is my next meeting"
2. **Data Fetching**: Calls calendar API through pluggable repository
3. **Event Formatting**: Returns both raw data and human-readable text
4. **No LLM Required**: Pre-formatted responses ready for display/TTS

## What the Library Does NOT Do

❌ Does NOT call an LLM  
❌ Does NOT generate conversational responses  
❌ Does NOT have application-specific logic  

The calling application decides whether to:
- Use formatted text directly (voice, CLI, TTS)
- Pass it to an LLM for conversational response (chat)
- Render the data as UI widgets (dashboard)

## Installation

```bash
# In any project
cd /path/to/your/project
uv pip install -e /opt/dockerapps/insightchat/calendar-intelligence
```

## Usage

### Basic Usage
```python
from calendar_intelligence import CalendarAnalyzer, IcsRepository

# Configure data source
repository = IcsRepository(api_url="https://ics.hlab.cam")

# Create analyzer
analyzer = CalendarAnalyzer(repository=repository, timezone="America/Denver")

# Analyze a query
result = await analyzer.analyze("What's on my calendar today?")

# Use the result
print(result['formatted_text'])  # Ready for display/TTS
print(result['events'])          # Raw data for processing
```

### Response Structure
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
        'timezone': 'America/Denver'
    }
}
```

## Changes to Flask Chat App

The [calendar_tool.py](../flask-chat-app/src/chat/tools/calendar_tool.py) was simplified from **515 lines** to a thin wrapper (~100 lines):

**Before**: Had all intent detection, API calling, and formatting logic  
**After**: Delegates everything to `calendar-intelligence` library

```python
# Old way (self-contained)
class CalendarTool:
    def execute(self, query):
        endpoint = self._determine_endpoint(query)  # 100+ lines of logic
        response = requests.get(f"{self.api_url}{endpoint}")
        return self._format_events(response.json())  # 200+ lines of formatting

# New way (using library)
class CalendarTool:
    def __init__(self, api_url, timeout, enabled):
        repository = IcsRepository(api_url=api_url, timeout=timeout)
        self.analyzer = CalendarAnalyzer(repository=repository)
    
    async def execute(self, query):
        result = await self.analyzer.analyze(query)
        return {
            'success': result['success'],
            'formatted_response': result['formatted_text'],
            'data': result['events']
        }
```

## Use Cases

### ✅ Chat Application (Current)
```python
result = await analyzer.analyze(user_query)
llm_response = generate_with_context(result['formatted_text'])
```

### ✅ Voice Assistant (Your Next Project)
```python
result = await analyzer.analyze(transcribed_voice)
await text_to_speech(result['formatted_text'])  # No LLM needed!
```

### ✅ CLI Tool
```python
result = await analyzer.analyze(sys.argv[1])
print(result['formatted_text'])
```

### ✅ Dashboard Widget
```python
result = await analyzer.analyze("next 7 days")
render_calendar(result['events'])
```

### ✅ Slack Bot
```python
result = await analyzer.analyze(command['text'])
await say(result['formatted_text'])
```

## Testing

```bash
# Test the library
cd /opt/dockerapps/insightchat/calendar-intelligence
/opt/dockerapps/insightchat/.venv/bin/python test_library.py

# Expected output:
# ✅ Repository created
# ✅ Analyzer created
# ✅ Intent detection working
# ✅ Analysis successful
```

## Adding New Calendar Sources

Create a new repository class:

```python
from calendar_intelligence.repositories import CalendarRepository

class GoogleCalendarRepository(CalendarRepository):
    def __init__(self, credentials_path: str):
        self.creds = load_google_credentials(credentials_path)
    
    async def get_events_today(self):
        # Call Google Calendar API
        return google_events
    
    async def get_events_tomorrow(self):
        # Call Google Calendar API
        return google_events
    
    async def get_events_next_n_days(self, days: int):
        # Call Google Calendar API
        return google_events
```

Then use it:
```python
repository = GoogleCalendarRepository(credentials_path="./creds.json")
analyzer = CalendarAnalyzer(repository=repository)
# Everything else works exactly the same!
```

## Next Steps

### Option 1: Keep in Monorepo (Recommended for Now)
```
/opt/dockerapps/insightchat/
├── flask-chat-app/          # Chat application
├── calendar-intelligence/   # Shared library
└── voice-app/              # Future: Voice assistant
```

Benefits:
- Easy to develop and test together
- Share one virtual environment
- Simple imports with `uv pip install -e ../calendar-intelligence`

### Option 2: Move to Separate Repository (Later)
When the library is stable:
```bash
mv calendar-intelligence /opt/dockerapps/calendar-intelligence
cd /opt/dockerapps/calendar-intelligence
git init
git remote add origin <new-repo-url>
```

Then install from Git:
```bash
uv pip install git+https://github.com/you/calendar-intelligence.git
```

### Option 3: Publish to PyPI (Future)
```bash
cd calendar-intelligence
uv build
uv publish
```

Then anyone can:
```bash
uv pip install calendar-intelligence
```

## Documentation

- **README.md**: Package overview and quick start
- **USAGE_EXAMPLES.md**: Detailed integration examples for 6+ use cases
- **test_library.py**: Quick verification script

## Benefits Achieved

✅ **Reusable**: Any Python app can use it  
✅ **Decoupled**: Calendar source (ICS/Google/etc.) separate from analysis logic  
✅ **No LLM Lock-in**: Returns both raw data and formatted text  
✅ **Tested**: Verified working with existing ICS API  
✅ **Documented**: Complete usage examples for multiple app types  
✅ **Modern**: Uses `uv` for fast, reliable dependency management  

## Migration Complete

Your chat application now uses the library and works exactly as before, but the calendar intelligence is now available to any application you build!
