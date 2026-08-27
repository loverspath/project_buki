# 🔮 Project BUKI (`project_buki`) - System Bible

> **차세대 인터랙티브 AI 컴패니언 & 버츄얼 아바타 시스템**  
> *LLM Streaming Chat × Real-time High-Quality TTS × 3D/2D Virtual Avatar Engine*

---

## 🌟 1. 프로젝트 비전 (Vision & Objective)

**Project BUKI**는 사용자와 실시간으로 교감하는 지능형 버츄얼 아바타 시스템입니다.
단순한 텍스트 챗봇을 넘어, **감정이 실린 자연스러운 음성(TTS)**과 **오디오 기반 실시간 립싱크 및 표정 변화를 지원하는 버츄얼 아바타(VRM / Live2D)**를 웹 브라우저 환경에서 경량으로 구동하는 것을 목표로 합니다.

```mermaid
flowchart LR
    User([👤 사용자]) <-->|텍스트 / 음성 입력| UI["🖥️ BUKI Web Client"]
    UI <-->|WebSocket / SSE 스트림| Server["⚡ BUKI Core Server"]
    
    subgraph ServerEngine["Server Intelligence"]
        PersonaMgr["🧠 페르소나 & 메모리"]
        LLM["🤖 LLM 엔진 (Gemini/Claude)"]
        TTS["🎙️ 실시간 스트리밍 TTS"]
        PersonaMgr --> LLM --> TTS
    end
    
    Server --> ServerEngine
    ServerEngine -->|오디오 + Viseme 데이터| UI
    
    subgraph ClientEngine["Client Rendering"]
        AvatarRenderer["🧍 3D VRM / Live2D 아바타"]
        LipSync["👄 실시간 립싱크 & 모핑"]
        AudioPlayback["🔊 Web Audio 재생"]
        AudioPlayback --> LipSync --> AvatarRenderer
    end
    
    UI --> ClientEngine
```

---

## 🎯 2. 3대 핵심 기둥 (Core Pillars)

1. **지능형 페르소나 챗 (Persona & Context Intelligence)**
   - 캐릭터별 말투, 가치관, 기억(컨텍스트)을 유지하는 동적 프롬프트 파이프라인.
   - 응답 텍스트에 감정 태그(`[emotion:happy]`, `[emotion:blush]` 등) 자동 임베딩.
2. **초저지연 실시간 스트리밍 TTS (Ultra-low Latency TTS)**
   - 문장이 생성되는 즉시 실시간 청크 단위 오디오 스트리밍 (Edge-TTS / ElevenLabs 등).
   - 음성 재생과 동시에 입모양 파라미터(Viseme A/I/U/E/O) 동기화.
3. **웹 기반 버츄얼 아바타 렌더러 (Web Virtual Avatar Engine)**
   - Three.js 기반 `@pixiv/three-vrm` 3D 아바타 렌더링.
   - 자연스러운 시선 추적(마우스/카메라 아이컨택), 대기 모션(Idle Motion), 물리(머리카락/의상).

---

## 🗺️ 3. 3단계 로드맵 요약

* **Phase 1 (MVP)**: LLM 실시간 스트리밍 챗 + 페르소나 전환 + 무료 고음질 Edge-TTS 음성 출력.
* **Phase 2 (LipSync & Emotion)**: 오디오 파형 분석 기반 실시간 립싱크 추출 및 감정별 표정 상태머신.
* **Phase 3 (Full Avatar Integration)**: Three.js 3D VRM 아바타 연동, 물리 효과, 인터랙티브 제스처.

---

## 📂 4. 위키 및 지식 베이스 네비게이션

* 👥 [페르소나 레지스트리](./wiki/01_personas/index.md)
* 🗺️ [전체 로드맵 명세](./wiki/02_roadmap_tasks/ROADMAP.md)
* 📋 [태스크 백로그](./wiki/02_roadmap_tasks/TASK_BACKLOG.md)
* ⚙️ [시스템 아키텍처 상세](./wiki/03_architecture/SYSTEM_DESIGN.md)
* 📜 [개발 로그 아카이브](./wiki/04_logs/DEV_LOG.md)