# 📘 Project BUKI - 텐코 시부키 보이스 데이터셋 수집 및 파인튜닝 인수인계 매뉴얼

> **문서 버전**: v2.1 (2026-08-28)  
> **현재 데이터셋 상태**: **105개 청정 샘플 수집 완료 (총 519.35초 / 약 8.66분 분량)**  
> **가중치 상태**: 이전 가중치(`shibuki_e12_s528.pth` + `shibuki-e20.ckpt`) ➔ **100+ 샘플 기반 대규모 파인튜닝 준비 완료**

---

## 1. 🚨 다음 세션 필수 준수 사항 (Golden Rules)

1. **파인튜닝 조기 실행 절대 금지**:
   * 샘플 수가 **100개 이상(약 10~15분 분량)** 모이기 전까지는 `train_shibuki_gpt_sovits.py`를 실행하지 마십시오.
   * 현재 29개 샘플로 음향 모델(SoVITS)은 톤이 안착되었으나, GPT 운율 모델이 완벽한 한국어 억양을 고정하기 위해서는 100개 이상의 청정 발화가 필수적입니다.
2. **엄격한 오염 데이터 배제 원칙**:
   * ❌ **도네이션 소리 오염 금지**: 투네이션, 트윕, 치지직 등 후원 알림음(띵동, 짤랑, 효과음)이 섞인 샘플 100% 폐기
   * ❌ **생활 소음 배제**: 비닐봉지 부스럭거림, 음식 포장지 소리, 마이크 충격음, 책상 치는 소리 배제
   * ❌ **BGM/노래 배제**: 초반 노래 부르는 구간, BGM이 과도하게 섞인 구간 배제
   * ❌ **외국어/환각 텍스트 배제**: STT 결과에 영어/러시아어/스페인어 등 라틴 문자가 섞인 클립은 즉시 폐기

---

## 2. 🔬 최신 음원 수집 및 전처리 파이프라인 구조 (Methodology)

최근 정립된 고품질 음원 수집 방식은 **오프라인 5단계 DSP 필터 체인 + 로컬 Whisper 음성 인식**으로 동작합니다.

```mermaid
flowchart TD
    A["YouTube 다시보기 저챗 구간<br/>(@shibukireplay)"] -->|"yt-dlp 구간 다운로드 (-ss, -t)"| B["Raw MP3 Audio"]
    B -->|"FFmpeg 5-Stage DSP<br/>(대역통과 + 노이즈 게이트 + LUFS)"| C["Clean 32kHz Mono PCM WAV"]
    C -->|"VAD Silence Removal<br/>(3.0s ~ 7.0s 단위 분할)"| D["Candidate Voice Clips"]
    D -->|"Local Whisper STT<br/>(base / small 모델)"| E["Korean Hangul Transcripts"]
    E -->|"품질 검수 필터<br/>(도네이션/라틴문자/노이즈 배제)"| F["Pristine shibuki.list<br/>(1:1 정합 데이터셋)"]
    F -->|"100개 달성 시"| G["GPT-SoVITS 5단계 파인튜닝"]
```

### 단계별 상세 로직

1. **Stage 1: 저챗(잡담) 구간 타겟팅 (`yt-dlp`)**:
   * 게임 플레이나 노래 방송을 피하고, 차분하게 소통하는 저스트채팅 구간만 타임스탬프로 지정하여 다운로드
   ```bash
   python -m yt_dlp --extract-audio --audio-format mp3 --postprocessor-args "-ss {start_sec} -t {duration}" -o "{output_mp3}" "{url}"
   ```
2. **Stage 2: 5단계 DSP 음향 정제 (`ffmpeg`)**:
   * 80Hz 이하 저주파 웅웅거림(Highpass) 및 12kHz 이상 고주파 치찰음(Lowpass) 제거
   * `anlmdn`(비로컬 평균 디노이즈) 필터로 주변 잡음 억제
   * EBU R128 (`loudnorm=I=-20:TP=-1.5:LRA=11`) 표준 음량 정규화
   * 32kHz 16-bit Mono PCM WAV로 통일
3. **Stage 3: VAD 무음 제거 및 3.0s~7.0s 정밀 슬라이싱**:
   * `silenceremove` 필터로 말과 말 사이의 공백을 자르고, 학습에 최적화된 3~7초 단위 클립 생성
4. **Stage 4: 로컬 Whisper 오프라인 STT (100% 무제한)**:
   * API 쿼터 제약이 없는 로컬 Whisper (`whisper.load_model('base')`, `language='ko'`)로 한국어 텍스트 전사
5. **Stage 5: 라틴 문자 및 환각 대사 정제 필터**:
   * 영문(`[a-zA-Z]`)이나 특수문자가 포함된 클립은 노이즈로 간주하여 자동 폐기
   * 순수 한글 완성형 문장만 `src/assets/voice_samples/shibuki/shibuki.list`에 1:1 매칭 등록

---

## 3. 🎯 100개 샘플 달성을 위한 추천 다시보기 풀 (Candidate Archives)

다음 세션에서 추가 다운로드 및 추출을 진행할 아카이브 목록입니다:

| 유튜브 영상 ID | 방송 제목 / 특징 | 권장 추출 구간 (초) |
| :--- | :--- | :--- |
| `msIPcAalaeI` | 휴가 다녀와서 잡담 (도네이션 적고 차분한 토크) | `900~1200`, `1800~2100`, `2700~3000` |
| `jkzH7Jm-NSo` | 유메퍼센트 썰풀이 (발화 밀도 높고 감정 풍부) | `400~700`, `1200~1500`, `1800~2100` |
| `sl2ipsuzJAk` | 2기 PPT 발표회 잡담 (목소리 톤 선명) | `600~900`, `1500~1800`, `2400~2700` |
| `dKNSz5UtAEY` | 8월 26일 최신 저챗 방송 | `300~600`, `1200~1500`, `2100~2400` |
| `AxeGn6xzVZM` | 8월 24일 소통 방송 | `600~900`, `1500~1800` |

---

## 4. 📋 다음 세션 작업 실행 체크리스트 (Next Agent Guide)

```markdown
- [ ] 1. 시스템 서비스 상태 점검 (포트 8000, 9880, 9882 활성화 여부 확인)
- [ ] 2. `scripts/collect_clean_shibuki_samples.py` 타겟 인터벌 확장 후 음원 수집 실행
- [ ] 3. `shibuki.list` 내 100% 한글 정합성 검수 스크립트 실행 (노이즈/영문 클립 배제)
- [ ] 4. 총 청정 샘플 수가 100개 이상(100~150개)에 도달했는지 확인
- [ ] 5. 100개 달성 확인 후 `python scripts/train_shibuki_gpt_sovits.py` 5단계 파인튜닝 가동
- [ ] 6. 생성된 신규 가중치(`SoVITS_weights_v2/`, `GPT_weights_v2/`)를 `gpt_sovits_service.py`에 등록 및 라이브 로드
- [ ] 7. 한국어 음성 합성 품질 검증 및 git commit/push
```

---

## 5. ⚙️ 현재 시스템 가동 정보

* **FastAPI 백엔드**: `http://127.0.0.1:8000`
* **GPT-SoVITS 추론 엔진**: `http://127.0.0.1:9880`
* **Chatterbox 다국어 엔진**: `http://127.0.0.1:9882`
* **Supervisor Watchdog**: `tools/supervisor.py` (자동 복구 데몬)
* **현재 활성 모델 가중치**:
  * SoVITS: `C:/Users/rerun/opendcmart/tools/GPT-SoVITS/SoVITS_weights_v2/shibuki_e12_s528.pth`
  * GPT: `C:/Users/rerun/opendcmart/tools/GPT-SoVITS/GPT_weights_v2/shibuki-e20.ckpt`
