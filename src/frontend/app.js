// Project BUKI - Enhanced Audio Engine & Client Orchestration
class BukiClient {
  constructor() {
    this.chatHistoryEl = document.getElementById('chatHistory');
    this.chatForm = document.getElementById('chatForm');
    this.messageInput = document.getElementById('messageInput');
    this.sendBtn = document.getElementById('sendBtn');
    this.personaSelect = document.getElementById('personaSelect');
    this.modelSelect = document.getElementById('modelSelect');
    this.voiceToggle = document.getElementById('voiceToggle');
    this.avatarOrb = document.getElementById('avatarOrb');
    this.avatarGlow = document.getElementById('avatarGlow');
    this.avatarFace = document.getElementById('avatarFace');
    this.badgeName = document.getElementById('badgeName');
    this.speakingState = document.getElementById('speakingState');

    this.history = [];
    this.audioQueue = [];
    this.isPlayingAudio = false;
    this.currentAudio = null;
    this.audioUnlocked = false;

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
  }

  // Unlock browser audio policy on first user interaction
  unlockAudio() {
    if (this.audioUnlocked) return;
    try {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      if (AudioContext) {
        const ctx = new AudioContext();
        ctx.resume().then(() => {
          this.audioUnlocked = true;
          console.log('[Audio] Browser audio context unlocked successfully.');
        });
      }
    } catch (e) {
      console.warn('[Audio] Could not unlock audio context:', e);
    }
  }

  setupEventListeners() {
    // Unlock audio on any click/touch
    document.addEventListener('click', () => this.unlockAudio(), { once: true });
    document.addEventListener('touchstart', () => this.unlockAudio(), { once: true });

    this.chatForm.addEventListener('submit', (e) => {
      e.preventDefault();
      this.unlockAudio();
      this.sendMessage();
    });

    this.messageInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.unlockAudio();
        this.sendMessage();
      }
    });

    this.personaSelect.addEventListener('change', () => {
      this.updateTheme();
    });
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
    this.badgeName.textContent = this.personaSelect.options[this.personaSelect.selectedIndex].text;
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
      <div class="bubble-footer" style="display:none; margin-top:8px;">
        <button class="replay-btn glass-btn" style="padding:2px 8px; font-size:0.75rem; border-radius:4px; cursor:pointer; background:rgba(255,255,255,0.1); border:1px solid rgba(255,255,255,0.2); color:#f0f6fc;">
          🔊 다시 듣기
        </button>
      </div>
    `;

    this.chatHistoryEl.appendChild(bubble);
    this.chatHistoryEl.scrollTop = this.chatHistoryEl.scrollHeight;
    return {
      bubbleEl: bubble,
      contentEl: bubble.querySelector('.bubble-content'),
      footerEl: bubble.querySelector('.bubble-footer'),
      replayBtn: bubble.querySelector('.replay-btn')
    };
  }

  async sendMessage() {
    const message = this.messageInput.value.trim();
    if (!message) return;

    this.appendMessage('user', message, '사용자');
    this.messageInput.value = '';
    this.sendBtn.disabled = true;

    const personaId = this.personaSelect.value;
    const personaName = this.personaSelect.options[this.personaSelect.selectedIndex].text;
    const model = this.modelSelect.value;
    const voiceEnabled = this.voiceToggle.checked;

    const msgObj = this.appendMessage('assistant', '', personaName);
    this.speakingState.textContent = '응답 생성 중...';
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
          history: this.history,
          voice_enabled: voiceEnabled
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
                this.chatHistoryEl.scrollTop = this.chatHistoryEl.scrollHeight;
              } else if (event.type === 'audio' && this.voiceToggle.checked) {
                messageAudios.push(event.audio_base64);
                this.enqueueAudio(event.audio_base64, event.spoken_text, event.actions);
              } else if (event.type === 'action_cue') {
                this.triggerActionExpression(event.actions);
              } else if (event.type === 'done') {
                if (!this.isPlayingAudio) {
                  this.speakingState.textContent = '대기 중';
                }
              }
            } catch (e) {
              console.error('SSE parse error:', e);
            }
          }
        }
      }

      // If audio chunks were generated, enable Replay button
      if (messageAudios.length > 0) {
        msgObj.footerEl.style.display = 'block';
        msgObj.replayBtn.onclick = () => {
          this.stopAudioQueue();
          messageAudios.forEach(b64 => this.audioQueue.push({ base64: b64, text: '다시 재생', actions: [] }));
          this.playNextAudio();
        };
      }

      this.history.push({ role: 'user', content: message });
      this.history.push({ role: 'assistant', content: accumulatedText });

    } catch (err) {
      msgObj.contentEl.textContent += `\n[오류 발생: ${err.message}]`;
      this.speakingState.textContent = '대기 중';
    } finally {
      this.sendBtn.disabled = false;
      if (!this.isPlayingAudio) {
        this.speakingState.textContent = '대기 중';
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
    this.speakingState.textContent = `(행동: ${actions[0].slice(0, 15)})`;
  }

  enqueueAudio(base64Audio, spokenText, actions) {
    this.audioQueue.push({ base64: base64Audio, text: spokenText, actions: actions });
    if (!this.isPlayingAudio) {
      this.playNextAudio();
    }
  }

  playNextAudio() {
    if (this.audioQueue.length === 0) {
      this.isPlayingAudio = false;
      this.avatarOrb.classList.remove('speaking');
      this.updateTheme();
      this.speakingState.textContent = '대기 중';
      return;
    }

    this.isPlayingAudio = true;
    const item = this.audioQueue.shift();
    const persona = this.personaSelect.value;

    this.avatarOrb.classList.add('speaking');
    this.avatarFace.textContent = (this.personaFaces[persona] || {}).speaking || '🗣️';
    this.speakingState.textContent = `말하는 중: "${(item.text || '').slice(0, 20)}..."`;

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
          console.warn('[Audio] Autoplay prevented by browser:', e);
          // Show unlock notification
          this.speakingState.textContent = '화면을 터치하면 음성이 재생됩니다 🔊';
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
    this.updateTheme();
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.buki = new BukiClient();
});