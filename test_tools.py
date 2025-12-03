#!/usr/bin/env python3
"""
Test script for InsightChat External Tools Integration

This script tests the tool system without requiring the full Flask app.
Run with: uv run python test_tools.py
"""

import sys
import os
import asyncio

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'flask-chat-app', 'src'))

# Set environment variables for testing
os.environ['TOOL_WEATHER_ENABLED'] = 'true'
os.environ['TOOL_WEATHER_API_URL'] = 'http://localhost:8000'
os.environ['TOOL_QUOTES_ENABLED'] = 'false'

# Import after setting up path
try:
    from chat.tool_router import get_tool_router
except ImportError as e:
    print(f"Error importing tool_router: {e}")
    print("\nPlease run this script with: uv run python test_tools.py")
    sys.exit(1)

def test_tool_detection():
    """Test that tools correctly detect intent from queries"""
    print("=" * 60)
    print("TESTING TOOL INTENT DETECTION")
    print("=" * 60)
    
    router = get_tool_router()
    
    test_queries = [
        ("What's the current temperature?", True, "weather"),
        ("Do I need an umbrella today?", True, "weather"),
        ("Tell me about Python programming", False, None),
        ("Is it windy outside?", True, "weather"),
        ("Show me a motivational quote", True, "quotes"),
        ("What's the humidity level?", True, "weather"),
    ]
    
    for query, should_match, expected_tool in test_queries:
        print(f"\nQuery: '{query}'")
        
        matching_tools = [tool for tool in router.tools if tool.can_handle(query)]
        
        if matching_tools:
            tool_names = [t.name for t in matching_tools]
            print(f"  ✓ Matched tools: {tool_names}")
            
            if should_match and expected_tool in tool_names:
                print(f"  ✓ Correct! Expected {expected_tool}")
            elif should_match and expected_tool not in tool_names:
                print(f"  ✗ Wrong tools! Expected {expected_tool}")
            elif not should_match:
                print(f"  ⚠ Unexpected match (expected no match)")
        else:
            print(f"  - No tools matched")
            if should_match:
                print(f"  ✗ Should have matched {expected_tool}")
            else:
                print(f"  ✓ Correct! (no match expected)")

async def test_tool_execution():
    """Test tool execution (requires actual APIs to be running)"""
    print("\n" + "=" * 60)
    print("TESTING TOOL EXECUTION")
    print("=" * 60)
    print("\nNote: This requires actual APIs to be running")
    
    router = get_tool_router()
    
    # Test weather query
    query = "What's the current temperature?"
    print(f"\nQuery: '{query}'")
    
    try:
        tool_results, tool_context = await router.route_query(query)
        
        if tool_results:
            print(f"\nTool Results:")
            for result in tool_results:
                tool_name = result['metadata']['tool']
                success = result['success']
                print(f"  - {tool_name}: {'✓ SUCCESS' if success else '✗ FAILED'}")
                
                if success:
                    print(f"    Data available: {bool(result.get('data'))}")
                else:
                    print(f"    Error: {result.get('error')}")
            
            if tool_context:
                print(f"\nContext for LLM ({len(tool_context)} chars):")
                print(tool_context[:200] + "..." if len(tool_context) > 200 else tool_context)
        else:
            print("  No tools executed")
            
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()

async def test_health_checks():
    """Test health checks for all tools"""
    print("\n" + "=" * 60)
    print("TESTING TOOL HEALTH CHECKS")
    print("=" * 60)
    
    router = get_tool_router()
    
    print(f"\nRegistered tools: {router.get_active_tools()}")
    
    health_status = await router.health_check_all()
    
    print("\nHealth Status:")
    for tool_name, is_healthy in health_status.items():
        status = "✓ HEALTHY" if is_healthy else "✗ UNHEALTHY"
        print(f"  - {tool_name}: {status}")

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("INSIGHTCHAT TOOLS TEST SUITE")
    print("=" * 60)
    
    # Test 1: Intent Detection
    test_tool_detection()
    
    # Test 2: Health Checks (async)
    print("\n")
    asyncio.run(test_health_checks())
    
    # Test 3: Tool Execution (async, requires APIs)
    print("\n")
    try:
        asyncio.run(test_tool_execution())
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
    
    print("\n" + "=" * 60)
    print("TESTS COMPLETE")
    print("=" * 60)
    print("\nTo test with live APIs:")
    print("1. Start PyWeather: cd ../pyweather && make dev")
    print("2. Set TOOL_WEATHER_ENABLED=true in .env")
    print("3. Run this script again")
    print()

if __name__ == "__main__":
    main()
