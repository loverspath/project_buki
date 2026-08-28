// Project BUKI - Bulletproof Mobile Audio & AI Messenger + Script Reader Client
class BukiMobileClient {
  constructor() {
    // Mode Switcher Tabs
    this.tabChatBtn = document.getElementById('tabChatBtn');
    this.tabScriptBtn = document.getElementById('tabScriptBtn');
    this.chatView = document.getElementById('chatView');
    this.scriptView = document.getElementById('scriptView');

    // Chat Elements
    this.chatContainer = document.getElementById('chatContainer');
    this.chatHistoryEl = document.getElementById('chatHistory');
    this.chatForm = document.getElementById('chatForm');
    this.messageInput = document.getElementById('messageInput');
    this.sendBtn = document.getElementById('sendBtn');
    
    // Controls & Settings
    this.emotionSelectTop = document.getElementById('emotionSelectTop');
    this.emotionSelectSheet = document.getElementById('emotionSelectSheet');
    this.actingEmotion = 'auto';

    this.quickVoiceBtn = document.getElementById('quickVoiceBtn');
    this.voiceStatusText = document.getElementById('voiceStatusText');
    this.openSettingsBtn = document.getElementById('openSettingsBtn');
    this.closeSettingsBtn = document.getElementById('closeSettingsBtn');
    this.modalBackdrop = document.getElementById('modalBackdrop');
    this.settingsSheet = document.getElementById('settingsSheet');
    this.personaGrid = document.getElementById('personaGrid');
    this.personaSelect = document.getElementById('personaSelect');
    this.modelSelect = document.getElementById('modelSelect');
    this.ttsEngineSelectTop = document.getElementById('ttsEngineSelectTop');
    this.ttsEngineSelect = document.getElementById('ttsEngineSelect');
    this.ttsStatusDetail = document.getElementById('ttsStatusDetail');
    this.testVoiceBtn = document.getElementById('testVoiceBtn');

    // Avatar & Wave
    this.avatarGlow = document.getElementById('avatarGlow');
    this.avatarOrb = document.getElementById('avatarOrb');
    this.avatarFace = document.getElementById('avatarFace');
    this.badgeName = document.getElementById('badgeName');
    this.currentEngineBadge = document.getElementById('currentEngineBadge');
    this.speakingState = document.getElementById('speakingState');
    this.audioWaveBox = document.getElementById('audioWaveBox');

    // Script Reader Elements
    this.scriptInputScreen = document.getElementById('scriptInputScreen');
    this.scriptPlayerScreen = document.getElementById('scriptPlayerScreen');
    this.scriptInputText = document.getElementById('scriptInputText');
    this.scriptPersonaSelect = document.getElementById('scriptPersonaSelect');
    this.scriptEngineSelect = document.getElementById('scriptEngineSelect');
    this.parseScriptBtn = document.getElementById('parseScriptBtn');
    this.editScriptBtn = document.getElementById('editScriptBtn');
    this.scriptDisplayContainer = document.getElementById('scriptDisplayContainer');
    this.playerProgressBadge = document.getElementById('playerProgressBadge');
    this.playerEmotionBadge = document.getElementById('playerEmotionBadge');
    this.playPauseScriptBtn = document.getElementById('playPauseScriptBtn');
    this.playIcon = document.getElementById('playIcon');
    this.playLabel = document.getElementById('playLabel');
    this.prevSegmentBtn = document.getElementById('prevSegmentBtn');
    this.nextSegmentBtn = document.getElementById('nextSegmentBtn');
    this.replaySegmentBtn = document.getElementById('replaySegmentBtn');
    
    // Script Presets
    this.presetMutsuki = document.getElementById('presetMutsuki');
    this.presetMorning = document.getElementById('presetMorning');
    this.presetSensual = document.getElementById('presetSensual');
    this.presetFear = document.getElementById('presetFear');
    this.presetResigned = document.getElementById('presetResigned');

    // Persistent Mobile Audio Engine
    this.audioPlayer = new Audio();
    this.audioPlayer.preload = 'auto';
    this.audioUnlocked = false;

    // Chat State
    this.history = [];
    this.audioQueue = [];
    this.isPlayingAudio = false;
    this.voiceEnabled = true;

    // Script Reader State
    this.scriptSegments = [];
    this.dialogueIndices = []; // indices of segments that are dialogues
    this.currentDialoguePointer = 0; // index into dialogueIndices
    this.isScriptPlaying = false;
    this.scriptAudioCache = {}; // id -> base64 audio

    this.personaColors = {
      shibuki: '#ff9900',
      shibuki_mesugaki: '#ff4d88',
      shibuki_rimuru: '#38bdf8',
      mesugaki: '#ff4d88',
      mutsuki: '#ff2d55',
      sayaka: '#4da6ff',
      ruri: '#a855f7'
    };

    this.personaFaces = {
      shibuki: { idle: '🦊', speaking: '🗣️', laugh: '😆', smug: '😏', pout: '😤' },
      shibuki_mesugaki: { idle: '😈', speaking: '😜', laugh: '😆', smug: '😏', pout: '😤' },
      shibuki_rimuru: { idle: '✨', speaking: '🗣️', laugh: '😆', smug: '😏', pout: '😤' },
      mesugaki: { idle: '😏', speaking: '😜', smirk: '😼', sigh: '😮‍💨', glare: '😒' },
      mutsuki: { idle: '💣', speaking: '😜', smirk: '😼', sigh: '😮‍💨', glare: '😈' },
      sayaka: { idle: '✨', speaking: '😊', laugh: '😆', think: '🤔' },
      ruri: { idle: '🧐', speaking: '🎙️', analyze: '📊', calm: '😌' }
    };

    this.init();
  }

  async init() {
    this.setupEventListeners();
    this.setupScriptReader();
    await this.fetchModelsAndPersonas();
    this.updateTheme();
    this.updateTTSBadge();
  }

  unlockAudio() {
    if (this.audioUnlocked) return;
    try {
      this.audioPlayer.src = 'data:audio/wav;base64,UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA';
      const playPromise = this.audioPlayer.play();
      if (playPromise !== undefined) {
        playPromise.then(() => {
          this.audioUnlocked = true;
          this.audioPlayer.pause();
        }).catch(e => {
          console.warn('[Audio Engine] Unlock pending:', e);
        });
      }
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) {
        const ctx = new AudioCtx();
        ctx.resume().then(() => { this.audioUnlocked = true; });
      }
    } catch (e) {
      console.warn('[Audio Engine] Unlock error:', e);
    }
  }

  setupEventListeners() {
    // Unlock on any touch/click
    document.addEventListener('click', () => this.unlockAudio(), { once: true });
    document.addEventListener('touchstart', () => this.unlockAudio(), { once: true });

    // Mode Switcher Tabs
    this.tabChatBtn.addEventListener('click', () => this.switchView('chat'));
    this.tabScriptBtn.addEventListener('click', () => this.switchView('script'));

    // Chat submit
    this.chatForm.addEventListener('submit', (e) => {
      e.preventDefault();
      this.sendMessage();
    });

    // Auto-grow textarea
    this.messageInput.addEventListener('input', () => {
      this.messageInput.style.height = 'auto';
      this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 100) + 'px';
    });

    // Enter to submit (Shift+Enter for newline)
    this.messageInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });

    // Acting Emotion Style Selector (Topbar & Settings Sheet)
    if (this.emotionSelectTop) {
      this.emotionSelectTop.addEventListener('change', (e) => {
        this.setActingEmotion(e.target.value);
      });
    }

    if (this.emotionSelectSheet) {
      this.emotionSelectSheet.addEventListener('change', (e) => {
        this.setActingEmotion(e.target.value);
      });
    }

    // Quick Voice Toggle Button
    this.quickVoiceBtn.addEventListener('click', () => {
      this.voiceEnabled = !this.voiceEnabled;
      if (this.voiceEnabled) {
        this.quickVoiceBtn.classList.add('active');
        this.quickVoiceBtn.querySelector('.pill-icon').textContent = '🔊';
        this.voiceStatusText.textContent = '음성 ON';
        this.unlockAudio();
      } else {
        this.quickVoiceBtn.classList.remove('active');
        this.quickVoiceBtn.querySelector('.pill-icon').textContent = '🔇';
        this.voiceStatusText.textContent = '음성 OFF';
        this.stopAudioQueue();
      }
      this.updateTTSBadge();
      this.saveSettings();
    });

    // Settings Modal
    this.openSettingsBtn.addEventListener('click', () => this.openSettings());
    this.closeSettingsBtn.addEventListener('click', () => this.closeSettings());
    this.modalBackdrop.addEventListener('click', () => this.closeSettings());

    // Persona Selection (Grid buttons)
    this.personaGrid.querySelectorAll('.segment-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        this.personaGrid.querySelectorAll('.segment-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const p = btn.dataset.persona;
        this.personaSelect.value = p;
        this.updateTheme();
        this.saveSettings();
      });
    });

    this.personaSelect.addEventListener('change', () => {
      const p = this.personaSelect.value;
      this.personaGrid.querySelectorAll('.segment-btn').forEach(b => {
        b.classList.toggle('active', b.dataset.persona === p);
      });
      this.updateTheme();
      this.saveSettings();
    });

    // Model Select change
    this.modelSelect.addEventListener('change', () => this.saveSettings());

    // TTS Engine Select (Topbar Quick Dropdown)
    if (this.ttsEngineSelectTop) {
      this.ttsEngineSelectTop.addEventListener('change', (e) => {
        if (this.ttsEngineSelect) this.ttsEngineSelect.value = e.target.value;
        if (this.scriptEngineSelect) this.scriptEngineSelect.value = e.target.value;
        this.updateTTSBadge();
        this.saveSettings();
      });
    }

    // TTS Engine Select (Settings Sheet Dropdown)
    if (this.ttsEngineSelect) {
      this.ttsEngineSelect.addEventListener('change', () => {
        if (this.ttsEngineSelectTop) this.ttsEngineSelectTop.value = this.ttsEngineSelect.value;
        if (this.scriptEngineSelect) this.scriptEngineSelect.value = this.ttsEngineSelect.value;
        this.updateTTSBadge();
        this.saveSettings();
      });
    }

    // Script Reader TTS Engine Select
    if (this.scriptEngineSelect) {
      this.scriptEngineSelect.addEventListener('change', () => {
        if (this.ttsEngineSelect) this.ttsEngineSelect.value = this.scriptEngineSelect.value;
        if (this.ttsEngineSelectTop) this.ttsEngineSelectTop.value = this.scriptEngineSelect.value;
        this.updateTTSBadge();
        this.saveSettings();
      });
    }

    // Quick Action Chips
    document.querySelectorAll('.quick-chips-bar .chip-btn').forEach(chip => {
      chip.addEventListener('click', () => {
        this.messageInput.value = chip.dataset.text;
        this.sendMessage();
      });
    });

    // Test Voice button
    this.testVoiceBtn.addEventListener('click', async () => {
      this.unlockAudio();
      this.testVoiceBtn.disabled = true;
      this.testVoiceBtn.textContent = '🎙️ 음성 합성 중...';
      try {
        const emotionSamples = {
          sensual: '(달아오른 목소리로) ...읏... 바보 오빠, 지금 내 목소리 잘 들려? 허접♡',
          panting: '(가쁜 숨을 헐떡이며) 하아, 하아... 오빠, 나 숨차단 말이야...',
          flustered: '앗, 바보야! 어딜 그렇게 뚫어져라 쳐다보는 거야?!',
          whisper: '(귓가에 살며시) 오빠, 가까이 와봐... 비밀 이야기 해줄게...',
          terrified: '히익...! 살려줘! 진짜 무섭단 말이야, 바보 오빠!',
          resigned: '하아... 이제 다 끝났어... 마음대로 해, 허접 오빠...',
          crying: '흑... 왜 자꾸 나만 괴롭히는 건데... 바보!',
          smug: '어라~? 고작 그 정도로 지친 거야? 풋, 진짜 못말리는 허접이네~',
          angry: '진짜 짜증 나게 왜 자꾸 사람 말을 못 알아듣는 건데?!',
          auto: '오빠, 지금 내 목소리 잘 들려? 허접♡'
        };

        const sampleText = emotionSamples[this.actingEmotion] || emotionSamples.auto;

        const res = await fetch('/api/tts', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            text: sampleText,
            persona_id: this.personaSelect.value,
            tts_engine: this.ttsEngineSelect.value,
            acting_emotion: this.actingEmotion
          })
        });
        if (res.ok) {
          const data = await res.json();
          this.enqueueAudio(data.audio_base64, '목소리 테스트', [], data.engine_used);
        } else {
          alert('TTS 생성 실패');
        }
      } catch (err) {
        alert('TTS 테스트 오류: ' + err.message);
      } finally {
        this.testVoiceBtn.disabled = false;
        this.testVoiceBtn.textContent = '🔊 목소리 테스트 재생';
      }
    });
  }

  switchView(viewName) {
    this.stopAudioQueue();
    this.isScriptPlaying = false;

    if (viewName === 'chat') {
      this.tabChatBtn.classList.add('active');
      this.tabScriptBtn.classList.remove('active');
      this.chatView.style.display = 'flex';
      this.scriptView.style.display = 'none';
    } else {
      this.tabScriptBtn.classList.add('active');
      this.tabChatBtn.classList.remove('active');
      this.scriptView.style.display = 'flex';
      this.chatView.style.display = 'none';
    }
  }

  // ===================================================
  // SCRIPT READER ENGINE
  // ===================================================
  setupScriptReader() {
    // Preset Buttons
    if (this.presetMutsuki) {
      this.presetMutsuki.addEventListener('click', () => {
        this.scriptInputText.value = 
`(오빠의 방 문을 벌컥 열며 짓궂은 미소를 짓는다.)
"쿠후후~ 바보 오빠, 아직도 침대에서 뒹굴거리고 있는 거야? 풋, 진짜 못말리는 허접이네~"
그녀는 혀를 차며 어이없다는 듯이 팔짱을 꼈다.
"내가 깨워주러 안 왔으면 하루 종일 잘 생각이었지? 오늘 나랑 약속한 거 잊어버린 건 아니겠지?"
그러고는 귓가에 살며시 다가와 귓속말로 속삭였다.
"자꾸 늦장 부리면... 오빠 방에 폭탄 설치해버릴지도 몰라? 우후후~"`;
      });
    }

    if (this.presetMorning) {
      this.presetMorning.addEventListener('click', () => {
        this.scriptInputText.value = 
`(이불을 홱 걷어차며 한심하다는 표정으로 째려본다.)
"하아?! 아직도 안 일어난 거야? 언제까지 잠만 잘 셈인데, 바보!"
그녀는 콧방귀를 뀌며 고개를 홱 돌렸다.
"내가 특별히 깨워주러 온 거니까 감사히 생각하라고, 알겠어?"
볼을 살짝 붉히며 우물쭈물거렸다.
"오, 오빠랑 같이 가고 싶어서 온 건 절대 아니거든?!"`;
      });
    }

    if (this.presetSensual) {
      this.presetSensual.addEventListener('click', () => {
        this.scriptInputText.value = 
`(부끄러운 듯 얼굴을 붉히며 가쁜 숨을 내쉰다.)
"바보 오빠... 어딜 그렇게 뚫어져라 보고 있는 거야...?"
그녀는 살짝 달아오른 목소리로 신음하듯 귓가에 속삭였다.
"자꾸 그렇게 쳐다보면... 나도 몰라... 읏...♡"
그러고는 부끄러운 듯 고개를 숙이며 앙탈을 부렸다.
"오빠는 진짜 못말리는 변태라니까..."`;
      });
    }

    if (this.presetFear) {
      this.presetFear.addEventListener('click', () => {
        this.scriptInputText.value = 
`(어둠 속에서 무언가 다가오자 사시나무처럼 벌벌 떨며 비명을 지른다.)
"히익...! 저, 저게 뭐야?! 오빠, 살려줘!"
겁에 질려 눈물을 글썽이며 오빠의 옷자락을 꽉 붙잡았다.
"제발... 무섭단 말이야...! 가지 마...!"`;
      });
    }

    if (this.presetResigned) {
      this.presetResigned.addEventListener('click', () => {
        this.scriptInputText.value = 
`(모든 것을 포기한 듯 깊은 한숨을 내쉬며 멍하니 쳐다본다.)
"하아... 이제 다 끝났어. 아무것도 소용없어..."
낮고 느린 지친 목소리로 무기력하게 중얼거렸다.
"마음대로 해... 어차피 난 상관없으니까..."`;
      });
    }

    // Parse script button
    this.parseScriptBtn.addEventListener('click', async () => {
      const text = this.scriptInputText.value.trim();
      if (!text) {
        alert('대본 텍스트를 입력해 주세요!');
        return;
      }
      await this.parseAndPrepareScript(text);
    });

    // Edit script button (back to input)
    this.editScriptBtn.addEventListener('click', () => {
      this.stopScriptPlayback();
      this.scriptPlayerScreen.style.display = 'none';
      this.scriptInputScreen.style.display = 'block';
    });

    // Player Controls
    this.playPauseScriptBtn.addEventListener('click', () => {
      this.toggleScriptPlayback();
    });

    this.nextSegmentBtn.addEventListener('click', () => {
      this.stepDialogue(1);
    });

    this.prevSegmentBtn.addEventListener('click', () => {
      this.stepDialogue(-1);
    });

    this.replaySegmentBtn.addEventListener('click', () => {
      this.playCurrentDialogue();
    });
  }

  async parseAndPrepareScript(rawText) {
    this.parseScriptBtn.disabled = true;
    this.parseScriptBtn.textContent = '⏳ 대본 분석 중...';

    try {
      const persona = this.scriptPersonaSelect.value;
      const res = await fetch('/api/script/parse', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          script_text: rawText,
          persona_id: persona
        })
      });

      if (!res.ok) throw new Error('대본 파싱 실패');
      const data = await res.json();

      this.scriptSegments = data.segments || [];
      this.dialogueIndices = [];
      this.scriptAudioCache = {};

      this.scriptSegments.forEach((seg, idx) => {
        if (seg.type === 'dialogue') {
          this.dialogueIndices.push(idx);
        }
      });

      if (this.dialogueIndices.length === 0) {
        alert('대본에서 큰따옴표(" ")로 묶인 대사를 찾을 수 없습니다!\n대사는 큰따옴표 안에 작성해 주세요.');
        return;
      }

      this.renderScriptViewer();
      this.currentDialoguePointer = 0;
      this.updatePlayerProgress();

      // Show Player Screen
      this.scriptInputScreen.style.display = 'none';
      this.scriptPlayerScreen.style.display = 'block';

      // Auto pre-fetch first dialogue
      this.prefetchDialogueAudio(this.dialogueIndices[0]);

    } catch (err) {
      alert('오류: ' + err.message);
    } finally {
      this.parseScriptBtn.disabled = false;
      this.parseScriptBtn.textContent = '▶️ 대본 분석 및 낭독 준비';
    }
  }

  renderScriptViewer() {
    this.scriptDisplayContainer.innerHTML = '';

    this.scriptSegments.forEach((seg, idx) => {
      const el = document.createElement('div');
      el.id = `script-seg-${idx}`;

      if (seg.type === 'narration') {
        el.className = 'script-item-narration';
        el.textContent = seg.text;
      } else {
        el.className = 'script-item-dialogue';
        
        const emotionLabels = {
          sensual: '💖 달아오름/신음',
          panting: '🥵 헐떡임/숨소리',
          flustered: '😳 부끄럼/당황',
          shy: '😳 부끄러움',
          whisper: '🤫 귓가 속삭임',
          terrified: '😱 공포에 질림',
          resigned: '🥀 낮고 느린 체념',
          crying: '😢 흐느낌/울먹임',
          smug: '😏 비웃음/조롱',
          tease: '✨ 장난/소악마',
          angry: '😡 분노/쏘아붙임',
          default: '💬 기본 대사'
        };

        const activeEmo = (this.actingEmotion && this.actingEmotion !== 'auto') 
          ? this.actingEmotion 
          : seg.inferred_emotion;

        const isForced = (this.actingEmotion && this.actingEmotion !== 'auto');
        const emotionTag = (isForced ? '⚡ ' : '') + (emotionLabels[activeEmo] || '💬 대사');
        const speakerNames = {
          shibuki: '시부키(학습)',
          shibuki_mesugaki: '시부키(메스가키)',
          shibuki_rimuru: '시부키(리무루)',
          mesugaki: '메스가키',
          mutsuki: '무츠키',
          sayaka: '사야카',
          ruri: '루리'
        };
        const speaker = speakerNames[seg.persona_id] || '시부키';

        el.innerHTML = `
          <div class="dialogue-meta-row">
            <span class="dialogue-speaker-name">${speaker}</span>
            <span class="dialogue-emotion-tag ${activeEmo}">${emotionTag}</span>
          </div>
          <div class="dialogue-spoken-text">"${seg.spoken_text}"</div>
        `;

        el.addEventListener('click', () => {
          const ptr = this.dialogueIndices.indexOf(idx);
          if (ptr !== -1) {
            this.currentDialoguePointer = ptr;
            this.playCurrentDialogue();
          }
        });
      }

      this.scriptDisplayContainer.appendChild(el);
    });
  }

  updatePlayerProgress() {
    const total = this.dialogueIndices.length;
    const current = this.currentDialoguePointer + 1;
    this.playerProgressBadge.textContent = `대사 ${current} / ${total}`;

    if (this.dialogueIndices.length > 0) {
      const curSegIdx = this.dialogueIndices[this.currentDialoguePointer];
      const curSeg = this.scriptSegments[curSegIdx];
      const emotionLabels = {
        sensual: '💖 달아오른 신음/앙탈 톤',
        panting: '🥵 가쁜 숨/헐떡임 톤',
        flustered: '😳 부끄러워하는 당황 톤',
        shy: '😳 부끄러워하는 톤',
        whisper: '🤫 귓가 속삭임/ASMR 톤',
        terrified: '😱 공포에 질린 비명 톤',
        resigned: '🥀 낮고 느린 체념 톤',
        crying: '😢 흐느끼는 울먹임 톤',
        smug: '😏 비웃는 조롱 톤',
        tease: '✨ 속삭이는 소악마 톤',
        angry: '😡 쏘아붙이는 도발 톤',
        default: '💬 기본 톤'
      };

      const activeEmo = (this.actingEmotion && this.actingEmotion !== 'auto') 
        ? this.actingEmotion 
        : curSeg.inferred_emotion;

      const isForced = (this.actingEmotion && this.actingEmotion !== 'auto');
      const prefix = isForced ? '⚡(강제) ' : '';
      this.playerEmotionBadge.textContent = prefix + (emotionLabels[activeEmo] || '🎭 연기 모드');
    }
  }

  async fetchSegmentAudio(segIdx) {
    const seg = this.scriptSegments[segIdx];
    if (!seg || seg.type !== 'dialogue') return null;

    if (this.scriptAudioCache[seg.id]) {
      return this.scriptAudioCache[seg.id];
    }

    const persona = this.scriptPersonaSelect.value;
    const engine = this.scriptEngineSelect.value;

    const res = await fetch('/api/script/tts_segment', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        dialogue: seg.spoken_text,
        persona_id: persona,
        inferred_emotion: seg.inferred_emotion,
        tts_engine: engine,
        context_narration: seg.context_narration,
        acting_emotion: this.actingEmotion
      })
    });

    if (res.ok) {
      const data = await res.json();
      this.scriptAudioCache[seg.id] = data.audio_base64;
      return data.audio_base64;
    }
    return null;
  }

  prefetchDialogueAudio(segIdx) {
    this.fetchSegmentAudio(segIdx).catch(() => {});
  }

  async playCurrentDialogue() {
    this.unlockAudio();
    if (this.currentDialoguePointer >= this.dialogueIndices.length) {
      this.stopScriptPlayback();
      return;
    }

    const segIdx = this.dialogueIndices[this.currentDialoguePointer];
    const seg = this.scriptSegments[segIdx];

    // Highlight current line
    document.querySelectorAll('.script-item-dialogue').forEach(el => el.classList.remove('active-playing'));
    const curEl = document.getElementById(`script-seg-${segIdx}`);
    if (curEl) {
      curEl.classList.add('active-playing');
      curEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    this.updatePlayerProgress();
    this.speakingState.textContent = `낭독 중: "${seg.spoken_text.slice(0, 16)}..."`;
    this.avatarOrb.classList.add('speaking');
    this.audioWaveBox.classList.add('active');

    // Trigger matching avatar face
    if (seg.inferred_emotion === 'smug') this.avatarFace.textContent = '😼';
    else if (seg.inferred_emotion === 'angry') this.avatarFace.textContent = '😒';
    else if (seg.inferred_emotion === 'tease') this.avatarFace.textContent = '😜';
    else this.avatarFace.textContent = '😏';

    const base64Audio = await this.fetchSegmentAudio(segIdx);
    if (!base64Audio) {
      console.warn('Could not load audio for segment', segIdx);
      if (this.isScriptPlaying) {
        setTimeout(() => this.stepDialogue(1), 1000);
      }
      return;
    }

    // Prefetch next segment in background
    if (this.currentDialoguePointer + 1 < this.dialogueIndices.length) {
      this.prefetchDialogueAudio(this.dialogueIndices[this.currentDialoguePointer + 1]);
    }

    try {
      const mime = base64Audio.startsWith('UklGR') ? 'audio/wav' : 'audio/mpeg';
      this.audioPlayer.src = `data:${mime};base64,${base64Audio}`;

      this.audioPlayer.onended = () => {
        if (this.isScriptPlaying) {
          setTimeout(() => this.stepDialogue(1), 600); // 600ms natural pause between sentences
        } else {
          this.avatarOrb.classList.remove('speaking');
          this.audioWaveBox.classList.remove('active');
          this.speakingState.textContent = '대기 중...';
        }
      };

      this.audioPlayer.onerror = (e) => {
        console.warn('Playback error:', e);
        if (this.isScriptPlaying) this.stepDialogue(1);
      };

      await this.audioPlayer.play();
    } catch (e) {
      console.warn('Play error:', e);
      if (this.isScriptPlaying) this.stepDialogue(1);
    }
  }

  toggleScriptPlayback() {
    this.unlockAudio();
    if (this.isScriptPlaying) {
      this.stopScriptPlayback();
    } else {
      this.isScriptPlaying = true;
      this.playIcon.textContent = '⏸️';
      this.playLabel.textContent = '일시 정지';
      this.playCurrentDialogue();
    }
  }

  stopScriptPlayback() {
    this.isScriptPlaying = false;
    this.playIcon.textContent = '▶️';
    this.playLabel.textContent = '낭독 시작';
    if (this.audioPlayer) {
      this.audioPlayer.pause();
    }
    this.avatarOrb.classList.remove('speaking');
    this.audioWaveBox.classList.remove('active');
    this.speakingState.textContent = '대기 중...';
  }

  stepDialogue(delta) {
    const nextPtr = this.currentDialoguePointer + delta;
    if (nextPtr >= 0 && nextPtr < this.dialogueIndices.length) {
      this.currentDialoguePointer = nextPtr;
      this.playCurrentDialogue();
    } else if (nextPtr >= this.dialogueIndices.length) {
      // Reached end of script
      this.stopScriptPlayback();
      this.currentDialoguePointer = 0;
      this.updatePlayerProgress();
      alert('🎉 대본 낭독이 완료되었습니다!');
    }
  }

  // ===================================================
  // CHAT & CORE LOGIC
  // ===================================================
  openSettings() {
    this.modalBackdrop.classList.add('show');
    this.settingsSheet.classList.add('show');
  }

  closeSettings() {
    this.modalBackdrop.classList.remove('show');
    this.settingsSheet.classList.remove('show');
  }

  updateTTSBadge() {
    const engine = this.ttsEngineSelect ? this.ttsEngineSelect.value : (this.ttsEngineSelectTop ? this.ttsEngineSelectTop.value : 'index_tts_2');
    
    // Sync topbar select and settings sheet select
    if (this.ttsEngineSelectTop && this.ttsEngineSelectTop.value !== engine) {
      this.ttsEngineSelectTop.value = engine;
    }
    if (this.ttsEngineSelect && this.ttsEngineSelect.value !== engine) {
      this.ttsEngineSelect.value = engine;
    }
    if (this.scriptEngineSelect && this.scriptEngineSelect.value !== engine) {
      this.scriptEngineSelect.value = engine;
    }

    if (!this.voiceEnabled) {
      this.currentEngineBadge.textContent = '🔇 MUTE';
      this.ttsStatusDetail.innerHTML = '현재 상태: <strong>음성 출력 꺼짐</strong>';
      return;
    }

    if (engine === 'index_tts_2' || engine === 'index_tts') {
      this.currentEngineBadge.textContent = '⚡ IndexTTS';
      this.ttsStatusDetail.innerHTML = '현재 상태: <strong>IndexTTS-2 제로샷 + 8D감정/길이제어 모드 (한국어 지원)</strong> (포트 9884)';
    } else if (engine === 'gpt_sovits') {
      this.currentEngineBadge.textContent = '🎙️ SoVITS';
      this.ttsStatusDetail.innerHTML = '현재 상태: <strong>GPT-SoVITS 3초 제로샷 모드</strong> (포트 9880)';
    } else if (engine === 'chatterbox') {
      this.currentEngineBadge.textContent = '🎭 Chatterbox';
      this.ttsStatusDetail.innerHTML = '현재 상태: <strong>Chatterbox 0.5B 감정/태그 제어 모드</strong> (포트 9882)';
    } else if (engine === 'auto') {
      this.currentEngineBadge.textContent = '⚡ AUTO';
      this.ttsStatusDetail.innerHTML = '현재 상태: <strong>스마트 자동 폴백 (IndexTTS ➔ SoVITS ➔ Edge)</strong>';
    } else {
      this.currentEngineBadge.textContent = '🔊 Edge';
      this.ttsStatusDetail.innerHTML = '현재 상태: <strong>Edge-TTS 초고속 모드</strong>';
    }
  }

  setActingEmotion(emotion) {
    this.actingEmotion = emotion || 'auto';
    this.scriptAudioCache = {}; // Invalidate cached audio for new emotion
    if (this.emotionSelectTop) {
      this.emotionSelectTop.value = this.actingEmotion;
      if (this.actingEmotion !== 'auto') {
        this.emotionSelectTop.style.borderColor = '#ff2d55';
        this.emotionSelectTop.style.boxShadow = '0 0 10px rgba(255, 45, 85, 0.4)';
      } else {
        this.emotionSelectTop.style.borderColor = '';
        this.emotionSelectTop.style.boxShadow = '';
      }
    }
    if (this.emotionSelectSheet) {
      this.emotionSelectSheet.value = this.actingEmotion;
    }
    if (this.scriptSegments && this.scriptSegments.length > 0) {
      this.renderScriptSegments();
      this.updatePlayerProgress();
    }
    this.saveSettings();
  }

  saveSettings() {
    try {
      const activeEngine = this.ttsEngineSelect ? this.ttsEngineSelect.value : (this.ttsEngineSelectTop ? this.ttsEngineSelectTop.value : 'index_tts_2');
      const settings = {
        persona: this.personaSelect ? this.personaSelect.value : 'shibuki',
        model: this.modelSelect ? this.modelSelect.value : 'gemini-3.6-flash',
        ttsEngine: activeEngine,
        voiceEnabled: this.voiceEnabled,
        actingEmotion: this.actingEmotion,
        scriptPersona: this.scriptPersonaSelect ? this.scriptPersonaSelect.value : 'shibuki',
        scriptTtsEngine: this.scriptEngineSelect ? this.scriptEngineSelect.value : activeEngine
      };
      localStorage.setItem('buki_user_settings', JSON.stringify(settings));
    } catch (e) {
      console.warn('Could not save settings to localStorage:', e);
    }
  }

  loadSavedSettings() {
    try {
      const raw = localStorage.getItem('buki_user_settings');
      if (!raw) return;
      const s = JSON.parse(raw);

      if (s.persona && this.personaSelect) {
        this.personaSelect.value = s.persona;
        this.personaGrid.querySelectorAll('.segment-btn').forEach(b => {
          b.classList.toggle('active', b.dataset.persona === s.persona);
        });
        this.updateTheme();
      }

      if (s.model && this.modelSelect) {
        // Check if option exists
        const opt = this.modelSelect.querySelector(`option[value="${s.model}"]`);
        if (opt) {
          this.modelSelect.value = s.model;
        }
      }

      if (s.ttsEngine) {
        if (this.ttsEngineSelect) this.ttsEngineSelect.value = s.ttsEngine;
        if (this.ttsEngineSelectTop) this.ttsEngineSelectTop.value = s.ttsEngine;
        if (this.scriptEngineSelect) this.scriptEngineSelect.value = s.ttsEngine;
        this.updateTTSBadge();
      }

      if (s.actingEmotion) {
        this.setActingEmotion(s.actingEmotion);
      }

      if (s.voiceEnabled !== undefined) {
        this.voiceEnabled = s.voiceEnabled;
        if (this.voiceEnabled) {
          this.quickVoiceBtn.classList.add('active');
          this.quickVoiceBtn.querySelector('.pill-icon').textContent = '🔊';
          this.voiceStatusText.textContent = '음성 ON';
        } else {
          this.quickVoiceBtn.classList.remove('active');
          this.quickVoiceBtn.querySelector('.pill-icon').textContent = '🔇';
          this.voiceStatusText.textContent = '음성 OFF';
        }
        this.updateTTSBadge();
      }

      if (s.scriptPersona && this.scriptPersonaSelect) {
        this.scriptPersonaSelect.value = s.scriptPersona;
      }

      if (s.scriptTtsEngine && this.scriptEngineSelect) {
        this.scriptEngineSelect.value = s.scriptTtsEngine;
      }
    } catch (e) {
      console.warn('Could not load saved settings:', e);
    }
  }

  async fetchModelsAndPersonas() {
    try {
      const res = await fetch('/api/info');
      if (res.ok) {
        const data = await res.json();
        const categorized = data.categorized_models || {};
        
        const friendlyNames = {
          // Google Gemini Official
          'gemini-3.6-flash': '✨ Google Gemini 3.6 Flash (⭐ 1순위 추천 - 초고속 플래시)',
          'gemini-3.7-flash': '🧠 Google Gemini 3.7 Flash (추론 강화 차세대 모델)',
          'gemini-flash-latest': '🌟 Google Gemini Flash Latest (최신 플래시)',
          'gemini-flash-lite-latest': '⚡ Google Gemini Flash Lite (초경량/초고속)',

          // OpenRouter Models
          'openrouter/free': '🚀 OpenRouter Free (⭐ 스마트 고가용성 무료 라우터 - 1순위 추천)',
          'minimax/minimax-m3:free': '⭐ MiniMax M3 (1M 초대용량 컨텍스트 무료)',
          'deepseek/deepseek-chat': '🧠 DeepSeek V3 (초고성능 범용 챗)',
          'nvidia/nemotron-3-super-120b-a12b:free': '⚡ NVIDIA Nemotron 120B (무료)',
          'nvidia/nemotron-3-ultra-550b-a55b:free': '👑 Nemotron 3 Ultra 550B (무료)',
          'liquid/lfm-2.5-2.6b:free': '💧 Liquid LFM 2.5 (초고속 추론 무료)',
          'thinkingmachines/inkling:free': '🧠 Thinking Machines Inkling (975B 무료)',
          'poolside/laguna-s-2.1:free': '💻 Poolside Laguna S 2.1 (코딩 118B)',
          'z-ai/glm-5.2:free': '⚡ Z.ai GLM 5.2 (256k 추론 무료)',
          
          // NVIDIA Direct Cloud
          'nvidia/nemotron-3-super-120b-a12b': '⚡ Nemotron 3 Super (120B 클라우드)',

          // Local GPU Ollama
          'huihui_ai/qwen2.5-coder-abliterate:14b': '💻 Qwen 2.5 14B 무검열 (로컬 추천)',
          'gemma4-uncensored:latest': '🌸 Gemma 4 12B 무검열 (로컬)',
          'gemma-mesugaki:latest': '😏 Gemma Mesugaki (로컬 전용)',
          'huihui_ai/qwen3.5-abliterated:9b': '⚡ Qwen 3.5 9B 무검열 (로컬 초고속)'
        };

        this.modelSelect.innerHTML = '';

        // 0. Google Gemini Group
        if (categorized.gemini_cloud && categorized.gemini_cloud.length > 0) {
          const grp = document.createElement('optgroup');
          grp.label = '✨ 구글 제미나이 무료 API (Google Gemini)';
          categorized.gemini_cloud.forEach(m => {
            const opt = document.createElement('option');
            opt.value = m;
            opt.textContent = friendlyNames[m] || m;
            grp.appendChild(opt);
          });
          this.modelSelect.appendChild(grp);
        }

        // 1. OpenRouter Group
        if (categorized.openrouter_free && categorized.openrouter_free.length > 0) {
          const grp = document.createElement('optgroup');
          grp.label = '🌐 오픈라우터 무료 AI (OpenRouter Free)';
          categorized.openrouter_free.forEach(m => {
            const opt = document.createElement('option');
            opt.value = m;
            opt.textContent = friendlyNames[m] || m;
            grp.appendChild(opt);
          });
          this.modelSelect.appendChild(grp);
        }

        // 2. NVIDIA Cloud Group
        if (categorized.nvidia_cloud && categorized.nvidia_cloud.length > 0) {
          const grp = document.createElement('optgroup');
          grp.label = '🚀 NVIDIA 클라우드 API (엔비디아)';
          categorized.nvidia_cloud.forEach(m => {
            const opt = document.createElement('option');
            opt.value = m;
            opt.textContent = friendlyNames[m] || m;
            grp.appendChild(opt);
          });
          this.modelSelect.appendChild(grp);
        }

        // 3. Local Ollama Group
        if (categorized.local_ollama && categorized.local_ollama.length > 0) {
          const grp = document.createElement('optgroup');
          grp.label = '💻 로컬 GPU 모델 (Ollama)';
          categorized.local_ollama.forEach(m => {
            const opt = document.createElement('option');
            opt.value = m;
            opt.textContent = friendlyNames[m] || m;
            grp.appendChild(opt);
          });
          this.modelSelect.appendChild(grp);
        }

        // 4. Populate Available TTS Engines dynamically
        if (data.available_tts_engines && data.available_tts_engines.length > 0) {
          const engines = data.available_tts_engines;
          if (this.ttsEngineSelect) {
            this.ttsEngineSelect.innerHTML = engines.map(e => `<option value="${e.id}">${e.name}</option>`).join('');
          }
          if (this.ttsEngineSelectTop) {
            const shortNames = {
              index_tts_2: '⚡ IndexTTS-2',
              gpt_sovits: '🎙️ SoVITS',
              chatterbox: '🎭 Chatterbox',
              auto: '⚡ AUTO',
              edge_tts: '🔊 Edge-TTS'
            };
            this.ttsEngineSelectTop.innerHTML = engines.map(e => `<option value="${e.id}">${shortNames[e.id] || e.id}</option>`).join('');
          }
          if (this.scriptEngineSelect) {
            this.scriptEngineSelect.innerHTML = engines.map(e => `<option value="${e.id}">${e.name}</option>`).join('');
          }
        }

        // Restore cached user settings
        this.loadSavedSettings();

        if (data.index_tts_online) {
          this.ttsStatusDetail.innerHTML = '현재 상태: 🟢 <strong>IndexTTS-2 온라인 연결됨</strong> (포트 9884)';
        } else if (data.gpt_sovits_online) {
          this.ttsStatusDetail.innerHTML = '현재 상태: 🟢 <strong>GPT-SoVITS 온라인 연결됨</strong> (포트 9880)';
        }
      }
    } catch (err) {
      console.warn('Could not fetch info:', err);
    }
  }

  updateTheme() {
    const persona = this.personaSelect.value;
    const color = this.personaColors[persona] || '#ff4d88';
    document.documentElement.style.setProperty('--accent-color', color);
    this.avatarGlow.style.background = color;
    
    const names = {
      shibuki: '시부키 (전용 학습 모델)',
      shibuki_mesugaki: '시부키 (메스가키 제로샷 - 하치쿠지)',
      shibuki_rimuru: '시부키 (발랄소녀 제로샷 - 리무루)',
      mesugaki: '메스가키',
      mutsuki: '무츠키',
      sayaka: '사야카',
      ruri: '루리'
    };
    this.badgeName.textContent = names[persona] || persona;
    this.avatarFace.textContent = (this.personaFaces[persona] || {}).idle || '😊';
  }

  formatContentHtml(rawText) {
    return rawText.replace(/(\([^\)]+\)|\[[^\]]+\]|\*[^\*]+\*)/g, '<span class="action-tag">$1</span>');
  }

  appendMessage(role, text, senderName) {
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${role === 'user' ? 'user-bubble' : 'assistant-bubble'}`;

    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    bubble.innerHTML = `
      <div class="bubble-header">
        <span class="sender-name">${senderName}</span>
        <span class="bubble-time">${now}</span>
      </div>
      <div class="bubble-content">${this.formatContentHtml(text)}</div>
      <div class="bubble-footer" style="display:none;">
        <button class="replay-btn">🔊 다시 듣기</button>
      </div>
    `;

    this.chatHistoryEl.appendChild(bubble);
    this.scrollToBottom();
    return {
      bubbleEl: bubble,
      contentEl: bubble.querySelector('.bubble-content'),
      footerEl: bubble.querySelector('.bubble-footer'),
      replayBtn: bubble.querySelector('.replay-btn')
    };
  }

  scrollToBottom() {
    this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
  }

  async sendMessage() {
    const message = this.messageInput.value.trim();
    if (!message) return;

    this.appendMessage('user', message, '나');
    this.messageInput.value = '';
    this.messageInput.style.height = 'auto';
    this.sendBtn.disabled = true;

    const personaId = this.personaSelect.value;
    const personaName = this.badgeName.textContent;
    const model = this.modelSelect.value;
    const ttsEngine = this.ttsEngineSelect.value;

    const msgObj = this.appendMessage('assistant', '', personaName);
    this.speakingState.textContent = '생각 중...';
    let accumulatedText = '';
    const messageAudios = [];

    this.stopAudioQueue();

    try {
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: message,
          persona_id: personaId,
          model: model,
          tts_engine: ttsEngine,
          history: this.history,
          voice_enabled: this.voiceEnabled,
          acting_emotion: this.actingEmotion
        })
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop();

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const jsonStr = line.replace('data: ', '').trim();
            if (!jsonStr) continue;

            try {
              const event = JSON.parse(jsonStr);
              if (event.type === 'token') {
                accumulatedText += event.token;
                msgObj.contentEl.innerHTML = this.formatContentHtml(accumulatedText);
                this.scrollToBottom();
              } else if (event.type === 'audio' && this.voiceEnabled) {
                messageAudios.push(event.audio_base64);
                this.enqueueAudio(event.audio_base64, event.spoken_text, event.actions, event.engine_used);
              } else if (event.type === 'action_cue') {
                this.triggerActionExpression(event.actions);
              } else if (event.type === 'done') {
                if (!this.isPlayingAudio) {
                  this.speakingState.textContent = '대기 중...';
                }
              }
            } catch (e) {
              console.error('SSE parse error:', e);
            }
          }
        }
      }

      if (messageAudios.length > 0) {
        msgObj.footerEl.style.display = 'block';
        msgObj.replayBtn.onclick = () => {
          this.unlockAudio();
          this.stopAudioQueue();
          messageAudios.forEach(b64 => this.audioQueue.push({ base64: b64, text: '다시 재생', actions: [], engine: 'replay' }));
          this.playNextAudio();
        };
      }

      this.history.push({ role: 'user', content: message });
      this.history.push({ role: 'assistant', content: accumulatedText });

    } catch (err) {
      msgObj.contentEl.textContent += `\n[오류: ${err.message}]`;
      this.speakingState.textContent = '대기 중...';
    } finally {
      this.sendBtn.disabled = false;
      if (!this.isPlayingAudio) {
        this.speakingState.textContent = '대기 중...';
      }
    }
  }

  triggerActionExpression(actions) {
    if (!actions || actions.length === 0) return;
    const actionText = actions.join(' ');
    const persona = this.personaSelect.value;
    const faces = this.personaFaces[persona] || {};

    if (actionText.includes('한숨') || actionText.includes('하품')) {
      this.avatarFace.textContent = faces.sigh || '😮‍💨';
    } else if (actionText.includes('비웃') || actionText.includes('피식') || actionText.includes('팔짱') || actionText.includes('허접')) {
      this.avatarFace.textContent = faces.smirk || '😼';
    } else if (actionText.includes('째려') || actionText.includes('인상')) {
      this.avatarFace.textContent = faces.glare || '😒';
    } else if (actionText.includes('웃')) {
      this.avatarFace.textContent = faces.laugh || '😆';
    }
    this.speakingState.textContent = `(${actions[0].slice(0, 14)})`;
  }

  enqueueAudio(base64Audio, spokenText, actions, engine) {
    this.audioQueue.push({ base64: base64Audio, text: spokenText, actions: actions, engine: engine });
    if (!this.isPlayingAudio) {
      this.playNextAudio();
    }
  }

  playNextAudio() {
    if (this.audioQueue.length === 0) {
      this.isPlayingAudio = false;
      this.avatarOrb.classList.remove('speaking');
      this.audioWaveBox.classList.remove('active');
      this.updateTheme();
      this.speakingState.textContent = '대기 중...';
      return;
    }

    this.isPlayingAudio = true;
    const item = this.audioQueue.shift();
    const persona = this.personaSelect.value;

    this.avatarOrb.classList.add('speaking');
    this.audioWaveBox.classList.add('active');
    this.avatarFace.textContent = (this.personaFaces[persona] || {}).speaking || '🗣️';
    this.speakingState.textContent = `"${(item.text || '').slice(0, 16)}..."`;

    if (item.actions && item.actions.length > 0) {
      this.triggerActionExpression(item.actions);
    }

    try {
      const mime = item.base64.startsWith('UklGR') ? 'audio/wav' : 'audio/mpeg';
      this.audioPlayer.src = `data:${mime};base64,${item.base64}`;

      this.audioPlayer.onended = () => {
        this.playNextAudio();
      };

      this.audioPlayer.onerror = (e) => {
        console.warn('[Audio Engine] Playback decode error:', e);
        this.playNextAudio();
      };

      const playPromise = this.audioPlayer.play();
      if (playPromise !== undefined) {
        playPromise.catch(e => {
          console.warn('[Audio Engine] Autoplay blocked:', e);
          this.speakingState.textContent = '🔊 터치하여 재생';
          this.playNextAudio();
        });
      }
    } catch (e) {
      console.warn('[Audio Engine] Creation error:', e);
      this.playNextAudio();
    }
  }

  stopAudioQueue() {
    if (this.audioPlayer) {
      this.audioPlayer.pause();
    }
    this.audioQueue = [];
    this.isPlayingAudio = false;
    this.avatarOrb.classList.remove('speaking');
    this.audioWaveBox.classList.remove('active');
    this.updateTheme();
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.buki = new BukiMobileClient();
});