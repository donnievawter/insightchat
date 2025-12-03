# Quick Start: Using Weather Tool with InsightChat

## Setup (2 minutes)

### 1. Enable Weather Tool

Edit `/opt/dockerapps/insightchat/flask-chat-app/.env`:

```bash
# Enable weather tool
TOOL_WEATHER_ENABLED=true
TOOL_WEATHER_API_URL=http://localhost:8000
TOOL_WEATHER_TIMEOUT=10
```

### 2. Start PyWeather (in separate terminal)

```bash
cd /opt/dockerapps/pyweather
make dev
```

### 3. Start InsightChat

```bash
cd /opt/dockerapps/insightchat
uv run main.py
```

### 4. Test It!

Open http://localhost:5030 and ask:
- "What's the current temperature?"
- "Do I need an umbrella today?"
- "Is it windy outside?"
- "What's the weather forecast?"

## Verify It's Working

### Check Tool Status
```bash
curl http://localhost:5030/tools/status | python3 -m json.tool
```

Should show:
```json
{
  "enabled": true,
  "active_tools": ["weather"],
  "health": {
    "weather": true
  }
}
```

### Check Logs

Look for these debug messages when asking weather questions:
```
DEBUG: Checking tools for query: What's the temperature?
DEBUG: Weather tool matched keyword: temperature
DEBUG: Tools executed: 1, successful: 1
DEBUG: Tool context length: XXX chars
```

## Example Conversations

### Pure Weather Query
```
👤 User: What's the temperature?
🤖 Assistant: The current temperature is 72°F with partly cloudy 
   skies. The humidity is at 45% and winds are light at 5 mph 
   from the northwest.
   
✅ Weather tool was used automatically
```

### Weather + RAG
```
👤 User: What's the weather and show me today's schedule
🤖 Assistant: Currently it's 72°F and partly cloudy. Perfect 
   weather for your outdoor meeting!
   
   According to your schedule:
   - 9:00 AM: Team standup
   - 11:00 AM: Client call
   - 2:00 PM: Outdoor team lunch (great weather for it!)
   
✅ Weather tool + RAG documents both used
```

## Troubleshooting

### Weather tool not triggering?

1. Check if enabled: `curl http://localhost:5030/tools/status`
2. Verify PyWeather is running: `curl http://localhost:8000/api/status`
3. Check logs for intent detection
4. Try more explicit query: "What is the current temperature outside?"

### PyWeather connection failed?

```bash
# Verify PyWeather is accessible
curl http://localhost:8000/api/status

# Check if PyWeather is running
ps aux | grep uvicorn
```

## Disable Weather Tool

To share code with someone without PyWeather:

```bash
# In .env
TOOL_WEATHER_ENABLED=false
```

That's it! No code changes needed.

## Next Steps

- Read [TOOLS.md](TOOLS.md) for complete documentation
- Add RSS quotes tool (template ready in `quotes_tool.py`)
- Create custom tools for your APIs

## Quick Test

Run the test suite:
```bash
cd /opt/dockerapps/insightchat
uv run python test_tools.py
```

Should show:
```
✓ Matched tools: ['weather']
✓ Correct! Expected weather
```
