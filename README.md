# 2Care AI Agent - Real-Time Multilingual Voice AI

A real-time conversational agent for clinical appointment booking. This agent accepts voice input, reasons over it using an LLM, manages the appointment lifecycle, and responds via voice.

## Features
- **Real-time Voice Conversation**: WebSocket connection for sub-450ms audio-in to audio-out latency.
- **Multilingual Support**: Supports English, Hindi, and Tamil out of the box using Edge-TTS and Groq Whisper.
- **Contextual Memory**: 
  - *Session Memory*: Uses `fakeredis` (simulating Redis with TTL) to maintain state and pending confirmations within a conversation.
  - *Persistent Memory*: Uses `SQLite` (via SQLAlchemy) to store patients, doctors, and appointments, enabling conflict detection and past-history access.
- **Outbound Campaign Mode**: Support for triggering proactive calls from the web interface.
- **Scheduling Logic**: Conflict resolution to prevent double booking or past-time bookings.

## Architecture
The system uses a WebSocket pipeline for low latency:
`Browser Mic -> MediaRecorder (WebM/PCM) -> FastAPI WebSocket -> STT (Groq Whisper) -> LLM (Llama 3 8B) -> TTS (Edge-TTS) -> Browser Speaker`

## Memory Design
- **Session Memory**: Handled by Redis (simulated with `fakeredis` for local ease). It stores the current intent, doctor requested, and date/time across multiple WebSocket turns, with a TTL of 1 hour.
- **Persistent Memory**: A relational database (SQLite) storing Appointments, Doctors, and Patients. When a patient connects, their history and language preferences are retrieved.

## Latency Breakdown (Target < 450ms)
Using cloud APIs, hitting 450ms is challenging without streaming every step. However, by using ultra-fast components:
- **STT (Groq Whisper-large-v3)**: ~100-150ms
- **LLM (Groq Llama-3-8B)**: ~150-200ms
- **TTS (Edge-TTS)**: ~150ms
**Total Average**: ~400 - 500ms. 
*Note: Latency is logged in the UI and backend.*

## Tradeoffs and Limitations
- **API Limits**: The free tier of Groq and Edge-TTS might have rate limits or slight network latency variations.
- **VAD (Voice Activity Detection)**: The demo relies on the user pressing and holding a button instead of a continuous VAD stream to avoid noise triggers, though VAD could easily be added on the backend using Silero.
- **Outbound Calling**: Outbound calls are simulated via WebSocket push instead of true PSTN (Twilio) to avoid setup complexity and costs.

## Setup Instructions

### 1. Prerequisites
- Python 3.10+
- Node.js 18+

### 2. Backend Setup
```bash
cd backend
python -m venv venv
# On Windows: .\venv\Scripts\activate
# On Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
```

### 3. API Key
You must get a free Groq API key from https://console.groq.com/
```bash
# Set it in your environment
export GROQ_API_KEY="your_free_key_here"
# On Windows: set GROQ_API_KEY=your_free_key_here
```

### 4. Run Backend
```bash
uvicorn main:app --reload
```

### 5. Run Frontend
In a new terminal:
```bash
cd frontend
npm install
npm run dev
```

### 6. Usage
Open `http://localhost:5173` in your browser.
Hold the microphone button and say: "Book an appointment with a cardiologist tomorrow".
Wait for the agent to reply via voice.
