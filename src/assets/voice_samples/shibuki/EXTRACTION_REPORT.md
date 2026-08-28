# 🎙️ Shibuki Voice Dataset Expansion Report

- **Persona Name**: 텐코 시부키 (Tenko Shibuki / 天柑しぶき)
- **Persona ID**: `shibuki`
- **Language**: `ko` (Korean)
- **Total Standardized Samples**: 55 (Original: 10, Added: 15)
- **Sample Specifications**: 32kHz, 16-bit PCM Mono WAV, EBU R128 (-20 LUFS normalized)
- **DSP Filter Pipeline**: Demucs Architecture / FFmpeg 5-Stage DSP (afftdn + highpass 80Hz + lowpass 12kHz + 2.5kHz Vocal Presence EQ + speechnorm)
- **STT Engine**: Google Gemini 3.6 Flash Multimodal Audio Analysis

## 📌 Active Emotion Banks

| Emotion | Reference Audio | Prompt Text |
| :--- | :--- | :--- |
| **TEASE** | `shibuki_sample_001.wav` | 아니, 너무 비닐 소리야. 뭐가 좋은 거야? 밤 |
| **FLUSTERED** | `shibuki_sample_003.wav` | 혹시 모르니까 벌레가 나올 수도 있으니까 밤을 그 뭐지 |
| **NEUTRAL** | `shibuki_sample_005.wav` | 컴퓨터 책상에서 뭐 먹었는데 비닐장갑을 그때 두 장을 뽑아와서 한 |
| **SMUG** | `shibuki_sample_014.wav` | 대박 대박 대박 구했습니다! 하하! |

## 📋 Newly Extracted Samples (011 ~ 025)

| # | Sample ID | Emotion | Duration | Source Window | Spoken Transcript | Quality / Conf |
| :---: | :--- | :---: | :---: | :---: | :--- | :---: |
| 11 | `shibuki_sample_011` | `neutral` | 5.5s | msIPcAalaeI_talk (15.7s~21.2s) | 구독 기념 인상화 되게 많아서 좀 밀렸나? 아이 구독 감사합니다. 고맙습니다. 2개월 | Clean (0.95) |
| 12 | `shibuki_sample_012` | `neutral` | 5.5s | msIPcAalaeI_talk (20.7s~26.2s) | 2개월 구독 감사합니다 고맙습니다. 아까 1개월 구독도 있었는데 1개월 구독도 고마워. 이나리 어서 | Clean (0.95) |
| 13 | `shibuki_sample_013` | `neutral` | 5.5s | msIPcAalaeI_talk (35.7s~41.2s) | 하앙 님 감사합니다 고맙습니다. 아 익명의 유저 님이 10만 치즈 공 | Clean (0.90) |
| 14 | `shibuki_sample_014` | `smug` | 5.5s | msIPcAalaeI_talk (40.7s~46.2s) | 생공냥의 대박 뽀! 대박 뽀! 구하겠습니다. 하! | Clean (0.95) |
| 15 | `shibuki_sample_015` | `tease` | 3.97s | msIPcAalaeI_talk (48.8s~52.8s) | 고마워요 고마워요 고마워요 고마워요 고마워요 고마워요 | Clean (0.95) |
| 16 | `shibuki_sample_016` | `neutral` | 5.5s | msIPcAalaeI_talk (64.9s~70.4s) | 일단은 전 되게 이번 친구도 없이 무사히 잘 다녀온 것 같아 다행이에요. | Clean (0.95) |
| 17 | `shibuki_sample_017` | `neutral` | 3.72s | msIPcAalaeI_talk (69.9s~73.6s) | 이번 여행은 운이 좋았었던 것 같아요. | Clean (0.98) |
| 18 | `shibuki_sample_018` | `smug` | 5.82s | msIPcAalaeI_talk (96.6s~102.4s) | 와 몰랐어. 거짓말 치지 마. 사랑스럽게 인사하래. 뭐야, 완전 털렸나 봐. | Clean (0.95) |
| 19 | `shibuki_sample_019` | `flustered` | 3.84s | msIPcAalaeI_talk (112.8s~116.7s) | 누군가 다 스포했 했대했어 했대했어 헸어 | Clean (0.88) |
| 20 | `shibuki_sample_020` | `neutral` | 4.17s | msIPcAalaeI_talk (123.7s~127.9s) | 장 몰랐는데. 아 몰랐던 인원들도 많았겠지만 | Clean (0.95) |
| 21 | `shibuki_sample_021` | `neutral` | 6.44s | msIPcAalaeI_talk (128.8s~135.2s) | 어디선가 들어 듣는 이나일들도 만났을 거야. 키우고 싶어. 아이 만치는 감사합니다. 고맙습니다. | Clean (0.88) |
| 22 | `shibuki_sample_022` | `neutral` | 4.51s | msIPcAalaeI_talk (149.5s~154.0s) | 에디베리 세동베리 잘 다녀왔어? 아, 잘 다녀왔어. | Clean (0.95) |
| 23 | `shibuki_sample_023` | `flustered` | 3.49s | msIPcAalaeI_talk (156.1s~159.6s) | 몰라요. 누군가가 우리 가기 전에 막 | Clean (0.92) |
| 24 | `shibuki_sample_024` | `neutral` | 4.14s | msIPcAalaeI_talk (160.6s~164.8s) | 멤버 멤버 멤버 | Clean (0.90) |
| 25 | `shibuki_sample_025` | `neutral` | 5.5s | msIPcAalaeI_talk (167.5s~173.0s) | 언제 만나야 됐나? 뭐 이렇게 이야기하기도 했대? 우리 가? | Clean (0.92) |

## 📋 Full Master Dataset (001 ~ 025)

| # | Sample ID | Emotion | Duration | Spoken Transcript |
| :---: | :--- | :---: | :---: | :--- |
| 1 | `shibuki_sample_001` | `tease` | 5.5s | 아니, 너무 비닐 소리야. 뭐가 좋은 거야? 밤 |
| 2 | `shibuki_sample_002` | `tease` | 5.31s | 하하하 헤헤헤 아니 |
| 3 | `shibuki_sample_003` | `flustered` | 6.04s | 혹시 모르니까 벌레가 나올 수도 있으니까 밤을 그 뭐지 |
| 4 | `shibuki_sample_004` | `tease` | 7.7s | 너 뭐야? 비닐장갑에 넣어 왔어? 아니 저번에 치킨 먹을 때 비닐장갑을 갖고 와서 |
| 5 | `shibuki_sample_005` | `neutral` | 5.5s | 컴퓨터 책상에서 뭐 먹었는데 비닐장갑을 그때 두 장을 뽑아와서 한 |
| 6 | `shibuki_sample_006` | `flustered` | 5.5s | 그래서 한 장이 컴퓨터 책상에 있었거든? 그래서 아니 거기다 놓아 |
| 7 | `shibuki_sample_007` | `neutral` | 5.5s | 읏... 그렇게 빤히 쳐다보면... 부끄럽잖아...♡ |
| 8 | `shibuki_sample_008` | `neutral` | 5.5s | 하아, 하아... 갑자기 소리 질렀더니 숨이 차네... 잠깐만 쉬자... |
| 9 | `shibuki_sample_009` | `neutral` | 5.5s | 하아... 또 저러네. 그래그래, 오빠 맘대로 해라... |
| 10 | `shibuki_sample_010` | `tease` | 3.01s | 여러분, 밤을 주웠어요. 상상도 못했죠? |
| 11 | `shibuki_sample_011` | `neutral` | 5.5s | 구독 기념 인사가 되게 많아서 좀 밀렸나? 아이 구독 감사합니다. 고맙습니다. 2개월 |
| 12 | `shibuki_sample_012` | `tease` | 5.5s | 어, 1개월 구독 감사... 고맙습니다. 아까 1개월 구독도 있었는데, 1개월 구독도 고마워, 이날이... 어서... |
| 13 | `shibuki_sample_013` | `flustered` | 5.5s | 하아! 밍 감사합니다. 고맙습니다. 아 익명의 후원자님이 10만 친... 친공... |
| 14 | `shibuki_sample_014` | `smug` | 5.5s | 대박 대박 대박 구했습니다! 하하! |
| 15 | `shibuki_sample_015` | `tease` | 3.97s | 고마워요, 고마워요, 고마워요, 고마워요, 고마워요, 고마워요 |
| 16 | `shibuki_sample_016` | `neutral` | 3.72s | 일본 여행의 운이 좋았었던 거 같아요 |
| 17 | `shibuki_sample_017` | `flustered` | 3.84s | 누군가 다 스포했- 했다 했어- 했대 했었댔어 |
| 18 | `shibuki_sample_018` | `neutral` | 6.44s | 어디선가 들어 들은 이나리들도 만났을 거야. 아이 만치님 감사합니다. 고맙습니다. |
| 19 | `shibuki_sample_019` | `flustered` | 3.49s | 몰라요. 누군가가 우리 가기 전에 막 |
| 20 | `shibuki_sample_020` | `tease` | 4.14s | 메모 메모 메모 |
| 21 | `shibuki_sample_021` | `tease` | 5.5s | 에이 만나야 된다나? 뭐 이렇게 얘기하기도 했대 우리 가기 |
| 22 | `shibuki_sample_022` | `neutral` | 5.5s | 가기 전에 사장님이랑 밥 먹었다고 하길래 부키 일본 가게 |
| 23 | `shibuki_sample_023` | `neutral` | 3.53s | 우린 같이 간 것도 아니고 우린 사장님이랑 밥 안 먹었어 |
| 24 | `shibuki_sample_024` | `neutral` | 3.77s | 근데 뭐 아무튼 아무튼 그렇게 얘기하기도 했고 |
| 25 | `shibuki_sample_025` | `neutral` | 6.48s | 우리 아직 우리 아직 돌아오지도 않았는데 막 만났다고 바로 스페에서 얘기도 했다고 그러더라고요. |
| 11 | `shibuki_sample_011` | `neutral` | 5.5s | 구독 기념 인사가 되게 많아서 좀 밀렸나? 아이 구독 감사합니다. 고맙습니다. 이개월 |
| 12 | `shibuki_sample_012` | `tease` | 5.5s | 어, 1개월 구독 감사... 고맙습니다. 아까 1개월 구독도 있었는데, 1개월 구독도 고마워 이날이 어서 |
| 13 | `shibuki_sample_013` | `flustered` | 5.5s | 하아! 님 감사합니다. 고맙습니다. 아 익명의 후원자님이 십만 친즈 공... |
| 14 | `shibuki_sample_014` | `smug` | 5.5s | 생공냥의 대박 뽀 대박 뽀 구원합니다. 하! |
| 15 | `shibuki_sample_015` | `smug` | 3.97s | 크나요, 크나요. 크나요, 크나요, 크나요, 크나요. |
| 16 | `shibuki_sample_016` | `neutral` | 5.5s | 일단은 전 되게 이번 친구도 없이 무사히 잘 다녀온 것 같아 다행이에요. |
| 17 | `shibuki_sample_017` | `neutral` | 3.72s | 이번 여행은 운이 좋았었던 것 같아요. |
| 18 | `shibuki_sample_018` | `smug` | 5.82s | 와 몰랐어 거짓말 치지 마. 사랑스럽게 인사하네. 와 완전 눌렸나 봐. |
| 19 | `shibuki_sample_019` | `flustered` | 3.84s | 누군가 다 스포했을 했을 했을 했을 |
| 20 | `shibuki_sample_020` | `neutral` | 4.17s | 장 몰랐는데. 아 몰랐던 인아네들도 많았겠지만, |
| 21 | `shibuki_sample_021` | `neutral` | 6.44s | 어디선가 들은 이나리즈도 만났을 거야. 아, 만치는 감사합니다. 고맙습니다. |
| 22 | `shibuki_sample_022` | `tease` | 4.51s | 에디베디, 세드롱베디, 잘 다녀왔어? 아, 응 잘 다녀왔어. |
| 23 | `shibuki_sample_023` | `flustered` | 3.49s | 몰라요. 누군가가 우리 가기 전에 막 |
| 24 | `shibuki_sample_024` | `neutral` | 4.14s | 멤버, 멤버, 멤버! 마시. |
| 25 | `shibuki_sample_025` | `neutral` | 5.5s | 만간 1분간 에이디 만나야 됐나? 뭐 이렇게 얘기하기도 했대. 우리 가기 |
| 11 | `shibuki_sample_011` | `neutral` | 5.5s | 구독 기념 인상화 되게 많아서 좀 밀렸나? 아이 구독 감사합니다. 고맙습니다. 2개월 |
| 12 | `shibuki_sample_012` | `neutral` | 5.5s | 2개월 구독 감사합니다 고맙습니다. 아까 1개월 구독도 있었는데 1개월 구독도 고마워. 이나리 어서 |
| 13 | `shibuki_sample_013` | `neutral` | 5.5s | 하앙 님 감사합니다 고맙습니다. 아 익명의 유저 님이 10만 치즈 공 |
| 14 | `shibuki_sample_014` | `smug` | 5.5s | 생공냥의 대박 뽀! 대박 뽀! 구하겠습니다. 하! |
| 15 | `shibuki_sample_015` | `tease` | 3.97s | 고마워요 고마워요 고마워요 고마워요 고마워요 고마워요 |
| 16 | `shibuki_sample_016` | `neutral` | 5.5s | 일단은 전 되게 이번 친구도 없이 무사히 잘 다녀온 것 같아 다행이에요. |
| 17 | `shibuki_sample_017` | `neutral` | 3.72s | 이번 여행은 운이 좋았었던 것 같아요. |
| 18 | `shibuki_sample_018` | `smug` | 5.82s | 와 몰랐어. 거짓말 치지 마. 사랑스럽게 인사하래. 뭐야, 완전 털렸나 봐. |
| 19 | `shibuki_sample_019` | `flustered` | 3.84s | 누군가 다 스포했 했대했어 했대했어 헸어 |
| 20 | `shibuki_sample_020` | `neutral` | 4.17s | 장 몰랐는데. 아 몰랐던 인원들도 많았겠지만 |
| 21 | `shibuki_sample_021` | `neutral` | 6.44s | 어디선가 들어 듣는 이나일들도 만났을 거야. 키우고 싶어. 아이 만치는 감사합니다. 고맙습니다. |
| 22 | `shibuki_sample_022` | `neutral` | 4.51s | 에디베리 세동베리 잘 다녀왔어? 아, 잘 다녀왔어. |
| 23 | `shibuki_sample_023` | `flustered` | 3.49s | 몰라요. 누군가가 우리 가기 전에 막 |
| 24 | `shibuki_sample_024` | `neutral` | 4.14s | 멤버 멤버 멤버 |
| 25 | `shibuki_sample_025` | `neutral` | 5.5s | 언제 만나야 됐나? 뭐 이렇게 이야기하기도 했대? 우리 가? |
