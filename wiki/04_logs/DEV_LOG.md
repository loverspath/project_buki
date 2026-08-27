# 📜 Project BUKI - Development Log

---

### 📅 2026-08-27 (Sprint 4: Google Gemini 2.0 Flash 공식 탑재 & app.py 설정/메인 JSON 분리 리팩토링)
* **작업 내용**:
  1. **Google Gemini 2.0 Flash / 1.5 Flash 공식 API 연동**:
     - `src/backend/app.py`: Gemini 공식 SSE 스트리밍 엔드포인트 연동 및 문장 단위 음성 합성 파이프라인 결합.
     - `src/frontend/app.js`: UI 모델 선택기 상단에 `✨ 구글 제미나이 무료 API` 전용 카테고리 신설.
     - `.env`: `GEMINI_API_KEY` 환경변수 지원.
  2. **`app.py` 갓오브젝트 해체 및 `ConfigManager` 싱글톤 분리**:
     - `src/backend/config/settings.json`: 모델 카탈로그, API URL, 10대 감정 연기 프롬프트, 키워드 룰셋을 전량 JSON으로 분리.
     - `src/backend/core/config_manager.py`: JSON 로딩, `.env` 오버라이드, 감정 추론 헬퍼 및 런타임 `reload()` 지원.
     - `POST /api/config/reload`: 서버 재부팅 없는 동적 핫 리로드 엔드포인트 제공.
  3. **회귀 검증 테스트 스위트 작성**:
     - `scripts/test_config_refactor.py`: 모델 카테고리 분기, 감정 프롬프트 매핑, 문맥 감정 추론, 대본 파싱 전수 검증 통과.

---

### 📅 2026-08-27 (Sprint 3: 10대 극적 연기 감정 & NSFW 보이스 필터 및 대본 낭독기 완비)
* **작업 내용**:
  1. **10가지 극적 연기 감정 (Acting Emotion Styles) 아키텍처 구축**:
     - `src/backend/tts/tts_manager.py`: `enrich_gpt_sovits_text()`에 템포, 피치 떨림, 호흡 감탄사 결합 파이프라인 구현.
       * `😱 공포에 질림 (terrified)`: 1.16배속 + `히익, ` 비명 호흡 + 성대 떨림
       * `🥀 낮고 느린 체념 (resigned)`: 0.78배속 초저속 + `하아... ` 깊은 한숨 톤
       * `💖 달아오름/신음 (sensual)`: 0.90배속 나긋나긋함 + `읏, ` 신음 호흡 + `~♡`
       * `🥵 헐떡임/숨소리 (panting)`: 1.05배속 + `하아, 하아, ` 거친 숨
       * `😢 흐느낌/울먹임 (crying)`: 0.95배속 + `흑... ` 서러운 눈물 톤
       * `🤫 귓가 속삭임 (whisper)`: 0.92배속 밀착 ASMR
       * `😳 부끄럼/당황 (flustered)`, `😏 메스가키 비웃음 (smug)`, `😡 분노/쏘아붙임 (angry)`, `🎭 자동 감정 (auto)`
  2. **LLM 지문 & 프롬프트 연동 및 원클릭 탑바 드롭다운 UI**:
     - `src/frontend/index.html` & `app.js`: 상단 헤더에 `🎭 연기 감정 드롭다운` 배치 및 `localStorage` 영속화.
     - `src/backend/app.py`: 감정 선택 시 LLM 시스템 프롬프트에 `[Acting Style: ...]`를 자동 주입하여 텍스트 답변과 음성 억양이 100% 일치하도록 보장.
  3. **대본 낭독기 (Script Reader) 2-Way 감정 파싱 & 낭독 엔진 연동**:
     - `parse_script_into_segments()`: 대본 속 지문 및 괄호 속 감정 키워드를 정밀 분석하여 대사별 감정 연기 톤 자동 전환.
     - 상단 드롭다운을 통해 대본 전체를 특정 감정으로 일괄 강제 낭독(Global Override) 지원.
     - 원클릭 테스트 프리셋(`💖 신음/달아오름`, `😱 공포/비명`, `🥀 체념/절망`) 탑재.

---

### 📅 2026-08-27 (Sprint 2: Chatterbox 0.5B 마이크로서비스 연동 & Prompt Leakage 원인 규명 및 버그 픽스)
* **작업 내용**:
  1. **Chatterbox 0.5B 감정/태그 제어 TTS 마이크로서비스 연동**:
     - `src/backend/tts/chatterbox_service.py`: 포트 9882 마이크로서비스 어댑터 구축 (`[laugh]`, `[sigh]`, `[whisper]`, `[chuckle]`).
     - 기본 남성 보이스 출력 버그 해결: `sample_registry.json` 경로 매핑 수정 및 `mesugaki_ref.wav` (여성 피치 260Hz) 하드 폴백 설정.
  2. **GPT-SoVITS 대사 첫머리 프롬프트 반복 누출(Prompt Leakage) 해결**:
     - **원인 규명**: `prompt_text`와 음성 불일치 + 텍스트 첫머리 문장부호(`...`, `,`)가 `cut5` 분할 시 빈 토큰 청크를 유발하여 오토리그레시브 트랜스포머가 참조 음성 마지막 어구(`"아무것도 못한다니까~"`)를 무한 루프 낭독하던 현상.
     - **조치**:
       * 음성 샘플 전체를 32kHz 16-bit PCM WAV 표준으로 변환.
       * `sample_registry.json`의 `prompt_text`를 `""`(빈 문자열)로 변경하여 순수 제로샷 텍스트 프리 모드로 전환.
       * 대사 앞뒤 문장부호 찌꺼기 정제 정규식 필터 적용.
  3. **Tailscale 원격 접속 최적화 & 브라우저 캐시 버스팅**:
     - `100.124.66.37:8000` 환경에서 모바일 브라우저 JS 캐시 고착을 방지하기 위해 `app.js?v=...` 쿼리스트링 자동 갱신.

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