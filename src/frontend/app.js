// Project BUKI - Client Orchestration & Audio Queue Manager
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

    this.personaColors = {
      mesugaki: '#ff4d88',
      sayaka: '#4da6ff',
      ruri: '#a855f7'
    };

    this.personaFaces = {
      mesugaki: { idle: '😏', speaking: '😜' },
      sayaka: { idle: '✨', speaking: '😊' },
      ruri: { idle: '🧐', speaking: '🎙️' }
    };

    this.init();
  }

  async init() {
    this.setupEventListeners();
    await this.fetchModelsAndPersonas();
    this.updateTheme();
  }

  setupEventListeners() {
    // Form Submit
    this.chatForm.addEventListener('submit', (e) => {
      e.preventDefault();
      this.sendMessage();
    });

    // Auto-resize textarea & Enter key submit
    this.messageInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });

    // Persona change
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

  appendMessage(role, text, senderName) {
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${role === 'user' ? 'user-bubble' : 'assistant-bubble'}`;

    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    bubble.innerHTML = `
      <div class="bubble-header">
        <span class="sender-name">${senderName}</span>
        <span class="bubble-time">${now}</span>
      </div>
      <div class="bubble-content">${text}</div>
    `;

    this.chatHistoryEl.appendChild(bubble);
    this.chatHistoryEl.scrollTop = this.chatHistoryEl.scrollHeight;
    return bubble.querySelector('.bubble-content');
  }

  async sendMessage() {
    const message = this.messageInput.value.trim();
    if (!message) return;

    // Append User Message
    this.appendMessage('user', message, '사용자');
    this.messageInput.value = '';
    this.sendBtn.disabled = true;

    const personaId = this.personaSelect.value;
    const personaName = this.personaSelect.options[this.personaSelect.selectedIndex].text;
    const model = this.modelSelect.value;
    const voiceEnabled = this.voiceToggle.checked;

    // Prepare Assistant Bubble for streaming
    const contentEl = this.appendMessage('assistant', '', personaName);
    this.speakingState.textContent = '생각 중...';

    // Clear Audio Queue
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
        buffer = lines.pop(); // Keep incomplete chunk

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const jsonStr = line.replace('data: ', '').trim();
            if (!jsonStr) continue;

            try {
              const event = JSON.parse(jsonStr);
              this.handleServerEvent(event, contentEl);
            } catch (e) {
              console.error('SSE parse error:', e);
            }
          }
        }
      }

      // Record to history
      this.history.push({ role: 'user', content: message });
      this.history.push({ role: 'assistant', content: contentEl.textContent });

    } catch (err) {
      contentEl.textContent += `\n[오류 발생: ${err.message}]`;
      this.speakingState.textContent = '대기 중...';
    } finally {
      this.sendBtn.disabled = false;
    }
  }

  handleServerEvent(event, contentEl) {
    if (event.type === 'token') {
      contentEl.textContent += event.token;
      this.chatHistoryEl.scrollTop = this.chatHistoryEl.scrollHeight;
    } else if (event.type === 'audio' && this.voiceToggle.checked) {
      this.enqueueAudio(event.audio_base64, event.text);
    } else if (event.type === 'done') {
      if (!this.isPlayingAudio) {
        this.speakingState.textContent = '대기 중...';
      }
    }
  }

  enqueueAudio(base64Audio, sentenceText) {
    this.audioQueue.push({ base64: base64Audio, text: sentenceText });
    if (!this.isPlayingAudio) {
      this.playNextAudio();
    }
  }

  playNextAudio() {
    if (this.audioQueue.length === 0) {
      this.isPlayingAudio = false;
      this.avatarOrb.classList.remove('speaking');
      this.updateTheme();
      this.speakingState.textContent = '대기 중...';
      return;
    }

    this.isPlayingAudio = true;
    const item = this.audioQueue.shift();
    const persona = this.personaSelect.value;

    this.avatarOrb.classList.add('speaking');
    this.avatarFace.textContent = (this.personaFaces[persona] || {}).speaking || '🗣️';
    this.speakingState.textContent = `말하는 중: "${item.text.slice(0, 20)}..."`;

    const audioUrl = `data:audio/mp3;base64,${item.base64}`;
    this.currentAudio = new Audio(audioUrl);

    this.currentAudio.onended = () => {
      this.playNextAudio();
    };

    this.currentAudio.onerror = (e) => {
      console.warn('Audio play error:', e);
      this.playNextAudio();
    };

    this.currentAudio.play().catch(e => {
      console.warn('Autoplay blocked or error:', e);
      this.playNextAudio();
    });
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