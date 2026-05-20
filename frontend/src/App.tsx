import { useState, useRef, useEffect } from 'react';
import './App.css';

interface Message {
  role: 'user' | 'agent';
  content: string;
}

interface Metrics {
  stt_ms: number;
  llm_ms: number;
  tts_ms: number;
  total_ms: number;
}

function App() {
  const [isRecording, setIsRecording] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    // Connect to WebSocket on mount
    const ws = new WebSocket('wss://twocare-voice-agent-j63x.onrender.com/ws/audio');
    
    ws.onopen = () => {
      console.log("Connected to WebSocket");
    };

    ws.onmessage = async (event) => {
      if (typeof event.data === "string") {
        const data = JSON.parse(event.data);
        if (data.type === 'text') {
          setMessages(prev => [...prev, { role: data.role, content: data.content }]);
        } else if (data.type === 'metrics') {
          setMetrics({
            stt_ms: data.stt_ms,
            llm_ms: data.llm_ms,
            tts_ms: data.tts_ms,
            total_ms: data.total_ms
          });
        }
      } else if (event.data instanceof Blob) {
        // Play received audio (Agent response)
        const audioUrl = URL.createObjectURL(event.data);
        const audio = new Audio(audioUrl);
        audio.play();
      }
    };

    ws.onclose = () => console.log("WebSocket disconnected");
    wsRef.current = ws;

    return () => {
      ws.close();
    };
  }, []);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        // Send audio file to server via WebSocket
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(audioBlob);
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error("Microphone access error:", err);
      alert("Failed to access microphone.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      // Stop all tracks to release mic
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
    }
  };

  const triggerOutbound = async () => {
    try {
      await fetch('https://twocare-voice-agent-j63x.onrender.com/outbound_call?patient_id=1', { method: 'POST' });
      setMessages(prev => [...prev, { role: 'agent', content: 'Outbound campaign triggered.' }]);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="app-container">
      <header className="header">
        <div className="logo-container">
          <div className="pulse-dot"></div>
          <h1>2Care AI Agent</h1>
        </div>
        <button className="outbound-btn" onClick={triggerOutbound}>
          Trigger Outbound Call
        </button>
      </header>

      <main className="main-content">
        <div className="chat-container">
          {messages.length === 0 ? (
            <div className="empty-state">
              <p>Press the microphone and speak to start booking your appointment.</p>
              <span className="subtitle">e.g. "I want to see a cardiologist tomorrow"</span>
            </div>
          ) : (
            messages.map((msg, index) => (
              <div key={index} className={`message ${msg.role}`}>
                <div className="message-bubble">{msg.content}</div>
              </div>
            ))
          )}
        </div>

        <div className="controls-container">
          <button 
            className={`mic-button ${isRecording ? 'recording' : ''}`}
            onMouseDown={startRecording}
            onMouseUp={stopRecording}
            onTouchStart={startRecording}
            onTouchEnd={stopRecording}
          >
            <div className="mic-icon">
              {isRecording ? "Listening..." : "Hold to Speak"}
            </div>
          </button>
          
          <div className="metrics-panel">
            <h3>System Latency</h3>
            {metrics ? (
              <div className="metrics-grid">
                <div className="metric-item">
                  <span className="metric-label">STT</span>
                  <span className="metric-value">{metrics.stt_ms} ms</span>
                </div>
                <div className="metric-item">
                  <span className="metric-label">LLM</span>
                  <span className="metric-value">{metrics.llm_ms} ms</span>
                </div>
                <div className="metric-item">
                  <span className="metric-label">TTS</span>
                  <span className="metric-value">{metrics.tts_ms} ms</span>
                </div>
                <div className="metric-item total">
                  <span className="metric-label">Total</span>
                  <span className="metric-value">{metrics.total_ms} ms</span>
                </div>
              </div>
            ) : (
              <p className="no-metrics">Awaiting interaction...</p>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
