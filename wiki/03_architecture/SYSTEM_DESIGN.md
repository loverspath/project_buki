# ⚙️ Project BUKI - System Architecture Specification

---

## 🏛️ 1. 모듈 계층 구조

```mermaid
graph TD
    Client["Client (Browser)"]
    Server["FastAPI Backend Server"]

    subgraph FrontendComponents["Frontend Layer"]
        UI["Chat & Controls UI"]
        Audio["WebAudio Stream Player & LipSync Analyzer"]
        Avatar["Three.js VRM Avatar Renderer"]
    end

    subgraph BackendServices["Backend Services"]
        LLMService["LLM Provider Service (Gemini/OpenAI)"]
        TTSService["Edge-TTS Synthesis Service"]
        PersonaService["Persona & Prompt Manager"]
    end

    Client --> FrontendComponents
    Server --> BackendServices

    UI -->|User Message| LLMService
    PersonaService -.->|Inject System Prompt| LLMService
    LLMService -->|Text Chunks (SSE)| UI
    LLMService -->|Complete Sentence| TTSService
    TTSService -->|Audio Binary Stream| Audio
    Audio -->|Viseme Volume/Frequencies| Avatar
```

---

## 🔌 2. API 엔드포인트 명세

### `POST /api/chat/stream`
* **요청 바디**:
  ```json
  {
    "message": "안녕! 오늘 기분 어때?",
    "persona_id": "sayaka",
    "history": []
  }
  ```
* **응답**: Server-Sent Events (SSE)
  * `event: text` -> LLM 스트리밍 텍스트 조각
  * `event: audio` -> 실시간 합성된 TTS Base64/Binary URL
  * `event: emotion` -> 감정 태그 (`happy`, `surprised`, etc.)