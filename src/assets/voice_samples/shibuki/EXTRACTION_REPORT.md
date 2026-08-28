# 🎙️ Shibuki Voice Dataset Expansion Report (25 Master Samples)

- **Persona Name**: 텐코 시부키 (Tenko Shibuki / 天柑しぶき)
- **Persona ID**: shibuki
- **Language**: ko (Korean)
- **Total Standardized Samples**: 25 (Original: 10, Added: 15)
- **Sample Specifications**: 32kHz, 16-bit PCM Mono WAV, EBU R128 (-20 LUFS normalized)
- **DSP Filter Pipeline**: FFmpeg 5-Stage DSP (afftdn + highpass 80Hz + lowpass 12kHz + 2.5kHz Vocal EQ + speechnorm)
- **STT Engine**: Google Gemini 3.5 Flash Multimodal Audio Analysis

## 📌 Active Emotion Banks

| Emotion | Reference Audio | Prompt Text |
| :--- | :--- | :--- |
| **TEASE** | shibuki_sample_001.wav | 아니, 너무 비닐 소리야. 뭐가 좋은 거야? 밤 |
| **FLUSTERED** | shibuki_sample_003.wav | 혹시 모르니까 벌레가 나올 수도 있으니까 밤을 그 뭐지 |
| **NEUTRAL** | shibuki_sample_005.wav | 컴퓨터 책상에서 뭐 먹었는데 비닐장갑을 그때 두 장을 뽑아와서 한 |
| **SMUG** | shibuki_sample_014.wav | 대박 대박 대박 구했습니다! 하하! |

## 📋 Full Master Dataset (001 ~ 025)

| # | Sample ID | Emotion | Duration | Spoken Transcript |
| :---: | :--- | :---: | :---: | :--- |
| 1 | shibuki_sample_001 | tease | 5.5s | 아니, 너무 비닐 소리야. 뭐가 좋은 거야? 밤 |
| 2 | shibuki_sample_002 | tease | 5.31s | 하하하 헤헤헤 아니 |
| 3 | shibuki_sample_003 | flustered | 6.04s | 혹시 모르니까 벌레가 나올 수도 있으니까 밤을 그 뭐지 |
| 4 | shibuki_sample_004 | tease | 7.7s | 너 뭐야? 비닐장갑에 넣어 왔어? 아니 저번에 치킨 먹을 때 비닐장갑을 갖고 와서 |
| 5 | shibuki_sample_005 | neutral | 5.5s | 컴퓨터 책상에서 뭐 먹었는데 비닐장갑을 그때 두 장을 뽑아와서 한 |
| 6 | shibuki_sample_006 | flustered | 5.5s | 그래서 한 장이 컴퓨터 책상에 있었거든? 그래서 아니 거기다 놓아 |
| 7 | shibuki_sample_007 | neutral | 5.5s | 읏... 그렇게 빤히 쳐다보면... 부끄럽잖아...♡ |
| 8 | shibuki_sample_008 | neutral | 5.5s | 하아, 하아... 갑자기 소리 질렀더니 숨이 차네... 잠깐만 쉬자... |
| 9 | shibuki_sample_009 | neutral | 5.5s | 하아... 또 저러네. 그래그래, 오빠 맘대로 해라... |
| 10 | shibuki_sample_010 | tease | 3.01s | 여러분, 밤을 주웠어요. 상상도 못했죠? |
| 11 | shibuki_sample_011 | neutral | 5.5s | 구독 기념 인사가 되게 많아서 좀 밀렸나? 아이 구독 감사합니다. 고맙습니다. 2개월 |
| 12 | shibuki_sample_012 | tease | 5.5s | 어, 1개월 구독 감사... 고맙습니다. 아까 1개월 구독도 있었는데, 1개월 구독도 고마워, 이날이... 어서... |
| 13 | shibuki_sample_013 | flustered | 5.5s | 하아! 밍 감사합니다. 고맙습니다. 아 익명의 후원자님이 10만 친... 친공... |
| 14 | shibuki_sample_014 | smug | 5.5s | 대박 대박 대박 구했습니다! 하하! |
| 15 | shibuki_sample_015 | tease | 3.97s | 고마워요, 고마워요, 고마워요, 고마워요, 고마워요, 고마워요 |
| 16 | shibuki_sample_016 | neutral | 3.72s | 일본 여행의 운이 좋았었던 거 같아요 |
| 17 | shibuki_sample_017 | flustered | 3.84s | 누군가 다 스포했- 했다 했어- 했대 했었댔어 |
| 18 | shibuki_sample_018 | neutral | 6.44s | 어디선가 들어 들은 이나리들도 만났을 거야. 아이 만치님 감사합니다. 고맙습니다. |
| 19 | shibuki_sample_019 | flustered | 3.49s | 몰라요. 누군가가 우리 가기 전에 막 |
| 20 | shibuki_sample_020 | tease | 4.14s | 메모 메모 메모 |
| 21 | shibuki_sample_021 | tease | 5.5s | 에이 만나야 된다나? 뭐 이렇게 얘기하기도 했대 우리 가기 |
| 22 | shibuki_sample_022 | neutral | 5.5s | 가기 전에 사장님이랑 밥 먹었다고 하길래 부키 일본 가게 |
| 23 | shibuki_sample_023 | neutral | 3.53s | 우린 같이 간 것도 아니고 우린 사장님이랑 밥 안 먹었어 |
| 24 | shibuki_sample_024 | neutral | 3.77s | 근데 뭐 아무튼 아무튼 그렇게 얘기하기도 했고 |
| 25 | shibuki_sample_025 | neutral | 6.48s | 우리 아직 우리 아직 돌아오지도 않았는데 막 만났다고 바로 스페에서 얘기도 했다고 그러더라고요. |
