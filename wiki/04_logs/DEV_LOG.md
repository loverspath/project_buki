# 📜 Project BUKI - Development Log

---

### 📅 2026-08-27 (Sprint 1: 대사/지문 분리 파서 및 GPT-SoVITS Zero-Shot 음성 아키텍처 완비)
* **작업 내용**:
  1. **대사(TTS) vs 지문/행동(UI 시각화) 3계층 파서 구축**:
     - `src/backend/core/persona.py`: 대사(평문)와 지문(`(소괄호)`, `*별표*`)을 엄격 분리하는 시스템 프롬프트 가이드 적용.
     - `src/backend/app.py`: `parse_dialogue_and_actions()` 정규식 파서를 통해 괄호/지문을 완전히 제거한 실제 대사만 TTS로 전송. 지문만 있는 문장은 TTS 합성을 자동 건너뛰어 무지연 처리.
  2. **모바일 브라우저 오디오 자동 재생 잠금 해제 (AudioContext Unlocker)**:
     - `src/frontend/app.js`: 첫 터치 및 전송 클릭 시 브라우저 오디오 권한을 즉시 열어 모바일(Z Fold)에서 소리가 차단되는 현상 완벽 해결.
     - 각 말풍선 하단에 `[🔊 다시 듣기]` 버튼 추가.
  3. **GPT-SoVITS 3초 제로샷(Zero-shot) 음성 어댑터 레이어 구축**:
     - `src/backend/tts/gpt_sovits_service.py`: 3초 레퍼런스 음성으로 추가 학습 없이 억양/목소리를 복제하는 API 연동 모듈 신설.
     - `src/backend/tts/tts_manager.py`: GPT-SoVITS 활성 시 캐릭터 보이스 출력, 미구동 시 `Edge-TTS`로 무중단 자동 폴백(Auto-Fallback) 및 감정별 레퍼런스 라우팅 구현.
     - `src/assets/voice_samples/sample_registry.json`: 캐릭터별 3초 레퍼런스 음성 뱅크 메타데이터 등록.
  4. **프론트엔드 TTS 제어 UI 확장**:
     - 헤더에 `[TTS 엔진 선택 드롭다운]` 및 실시간 GPT-SoVITS 온/오프라인 상태 배지 추가.