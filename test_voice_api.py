#!/usr/bin/env python3
"""
Test script for the voice query API endpoint.

Usage:
    # With pre-transcribed text:
    python test_voice_api.py --text "What's the weather like?"
    
    # With audio file:
    python test_voice_api.py --audio recording.wav
    
    # With broadcast to TTS:
    python test_voice_api.py --text "What's on my calendar today?" --broadcast
"""

import requests
import argparse
import json
import sys

def test_voice_query(text=None, audio_file=None, model=None, use_rag=True, broadcast=False, speaker=None, tts_model=None, engine=None, api_url="http://localhost:5030"):
    """
    Test the /api/voice-query endpoint.
    
    Args:
        text: Pre-transcribed text query
        audio_file: Path to audio file to transcribe
        model: Optional LLM model name
        use_rag: Whether to use RAG context
        broadcast: Whether to broadcast response to TTS
        speaker: TTS speaker/media player (required if broadcast=True)
        tts_model: Optional TTS model name
        engine: Optional TTS engine name
        api_url: Base URL of the API
    """
    endpoint = f"{api_url}/api/voice-query"
    
    try:
        if audio_file:
            # Send audio file
            print(f"Sending audio file: {audio_file}")
            with open(audio_file, 'rb') as f:
                files = {'file': (audio_file, f, 'audio/wav')}
                data = {
                    'use_rag': str(use_rag).lower(),
                    'broadcast': str(broadcast).lower()
                }
                if model:
                    data['model'] = model
                if speaker:
                    data['speaker'] = speaker
                if tts_model:
                    data['tts_model'] = tts_model
                if engine:
                    data['engine'] = engine
                
                response = requests.post(endpoint, files=files, data=data)
        else:
            # Send text query
            print(f"Sending text query: {text}")
            payload = {
                'text': text,
                'use_rag': use_rag,
                'broadcast': broadcast
            }
            if model:
                payload['model'] = model
            if speaker:
                payload['speaker'] = speaker
            if tts_model:
                payload['tts_model'] = tts_model
            if engine:
                payload['engine'] = engine
            
            response = requests.post(endpoint, json=payload)
        
        # Check response
        response.raise_for_status()
        result = response.json()
        
        # Display results
        print("\n" + "="*60)
        print("SUCCESS!")
        print("="*60)
        print(f"\nQuery: {result.get('query')}")
        print(f"\nResponse:\n{result.get('response')}")
        
        if result.get('tools_used'):
            print(f"\nTools Used: {', '.join(result.get('tools_used'))}")
        
        if result.get('broadcast_sent'):
            print("\n✓ Response broadcast to TTS speakers")
        
        print("="*60)
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"\nERROR: Request failed")
        print(f"Status: {e.response.status_code if hasattr(e, 'response') else 'N/A'}")
        if hasattr(e, 'response') and e.response.text:
            try:
                error_data = e.response.json()
                print(f"Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"Response: {e.response.text}")
        else:
            print(f"Error: {str(e)}")
        return None
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        return None


def main():
    parser = argparse.ArgumentParser(description='Test the voice query API')
    parser.add_argument('--text', type=str, help='Text query to send')
    parser.add_argument('--audio', type=str, help='Audio file path to transcribe and query')
    parser.add_argument('--model', type=str, help='LLM model to use (optional)')
    parser.add_argument('--no-rag', action='store_true', help='Disable RAG context')
    parser.add_argument('--broadcast', action='store_true', help='Broadcast response to TTS')
    parser.add_argument('--speaker', type=str, help='TTS speaker/media player (e.g., media_player.bedoffice)')
    parser.add_argument('--tts-model', type=str, help='TTS model name (e.g., random)')
    parser.add_argument('--engine', type=str, help='TTS engine name (optional)')
    parser.add_argument('--api-url', type=str, default='http://localhost:5030', 
                       help='API base URL (default: http://localhost:5030)')
    
    args = parser.parse_args()
    
    if not args.text and not args.audio:
        parser.error("Either --text or --audio must be provided")
    
    if args.text and args.audio:
        parser.error("Cannot specify both --text and --audio")
    
    test_voice_query(
        text=args.text,
        audio_file=args.audio,
        model=args.model,
        use_rag=not args.no_rag,
        broadcast=args.broadcast,
        speaker=args.speaker,
        tts_model=args.tts_model,
        engine=args.engine,
        api_url=args.api_url
    )


if __name__ == '__main__':
    main()
