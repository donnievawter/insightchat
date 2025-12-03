# External Tools Integration for InsightChat

InsightChat can integrate with external APIs to provide specialized data and enhance responses with real-time information from external services.

## Overview

The tool system allows InsightChat to:
- Automatically detect when a query requires external data (weather, quotes, etc.)
- Call appropriate APIs to fetch specialized information
- Combine tool results with RAG document context
- Provide intelligent responses using both sources

## Features

✅ **Intent-Based Routing** - Automatically detects which tools to use based on query keywords  
✅ **Configuration-Driven** - Enable/disable tools via environment variables  
✅ **Extensible Architecture** - Easy to add new tools  
✅ **Graceful Degradation** - Works without tools if they're unavailable  
✅ **Health Monitoring** - Check tool status via API endpoint

## Available Tools

### Weather Tool (PyWeather Integration)

Provides current weather conditions and forecasts from your PyWeather API.

**Enabled Keywords:** weather, temperature, temp, forecast, rain, sunny, wind, humidity, hot, cold, umbrella, etc.

**Example Queries:**
- "What's the current temperature?"
- "Do I need an umbrella today?"
- "What's the weather like outside?"
- "Is it windy right now?"

### Quotes Tool (Placeholder)

Template for RSS quotes API integration. Customize based on your API structure.

**Enabled Keywords:** quote, quotes, inspiration, motivation, saying, wisdom

## Configuration

### 1. Enable Tools in `.env`

Copy the tool configuration from `.env.example` to your `.env` file:

```bash
# Weather Tool - PyWeather Integration
TOOL_WEATHER_ENABLED=true
TOOL_WEATHER_API_URL=http://localhost:8000
TOOL_WEATHER_TIMEOUT=10

# Quotes Tool - RSS Quotes API
TOOL_QUOTES_ENABLED=false
TOOL_QUOTES_API_URL=
TOOL_QUOTES_TIMEOUT=10
```

### 2. Configuration Parameters

Each tool requires:

- `TOOL_<NAME>_ENABLED` - Set to `true` to enable the tool
- `TOOL_<NAME>_API_URL` - Base URL of the external API
- `TOOL_<NAME>_TIMEOUT` - Request timeout in seconds (default: 10)

### 3. Master Switch

The tool system can be completely disabled in `config.py`:

```python
TOOL_SYSTEM_ENABLED = True  # Set to False to disable all tools
```

## Using Tools

### Automatic Detection

Tools are invoked automatically based on query content. No special syntax required!

```
User: "What's the temperature outside?"
→ Weather tool is automatically invoked
→ Response includes current weather data
```

### With RAG Documents

Tools work alongside RAG document retrieval:

```
User: "What's the weather like and show me the meeting notes"
→ Weather tool provides current conditions
→ RAG retrieves relevant documents
→ LLM synthesizes both sources
```

### Checking Tool Status

Visit the tools status endpoint:

```bash
curl http://localhost:5030/tools/status
```

Response:
```json
{
  "enabled": true,
  "tools": [
    {
      "name": "weather",
      "description": "Weather tool - provides current conditions and forecasts",
      "enabled": true,
      "available": true,
      "keywords": ["weather", "temperature", "temp", "forecast", ...]
    }
  ],
  "active_tools": ["weather"],
  "health": {
    "weather": true
  }
}
```

## Adding New Tools

### 1. Create Tool Class

Create a new file in `flask-chat-app/src/chat/tools/your_tool.py`:

```python
from typing import Dict, Any, List
import requests
from .base_tool import BaseTool

class YourTool(BaseTool):
    """Your tool description"""
    
    def __init__(self, api_url: str = None, timeout: int = 10, enabled: bool = True):
        super().__init__(enabled=enabled, api_url=api_url, timeout=timeout)
        self.api_url = api_url.rstrip('/') if api_url else None
        self.timeout = timeout
    
    def get_intent_keywords(self) -> List[str]:
        """Keywords that trigger this tool"""
        return ['keyword1', 'keyword2', 'keyword3']
    
    def can_handle(self, query: str) -> bool:
        """Determine if this tool should handle the query"""
        if not self.is_available():
            return False
        query_lower = query.lower()
        return any(kw in query_lower for kw in self.get_intent_keywords())
    
    async def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """Execute the tool and return results"""
        if not self.is_available():
            return {
                'success': False,
                'error': 'Tool not available',
                'data': None,
                'metadata': {'tool': 'your_tool'}
            }
        
        try:
            # Call your external API
            response = requests.get(
                f"{self.api_url}/endpoint",
                params={'query': query},
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                'success': True,
                'data': data,
                'error': None,
                'metadata': {'tool': 'your_tool'}
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'data': None,
                'metadata': {'tool': 'your_tool'}
            }
    
    def format_for_llm(self, result: Dict[str, Any]) -> str:
        """Format results for LLM context"""
        if not result.get('success'):
            return f"\n\n[Tool error: {result.get('error')}]"
        
        data = result.get('data', {})
        return f"\n\n---\nYOUR TOOL DATA:\n{data}\n---\n"
    
    def get_required_config(self) -> List[str]:
        """Required configuration keys"""
        return ['api_url']
    
    def get_tool_description(self) -> str:
        """Tool description"""
        return "Your tool - does something useful"
```

### 2. Register Tool in Router

Edit `tool_router.py` and add your tool to the `_initialize_tools()` method:

```python
from .tools.your_tool import YourTool

def _initialize_tools(self):
    # ... existing tools ...
    
    # Your Tool
    your_tool_enabled = os.getenv('TOOL_YOURTOOL_ENABLED', 'false').lower() == 'true'
    your_tool_url = os.getenv('TOOL_YOURTOOL_API_URL', '')
    your_tool_timeout = int(os.getenv('TOOL_YOURTOOL_TIMEOUT', '10'))
    
    if your_tool_enabled and your_tool_url:
        try:
            your_tool = YourTool(
                api_url=your_tool_url,
                timeout=your_tool_timeout,
                enabled=True
            )
            self.tools.append(your_tool)
            logger.info(f"✓ Your tool registered: {your_tool_url}")
        except Exception as e:
            logger.error(f"Failed to initialize your tool: {e}")
```

### 3. Add Configuration

Add to `.env.example`:

```bash
# Your Tool - Description
TOOL_YOURTOOL_ENABLED=false
TOOL_YOURTOOL_API_URL=
TOOL_YOURTOOL_TIMEOUT=10
```

### 4. Test Your Tool

1. Enable in `.env`: `TOOL_YOURTOOL_ENABLED=true`
2. Set API URL: `TOOL_YOURTOOL_API_URL=http://your-api:8000`
3. Restart InsightChat
4. Check status: `curl http://localhost:5030/tools/status`
5. Test with relevant query

## Architecture

```
User Query
    ↓
Tool Router (intent detection)
    ↓
Matching Tools Execute (parallel)
    ↓
Tool Results → LLM Context
    ↓
RAG Retrieval (if enabled)
    ↓
RAG Results → LLM Context
    ↓
Combined Context → Ollama
    ↓
Response to User
```

## Design Principles

1. **Configuration Over Code** - Tools are enabled/disabled via environment variables
2. **Graceful Degradation** - System works without tools if they're unavailable
3. **Keyword-Based Intent** - Simple, effective query routing
4. **Async Execution** - Tools can be called in parallel for efficiency
5. **Health Monitoring** - Built-in health checks for all tools

## Troubleshooting

### Tool Not Triggering

1. Check if tool is enabled: `curl http://localhost:5030/tools/status`
2. Verify keywords match your query
3. Check debug logs for intent detection
4. Ensure API URL is correct and reachable

### Tool Fails to Execute

1. Check tool health: `curl http://localhost:5030/tools/status`
2. Verify external API is running and accessible
3. Check timeout settings (increase if needed)
4. Review application logs for detailed errors

### Tool Slows Down Responses

1. Reduce timeout: `TOOL_<NAME>_TIMEOUT=5`
2. Optimize external API response time
3. Consider caching in your external API

## Example: Weather Integration

With PyWeather running on `http://localhost:8000`:

```bash
# Enable weather tool
TOOL_WEATHER_ENABLED=true
TOOL_WEATHER_API_URL=http://localhost:8000
```

Restart InsightChat, then ask:
- "What's the temperature?"
- "Do I need a jacket?"
- "Is it going to rain today?"

The weather tool will automatically provide current conditions and forecast data to the LLM.

## Sharing with Colleagues

For colleagues without PyWeather or other tools:

1. Set `TOOL_WEATHER_ENABLED=false` in `.env`
2. Set `TOOL_QUOTES_ENABLED=false` in `.env`
3. Tools are disabled, no code changes needed
4. InsightChat works normally with RAG only

## Next Steps

- Implement your RSS quotes API integration in `quotes_tool.py`
- Add more specialized tools (calendar, email, databases, etc.)
- Enhance intent detection with LLM-based classification
- Add tool result caching for frequently asked queries
