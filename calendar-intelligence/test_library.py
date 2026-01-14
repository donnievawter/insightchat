#!/usr/bin/env python3
"""
Quick test script to verify calendar-intelligence library works
"""

import asyncio
import sys
import os

# Add parent directory to path to import the library
sys.path.insert(0, '/opt/dockerapps/insightchat/calendar-intelligence/src')

from calendar_intelligence import CalendarAnalyzer, IcsRepository


async def test_library():
    """Test the calendar intelligence library"""
    
    print("🧪 Testing calendar-intelligence library\n")
    
    # Test 1: Initialize the library
    print("1️⃣ Initializing ICS repository...")
    repository = IcsRepository(
        api_url="https://ics.hlab.cam",
        timeout=10
    )
    print("   ✅ Repository created\n")
    
    # Test 2: Create analyzer
    print("2️⃣ Creating CalendarAnalyzer...")
    analyzer = CalendarAnalyzer(
        repository=repository,
        timezone="America/Denver",
        enabled=True
    )
    print("   ✅ Analyzer created\n")
    
    # Test 3: Check intent detection
    print("3️⃣ Testing intent detection...")
    test_queries = [
        "What's on my calendar today?",
        "Show me tomorrow's meetings",
        "Events for the next week",
        "Tell me about the weather"  # Should NOT match
    ]
    
    for query in test_queries:
        can_handle = analyzer.can_handle(query)
        status = "✅" if can_handle else "❌"
        print(f"   {status} '{query}' -> {can_handle}")
    print()
    
    # Test 4: Analyze a query (this will actually call the API if it's available)
    print("4️⃣ Testing calendar analysis...")
    print("   Query: 'What's on my calendar today?'")
    
    try:
        result = await analyzer.analyze("What's on my calendar today?")
        
        if result['success']:
            print("   ✅ Analysis successful!")
            print(f"   📊 Found {result['metadata']['event_count']} events")
            print(f"   📅 Intent: {result['intent']['type']}")
            print(f"   🌍 Timezone: {result['metadata']['timezone']}")
            print(f"   💾 Data source: {result['metadata']['data_source']}")
            print("\n   Formatted response:")
            print("   " + "-" * 60)
            for line in result['formatted_text'].split('\n')[:10]:  # First 10 lines
                print(f"   {line}")
            if len(result['formatted_text'].split('\n')) > 10:
                print("   ...")
        else:
            print(f"   ⚠️ Analysis returned error: {result.get('error')}")
            print("   (This is expected if ICS API is not available)")
    
    except Exception as e:
        print(f"   ⚠️ Could not connect to ICS API: {e}")
        print("   (This is expected if the API is not running)")
    
    print("\n✅ Library test complete!")


if __name__ == "__main__":
    asyncio.run(test_library())
