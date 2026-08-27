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
    this.quickVoiceBtn = document.getElementById('quickVoiceBtn');
    this.voiceStatusText = document.getElementById('voiceStatusText');
    this.openSettingsBtn = document.getElementById('openSettingsBtn');
    this.closeSettingsBtn = document.getElementById('closeSettingsBtn');
    this.modalBackdrop = document.getElementById('modalBackdrop');
    this.settingsSheet = document.getElementById('settingsSheet');
    this.personaGrid = document.getElementById('personaGrid');
    this.personaSelect = document.getElementById('personaSelect');
    this.modelSelect = document.getElementById('modelSelect');
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
    this.presetTsundere = document.getElementById('presetTsundere');

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
      mesugaki: '#ff4d88',
      mutsuki: '#ff2d55',
      sayaka: '#4da6ff',
      ruri: '#a855f7'
    };

    this.personaFaces = {
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
      });
    });

    // TTS Engine Select change
    this.ttsEngineSelect.addEventListener('change', () => this.updateTTSBadge());

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
        const res = await fetch('/api/tts', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            text: '오빠, 지금 내 목소리 잘 들려? 허접♡',
            persona_id: this.personaSelect.value,
            tts_engine: this.ttsEngineSelect.value
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

    if (this.presetTsundere) {
      this.presetTsundere.addEventListener('click', () => {
        this.scriptInputText.value = 
`(팔짱을 끼고 턱을 치켜들며 비웃는다.)
"어라~? 그 정도 문제도 혼자서 못 풀어서 끙끙대고 있었던 거야?"
피식 웃으며 머리를 콩 쥐어박았다.
"진짜 한심하네~ 오빠는 내가 없으면 아무것도 못 하는 게 분명해."
도발적인 눈빛으로 쳐다보며 말했다.
"뭐, 정 부탁하면 이 천재인 내가 조금은 도와줄 수도 있는데... 어때?"`;
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
          smug: '😏 비웃음/Smug',
          tease: '✨ 장난/Tease',
          angry: '😡 도발/Angry',
          shy: '😳 부끄러움/Shy',
          default: '💬 기본 대사'
        };

        const emotionTag = emotionLabels[seg.inferred_emotion] || '💬 대사';
        const speakerNames = { mesugaki: '메스가키', mutsuki: '무츠키', sayaka: '사야카', ruri: '루리' };
        const speaker = speakerNames[seg.persona_id] || '캐릭터';

        el.innerHTML = `
          <div class="dialogue-meta-row">
            <span class="dialogue-speaker-name">${speaker}</span>
            <span class="dialogue-emotion-tag">${emotionTag}</span>
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
        smug: '😏 비웃는 연기 톤',
        tease: '✨ 속삭이는 소악마 톤',
        angry: '😡 쏘아붙이는 도발 톤',
        shy: '😳 부끄러워하는 톤',
        default: '💬 기본 톤'
      };
      this.playerEmotionBadge.textContent = emotionLabels[curSeg.inferred_emotion] || '🎭 연기 모드';
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
        context_narration: seg.context_narration
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
    const engine = this.ttsEngineSelect.value;
    if (!this.voiceEnabled) {
      this.currentEngineBadge.textContent = '🔇 MUTE';
      this.ttsStatusDetail.innerHTML = '현재 상태: <strong>음성 출력 꺼짐</strong>';
      return;
    }

    if (engine === 'gpt_sovits') {
      this.currentEngineBadge.textContent = '🎙️ SoVITS';
      this.ttsStatusDetail.innerHTML = '현재 상태: <strong>GPT-SoVITS 모드</strong> (미구동 시 Edge 자동 폴백)';
    } else if (engine === 'auto') {
      this.currentEngineBadge.textContent = '⚡ AUTO';
      this.ttsStatusDetail.innerHTML = '현재 상태: <strong>자동 폴백 (SoVITS ➔ Edge)</strong>';
    } else {
      this.currentEngineBadge.textContent = '🔊 Edge';
      this.ttsStatusDetail.innerHTML = '현재 상태: <strong>Edge-TTS 초고속 모드</strong>';
    }
  }

  async fetchModelsAndPersonas() {
    try {
      const res = await fetch('/api/info');
      if (res.ok) {
        const data = await res.json();
        if (data.models && data.models.length > 0) {
          this.modelSelect.innerHTML = '';
          data.models.forEach(m => {
            const opt = document.createElement('option');
            opt.value = m;
            opt.textContent = m;
            if (m === 'gemma-mesugaki:latest' || m.includes('mesugaki')) {
              opt.selected = true;
            }
            this.modelSelect.appendChild(opt);
          });
        }
        if (data.gpt_sovits_online) {
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
    
    const names = { mesugaki: '메스가키', mutsuki: '무츠키', sayaka: '사야카', ruri: '루리' };
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
          voice_enabled: this.voiceEnabled
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