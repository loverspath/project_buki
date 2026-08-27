# 🗺️ Project BUKI - Development Roadmap

---

## 🏁 Phase 1: MVP (LLM Streaming + Tri-Engine Multi-TTS) `[✅ 완료]`
- [x] 프로젝트 디렉토리 및 LLM Wiki 매니지먼트 구조 셋업
- [x] FastAPI 경량 백엔드 구축 (Ollama + OpenRouter + SSE 스트리밍)
- [x] Tri-Engine Multi-TTS 파이프라인 (GPT-SoVITS + Chatterbox 0.5B + Edge-TTS)
- [x] 대사(TTS 음성) vs 지문/행동(UI 시각화) 3계층 파서 구축
- [x] Glassmorphism 모던 챗 UI & 모바일 AudioContext Unlocker
- [x] 페르소나 선택 시스템 (메스가키, 무츠키, 사야카, 루리 등 4종 탑재)

## 🎭 Phase 2: 10 Acting Emotions & Script Reader `[✅ 완료]`
- [x] 10가지 극적 연기 감정(공포, 체념, 신음, 헐떡임, 속삭임 등) 프로소디 엔진
- [x] GPT-SoVITS 32kHz 16-bit PCM WAV 무손실 표준화 및 텍스트 프리 제로샷 모드 전환
- [x] 대본 낭독기 (Script Reader) 2-Way 파싱 (지문 기반 자동 추론 & 전체 일괄 강제 낭독)
- [x] 모바일(Samsung Galaxy Z Fold) 반응형 디자인 및 Tailscale 원격 서빙

## 🧍 Phase 3: 3D VRM Virtual Avatar Integration `[⏳ 차기 스프린트]`
- [ ] Three.js + `@pixiv/three-vrm` 웹 3D 아바타 렌더러 탑재
- [ ] 오디오 파형 분석 기반 실시간 립싱크 추출 및 BlendShape 모핑 (A/I/U/E/O)
- [ ] 자동 눈 깜빡임(Blink), 대기 호흡 모션(Idle Motion), 시선 추적(LookAt)
- [ ] VRoid 커스텀 모델 드래그 앤 드롭 로더 및 모션 인터랙션