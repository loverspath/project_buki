# 📜 Project BUKI - Development Log

---

### 📅 2026-08-27 (Sprint 1: MVP 완성 - Ollama 메스가키 모델 + 실시간 Edge-TTS + Web UI + Tailscale 서빙)
* **작업 내용**:
  1. **하드웨어 및 VRAM 최적화 분석**:
     - NVIDIA RTX 3080 Ti Laptop GPU (16GB VRAM) 환경 전수 검증.
     - Ollama `gemma-mesugaki:latest` 모델 100% GPU(3.3GB VRAM) 로드 및 35~50 tok/s 초고속 스트리밍 확인.
  2. **FastAPI 백엔드 파이프라인 구축 (`src/backend/`)**:
     - `app.py`: Ollama SSE 스트리밍 + 문장 경계(`.!?,~`) 감지 실시간 비동기 Edge-TTS(`ko-KR-SunHiNeural`) 합성 파이프라인 완성.
     - `core/persona.py`: 메스가키, 사야카, 루리 등 페르소나별 시스템 프롬프트 및 음성 피치/속도 프로필 등록.
     - `tts/tts_service.py`: Base64 MP3 합성 서비스.
  3. **프론트엔드 모던 웹 UI 구축 (`src/frontend/`)**:
     - `index.html`, `style.css`: 모바일(Z Fold) & PC 반응형 Cyberpunk Dark Glassmorphism 테마.
     - `app.js`: SSE 스트리밍 타이핑 효과, 문장별 오디오 큐 순차 자동 재생, 음성 출력 시 펄스/표정 반응 이펙트.
  4. **Tailscale 외부 서빙 지원**:
     - `0.0.0.0:8000` 바인딩을 통해 Tailscale IP(`http://100.124.66.37:8000`) 및 Funnel URL로 모바일 기기(Z Fold8)에서 즉시 접속 가능.
* **다음 마일스톤 (Phase 2 & 3)**:
  - Three.js 기반 3D VRM 모델 연동 및 오디오 주파수 분석 기반 실시간 입모양(A/I/U/E/O) 모핑.