# TTS Engine Parameter Support

**Date:** January 30, 2026

## Summary

Added support for the optional `engine` parameter in TTS speak endpoint calls to match the updated contract specification.

## Updated TTS Contract

The TTS speak endpoint now supports the following payload structure:

```json
{
  "text": "string",
  "model_name": "string",
  "speaker": "string",
  "override": false,
  "engine": "string"
}
```

## Changes Made

### 1. Voice Query API Endpoint (`flask-chat-app/src/chat/routes.py`)

- Added extraction of optional `engine` parameter from request inputs (both form data and JSON)
- Updated TTS broadcast payload to include `engine` field when provided
- Maintained backward compatibility - parameter is optional

**Key Implementation:**
```python
# Extract engine from request
tts_engine = request.form.get('engine')  # or data.get('engine')

# Include in TTS payload if provided
if tts_engine:
    tts_payload["engine"] = tts_engine
```

### 2. Test Script (`test_voice_api.py`)

- Added `engine` parameter to `test_voice_query()` function
- Updated both audio and text query paths to pass engine parameter
- Added `--engine` CLI argument for testing

**Usage Example:**
```bash
python test_voice_api.py \
  --text "What's the weather today?" \
  --broadcast \
  --speaker "media_player.bedroom" \
  --tts-model "random" \
  --engine "piper"
```

## Backward Compatibility

All changes are backward compatible. The `engine` parameter is optional and only included in API calls when explicitly provided by the client.

## Testing

Test the new parameter using the updated test script:

```bash
# With engine parameter
python test_voice_api.py --text "Test message" --broadcast --speaker "media_player.office" --engine "piper"

# Without engine parameter (backward compatible)
python test_voice_api.py --text "Test message" --broadcast --speaker "media_player.office"
```

## Files Modified

- `flask-chat-app/src/chat/routes.py` - Voice query endpoint implementation
- `test_voice_api.py` - Test script with engine parameter support
