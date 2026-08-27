# 🔮 Project BUKI (`project_buki`)

> **Interactive AI Companion & Virtual Avatar Web Engine**  
> *LLM Streaming Chat × Real-time High-Quality TTS × 3D VRM & 2D Avatar*

---

## 🚀 빠른 시작 (Quickstart)

```bash
# 1. 의존성 설치 (Python 가상환경 권장)
cd src/backend
pip install -r requirements.txt

# 2. 로컬 개발 서버 실행
python app.py

# 3. 브라우저 접속
# http://localhost:8000
```

---

## 📁 프로젝트 구조

```text
project_buki/
├── wiki/                      # 📚 프로젝트 매니지먼트 LLM Wiki (Obsidian 호환)
│   ├── 00_meta/               # 시스템 바이블, 에이전트 지침, 템플릿
│   ├── 01_personas/           # 캐릭터 페르소나 및 보이스 프로필
│   ├── 02_roadmap_tasks/      # 로드맵, 스프린트, 태스크 백로그
│   ├── 03_architecture/       # 상세 아키텍처 및 API 명세
│   └── 04_logs/               # 개발 로그 및 의사결정 기록 (ADR)
│
├── src/                       # 💻 소스코드
│   ├── backend/               # FastAPI 백엔드 (LLM 스트리밍 + Edge-TTS + Viseme)
│   ├── frontend/              # Web UI (Three.js VRM 아바타, 챗 UI, Web Audio)
│   └── assets/                # 3D VRM 모델, 아이콘, 효과음
│
└── scripts/                   # 🛠️ 개발 및 자동화 스크립트
```

---

## 📖 문서 링크 (Wiki)
* [📘 시스템 바이블 (PROJECT_BIBLE.md)](./wiki/00_meta/PROJECT_BIBLE.md)
* [🗺️ 개발 로드맵 (ROADMAP.md)](./wiki/02_roadmap_tasks/ROADMAP.md)
* [📋 태스크 보드 (TASK_BACKLOG.md)](./wiki/02_roadmap_tasks/TASK_BACKLOG.md)
* [⚙️ 시스템 설계서 (SYSTEM_DESIGN.md)](./wiki/03_architecture/SYSTEM_DESIGN.md)