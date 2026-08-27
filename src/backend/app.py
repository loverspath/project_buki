# -*- coding: utf-8 -*-
"""
Project BUKI - Main FastAPI Application Server
Refactored: Decoupled configurations and business logic into ConfigManager.
"""
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

from core.config_manager import config
from core.persona import PERSONAS
from tts.tts_manager import synthesize_smart_speech
from tts.gpt_sovits_service import is_gpt_sovits_alive, GPT_SOVITS_URL
from tts.chatterbox_service import is_chatterbox_alive

app = FastAPI(title="Project BUKI - Local & Cloud LLM + TTS Companion Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for web client
frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")


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
    nsfw_mode: Optional[bool] = False
    acting_emotion: Optional[str] = "auto"


class DirectTTSRequest(BaseModel):
    text: str
    persona_id: Optional[str] = "mesugaki"
    tts_engine: Optional[str] = "gpt_sovits"
    nsfw_mode: Optional[bool] = False
    acting_emotion: Optional[str] = "auto"


class ScriptParseRequest(BaseModel):
    script_text: str
    persona_id: Optional[str] = "mesugaki"


class ScriptSegmentTTSRequest(BaseModel):
    dialogue: str
    persona_id: Optional[str] = "mesugaki"
    inferred_emotion: Optional[str] = "default"
    context_narration: Optional[str] = ""
    tts_engine: Optional[str] = "gpt_sovits"
    nsfw_mode: Optional[bool] = False
    acting_emotion: Optional[str] = "auto"


# --- HELPER FUNCTIONS ---

def parse_dialogue_and_actions(text: str) -> Tuple[str, List[str]]:
    """
    Extracts spoken dialogue (outside parentheses) and action cues (inside parentheses).
    Example: '(혀를 차며) ... 하아? 바보 오빠~' -> ('하아? 바보 오빠~', ['혀를 차며'])
    """
    action_matches = re.findall(r"\((.*?)\)", text)
    cleaned_speech = re.sub(r"\(.*?\)", "", text).strip()
    # Strip leading/trailing punctuation debris that causes TTS hallucination
    cleaned_speech = re.sub(r"^[\s.,~…·!?;:]+", "", cleaned_speech).strip()
    return cleaned_speech, action_matches


def is_safe_sentence_boundary(buffer: str) -> bool:
    """Checks if buffer has a complete sentence and not inside unclosed parenthesis."""
    if "(" in buffer and ")" not in buffer:
        return False
    return any(p in buffer for p in [".", "!", "?", "\n", "~", "…"])


def parse_script_into_segments(script_text: str, default_persona: str = "mesugaki") -> List[Dict[str, Any]]:
    """Parses raw script text into dialogue and narration segments with emotion analysis."""
    normalized = script_text.replace("“", '"').replace("”", '"').replace("「", '"').replace("」", '"').replace("『", '"').replace("』", '"')
    parts = re.split(r'(".*?")', normalized)
    
    segments = []
    seg_id = 0
    current_context = ""

    for part in parts:
        part_str = part.strip()
        if not part_str:
            continue
            
        if part_str.startswith('"') and part_str.endswith('"'):
            raw_dialogue = part_str[1:-1].strip()
            if not raw_dialogue:
                continue
            
            clean_speech, inline_actions = parse_dialogue_and_actions(raw_dialogue)
            action_text = " ".join(inline_actions)
            combined_ctx = f"{current_context} {action_text}".lower()
            
            # Delegate emotion inference to ConfigManager
            inferred_emotion = config.infer_emotion_from_context(combined_ctx)
                
            segments.append({
                "id": seg_id,
                "type": "dialogue",
                "text": part_str,
                "spoken_text": clean_speech or raw_dialogue,
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

@app.get("/")
async def root():
    index_file = frontend_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "Project BUKI Backend is running. Access /static/index.html"}


@app.get("/api/info")
async def get_system_info():
    local_models = []
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(f"{config.ollama_base_url}/api/tags")
            if res.status_code == 200:
                data = res.json()
                local_models = [m.get("name") for m in data.get("models", [])]
    except Exception as e:
        print(f"[Ollama Tags Error] {e}")

    categorized_models = config.get_categorized_models(local_models)
    flat_models = config.get_flat_models(local_models)
    gpt_sovits_status = await is_gpt_sovits_alive()
    chatterbox_status = await is_chatterbox_alive()

    return {
        "personas": list(PERSONAS.values()),
        "models": flat_models,
        "categorized_models": categorized_models,
        "default_persona": config.default_persona,
        "default_model": config.default_model,
        "default_tts_engine": config.default_tts_engine,
        "gpt_sovits_url": GPT_SOVITS_URL,
        "gpt_sovits_online": gpt_sovits_status,
        "chatterbox_online": chatterbox_status,
        "available_tts_engines": config.available_tts_engines
    }


@app.post("/api/config/reload")
async def reload_configuration():
    """Hot-reloads settings.json and environment variables."""
    try:
        config.reload()
        return {"status": "success", "message": "Configuration reloaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload config: {e}")


@app.post("/api/tts")
async def direct_tts(req: DirectTTSRequest):
    persona = PERSONAS.get(req.persona_id, PERSONAS[config.default_persona])
    speech_text, actions = parse_dialogue_and_actions(req.text)
    if not speech_text:
        return {"audio_base64": "", "spoken_text": "", "actions": actions, "engine_used": "none"}
        
    override_emo = req.acting_emotion if (req.acting_emotion and req.acting_emotion not in ["auto", "default"]) else ("sensual" if req.nsfw_mode else None)
    audio_base64, engine_used = await synthesize_smart_speech(
        text=speech_text,
        persona_id=req.persona_id,
        persona_config=persona,
        detected_actions=actions,
        preferred_engine=req.tts_engine or config.default_tts_engine,
        override_emotion=override_emo
    )
    if not audio_base64:
        raise HTTPException(status_code=500, detail="Failed to synthesize speech")
    return {"audio_base64": audio_base64, "spoken_text": speech_text, "engine_used": engine_used}


@app.post("/api/script/parse")
async def parse_script_endpoint(req: ScriptParseRequest):
    if not req.script_text.strip():
        return {"segments": []}
    segments = parse_script_into_segments(req.script_text, req.persona_id or config.default_persona)
    return {"segments": segments, "total": len(segments)}


@app.post("/api/script/tts_segment")
async def tts_script_segment(req: ScriptSegmentTTSRequest):
    persona = PERSONAS.get(req.persona_id, PERSONAS[config.default_persona])
    override_emo = req.acting_emotion if (req.acting_emotion and req.acting_emotion not in ["auto", "default"]) else ("sensual" if req.nsfw_mode else (req.inferred_emotion if req.inferred_emotion != "default" else None))
    audio_base64, engine_used = await synthesize_smart_speech(
        text=req.dialogue,
        persona_id=req.persona_id,
        persona_config=persona,
        detected_actions=[req.context_narration] if req.context_narration else [],
        preferred_engine=req.tts_engine or config.default_tts_engine,
        override_emotion=override_emo
    )
    if not audio_base64:
        raise HTTPException(status_code=500, detail="Failed to synthesize segment speech")
    return {
        "audio_base64": audio_base64,
        "spoken_text": req.dialogue,
        "engine_used": engine_used,
        "inferred_emotion": override_emo or req.inferred_emotion
    }


@app.post("/api/chat/stream")
async def chat_stream(req: ChatStreamRequest):
    persona = PERSONAS.get(req.persona_id, PERSONAS[config.default_persona])
    model_to_use = req.model or config.default_model
    system_prompt = req.custom_system_prompt or persona.get("system_prompt", "")
    tts_engine_pref = req.tts_engine or config.default_tts_engine
    override_emo = req.acting_emotion if (req.acting_emotion and req.acting_emotion not in ["auto", "default"]) else ("sensual" if req.nsfw_mode else None)

    # Inject acting style from ConfigManager
    style_instruction = config.get_acting_style_prompt(override_emo)
    if style_instruction and system_prompt:
        system_prompt += style_instruction

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

            # Check Model Source via ConfigManager
            is_gemini = model_to_use in config.gemini_models or model_to_use.startswith("gemini-")
            is_nvidia = (not is_gemini) and (model_to_use in config.nvidia_models or any(model_to_use.startswith(p) for p in ["nvidia/", "meta/", "mistralai/"]))
            is_openrouter = (not is_gemini) and (not is_nvidia) and (
                model_to_use in config.openrouter_models or 
                ":free" in model_to_use or 
                model_to_use == "openrouter/free" or 
                any(model_to_use.startswith(p) for p in ["deepseek/", "z-ai/", "minimax/", "thinkingmachines/", "poolside/", "liquid/", "google/", "meta-llama/"])
            )

            if is_gemini:
                # 0. Google Gemini API Streaming
                if not config.gemini_api_key:
                    err_chunk = {"type": "error", "message": "GEMINI_API_KEY가 설정되지 않았습니다. .env 파일에 키를 입력해주세요. (발급: https://aistudio.google.com/apikey)"}
                    yield f"data: {json.dumps(err_chunk, ensure_ascii=False)}\n\n"
                    return

                gemini_contents = []
                gemini_system = None
                for m in messages:
                    if m["role"] == "system":
                        gemini_system = {"parts": [{"text": m["content"]}]}
                    elif m["role"] == "user":
                        gemini_contents.append({"role": "user", "parts": [{"text": m["content"]}]})
                    elif m["role"] == "assistant":
                        gemini_contents.append({"role": "model", "parts": [{"text": m["content"]}]})

                gemini_payload = {
                    "contents": gemini_contents,
                    "generationConfig": {
                        "temperature": 0.85,
                        "maxOutputTokens": 1024
                    }
                }
                if gemini_system:
                    gemini_payload["systemInstruction"] = gemini_system

                gemini_url = f"{config.gemini_base_url}/models/{model_to_use}:streamGenerateContent?alt=sse&key={config.gemini_api_key}"
                yield ": keep-alive\n\n"
                timeout_cfg = httpx.Timeout(120.0, connect=30.0, read=120.0, write=30.0)

                async with httpx.AsyncClient(timeout=timeout_cfg) as client:
                    async with client.stream(
                        "POST",
                        gemini_url,
                        json=gemini_payload,
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        if response.status_code != 200:
                            err_body = await response.aread()
                            err_chunk = {"type": "error", "message": f"Gemini API Error {response.status_code}: {err_body.decode()[:200]}"}
                            yield f"data: {json.dumps(err_chunk, ensure_ascii=False)}\n\n"
                            return

                        async for line in response.aiter_lines():
                            if not line:
                                continue
                            if line.startswith("data: "):
                                try:
                                    chunk_json = json.loads(line[6:])
                                    candidates = chunk_json.get("candidates", [])
                                    if candidates:
                                        parts = candidates[0].get("content", {}).get("parts", [])
                                        token = "".join(p.get("text", "") for p in parts)
                                    else:
                                        token = ""
                                except Exception:
                                    continue

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
                                                preferred_engine=tts_engine_pref,
                                                override_emotion=override_emo
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

            elif is_openrouter:
                # 1. OpenRouter API Streaming
                openrouter_payload = {
                    "model": model_to_use,
                    "messages": messages,
                    "temperature": 0.8,
                    "stream": True
                }
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {config.openrouter_api_key}",
                    "HTTP-Referer": "https://github.com/loverspath/project_buki",
                    "X-Title": "Project BUKI"
                }

                yield ": keep-alive\n\n"
                timeout_cfg = httpx.Timeout(240.0, connect=30.0, read=240.0, write=30.0)

                async with httpx.AsyncClient(timeout=timeout_cfg) as client:
                    async with client.stream(
                        "POST",
                        f"{config.openrouter_base_url}/chat/completions",
                        json=openrouter_payload,
                        headers=headers
                    ) as response:
                        if response.status_code != 200:
                            err_body = await response.aread()
                            err_chunk = {"type": "error", "message": f"OpenRouter HTTP {response.status_code}: {err_body.decode()[:150]}"}
                            yield f"data: {json.dumps(err_chunk, ensure_ascii=False)}\n\n"
                            return

                        async for line in response.aiter_lines():
                            if not line:
                                continue
                            if line.startswith("data: ") and line.strip() != "data: [DONE]":
                                try:
                                    chunk_json = json.loads(line[6:])
                                    delta = chunk_json.get("choices", [{}])[0].get("delta", {})
                                    token = delta.get("content", "")
                                except Exception:
                                    continue

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
                                                preferred_engine=tts_engine_pref,
                                                override_emotion=override_emo
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

            elif is_nvidia:
                # 2. NVIDIA Direct API Streaming
                nvidia_payload = {
                    "model": model_to_use,
                    "messages": messages,
                    "temperature": 0.85,
                    "top_p": 0.95,
                    "max_tokens": 1024,
                    "stream": True
                }
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {config.nvidia_api_key}"
                }

                yield ": keep-alive\n\n"
                timeout_cfg = httpx.Timeout(240.0, connect=30.0, read=240.0, write=30.0)

                async with httpx.AsyncClient(timeout=timeout_cfg) as client:
                    async with client.stream(
                        "POST",
                        f"{config.nvidia_base_url}/chat/completions",
                        json=nvidia_payload,
                        headers=headers
                    ) as response:
                        if response.status_code != 200:
                            err_body = await response.aread()
                            err_chunk = {"type": "error", "message": f"NVIDIA API Error {response.status_code}: {err_body.decode()[:150]}"}
                            yield f"data: {json.dumps(err_chunk, ensure_ascii=False)}\n\n"
                            return

                        async for line in response.aiter_lines():
                            if not line:
                                continue
                            if line.startswith("data: ") and line.strip() != "data: [DONE]":
                                try:
                                    chunk_json = json.loads(line[6:])
                                    delta = chunk_json.get("choices", [{}])[0].get("delta", {})
                                    token = delta.get("content", "")
                                except Exception:
                                    continue

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
                                                preferred_engine=tts_engine_pref,
                                                override_emotion=override_emo
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

            else:
                # 3. Local Ollama Streaming
                ollama_payload = {
                    "model": model_to_use,
                    "messages": messages,
                    "stream": True,
                    "options": {
                        "temperature": 0.85,
                        "top_p": 0.9,
                        "repeat_penalty": 1.15,
                        "num_ctx": 4096
                    }
                }

                async with httpx.AsyncClient(timeout=120.0) as client:
                    async with client.stream(
                        "POST",
                        f"{config.ollama_base_url}/api/chat",
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
                                            preferred_engine=tts_engine_pref,
                                            override_emotion=override_emo
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

            # Flush remaining sentence buffer if any
            if sentence_buffer.strip():
                speech_to_synthesize, detected_actions = parse_dialogue_and_actions(sentence_buffer)
                raw_sentence = sentence_buffer.strip()

                if req.voice_enabled and speech_to_synthesize:
                    cur_idx = sentence_index
                    sentence_index += 1
                    audio_b64, engine_used = await synthesize_smart_speech(
                        text=speech_to_synthesize,
                        persona_id=persona["id"],
                        persona_config=persona,
                        detected_actions=detected_actions,
                        preferred_engine=tts_engine_pref,
                        override_emotion=override_emo
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

            done_event = {"type": "done", "full_text": full_response_text}
            yield f"data: {json.dumps(done_event, ensure_ascii=False)}\n\n"

        except Exception as e:
            err_event = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(err_event, ensure_ascii=False)}\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)