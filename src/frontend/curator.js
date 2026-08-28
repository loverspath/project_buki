// Project BUKI - Voice Dataset Studio Frontend Logic
document.addEventListener('DOMContentLoaded', () => {
    let samples = [];
    let activeAudio = null;
    let activeCardId = null;
    let isTrimPreviewing = false;
    let trimPreviewEnd = 0;

    // Elements
    const sampleContainer = document.getElementById('sample-container');
    const statTotal = document.getElementById('stat-total');
    const statIncluded = document.getElementById('stat-included');
    const statDuration = document.getElementById('stat-duration');
    const searchInput = document.getElementById('search-input');
    const searchClear = document.getElementById('search-clear');
    const filterStatus = document.getElementById('filter-status');
    const filterEmotion = document.getElementById('filter-emotion');
    const sortOrder = document.getElementById('sort-order');
    const btnRefresh = document.getElementById('btn-refresh');
    const btnSaveAll = document.getElementById('btn-save-all');
    const btnSyncGdrive = document.getElementById('btn-sync-gdrive');
    const btnSelectAll = document.getElementById('btn-select-all');
    const btnDeselectAll = document.getElementById('btn-deselect-all');

    // Global Player Elements
    const globalPlayer = document.getElementById('global-player');
    const playerTitle = document.getElementById('player-title');
    const playerTime = document.getElementById('player-time');
    const playerPlayBtn = document.getElementById('player-play-btn');
    const playerSeek = document.getElementById('player-seek');
    const playerLoopBtn = document.getElementById('player-loop-btn');
    const playerCloseBtn = document.getElementById('player-close-btn');

    // Load Manifest on init
    loadManifest();

    // Event Listeners
    btnRefresh.addEventListener('click', () => loadManifest(true));
    btnSaveAll.addEventListener('click', saveAllChanges);
    btnSyncGdrive.addEventListener('click', syncToGoogleDrive);
    btnSelectAll.addEventListener('click', () => setAllInclusion(true));
    btnDeselectAll.addEventListener('click', () => setAllInclusion(false));

    searchInput.addEventListener('input', () => {
        searchClear.style.display = searchInput.value ? 'block' : 'none';
        renderSamples();
    });
    searchClear.addEventListener('click', () => {
        searchInput.value = '';
        searchClear.style.display = 'none';
        renderSamples();
    });

    filterStatus.addEventListener('change', renderSamples);
    filterEmotion.addEventListener('change', renderSamples);
    sortOrder.addEventListener('change', renderSamples);

    // Global keyboard shortcut: Ctrl+S to save
    window.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
            e.preventDefault();
            saveAllChanges();
        }
    });

    // --- API Interactions ---

    async function loadManifest(showToastOnSuccess = false) {
        try {
            const resp = await fetch('/api/curator/manifest');
            if (!resp.ok) throw new Error('데이터셋 매니페스트를 불러오지 못했습니다.');
            const data = await resp.json();
            samples = data.samples || [];
            updateStats();
            renderSamples();
            if (showToastOnSuccess) showToast('데이터셋 목록을 새로고침했습니다.', 'info');
        } catch (err) {
            showToast(err.message, 'error');
        }
    }

    async function saveAllChanges() {
        try {
            // Collect latest form state
            syncFormStateToMemory();
            const resp = await fetch('/api/curator/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ samples })
            });
            if (!resp.ok) throw new Error('전체 저장에 실패했습니다.');
            const res = await resp.json();
            showToast(res.message || '전체 변경사항이 성공적으로 저장되었습니다! (shibuki.list 갱신)', 'success');
            updateStats();
        } catch (err) {
            showToast(err.message, 'error');
        }
    }

    async function syncToGoogleDrive() {
        try {
            const resp = await fetch('/api/curator/sync_gdrive', { method: 'POST' });
            if (!resp.ok) throw new Error('G-Drive 동기화 시작 실패');
            showToast('Google Drive 백업을 백그라운드에서 시작했습니다. (rclone)', 'info');
        } catch (err) {
            showToast(err.message, 'error');
        }
    }

    // --- Rendering & Filtering ---

    function updateStats() {
        const total = samples.length;
        const included = samples.filter(s => s.is_included).length;
        const totalSec = samples.filter(s => s.is_included).reduce((acc, s) => acc + (s.duration || 0), 0);
        const mins = Math.floor(totalSec / 60);
        const secs = Math.floor(totalSec % 60);

        statTotal.textContent = ${total}개;
        statIncluded.textContent = ${included}개 활성;
        statDuration.textContent = ${mins}분 초;
    }

    function syncFormStateToMemory() {
        samples.forEach(s => {
            const card = document.getElementById(card-);
            if (card) {
                const chk = card.querySelector('.chk-include');
                const emo = card.querySelector('.emotion-select');
                const txt = card.querySelector('.transcript-textarea');
                const notes = card.querySelector('.notes-input');
                const tStart = card.querySelector('.trim-start-input');
                const tEnd = card.querySelector('.trim-end-input');

                if (chk) s.is_included = chk.checked;
                if (emo) s.emotion = emo.value;
                if (txt) s.transcript = txt.value.trim();
                if (notes) s.agent_notes = notes.value.trim();
                if (tStart) s.trim_start = parseFloat(tStart.value) || 0.0;
                if (tEnd) s.trim_end = parseFloat(tEnd.value) || s.duration;
            }
        });
    }

    function renderSamples() {
        syncFormStateToMemory();

        const query = searchInput.value.toLowerCase().trim();
        const statusVal = filterStatus.value;
        const emotionVal = filterEmotion.value;
        const sortVal = sortOrder.value;

        let filtered = samples.filter(s => {
            // Text search
            if (query) {
                const matchName = s.filename.toLowerCase().includes(query);
                const matchText = (s.transcript || '').toLowerCase().includes(query);
                const matchNotes = (s.agent_notes || '').toLowerCase().includes(query);
                if (!matchName && !matchText && !matchNotes) return false;
            }
            // Status filter
            if (statusVal === 'included' && !s.is_included) return false;
            if (statusVal === 'excluded' && s.is_included) return false;
            if (statusVal === 'has_notes' && !(s.agent_notes || '').trim()) return false;

            // Emotion filter
            if (emotionVal !== 'all' && s.emotion !== emotionVal) return false;

            return true;
        });

        // Sorting
        filtered.sort((a, b) => {
            if (sortVal === 'num_asc') return a.filename.localeCompare(b.filename, undefined, { numeric: true });
            if (sortVal === 'num_desc') return b.filename.localeCompare(a.filename, undefined, { numeric: true });
            if (sortVal === 'dur_asc') return a.duration - b.duration;
            if (sortVal === 'dur_desc') return b.duration - a.duration;
            return 0;
        });

        sampleContainer.innerHTML = '';
        if (filtered.length === 0) {
            sampleContainer.innerHTML = 
                <div class="loading-spinner">
                    <p>검색/필터 조건에 맞는 샘플이 없습니다.</p>
                </div>
            ;
            return;
        }

        filtered.forEach(s => {
            const card = createSampleCard(s);
            sampleContainer.appendChild(card);
        });
    }

    function createSampleCard(s) {
        const card = document.createElement('div');
        card.className = sample-card ;
        card.id = card-;

        const trimStart = (s.trim_start !== undefined) ? s.trim_start : 0.0;
        const trimEnd = (s.trim_end !== undefined) ? s.trim_end : s.duration;

        card.innerHTML = 
            <!-- Card Top Header -->
            <div class="card-header">
                <div class="card-header-left">
                    <label class="custom-checkbox" title="학습 데이터셋 포함 여부">
                        <input type="checkbox" class="chk-include" >
                        <span>포함</span>
                    </label>
                    <span class="file-badge"></span>
                    <span class="dur-badge" id="dur-label-">s</span>
                </div>
                <select class="emotion-select select-box" title="감정/문맥 톤 지정">
                    <option value="neutral" >평서문 / neutral</option>
                    <option value="question" >의문문 / question</option>
                    <option value="tease" >장난 / tease</option>
                    <option value="smug" >도도 / smug</option>
                    <option value="flustered" >당황 / flustered</option>
                    <option value="angry" >화남 / angry</option>
                </select>
            </div>

            <!-- Built-in Audio Player -->
            <div class="card-player">
                <button class="btn-play-card" id="btn-play-" title="재생 / 일시정지">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
                </button>
                <div class="player-progress-bar">
                    <div class="progress-track" id="track-">
                        <div class="progress-fill" id="fill-"></div>
                    </div>
                    <div class="time-labels">
                        <span id="time-cur-">0.0s</span>
                        <span id="time-dur-">s</span>
                    </div>
                </div>
            </div>

            <!-- 0.1s Lossless Precision Audio Trimming Toolset -->
            <div class="trim-toolbar">
                <div class="trim-controls-row">
                    <div class="trim-unit">
                        <span class="trim-label">앞 자르기</span>
                        <div class="trim-btn-group">
                            <button class="btn-trim-adj" data-target="start" data-delta="-0.1">-0.1s</button>
                            <input type="text" class="trim-input trim-start-input" id="trim-start-" value="">
                            <button class="btn-trim-adj" data-target="start" data-delta="+0.1">+0.1s</button>
                        </div>
                    </div>

                    <div class="trim-unit">
                        <span class="trim-label">뒤 자르기</span>
                        <div class="trim-btn-group">
                            <button class="btn-trim-adj" data-target="end" data-delta="-0.1">-0.1s</button>
                            <input type="text" class="trim-input trim-end-input" id="trim-end-" value="">
                            <button class="btn-trim-adj" data-target="end" data-delta="+0.1">+0.1s</button>
                        </div>
                    </div>

                    <div class="trim-actions">
                        <button class="btn-trim-preview" id="btn-preview-" title="자른 구간만 미리듣기">🎧 구간 미리듣기</button>
                        <button class="btn-trim-apply" id="btn-apply-trim-" title="오디오 파일 0.1초 단위 즉시 손실없이 컷팅">✂️ 자르기 적용</button>
                        <button class="btn-restore" id="btn-restore-" title="원본 백업으로 되돌리기">↺ 원본복구</button>
                    </div>
                </div>
            </div>

            <!-- Linked Transcript / Caption Editor -->
            <div class="card-transcript">
                <div class="transcript-header">
                    <span class="section-label">자막 / 캡션 텍스트 (BERT 프롬프트 매칭)</span>
                    <button class="btn-whisper" id="btn-whisper-">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z"/><path d="M19 10v2a7 7 0 01-14 0v-2M12 19v4M8 23h8"/></svg>
                        Whisper 재전사
                    </button>
                </div>
                <textarea class="transcript-textarea" placeholder="오디오와 100% 일치하는 한국어 자막을 입력하세요"></textarea>
            </div>

            <!-- Agent Instruction Notes -->
            <div class="card-notes">
                <span class="section-label">📝 AI 에이전트 지시사항 / 메모</span>
                <input type="text" class="notes-input" placeholder="에이전트에게 남길 코멘트 (예: 끝부분 숨소리 제거, 화난 억양)" value="">
            </div>
        ;

        // Bind Card Event Handlers
        bindCardEvents(card, s);
        return card;
    }

    function bindCardEvents(card, s) {
        const chk = card.querySelector('.chk-include');
        const playBtn = card.querySelector(#btn-play-);
        const track = card.querySelector(#track-);
        const previewBtn = card.querySelector(#btn-preview-);
        const applyTrimBtn = card.querySelector(#btn-apply-trim-);
        const restoreBtn = card.querySelector(#btn-restore-);
        const whisperBtn = card.querySelector(#btn-whisper-);
        const tStartInput = card.querySelector(#trim-start-);
        const tEndInput = card.querySelector(#trim-end-);

        // Inclusion Toggle
        chk.addEventListener('change', () => {
            s.is_included = chk.checked;
            card.classList.toggle('excluded', !chk.checked);
            updateStats();
        });

        // Play/Pause
        playBtn.addEventListener('click', () => togglePlayAudio(s, false));

        // Click track to seek
        track.addEventListener('click', (e) => {
            if (activeAudio && activeCardId === s.sample_id) {
                const rect = track.getBoundingClientRect();
                const pos = (e.clientX - rect.left) / rect.width;
                activeAudio.currentTime = pos * activeAudio.duration;
            } else {
                togglePlayAudio(s, false);
            }
        });

        // 0.1s Adjustment Buttons
        card.querySelectorAll('.btn-trim-adj').forEach(btn => {
            btn.addEventListener('click', () => {
                const target = btn.getAttribute('data-target');
                const delta = parseFloat(btn.getAttribute('data-delta'));
                if (target === 'start') {
                    let v = Math.max(0, Math.min(s.duration - 0.1, (parseFloat(tStartInput.value) || 0) + delta));
                    tStartInput.value = v.toFixed(2);
                    s.trim_start = v;
                } else {
                    let v = Math.max((parseFloat(tStartInput.value) || 0) + 0.1, Math.min(s.duration, (parseFloat(tEndInput.value) || s.duration) + delta));
                    tEndInput.value = v.toFixed(2);
                    s.trim_end = v;
                }
            });
        });

        // Preview Trim Slicing (Plays only start -> end)
        previewBtn.addEventListener('click', () => {
            const startSec = parseFloat(tStartInput.value) || 0.0;
            const endSec = parseFloat(tEndInput.value) || s.duration;
            playAudioSlice(s, startSec, endSec);
        });

        // Apply Lossless Trim (Overwrite)
        applyTrimBtn.addEventListener('click', async () => {
            const startSec = parseFloat(tStartInput.value) || 0.0;
            const endSec = parseFloat(tEndInput.value) || s.duration;
            if (startSec <= 0.0 && endSec >= s.duration) {
                showToast('트리밍할 구간(앞/뒤)을 0.1초 이상 조정해 주세요.', 'info');
                return;
            }
            try {
                applyTrimBtn.disabled = true;
                applyTrimBtn.textContent = '자르는 중...';
                const resp = await fetch('/api/curator/trim', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        filename: s.filename,
                        trim_start: startSec,
                        trim_end: endSec
                    })
                });
                if (!resp.ok) throw new Error('오디오 자르기에 실패했습니다.');
                const res = await resp.json();
                
                s.duration = res.new_duration;
                s.trim_start = 0.0;
                s.trim_end = res.new_duration;

                tStartInput.value = '0.00';
                tEndInput.value = res.new_duration.toFixed(2);
                card.querySelector(#dur-label-).textContent = ${res.new_duration.toFixed(2)}s;
                card.querySelector(#time-dur-).textContent = ${res.new_duration.toFixed(2)}s;
                
                // Bust audio cache
                if (activeCardId === s.sample_id && activeAudio) {
                    activeAudio.pause();
                    activeAudio = null;
                }

                showToast([] 초로 손실없이 자르기 완료!, 'success');
                updateStats();
            } catch (err) {
                showToast(err.message, 'error');
            } finally {
                applyTrimBtn.disabled = false;
                applyTrimBtn.textContent = '✂️ 자르기 적용';
            }
        });

        // Restore Original Backup
        restoreBtn.addEventListener('click', async () => {
            if (!confirm([] 원본 파일로 복구하시겠습니까?)) return;
            try {
                const resp = await fetch('/api/curator/restore_original', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ filename: s.filename })
                });
                if (!resp.ok) throw new Error('원본 복구에 실패했습니다.');
                const res = await resp.json();
                s.duration = res.duration;
                s.trim_start = 0.0;
                s.trim_end = res.duration;

                tStartInput.value = '0.00';
                tEndInput.value = res.duration.toFixed(2);
                card.querySelector(#dur-label-).textContent = ${res.duration.toFixed(2)}s;
                card.querySelector(#time-dur-).textContent = ${res.duration.toFixed(2)}s;
                showToast([] 원본 복구 완료! (초), 'success');
                updateStats();
            } catch (err) {
                showToast(err.message, 'error');
            }
        });

        // Whisper AI Re-transcribe
        whisperBtn.addEventListener('click', async () => {
            try {
                whisperBtn.disabled = true;
                whisperBtn.innerHTML = '전사 중...';
                const resp = await fetch('/api/curator/transcribe', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ filename: s.filename })
                });
                if (!resp.ok) throw new Error('Whisper 전사 실패');
                const res = await resp.json();
                if (res.transcript) {
                    s.transcript = res.transcript;
                    card.querySelector('.transcript-textarea').value = res.transcript;
                    showToast([] Whisper 전사 완료!, 'success');
                } else {
                    showToast('전사 결과가 비어 있습니다.', 'info');
                }
            } catch (err) {
                showToast(err.message, 'error');
            } finally {
                whisperBtn.disabled = false;
                whisperBtn.innerHTML = 
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z"/><path d="M19 10v2a7 7 0 01-14 0v-2M12 19v4M8 23h8"/></svg>
                    Whisper 재전사
                ;
            }
        });
    }

    // --- Audio Playback Engine ---

    function togglePlayAudio(s, isSlice = false) {
        const playBtn = document.getElementById(tn-play-);

        if (activeAudio && activeCardId === s.sample_id) {
            if (activeAudio.paused) {
                activeAudio.play();
                updatePlayBtnIcon(playBtn, true);
            } else {
                activeAudio.pause();
                updatePlayBtnIcon(playBtn, false);
            }
            return;
        }

        // Stop current audio if playing
        if (activeAudio) {
            activeAudio.pause();
            resetCardPlayState(activeCardId);
        }

        // Create new audio instance
        const audioUrl = /api/curator/audio/?t=;
        activeAudio = new Audio(audioUrl);
        activeCardId = s.sample_id;
        isTrimPreviewing = false;

        // Show global floating player
        showGlobalPlayer(s);

        activeAudio.addEventListener('timeupdate', () => {
            if (!activeAudio) return;
            const cur = activeAudio.currentTime;
            const dur = activeAudio.duration || s.duration;

            // Update card progress
            const fill = document.getElementById(ill-);
            const timeCur = document.getElementById(	ime-cur-);
            if (fill) fill.style.width = ${(cur / dur) * 100}%;
            if (timeCur) timeCur.textContent = ${cur.toFixed(1)}s;

            // Update global player
            if (playerTime) playerTime.textContent = ${cur.toFixed(1)}s / s;
            if (playerSeek) playerSeek.value = (cur / dur) * 100;

            // If slice previewing, auto pause at end
            if (isTrimPreviewing && cur >= trimPreviewEnd) {
                activeAudio.pause();
                isTrimPreviewing = false;
                updatePlayBtnIcon(playBtn, false);
            }
        });

        activeAudio.addEventListener('ended', () => {
            resetCardPlayState(s.sample_id);
            if (playerPlayBtn) playerPlayBtn.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>';
        });

        activeAudio.play().then(() => {
            updatePlayBtnIcon(playBtn, true);
        }).catch(err => {
            console.error('Audio play error:', err);
        });
    }

    function playAudioSlice(s, startSec, endSec) {
        togglePlayAudio(s, true);
        if (activeAudio) {
            activeAudio.currentTime = startSec;
            isTrimPreviewing = true;
            trimPreviewEnd = endSec;
            activeAudio.play();
            const playBtn = document.getElementById(tn-play-);
            updatePlayBtnIcon(playBtn, true);
            showToast(구간 미리듣기: s ~ s, 'info');
        }
    }

    function updatePlayBtnIcon(btn, isPlaying) {
        if (!btn) return;
        btn.innerHTML = isPlaying ? 
            '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>' :
            '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>';
        if (playerPlayBtn) {
            playerPlayBtn.innerHTML = isPlaying ? 
                '<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>' :
                '<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>';
        }
    }

    function resetCardPlayState(cardId) {
        if (!cardId) return;
        const playBtn = document.getElementById(tn-play-);
        const fill = document.getElementById(ill-);
        const timeCur = document.getElementById(	ime-cur-);
        updatePlayBtnIcon(playBtn, false);
        if (fill) fill.style.width = '0%';
        if (timeCur) timeCur.textContent = '0.0s';
    }

    function showGlobalPlayer(s) {
        globalPlayer.style.display = 'flex';
        playerTitle.textContent = s.filename;
        playerSeek.value = 0;
    }

    playerPlayBtn.addEventListener('click', () => {
        if (activeAudio) {
            if (activeAudio.paused) activeAudio.play();
            else activeAudio.pause();
            const playBtn = document.getElementById(tn-play-);
            updatePlayBtnIcon(playBtn, !activeAudio.paused);
        }
    });

    playerSeek.addEventListener('input', () => {
        if (activeAudio && activeAudio.duration) {
            activeAudio.currentTime = (playerSeek.value / 100) * activeAudio.duration;
        }
    });

    playerCloseBtn.addEventListener('click', () => {
        if (activeAudio) {
            activeAudio.pause();
            resetCardPlayState(activeCardId);
            activeAudio = null;
        }
        globalPlayer.style.display = 'none';
    });

    function setAllInclusion(val) {
        samples.forEach(s => s.is_included = val);
        document.querySelectorAll('.chk-include').forEach(c => c.checked = val);
        document.querySelectorAll('.sample-card').forEach(c => c.classList.toggle('excluded', !val));
        updateStats();
        showToast(val ? '전체 샘플을 포함 상태로 변경했습니다.' : '전체 샘플을 제외 상태로 변경했습니다.', 'info');
    }

    // --- Toast Notifications ---

    function showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = 	oast ;
        
        let icon = 'ℹ️';
        if (type === 'success') icon = '✅';
        else if (type === 'error') icon = '⚠️';

        toast.innerHTML = <span></span> <span></span>;
        container.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3500);
    }
});
