# 🔮 Project BUKI (`project_buki`)

> **Interactive AI Companion & Virtual Avatar Web Engine**  
> *LLM Streaming Chat × Multi-TTS Quad-Engine (IndexTTS-2 / GPT-SoVITS / Chatterbox / Edge-TTS) × 10 Acting Emotion Styles × Script Reader × VTuber Voice Extractor*

---

## 🌟 핵심 기능 (Key Features)

1. **🤖 Multi-LLM 하이브리드 인텔리전스 (Gemini / OpenRouter / NVIDIA / Ollama)**:
   * **Google Gemini 2.0/3.6 Flash**: 차세대 무료 초고속 LLM 엔진 공식 탑재 (지문 분리 & 서브컬처 페르소나 연기력 극대화)
   * **OpenRouter Free & NVIDIA Cloud**: 옥스알파(GLM-5.3), MiniMax M3, Nemotron 등 다양한 무료 클라우드 모델 지원
   * **로컬 GPU (Ollama)**: 로컬 무검열 모델 지원
2. **🎙️ Multi-TTS 하이브리드 음성 엔진 (Quad-Engine Architecture)**:
   * **IndexTTS-2 (포트 9884)**: 한국어/일본어/영어/중국어 네이티브 제로샷 복제 + 8차원 감정 벡터 블렌딩 + 발화 시간(Duration) 정밀 제어
   * **GPT-SoVITS (포트 9880)**: 3초 제로샷(Zero-shot) 캐릭터 음성 복제 및 감정 뱅크 라우팅
   * **Chatterbox 0.5B (포트 9882)**: 의성어/호흡 태그(`[laugh]`, `[sigh]`, `[whisper]`) 및 감정 과장도(Exaggeration) 제어
   * **Edge-TTS**: 초고속 무중단 자동 폴백(Auto-Fallback) 지원
3. **🎭 10가지 극적 연기 감정 & NSFW 보이스 필터 (Acting Emotion Styles)**:
   * `💖 달아오름/신음` (0.90배속 + 성대 떨림 + `읏, ` 호흡)
   * `🥵 헐떡임/숨소리` (1.05배속 + `하아, 하아, ` 거친 호흡)
   * `😱 공포에 질림` (1.16배속 + `히익, ` 비명 호흡 + 떨림)
   * `🥀 낮고 느린 체념` (0.78배속 + `하아... ` 깊은 한숨 톤)
   * `😢 흐느낌/울먹임` (0.95배속 + `흑... ` 서러운 눈물 톤)
   * `🤫 귓가 속삭임` (0.92배속 + 밀착 ASMR)
   * `😳 부끄럼/당황`, `😏 메스가키 비웃음`, `😡 분노/쏘아붙임`, `🎭 자동 감정`
   * 상단 원클릭 드롭다운을 통해 LLM 텍스트 생성과 음성 억양이 100% 일치하도록 실시간 연동
4. **📖 대본 낭독기 (Script Reader)**:
   * 소설/대본 텍스트를 대사(`"큰따옴표"`)와 지문으로 자동 파싱
   * 지문 문맥에 따라 대사별 감정 연기 톤 자동 전환 또는 상단 필터를 통한 전 대사 일괄 강제 낭독
5. **🎬 VTuber 고음질 보이스 추출 5단계 자동화 파이프라인 (`extract_shibuki_voice.py`)**:
   * 유튜브 아카이브/로컬 영상에서 저스트채팅(잡담) 구간 자동 탐색 ➔ DSP 배경음 제거 ➔ VAD 3~8초 슬라이싱 ➔ 32kHz/-20LUFS 표준화 ➔ 전사 및 감정 레지스트리 자동 갱신
6. **⚙️ JSON 기반 설정 관리 & 핫 리로드 (ConfigManager)**:
   * 모델 카탈로그, API URL, 감정 프롬프트, 키워드 룰셋을 `config/settings.json`으로 완전 분리
   * 코드 재시작 없이 `POST /api/config/reload`를 통한 런타임 핫 리로드 지원
7. **📱 모바일 / Tailscale 원격 최적화**:
   * Galaxy Z Fold 및 모바일 브라우저에 최적화된 Glassmorphism UI
   * 모바일 Web Audio 자동 잠금 해제(AudioContext Unlocker) 및 캐시 버스팅

---

## 🚀 빠른 시작 (Quickstart)

```bash
# 1. 의존성 설치 (Python 가상환경 권장)
cd src/backend
pip install -r requirements.txt

# 2. 로컬 백엔드 서버 실행 (0.0.0.0 바인딩)
python -m uvicorn app:app --host 0.0.0.0 --port 8000

# 3. 브라우저 접속 (로컬 또는 테일스케일 IP)
# 로컬: http://localhost:8000
# 테일스케일: http://100.124.66.37:8000
```

---

## 📁 프로젝트 구조

```text
project_buki/
├── wiki/                      # 📚 프로젝트 매니지먼트 LLM Wiki (Obsidian 호환)
│   ├── 00_meta/               # 시스템 바이블, 에이전트 지침, 템플릿
│   ├── 01_personas/           # 캐릭터 페르소나 및 보이스 프로필
│   ├── 02_roadmap_tasks/      # 로드맵, 스프린트, 태스크 백로그
│   ├── 03_architecture/       # 상세 아키텍처 및 시스템 설계서
│   └── 04_logs/               # 개발 로그 (DEV_LOG.md)
│
├── src/                       # 💻 소스코드
│   ├── backend/               # FastAPI 백엔드 (LLM + Multi-TTS + 대본 파서)
│   │   ├── config/            # 📄 JSON 설정 (settings.json)
│   │   ├── core/              # ConfigManager, 페르소나 정의
│   │   ├── tts/               # GPT-SoVITS, Chatterbox, Edge-TTS 어댑터 & 매니저
│   │   └── app.py             # REST API & SSE 스트리밍 엔드포인트
│   │
│   ├── frontend/              # Web UI (Vanilla JS, Glassmorphism CSS, Web Audio)
│   │   ├── index.html         # 챗 UI + 대본 낭독기 + 설정 바텀시트
│   │   ├── app.js             # 상태 관리, 오디오 큐, 감정 필터 연동
│   │   └── style.css          # 모바일 반응형 디자인
│   │
│   └── assets/                # 음성 레퍼런스 샘플, 아이콘
│       └── voice_samples/     # 32kHz 16-bit PCM WAV 레퍼런스 및 메타데이터
│
└── scripts/                   # 🛠️ 개발 및 자동화 스크립트
```

---

## 📖 문서 링크 (Wiki)
* [📘 시스템 바이블 (PROJECT_BIBLE.md)](./wiki/00_meta/PROJECT_BIBLE.md)
* [🗺️ 개발 로드맵 (ROADMAP.md)](./wiki/02_roadmap_tasks/ROADMAP.md)
* [📋 태스크 보드 (TASK_BACKLOG.md)](./wiki/02_roadmap_tasks/TASK_BACKLOG.md)
* [⚙️ 시스템 설계서 (SYSTEM_DESIGN.md)](./wiki/03_architecture/SYSTEM_DESIGN.md)
* [📜 개발 일지 (DEV_LOG.md)](./wiki/04_logs/DEV_LOG.md)