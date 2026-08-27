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
from tts.tts_manager import synthesize_smart_speech
from tts.gpt_sovits_service import is_gpt_sovits_alive, GPT_SOVITS_URL

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
    tts_engine: Optional[str] = "gpt_sovits"
    custom_system_prompt: Optional[str] = None

class DirectTTSRequest(BaseModel):
    text: str
    persona_id: Optional[str] = "mesugaki"
    tts_engine: Optional[str] = "gpt_sovits"

class ScriptParseRequest(BaseModel):
    script_text: str
    persona_id: Optional[str] = "mesugaki"

class ScriptSegmentTTSRequest(BaseModel):
    dialogue: str
    persona_id: Optional[str] = "mesugaki"
    inferred_emotion: Optional[str] = "default"
    tts_engine: Optional[str] = "gpt_sovits"
    context_narration: Optional[str] = ""

def is_bracket_balanced(text: str) -> bool:
    """Checks if all opening action delimiters are properly closed."""
    if text.count('(') > text.count(')'): return False
    if text.count('[') > text.count(']'): return False
    if text.count('{') > text.count('}'): return False
    if text.count('〈') > text.count('〉'): return False
    if text.count('《') > text.count('》'): return False
    if text.count('*') % 2 != 0: return False
    return True

def is_safe_sentence_boundary(buffer: str) -> bool:
    """Returns True only when buffer ends with punctuation AND brackets are balanced."""
    if not is_bracket_balanced(buffer):
        return False
    if re.search(r'([.!?！？\n]+)\s*$', buffer):
        return True
    if re.search(r'(~+)\s*$', buffer) and len(buffer.strip()) >= 6:
        return True
    return False

def parse_dialogue_and_actions(text: str) -> Tuple[str, List[str]]:
    """Separates spoken dialogue from action/narration tags for live chat."""
    action_matches = re.findall(r'[\(\[\*〈《]([^\)\]\*〉》]+)[\)\]\*〉》]', text)
    actions = [a.strip() for a in action_matches if a.strip()]

    cleaned = re.sub(r'\([^\)]*\)|\[[^\]]*\]|\*[^\*]*\*|\<[^\>]*\>|〈[^〉]*〉|《[^》]*》', ' ', text)
    cleaned = re.sub(r'[\(\[\*〈《][^\)\]\*〉》]*$', '', cleaned)
    cleaned = re.sub(r'^(대사|말|응답)\s*:\s*', '', cleaned)
    clean_speech = re.sub(r'[\*\#\_`"]', '', cleaned).strip()
    clean_speech = re.sub(r'\s+', ' ', clean_speech).strip()
    has_pronounceable = bool(re.search(r'[가-힣a-zA-Z0-9]', clean_speech))
    if not has_pronounceable:
        clean_speech = ""
    return clean_speech, actions

def parse_script_into_segments(script_text: str, default_persona: str = "mesugaki") -> List[Dict[str, Any]]:
    """
    Parses a novel/script into sequential segments:
    - Text in double quotes "..." is treated as spoken dialogue.
    - Text outside quotes is context narration/situation.
    - Infers emotional tone from surrounding situation for rich neural acting.
    """
    normalized = script_text.replace('“', '"').replace('”', '"').replace('「', '"').replace('」', '"').replace('『', '"').replace('』', '"')
    parts = re.split(r'("[^"]+")', normalized)
    
    segments = []
    current_context = ""
    seg_id = 0
    
    for part in parts:
        part_str = part.strip()
        if not part_str:
            continue
            
        if part_str.startswith('"') and part_str.endswith('"') and len(part_str) >= 2:
            dialogue_text = part_str[1:-1].strip()
            
            # Emotion inference from surrounding context narration
            inferred_emotion = "default"
            ctx_lower = current_context.lower()
            
            if any(k in ctx_lower for k in ["비웃", "피식", "혀를 차", "한심", "콧방귀", "멍청", "허접", "풋", "깔보", "우쭐"]):
                inferred_emotion = "smug"
            elif any(k in ctx_lower for k in ["놀리", "장난", "귓가", "속삭", "살살", "우후후", "쿠후후", "킥킥", "쿡쿡"]):
                inferred_emotion = "tease"
            elif any(k in ctx_lower for k in ["화", "버럭", "소리치", "짜증", "인상", "노려보", "째려", "가만 안"]):
                inferred_emotion = "angry"
            elif any(k in ctx_lower for k in ["얼굴을 붉", "부끄러", "더듬", "우물쭈물", "시선을 피", "당황", "홍조"]):
                inferred_emotion = "shy"
                
            segments.append({
                "id": seg_id,
                "type": "dialogue",
                "text": part_str,
                "spoken_text": dialogue_text,
                "context_narration": current_context,
                "inferred_emotion": inferred_emotion,
                "persona_id": default_persona
            })
            seg_id += 1
            current_context = ""
        else:
            narration_text = part_str
            current_context = narration_text
            segments.append({
                "id": seg_id,
                "type": "narration",
                "text": narration_text,
                "spoken_text": "",
                "context_narration": "",
                "inferred_emotion": "none",
                "persona_id": default_persona
            })
            seg_id += 1
            
    return segments

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

    gpt_sovits_status = await is_gpt_sovits_alive()

    return {
        "personas": list(PERSONAS.values()),
        "models": models,
        "default_persona": "mesugaki",
        "default_tts_engine": "gpt_sovits",
        "gpt_sovits_url": GPT_SOVITS_URL,
        "gpt_sovits_online": gpt_sovits_status,
        "available_tts_engines": [
            {"id": "gpt_sovits", "name": "GPT-SoVITS (3초 제로샷 - 기본)"},
            {"id": "auto", "name": "자동 (GPT-SoVITS ➔ Edge-TTS 폴백)"},
            {"id": "edge_tts", "name": "Edge-TTS (초고속 기본 음성)"}
        ]
    }

@app.post("/api/tts")
async def direct_tts(req: DirectTTSRequest):
    persona = PERSONAS.get(req.persona_id, PERSONAS["mesugaki"])
    speech_text, actions = parse_dialogue_and_actions(req.text)
    if not speech_text:
        return {"audio_base64": "", "spoken_text": "", "actions": actions, "engine_used": "none"}
        
    audio_base64, engine_used = await synthesize_smart_speech(
        text=speech_text,
        persona_id=req.persona_id,
        persona_config=persona,
        detected_actions=actions,
        preferred_engine=req.tts_engine or "gpt_sovits"
    )
    if not audio_base64:
        raise HTTPException(status_code=500, detail="Failed to synthesize speech")
    return {"audio_base64": audio_base64, "spoken_text": speech_text, "engine_used": engine_used}

@app.post("/api/script/parse")
async def parse_script_endpoint(req: ScriptParseRequest):
    segments = parse_script_into_segments(req.script_text, req.persona_id or "mesugaki")
    total_dialogues = sum(1 for s in segments if s["type"] == "dialogue")
    return {"segments": segments, "total_dialogues": total_dialogues}

@app.post("/api/script/tts_segment")
async def tts_segment_endpoint(req: ScriptSegmentTTSRequest):
    persona = PERSONAS.get(req.persona_id, PERSONAS["mesugaki"])
    audio_base64, engine_used = await synthesize_smart_speech(
        text=req.dialogue,
        persona_id=req.persona_id,
        persona_config=persona,
        detected_actions=[req.context_narration] if req.context_narration else [],
        preferred_engine=req.tts_engine or "gpt_sovits",
        override_emotion=req.inferred_emotion if req.inferred_emotion != "default" else None
    )
    if not audio_base64:
        raise HTTPException(status_code=500, detail="Failed to synthesize segment speech")
    return {
        "audio_base64": audio_base64,
        "spoken_text": req.dialogue,
        "engine_used": engine_used,
        "inferred_emotion": req.inferred_emotion
    }

@app.post("/api/chat/stream")
async def chat_stream(req: ChatStreamRequest):
    persona = PERSONAS.get(req.persona_id, PERSONAS["mesugaki"])
    model_to_use = req.model or persona.get("default_model", "gemma-mesugaki:latest")
    system_prompt = req.custom_system_prompt or persona.get("system_prompt", "")
    tts_engine_pref = req.tts_engine or "gpt_sovits"

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
                "model": model_to_use,
                "tts_engine": tts_engine_pref
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

                            token_event = {"type": "token", "token": token}
                            yield f"data: {json.dumps(token_event, ensure_ascii=False)}\n\n"

                            if req.voice_enabled and is_safe_sentence_boundary(sentence_buffer):
                                speech_to_synthesize, detected_actions = parse_dialogue_and_actions(sentence_buffer)
                                raw_sentence = sentence_buffer.strip()
                                sentence_buffer = ""

                                if speech_to_synthesize:
                                    cur_idx = sentence_index
                                    sentence_index += 1

                                    audio_b64, engine_used = await synthesize_smart_speech(
                                        text=speech_to_synthesize,
                                        persona_id=persona["id"],
                                        persona_config=persona,
                                        detected_actions=detected_actions,
                                        preferred_engine=tts_engine_pref
                                    )
                                    if audio_b64:
                                        audio_event = {
                                            "type": "audio",
                                            "index": cur_idx,
                                            "raw_text": raw_sentence,
                                            "spoken_text": speech_to_synthesize,
                                            "actions": detected_actions,
                                            "engine_used": engine_used,
                                            "audio_base64": audio_b64
                                        }
                                        yield f"data: {json.dumps(audio_event, ensure_ascii=False)}\n\n"
                                elif detected_actions:
                                    action_event = {
                                        "type": "action_cue",
                                        "actions": detected_actions
                                    }
                                    yield f"data: {json.dumps(action_event, ensure_ascii=False)}\n\n"

                        if chunk_json.get("done", False):
                            break

            if req.voice_enabled and sentence_buffer.strip():
                speech_to_synthesize, detected_actions = parse_dialogue_and_actions(sentence_buffer)
                if speech_to_synthesize:
                    audio_b64, engine_used = await synthesize_smart_speech(
                        text=speech_to_synthesize,
                        persona_id=persona["id"],
                        persona_config=persona,
                        detected_actions=detected_actions,
                        preferred_engine=tts_engine_pref
                    )
                    if audio_b64:
                        audio_event = {
                            "type": "audio",
                            "index": sentence_index,
                            "raw_text": sentence_buffer.strip(),
                            "spoken_text": speech_to_synthesize,
                            "actions": detected_actions,
                            "engine_used": engine_used,
                            "audio_base64": audio_b64
                        }
                        yield f"data: {json.dumps(audio_event, ensure_ascii=False)}\n\n"
                elif detected_actions:
                    action_event = {
                        "type": "action_cue",
                        "actions": detected_actions
                    }
                    yield f"data: {json.dumps(action_event, ensure_ascii=False)}\n\n"

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