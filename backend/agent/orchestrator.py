import time
import asyncio
import uuid
import logging
from fastapi import WebSocket
from agent.llm_agent import Agent
from services.stt_service import speech_to_text
from services.tts_service import text_to_speech

logger = logging.getLogger(__name__)

class RealTimeOrchestrator:
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.session_id = str(uuid.uuid4())
        # Hardcoding a patient ID for demo purposes
        self.patient_id = 1 
        self.agent = Agent(self.session_id, self.patient_id)
        
    async def start_session(self):
        logger.info(f"Started session {self.session_id}")
        
    async def process_audio_chunk(self, audio_data: bytes):
        """Processes an incoming audio chunk through the entire pipeline."""
        start_time = time.time()
        
        # 1. STT
        stt_start = time.time()
        text = await speech_to_text(audio_data)
        stt_latency = time.time() - stt_start
        logger.info(f"STT Latency: {stt_latency*1000:.2f} ms | Text: {text}")
        
        if not text or len(text.strip()) < 2:
            return # Ignore silence or noise
            
        # 2. Agent / LLM
        llm_start = time.time()
        agent_response = await self.agent.process_text(text)
        llm_latency = time.time() - llm_start
        logger.info(f"LLM Latency: {llm_latency*1000:.2f} ms | Response: {agent_response}")
        
        # Send text back to client for UI
        await self.websocket.send_json({"type": "text", "role": "user", "content": text})
        await self.websocket.send_json({"type": "text", "role": "agent", "content": agent_response})
        
        # 3. TTS
        tts_start = time.time()
        audio_response = await text_to_speech(agent_response)
        tts_latency = time.time() - tts_start
        logger.info(f"TTS Latency: {tts_latency*1000:.2f} ms")
        
        # Send audio back to client
        if audio_response:
            # We send raw MP3 bytes
            await self.websocket.send_bytes(audio_response)
            
        total_latency = time.time() - start_time
        logger.info(f"Total Pipeline Latency (Speech end to audio out): {total_latency*1000:.2f} ms")
        
        # Send latency metrics for frontend display
        await self.websocket.send_json({
            "type": "metrics",
            "stt_ms": round(stt_latency*1000, 2),
            "llm_ms": round(llm_latency*1000, 2),
            "tts_ms": round(tts_latency*1000, 2),
            "total_ms": round(total_latency*1000, 2)
        })
