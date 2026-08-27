# -*- coding: utf-8 -*-
import os
import re
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx

import sys; from pathlib import Path; sys.path.insert(0, str(Path(__file__).parent)); from core.persona import PERSONAS
from tts.tts_service import synthesize_speech_base64

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")

app = FastAPI(title="Project BUKI - Local LLM & TTS Companion Engine")

# CORS middleware for Tailscale and local access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatStreamRequest(BaseModel):
    message: str
    persona_id: Optional[str] = "mesugaki"
    model: Optional[str] = None
    history: Optional[List[ChatMessage]] = []
    voice_enabled: Optional[bool] = True
    custom_system_prompt: Optional[str] = None

class DirectTTSRequest(BaseModel):
    text: str
    voice: Optional[str] = "ko-KR-SunHiNeural"
    pitch: Optional[str] = "+0Hz"
    rate: Optional[str] = "+0%"

# --- REST ENDPOINTS ---

@app.get("/api/info")
async def get_system_info():
    """Returns available personas and local Ollama models."""
    models = []
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if res.status_code == 200:
                data = res.json()
                models = [m.get("name") for m in data.get("models", [])]
    except Exception as e:
        print(f"[Ollama Tags Error] {e}")

    return {
        "personas": list(PERSONAS.values()),
        "models": models,
        "default_persona": "mesugaki"
    }

@app.post("/api/tts")
async def direct_tts(req: DirectTTSRequest):
    """Direct text to speech synthesis endpoint."""
    audio_base64 = await synthesize_speech_base64(
        text=req.text,
        voice=req.voice or "ko-KR-SunHiNeural",
        pitch=req.pitch or "+0Hz",
        rate=req.rate or "+0%"
    )
    if not audio_base64:
        raise HTTPException(status_code=500, detail="Failed to synthesize speech")
    return {"audio_base64": audio_base64}

@app.post("/api/chat/stream")
async def chat_stream(req: ChatStreamRequest):
    """Streams LLM tokens + background sentence-level TTS audio chunks via SSE."""
    persona = PERSONAS.get(req.persona_id, PERSONAS["mesugaki"])
    model_to_use = req.model or persona.get("default_model", "gemma-mesugaki:latest")
    system_prompt = req.custom_system_prompt or persona.get("system_prompt", "")
    voice = persona.get("voice", "ko-KR-SunHiNeural")
    pitch = persona.get("voice_pitch", "+0Hz")
    rate = persona.get("voice_rate", "+0%")

    # Construct chat messages
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    if req.history:
        for h in req.history[-10:]: # Keep last 10 turns
            messages.append({"role": h.role, "content": h.content})
            
    messages.append({"role": "user", "content": req.message})

    async def sse_generator():
        sentence_buffer = ""
        full_response_text = ""
        sentence_index = 0
        audio_tasks = []

        try:
            # Yield persona info event
            init_event = {
                "type": "init",
                "persona_id": persona["id"],
                "persona_name": persona["name"],
                "model": model_to_use
            }
            yield f"data: {json.dumps(init_event, ensure_ascii=False)}\n\n"

            # Stream from Ollama API
            ollama_payload = {
                "model": model_to_use,
                "messages": messages,
                "stream": True,
                "options": {
                    "temperature": 0.85,
                    "top_p": 0.9,
                    "num_ctx": 4096
                }
            }

            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST",
                    f"{OLLAMA_BASE_URL}/api/chat",
                    json=ollama_payload
                ) as response:
                    if response.status_code != 200:
                        err_chunk = {"type": "error", "message": f"Ollama HTTP {response.status_code}"}
                        yield f"data: {json.dumps(err_chunk, ensure_ascii=False)}\n\n"
                        return

                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            chunk_json = json.loads(line)
                        except Exception:
                            continue

                        token = chunk_json.get("message", {}).get("content", "")
                        if token:
                            full_response_text += token
                            sentence_buffer += token

                            # Stream token to client
                            token_event = {"type": "token", "token": token}
                            yield f"data: {json.dumps(token_event, ensure_ascii=False)}\n\n"

                            # Sentence boundary check: . ! ? or \n
                            if req.voice_enabled and re.search(r'([.!?！？\n]+|\~+)\s*$', sentence_buffer):
                                sentence_to_speak = sentence_buffer.strip()
                                # Clean emojis/markdown for speech
                                clean_speech_text = re.sub(r'[\*\#\_`\[\]\(\)\{\}]', '', sentence_to_speak)
                                if len(clean_speech_text) >= 2:
                                    cur_idx = sentence_index
                                    sentence_index += 1
                                    sentence_buffer = ""

                                    # Synthesize TTS concurrently
                                    audio_b64 = await synthesize_speech_base64(clean_speech_text, voice, pitch, rate)
                                    if audio_b64:
                                        audio_event = {
                                            "type": "audio",
                                            "index": cur_idx,
                                            "text": sentence_to_speak,
                                            "audio_base64": audio_b64
                                        }
                                        yield f"data: {json.dumps(audio_event, ensure_ascii=False)}\n\n"

                        if chunk_json.get("done", False):
                            break

            # Flush remaining sentence buffer if any
            if req.voice_enabled and sentence_buffer.strip():
                clean_speech_text = re.sub(r'[\*\#\_`\[\]\(\)\{\}]', '', sentence_buffer.strip())
                if len(clean_speech_text) >= 1:
                    audio_b64 = await synthesize_speech_base64(clean_speech_text, voice, pitch, rate)
                    if audio_b64:
                        audio_event = {
                            "type": "audio",
                            "index": sentence_index,
                            "text": sentence_buffer.strip(),
                            "audio_base64": audio_b64
                        }
                        yield f"data: {json.dumps(audio_event, ensure_ascii=False)}\n\n"

            # Completion event
            done_event = {"type": "done", "full_text": full_response_text}
            yield f"data: {json.dumps(done_event, ensure_ascii=False)}\n\n"

        except Exception as e:
            err_event = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(err_event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

# --- STATIC FRONTEND SERVING ---
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(frontend_path / "index.html")