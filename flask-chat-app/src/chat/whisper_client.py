"""Whisper transcription service client."""

import httpx
from typing import Optional
import os


class WhisperClient:
    """Client for interacting with the Whisper transcription service."""

    def __init__(self, base_url: Optional[str] = None, timeout: Optional[int] = None):
        self.base_url = base_url or os.getenv("WHISPER_URL", "https://whisper.hlab.cam")
        self.timeout = timeout or int(os.getenv("SERVICE_TIMEOUT", "60"))

    async def transcribe(
        self, audio_file: bytes, filename: str, language: Optional[str] = None
    ) -> dict:
        """
        Transcribe audio file using Whisper.

        Args:
            audio_file: Audio file content as bytes
            filename: Original filename
            language: Optional language code (e.g., 'en', 'es', 'fr')

        Returns:
            dict with transcription result containing 'text', 'language', 'duration'

        Raises:
            httpx.HTTPError: If the request fails
        """
        # Determine mime type from filename
        mime_type = "audio/webm"
        if filename.endswith('.wav'):
            mime_type = "audio/wav"
        elif filename.endswith('.mp3'):
            mime_type = "audio/mpeg"
        elif filename.endswith('.m4a'):
            mime_type = "audio/mp4"
        elif filename.endswith('.ogg'):
            mime_type = "audio/ogg"
        elif filename.endswith('.opus'):
            mime_type = "audio/opus"
        elif filename.endswith('.flac'):
            mime_type = "audio/flac"
            
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            files = {"file": (filename, audio_file, mime_type)}
            data = {"task": "transcribe"}
            if language:
                data["language"] = language

            response = await client.post(
                f"{self.base_url}/transcribe",
                files=files,
                data=data,
            )
            
            # Log response for debugging
            if response.status_code != 200:
                print(f"Whisper API error: {response.status_code} - {response.text}")
            
            response.raise_for_status()
            return response.json()
