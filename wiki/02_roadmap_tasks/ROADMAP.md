# 🗺️ Project BUKI - Development Roadmap

---

## 🏁 Phase 1: MVP (LLM Streaming + High-Quality TTS) `[진행 중]`
- [x] 프로젝트 디렉토리 및 LLM Wiki 매니지먼트 구조 셋업
- [ ] FastAPI 경량 백엔드 구축 (Gemini API 스트리밍 + SSE)
- [ ] Edge-TTS 고음질 음성 합성 파이프라인 (한국어 `ko-KR-SunHiNeural` 등)
- [ ] Glassmorphism 모던 챗 UI & 오디오 플레이어 연동
- [ ] 페르소나 선택 시스템 (기본 페르소나 2종 탑재)

## 🎨 Phase 2: Lip-Sync Engine & Emotion Parsing `[대기]`
- [ ] Web Audio API 파형 분석 기반 실시간 립싱크 (A/I/U/E/O) 파라미터 추출
- [ ] LLM 응답 텍스트 내 감정 태그(`[emotion:...]`) 정규식 파서
- [ ] 2D 감정 표정 일러스트 모핑 또는 실시간 상태머신 연동

## 🧍 Phase 3: 3D VRM Virtual Avatar Integration `[대기]`
- [ ] Three.js + `@pixiv/three-vrm` 웹 3D 아바타 렌더러 탑재
- [ ] 자동 눈 깜빡임(Blink), 대기 호흡 모션(Idle Motion), 마우스 시선 추적(LookAt)
- [ ] 립싱크 BlendShape 실시간 바인딩 (VOWEL_A, VOWEL_I, VOWEL_U, VOWEL_E, VOWEL_O)
- [ ] VRoid 커스텀 모델 드래그 앤 드롭 로더