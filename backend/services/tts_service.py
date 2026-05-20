import os
import edge_tts
import tempfile

async def text_to_speech(text: str) -> bytes:
    """Converts text to speech using edge-tts. Returns MP3 audio bytes."""
    if not text:
        return b""
        
    try:
        # Detect language loosely or default to a good multilingual voice.
        # Edge TTS has voices like en-US-AriaNeural, hi-IN-SwaraNeural, ta-IN-PallaviNeural.
        # We can dynamically select the voice if we wanted to detect language, but for simplicity
        # we can just use an Indian English voice which handles English well and might do okay with Hindi words,
        # OR better yet, let's use a multilingual voice or pick one.
        # Actually edge_tts doesn't have a single universal voice, so we will use en-IN-NeerjaNeural.
        
        voice = "en-IN-NeerjaNeural" 
        # In a complete implementation, the LLM could return the language it spoke in
        # or we could use a fast language detection library on the text to pick:
        # if "है" in text: voice = "hi-IN-SwaraNeural"
        # elif "ஆ" in text: voice = "ta-IN-PallaviNeural"
        
        if any(c in text for c in "\u0900-\u097F"):
            voice = "hi-IN-SwaraNeural"
        elif any(c in text for c in "\u0B80-\u0BFF"):
            voice = "ta-IN-PallaviNeural"
            
        communicate = edge_tts.Communicate(text, voice)
        
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
                
        return audio_data
    except Exception as e:
        print(f"TTS Error: {e}")
        return b""
