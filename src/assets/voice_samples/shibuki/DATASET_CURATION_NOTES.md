# 텐코 시부키(Tenko Shibuki) 음성 데이터셋 큐레이션 및 정제 관리 대장

## 1. 큐레이션 및 필터링 지침 (2026-08-28 사용자 지침 반영)

### 🚫 즉시 제외 (도네이션/배경음 소리 오염)
다음 샘플들은 도네이션 알림음, 알림 효과음 또는 BGM이 혼입되어 다음 파인튜닝 학습 데이터셋 및 레퍼런스 프롬프트에서 **즉시 사용 금지(제외)** 조치합니다:
- **`shibuki_sample_006.wav`** (도네이션 소리 오염)
- **`shibuki_sample_007.wav`** (도네이션 소리 오염)
- **`shibuki_sample_008.wav`** (도네이션 소리 오염)
- **`shibuki_sample_016.wav`** (도네이션 소리 오염)
- **`shibuki_sample_018.wav`** (도네이션 소리 오염)
- **`shibuki_sample_020.wav`** (도네이션 소리 오염)
- **`shibuki_sample_021.wav`** (도네이션 소리 오염)
- **`shibuki_sample_022.wav`** (도네이션 소리 오염)
- **`shibuki_sample_024.wav`** (도네이션 소리 오염)
- **`shibuki_sample_025.wav`** (도네이션 소리 오염)

---

### ⚠️ 정제 필요 및 특이사항 샘플

1. **`001` ~ `010`번 샘플**:
   - **이슈**: 비닐포장/바스락거리는 환경 소음 혼입 (치킨/비닐장갑 잡담 구간)
   - **정제 방안**:
     - ① **스펙트럴 게이팅(Spectral Gating) & RNNoise/Demucs 고주파 노이즈 제거 필터** 적용 테스트
     - ② 노이즈 제거 후에도 잔향/위상 왜곡이 남을 경우, 비닐 소리가 전혀 없는 **완전 청정 저스트채팅 구간으로 1:1 대체 재추출**
2. **`009`번 샘플**:
   - **이슈**: 음원 초반부에 노래 소리/BGM 혼입
   - **정제 방안**: 앞부분 노래 구간을 슬라이싱(트림)하거나 완전 제외
3. **`023`번 샘플**:
   - **이슈**: 파일 2개 중복 또는 다른 음원 혼선 발생
   - **정제 방안**: 단일 정확한 시부키 음원으로 통합 및 메타데이터 정합성 검증

---

### 🌟 현재 청정/사용 가능 추천 샘플 (Clean Bank)
- **`shibuki_sample_010.wav`** (장난기/Tease)
- **`shibuki_sample_011.wav`** (차분한 소통/Neutral)
- **`shibuki_sample_012.wav`** (소통/Neutral)
- **`shibuki_sample_013.wav`** (당황/Flustered)
- **`shibuki_sample_014.wav`** (자신만만/Smug)
- **`shibuki_sample_015.wav`** (감사/Tease)
- **`shibuki_sample_017.wav`** (소통/Neutral)
- **`shibuki_sample_019.wav`** (소통/Neutral)
- **`shibuki_sample_023.wav`** (정리 후 편입)

---

## 2. 차기 파인튜닝 실행 계획
1. **오염 샘플 완전 배제**: `shibuki.list` 및 `voice_manifest.json`에서 오염 10개 샘플 제외
2. **추가 청정 음원 보충**: 유튜브 다시보기에서 도네이션 없는 청정 저챗 구간 15~20개 신규 추출
3. **신규 30~40개 마스터 데이터셋 구축 후 SoVITS + GPT 재학습** 진행
