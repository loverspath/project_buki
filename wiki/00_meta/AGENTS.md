# 🤖 Project BUKI - Multi-Agent System & Guidelines

> **AI 에이전트 협업 지침 및 페르소나 분담 체계**

---

## 👥 1. 개발 에이전트 역할 분담

1. **Architect & Planner Agent**
   - 시스템 아키텍처 설계, API 규격 정의, 위키 문서화 및 로드맵 관리.
2. **Backend & Audio Agent**
   - FastAPI 백엔드, LLM Provider 연동 (Gemini/Claude), Edge-TTS 음성 스트리밍 파이프라인.
3. **Frontend & Avatar Agent**
   - Three.js / `@pixiv/three-vrm` 3D 아바타 렌더링, Web Audio 립싱크 분석기, 모던 Glassmorphism UI.

---

## 📐 2. 에이전트 작업 원칙

1. **무결성 유지**: 코드 수정 전후로 모듈 임포트 및 구문 에러를 상시 검증한다.
2. **지식 동기화**: 주요 기능 구현 및 아키텍처 변경 시 `wiki/04_logs/DEV_LOG.md`와 `TASK_BACKLOG.md`를 즉시 갱신한다.
3. **경량화 & 실시간성**: 클라이언트 리소스 부담을 최소화하고 스트리밍 딜레이를 최우선으로 단축한다.