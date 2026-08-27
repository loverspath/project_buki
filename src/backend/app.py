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

# Load local .env if available
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.strip().split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())
    except Exception as e:
        print(f"[Env Loader] Error: {e}")

# NVIDIA API Configuration
NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")

# OpenRouter API Configuration
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# Curated Model Catalog
OPENROUTER_MODELS = [
    "z-ai/glm-5.3-flash",                    # 옥스알파 (OxAlpha / 0xAlpha) 스텔스 최신 모델!
    "minimax/minimax-m3:free",               # MiniMax M3 (1M 컨텍스트 무료)
    "openrouter/free",                       # OpenRouter 스마트 자동 라우터
    "google/gemma-4-31b-it:free",            # Google Gemma 4 31B
    "google/gemma-4-26b-a4b-it:free",        # Google Gemma 4 26B MoE
    "nvidia/nemotron-3-ultra-550b-a55b:free", # OpenRouter Nemotron 550B 무료
    "thinkingmachines/inkling:free",         # Thinking Machines Inkling (975B)
    "poolside/laguna-s-2.1:free",            # Poolside Laguna S 2.1 (코딩 118B)
    "z-ai/glm-5.2:free"                      # Z.ai GLM 5.2
]

NVIDIA_MODELS = [
    "nvidia/nemotron-3-ultra-550b-a55b",     # NVIDIA 직접 550B 플래그십
    "nvidia/nemotron-3-super-120b-a12b",
    "nvidia/llama-3.1-nemotron-70b-instruct",
    "deepseek-ai/deepseek-v4-pro-0813"
]

app = FastAPI(title="Project BUKI - Local & Cloud LLM + TTS Companion Engine")

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
    """Parses raw script text into dialogue and narration segments with comprehensive emotion analysis."""
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
            
            inferred_emotion = "default"
            # 1. Sensual / Moan
            if any(k in combined_ctx for k in ["신음", "달아오른", "야릇", "흐트러", "앙탈", "달콤한 교성", "허덕이", "교태", "녹아내리", "애원"]):
                inferred_emotion = "sensual"
            # 2. Panting / Heavy Breath
            elif any(k in combined_ctx for k in ["헐떡", "가쁜 숨", "거친 숨", "숨을 몰아쉬", "하악", "하아하아", "숨이 차"]):
                inferred_emotion = "panting"
            # 3. Terrified / Fear
            elif any(k in combined_ctx for k in ["공포", "비명", "겁에 질", "사시나무", "떨며", "살려", "무서", "히익", "경악", "벌벌"]):
                inferred_emotion = "terrified"
            # 4. Resigned / Despair / Low & Slow
            elif any(k in combined_ctx for k in ["체념", "낮은 목소리", "느린 목소리", "한숨", "절망", "무기력", "멍하니", "지친", "포기"]):
                inferred_emotion = "resigned"
            # 5. Crying / Weeping
            elif any(k in combined_ctx for k in ["울먹", "눈물", "흐느끼", "훌쩍", "흑흑"]):
                inferred_emotion = "crying"
            # 6. Whisper / ASMR
            elif any(k in combined_ctx for k in ["속삭", "귓가", "소곤", "귓속말", "살며시 다가와", "귀에 대고"]):
                inferred_emotion = "whisper"
            # 7. Flustered / Shy
            elif any(k in combined_ctx for k in ["얼굴을 붉", "부끄러", "더듬", "우물쭈물", "시선을 피", "당황", "홍조", "부끄"]):
                inferred_emotion = "flustered"
            # 8. Smug / Mesugaki
            elif any(k in combined_ctx for k in ["비웃", "피식", "혀를 차", "한심", "콧방귀", "멍청", "허접", "풋", "깔보", "우쭐"]):
                inferred_emotion = "smug"
            # 9. Tease / Playful
            elif any(k in combined_ctx for k in ["놀리", "장난", "우후후", "쿠후후", "킥킥", "쿡쿡"]):
                inferred_emotion = "tease"
            # 10. Angry / Scream
            elif any(k in combined_ctx for k in ["화", "버럭", "소리치", "짜증", "인상", "노려보", "째려", "가만 안"]):
                inferred_emotion = "angry"
                
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

@app.get("/api/info")
async def get_system_info():
    local_models = []
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if res.status_code == 200:
                data = res.json()
                local_models = [m.get("name") for m in data.get("models", [])]
    except Exception as e:
        print(f"[Ollama Tags Error] {e}")

    categorized_models = {
        "openrouter_free": OPENROUTER_MODELS,
        "nvidia_cloud": NVIDIA_MODELS,
        "local_ollama": [m for m in local_models if m not in NVIDIA_MODELS and m not in OPENROUTER_MODELS]
    }

    flat_models = OPENROUTER_MODELS + NVIDIA_MODELS + categorized_models["local_ollama"]
    gpt_sovits_status = await is_gpt_sovits_alive()
    from tts.chatterbox_service import is_chatterbox_alive
    chatterbox_status = await is_chatterbox_alive()

    return {
        "personas": list(PERSONAS.values()),
        "models": flat_models,
        "categorized_models": categorized_models,
        "default_persona": "mesugaki",
        "default_model": "z-ai/glm-5.3-flash",
        "default_tts_engine": "gpt_sovits",
        "gpt_sovits_url": GPT_SOVITS_URL,
        "gpt_sovits_online": gpt_sovits_status,
        "chatterbox_online": chatterbox_status,
        "available_tts_engines": [
            {"id": "gpt_sovits", "name": "🎙️ GPT-SoVITS (3초 제로샷 - 기본)"},
            {"id": "chatterbox", "name": "🎭 Chatterbox (0.5B 감정/태그 제어)"},
            {"id": "auto", "name": "⚡ 자동 (SoVITS ➔ Chatterbox ➔ Edge)"},
            {"id": "edge_tts", "name": "🔊 Edge-TTS (초고속 기본 음성)"}
        ]
    }

@app.post("/api/tts")
async def direct_tts(req: DirectTTSRequest):
    persona = PERSONAS.get(req.persona_id, PERSONAS["mesugaki"])
    speech_text, actions = parse_dialogue_and_actions(req.text)
    if not speech_text:
        return {"audio_base64": "", "spoken_text": "", "actions": actions, "engine_used": "none"}
        
    override_emo = req.acting_emotion if (req.acting_emotion and req.acting_emotion not in ["auto", "default"]) else ("sensual" if req.nsfw_mode else None)
    audio_base64, engine_used = await synthesize_smart_speech(
        text=speech_text,
        persona_id=req.persona_id,
        persona_config=persona,
        detected_actions=actions,
        preferred_engine=req.tts_engine or "gpt_sovits",
        override_emotion=override_emo
    )
    if not audio_base64:
        raise HTTPException(status_code=500, detail="Failed to synthesize speech")
    return {"audio_base64": audio_base64, "spoken_text": speech_text, "engine_used": engine_used}

@app.post("/api/script/parse")
async def parse_script_endpoint(req: ScriptParseRequest):
    if not req.script_text.strip():
        return {"segments": []}
    segments = parse_script_into_segments(req.script_text, req.persona_id or "mesugaki")
    return {"segments": segments, "total": len(segments)}

@app.post("/api/script/tts_segment")
async def tts_script_segment(req: ScriptSegmentTTSRequest):
    persona = PERSONAS.get(req.persona_id, PERSONAS["mesugaki"])
    override_emo = req.acting_emotion if (req.acting_emotion and req.acting_emotion not in ["auto", "default"]) else ("sensual" if req.nsfw_mode else (req.inferred_emotion if req.inferred_emotion != "default" else None))
    audio_base64, engine_used = await synthesize_smart_speech(
        text=req.dialogue,
        persona_id=req.persona_id,
        persona_config=persona,
        detected_actions=[req.context_narration] if req.context_narration else [],
        preferred_engine=req.tts_engine or "gpt_sovits",
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
    persona = PERSONAS.get(req.persona_id, PERSONAS["mesugaki"])
    model_to_use = req.model or "z-ai/glm-5.3-flash"
    system_prompt = req.custom_system_prompt or persona.get("system_prompt", "")
    tts_engine_pref = req.tts_engine or "gpt_sovits"
    override_emo = req.acting_emotion if (req.acting_emotion and req.acting_emotion not in ["auto", "default"]) else ("sensual" if req.nsfw_mode else None)

    style_prompts = {
        "sensual": "\n[Acting Style: 살짝 달아오른 목소리와 부끄러운 앙탈/귓속말, 호흡 감탄사(...읏..., ...하아...)를 섞어 대답할 것]",
        "terrified": "\n[Acting Style: 공포에 질려 벌벌 떨며, 사시나무처럼 떨리는 비명과 호흡 감탄사(히익...!, 으악...!)를 섞어 대답할 것]",
        "resigned": "\n[Acting Style: 모든 것을 체념한 듯 낮고 느린 톤으로 깊은 한숨(...하아...)과 함께 무기력하게 대답할 것]",
        "panting": "\n[Acting Style: 가쁜 숨을 헐떡이며(...하아, 하아...) 대답할 것]",
        "flustered": "\n[Acting Style: 얼굴이 새빨개져서 당황하고 더듬거리며(...앗, 바, 바보...!) 대답할 것]",
        "whisper": "\n[Acting Style: 귓가에 조용히 밀착하여 속삭이듯 나긋나긋하게 대답할 것]",
        "crying": "\n[Acting Style: 눈물을 글썽이며 서럽게 울먹이고 흐느끼며(...흑, 훌쩍...) 대답할 것]",
        "angry": "\n[Acting Style: 극도로 화가 나서 앙칼지게 쏘아붙이며 대답할 것]",
        "smug": "\n[Acting Style: 비웃음(풋, 큭큭)과 함께 상대를 깔보고 놀리듯 대답할 것]"
    }
    if override_emo in style_prompts and system_prompt:
        system_prompt += style_prompts[override_emo]

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

            # Check Model Source
            is_openrouter = model_to_use in OPENROUTER_MODELS or ":free" in model_to_use or model_to_use.startswith("z-ai/") or model_to_use.startswith("minimax/") or model_to_use.startswith("thinkingmachines/") or model_to_use.startswith("poolside/")
            is_nvidia = (not is_openrouter) and any(model_to_use.startswith(prefix) for prefix in ["nvidia/", "deepseek-ai/", "meta/", "mistralai/"])

            if is_openrouter:
                # 1. OpenRouter API Streaming
                openrouter_payload = {
                    "model": model_to_use,
                    "messages": messages,
                    "temperature": 0.8,
                    "stream": True
                }
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "HTTP-Referer": "https://github.com/loverspath/project_buki",
                    "X-Title": "Project BUKI"
                }

                yield ": keep-alive\n\n"
                timeout_cfg = httpx.Timeout(240.0, connect=30.0, read=240.0, write=30.0)

                async with httpx.AsyncClient(timeout=timeout_cfg) as client:
                    async with client.stream(
                        "POST",
                        f"{OPENROUTER_BASE_URL}/chat/completions",
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
                    "Authorization": f"Bearer {NVIDIA_API_KEY}"
                }

                yield ": keep-alive\n\n"
                timeout_cfg = httpx.Timeout(240.0, connect=30.0, read=240.0, write=30.0)

                async with httpx.AsyncClient(timeout=timeout_cfg) as client:
                    async with client.stream(
                        "POST",
                        f"{NVIDIA_BASE_URL}/chat/completions",
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

                            if chunk_json.get("done", False):
                                break

            # Flush remaining buffer
            if req.voice_enabled and sentence_buffer.strip():
                speech_to_synthesize, detected_actions = parse_dialogue_and_actions(sentence_buffer)
                if speech_to_synthesize:
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