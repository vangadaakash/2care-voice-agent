import json
import logging
import asyncio
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from agent.orchestrator import RealTimeOrchestrator
from memory.db_store import init_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Real-Time Multilingual Voice AI Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing database...")
    init_db()

@app.get("/")
def health():
    return {"status": "running"}

@app.websocket("/ws/audio")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection accepted.")
    orchestrator = RealTimeOrchestrator(websocket)
    try:
        await orchestrator.start_session()
        while True:
            data = await websocket.receive_bytes()
            # Feed incoming audio chunk to the orchestrator
            await orchestrator.process_audio_chunk(data)
    except WebSocketDisconnect:
        logger.info("Client disconnected.")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        try:
            await websocket.close()
        except RuntimeError:
            pass

# Endpoint to trigger outbound call simulation
@app.post("/outbound_call")
async def trigger_outbound_call(patient_id: int):
    # In a real app, this would use Twilio.
    # For demo, we just trigger a system event.
    return {"status": "outbound call initiated for patient", "patient_id": patient_id}
