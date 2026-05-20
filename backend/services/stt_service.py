import os
import tempfile
from groq import AsyncGroq

client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY", "mock_key"))

async def speech_to_text(audio_data: bytes) -> str:
    """Converts audio bytes to text using Groq's Whisper-large-v3 model."""
    if not audio_data:
        return ""
    
    if os.environ.get("GROQ_API_KEY", "mock_key") == "mock_key":
        return "System Warning: Provide GROQ API Key to enable STT."
        
    try:
        # Groq API requires a file object for STT
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f:
            f.write(audio_data)
            temp_path = f.name
            
        with open(temp_path, "rb") as audio_file:
            transcription = await client.audio.transcriptions.create(
                file=(os.path.basename(temp_path), audio_file.read()),
                model="whisper-large-v3",
                response_format="text"
            )
        
        os.remove(temp_path)
        return transcription
    except Exception as e:
        print(f"STT Error: {e}")
        return ""
