# -*- coding: utf-8 -*-
import os
import re
import sys
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx

from core.persona import PERSONAS
from tts.tts_service import synthesize_speech_base64

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")

app = FastAPI(title="Project BUKI - Local LLM & TTS Companion Engine")

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

def parse_dialogue_and_actions(text: str) -> Tuple[str, List[str]]:
    """
    Separates spoken dialogue from action/narration tags.
    - Actions: enclosed in (...), [...], *...*, <...>
    - Dialogue: spoken text outside of action brackets.
    """
    # 1. Extract action cues
    action_matches = re.findall(r'[\(\[\*]([^\)\]\*]+)[\)\]\*]', text)
    actions = [a.strip() for a in action_matches if a.strip()]

    # 2. Strip action blocks completely for TTS
    spoken = re.sub(r'\([^\)]*\)|\[[^\]]*\]|\*[^\*]*\*|\<[^\>]*\>', '', text).strip()

    # 3. Clean markdown and special symbols
    clean_speech = re.sub(r'[\*\#\_`~]', '', spoken).strip()
    
    # 4. Ensure there is actual pronounceable text (Hangul, English, digits)
    has_pronounceable = bool(re.search(r'[가-힣a-zA-Z0-9]', clean_speech))
    if not has_pronounceable:
        clean_speech = ""

    return clean_speech, actions

# --- REST ENDPOINTS ---

@app.get("/api/info")
async def get_system_info():
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
    speech_text, _ = parse_dialogue_and_actions(req.text)
    if not speech_text:
        speech_text = req.text
        
    audio_base64 = await synthesize_speech_base64(
        text=speech_text,
        voice=req.voice or "ko-KR-SunHiNeural",
        pitch=req.pitch or "+0Hz",
        rate=req.rate or "+0%"
    )
    if not audio_base64:
        raise HTTPException(status_code=500, detail="Failed to synthesize speech")
    return {"audio_base64": audio_base64, "spoken_text": speech_text}

@app.post("/api/chat/stream")
async def chat_stream(req: ChatStreamRequest):
    persona = PERSONAS.get(req.persona_id, PERSONAS["mesugaki"])
    model_to_use = req.model or persona.get("default_model", "gemma-mesugaki:latest")
    system_prompt = req.custom_system_prompt or persona.get("system_prompt", "")
    voice = persona.get("voice", "ko-KR-SunHiNeural")
    pitch = persona.get("voice_pitch", "+0Hz")
    rate = persona.get("voice_rate", "+0%")

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    if req.history:
        for h in req.history[-10:]:
            messages.append({"role": h.role, "content": h.content})
            
    messages.append({"role": "user", "content": req.message})

    async def sse_generator():
        sentence_buffer = ""
        full_response_text = ""
        sentence_index = 0

        try:
            init_event = {
                "type": "init",
                "persona_id": persona["id"],
                "persona_name": persona["name"],
                "model": model_to_use
            }
            yield f"data: {json.dumps(init_event, ensure_ascii=False)}\n\n"

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

                            # Stream raw token for UI rendering
                            token_event = {"type": "token", "token": token}
                            yield f"data: {json.dumps(token_event, ensure_ascii=False)}\n\n"

                            # Sentence boundary: . ! ? \n or closing parenthesis + punctuation
                            if req.voice_enabled and re.search(r'([.!?！？\n]+|\~+)\s*$', sentence_buffer):
                                speech_to_synthesize, detected_actions = parse_dialogue_and_actions(sentence_buffer)
                                raw_sentence = sentence_buffer.strip()
                                sentence_buffer = ""

                                if speech_to_synthesize:
                                    cur_idx = sentence_index
                                    sentence_index += 1

                                    audio_b64 = await synthesize_speech_base64(speech_to_synthesize, voice, pitch, rate)
                                    if audio_b64:
                                        audio_event = {
                                            "type": "audio",
                                            "index": cur_idx,
                                            "raw_text": raw_sentence,
                                            "spoken_text": speech_to_synthesize,
                                            "actions": detected_actions,
                                            "audio_base64": audio_b64
                                        }
                                        yield f"data: {json.dumps(audio_event, ensure_ascii=False)}\n\n"
                                elif detected_actions:
                                    # Action-only event (e.g. avatar expression change without speech)
                                    action_event = {
                                        "type": "action_cue",
                                        "actions": detected_actions
                                    }
                                    yield f"data: {json.dumps(action_event, ensure_ascii=False)}\n\n"

                        if chunk_json.get("done", False):
                            break

            # Flush remaining buffer
            if req.voice_enabled and sentence_buffer.strip():
                speech_to_synthesize, detected_actions = parse_dialogue_and_actions(sentence_buffer)
                if speech_to_synthesize:
                    audio_b64 = await synthesize_speech_base64(speech_to_synthesize, voice, pitch, rate)
                    if audio_b64:
                        audio_event = {
                            "type": "audio",
                            "index": sentence_index,
                            "raw_text": sentence_buffer.strip(),
                            "spoken_text": speech_to_synthesize,
                            "actions": detected_actions,
                            "audio_base64": audio_b64
                        }
                        yield f"data: {json.dumps(audio_event, ensure_ascii=False)}\n\n"

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