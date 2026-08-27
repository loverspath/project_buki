// Project BUKI - Mobile-First AI Messenger & Voice Orchestration Client
class BukiMobileClient {
  constructor() {
    // Elements
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

    // State
    this.history = [];
    this.audioQueue = [];
    this.isPlayingAudio = false;
    this.currentAudio = null;
    this.audioUnlocked = false;
    this.voiceEnabled = true;

    this.personaColors = {
      mesugaki: '#ff4d88',
      sayaka: '#4da6ff',
      ruri: '#a855f7'
    };

    this.personaFaces = {
      mesugaki: { idle: '😏', speaking: '😜', smirk: '😼', sigh: '😮‍💨', glare: '😒' },
      sayaka: { idle: '✨', speaking: '😊', laugh: '😆', think: '🤔' },
      ruri: { idle: '🧐', speaking: '🎙️', analyze: '📊', calm: '😌' }
    };

    this.init();
  }

  async init() {
    this.setupEventListeners();
    await this.fetchModelsAndPersonas();
    this.updateTheme();
    this.updateTTSBadge();
  }

  unlockAudio() {
    if (this.audioUnlocked) return;
    try {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      if (AudioContext) {
        const ctx = new AudioContext();
        ctx.resume().then(() => {
          this.audioUnlocked = true;
          console.log('[Audio] Mobile AudioContext unlocked.');
        });
      }
    } catch (e) {
      console.warn('[Audio] AudioContext unlock error:', e);
    }
  }

  setupEventListeners() {
    // Unlock WebAudio on any first tap
    document.addEventListener('click', () => this.unlockAudio(), { once: true });
    document.addEventListener('touchstart', () => this.unlockAudio(), { once: true });

    // Chat submit
    this.chatForm.addEventListener('submit', (e) => {
      e.preventDefault();
      this.unlockAudio();
      this.sendMessage();
    });

    // Auto-resize textarea on input
    this.messageInput.addEventListener('input', () => {
      this.messageInput.style.height = 'auto';
      this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 100) + 'px';
    });

    this.messageInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.unlockAudio();
        this.sendMessage();
      }
    });

    // Quick Voice Toggle
    this.quickVoiceBtn.addEventListener('click', () => {
      this.voiceEnabled = !this.voiceEnabled;
      if (this.voiceEnabled) {
        this.quickVoiceBtn.classList.add('active');
        this.quickVoiceBtn.querySelector('.pill-icon').textContent = '🔊';
        this.voiceStatusText.textContent = '음성 ON';
      } else {
        this.quickVoiceBtn.classList.remove('active');
        this.quickVoiceBtn.querySelector('.pill-icon').textContent = '🔇';
        this.voiceStatusText.textContent = '음성 OFF';
        this.stopAudioQueue();
      }
      this.updateTTSBadge();
    });

    // Settings Bottom Sheet Modal
    this.openSettingsBtn.addEventListener('click', () => this.openSettings());
    this.closeSettingsBtn.addEventListener('click', () => this.closeSettings());
    this.modalBackdrop.addEventListener('click', () => this.closeSettings());

    // Segmented Persona Buttons
    this.personaGrid.querySelectorAll('.segment-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        this.personaGrid.querySelectorAll('.segment-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const p = btn.getAttribute('data-persona');
        this.personaSelect.value = p;
        this.updateTheme();
      });
    });

    // Quick Prompt Chips
    document.querySelectorAll('.chip-btn').forEach(chip => {
      chip.addEventListener('click', () => {
        const txt = chip.getAttribute('data-text');
        this.messageInput.value = txt;
        this.unlockAudio();
        this.sendMessage();
      });
    });

    // TTS Engine Select in Settings
    this.ttsEngineSelect.addEventListener('change', () => {
      this.updateTTSBadge();
    });

    // Test Voice Button in Settings
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
        }
      } catch (err) {
        alert('TTS 테스트 실패: ' + err.message);
      } finally {
        this.testVoiceBtn.disabled = false;
        this.testVoiceBtn.textContent = '🔊 목소리 테스트 재생';
      }
    });
  }

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
      this.ttsStatusDetail.innerHTML = '현재 상태: <strong>GPT-SoVITS 3초 제로샷 모드</strong>';
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
    
    const names = { mesugaki: '메스가키', sayaka: '사야카', ruri: '루리' };
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
      const audioUrl = `data:audio/mp3;base64,${item.base64}`;
      this.currentAudio = new Audio(audioUrl);

      this.currentAudio.onended = () => {
        this.playNextAudio();
      };

      this.currentAudio.onerror = (e) => {
        console.warn('[Audio] playback error:', e);
        this.playNextAudio();
      };

      const playPromise = this.currentAudio.play();
      if (playPromise !== undefined) {
        playPromise.catch(e => {
          console.warn('[Audio] Autoplay prevented by mobile browser:', e);
          this.speakingState.textContent = '화면을 터치하면 음성 재생 🔊';
          this.playNextAudio();
        });
      }
    } catch (e) {
      console.warn('[Audio] Creation error:', e);
      this.playNextAudio();
    }
  }

  stopAudioQueue() {
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio = null;
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