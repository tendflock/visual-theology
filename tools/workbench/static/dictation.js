/**
 * dictation.js — Hybrid voice-to-text for /study.
 *
 * Live phase: Web Speech API streams interim text into the textarea as you
 * speak (free, low-latency, quality mediocre on theological vocabulary).
 * Final phase: MediaRecorder audio is POSTed to /study/session/<id>/transcribe
 * where local Whisper produces an accurate transcript, which replaces the
 * live-preview text in the textarea.
 *
 * Every Dictation instance tracks a [previewStart, previewStart + previewLen)
 * range in its target element. Interim Web Speech results rewrite that range;
 * Whisper's final text rewrites it one last time when recording stops.
 */

'use strict';

(function () {
    var STORAGE_KEY = 'logos4.dictation.deviceId';

    function hasRecorderSupport() {
        return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia && window.MediaRecorder);
    }

    function getSpeechRecognitionCtor() {
        return window.SpeechRecognition || window.webkitSpeechRecognition || null;
    }

    function pickMimeType() {
        var candidates = ['audio/mp4', 'audio/webm;codecs=opus', 'audio/webm', 'audio/ogg'];
        for (var i = 0; i < candidates.length; i++) {
            if (MediaRecorder.isTypeSupported(candidates[i])) return candidates[i];
        }
        return '';
    }

    function getAudioConstraints(deviceId) {
        if (!deviceId) return { audio: true };
        return { audio: { deviceId: deviceId } };
    }

    function shouldRetryWithDefaultMic(err) {
        if (!err) return false;
        var name = err.name || '';
        var message = err.message || '';
        return name === 'OverconstrainedError' ||
            name === 'ConstraintNotSatisfiedError' ||
            name === 'TypeError' ||
            /invalid constraint/i.test(message);
    }

    function setState(wrap, state, label) {
        wrap.classList.remove('state-idle', 'state-starting', 'state-recording', 'state-processing', 'state-error');
        wrap.classList.add('state-' + state);
        var statusEl = wrap.querySelector('.mic-status');
        var readout = wrap.querySelector('.mic-readout');
        var readoutStatus = wrap.querySelector('.mic-readout-status');
        var text = '';
        if (label) text = label;
        else if (state === 'starting') text = 'Starting...';
        else if (state === 'recording') text = 'Recording';
        else if (state === 'processing') text = 'Transcribing';
        else if (state === 'error') text = 'Error';
        if (statusEl) statusEl.textContent = text;
        if (readoutStatus) readoutStatus.textContent = text || 'Idle';
        if (readout) readout.hidden = state === 'idle';
    }

    function setLevel(wrap, ratio) {
        var pct = Math.max(2, Math.min(100, Math.round((ratio || 0) * 100)));
        var bars = wrap.querySelectorAll('.mic-level span, .mic-readout-meter span');
        bars.forEach(function (bar) {
            bar.style.width = pct + '%';
        });
    }

    function clearChildren(node) {
        while (node.firstChild) node.removeChild(node.firstChild);
    }

    function populatePicker(wrap) {
        var select = wrap.querySelector('.mic-picker-select');
        if (!select) return Promise.resolve();
        return navigator.mediaDevices.enumerateDevices().then(function (devices) {
            var stored = localStorage.getItem(STORAGE_KEY) || '';
            clearChildren(select);
            var audioInputs = devices.filter(function (d) { return d.kind === 'audioinput'; });
            if (!audioInputs.length) {
                var empty = document.createElement('option');
                empty.value = '';
                empty.textContent = 'No microphone found';
                select.appendChild(empty);
                return;
            }
            var sysOpt = document.createElement('option');
            sysOpt.value = '';
            sysOpt.textContent = 'System default';
            select.appendChild(sysOpt);
            audioInputs.forEach(function (d, i) {
                var opt = document.createElement('option');
                opt.value = d.deviceId;
                opt.textContent = d.label || ('Microphone ' + (i + 1));
                select.appendChild(opt);
            });
            select.value = stored;
        });
    }

    function bindPicker(wrap) {
        var toggle = wrap.querySelector('.mic-picker-toggle');
        var picker = wrap.querySelector('.mic-picker');
        var select = wrap.querySelector('.mic-picker-select');
        if (!toggle || !picker || !select) return;

        function openPicker() {
            populatePicker(wrap);
            picker.hidden = false;
            toggle.setAttribute('aria-expanded', 'true');
            wrap.classList.add('picker-open');
        }
        function closePicker() {
            picker.hidden = true;
            toggle.setAttribute('aria-expanded', 'false');
            wrap.classList.remove('picker-open');
        }

        toggle.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();
            if (picker.hidden) openPicker();
            else closePicker();
        });

        // Selecting a mic commits the choice and dismisses the dropdown.
        select.addEventListener('change', function () {
            localStorage.setItem(STORAGE_KEY, select.value);
            closePicker();
        });

        // Clicks inside the picker (select, label) must not bubble to the
        // document-level close handler registered below.
        picker.addEventListener('click', function (e) { e.stopPropagation(); });

        document.addEventListener('click', function (e) {
            if (!wrap.contains(e.target)) closePicker();
        });
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && !picker.hidden) closePicker();
        });
    }

    function Dictation(wrap) {
        this.wrap = wrap;
        this.btn = wrap.querySelector('.mic-button');
        this.targetSelector = wrap.getAttribute('data-target');
        this.sessionId = wrap.getAttribute('data-session-id');
        this.recorder = null;
        this.stream = null;
        this.chunks = [];
        this.recording = false;
        this.recognition = null;
        this.previewStart = null;
        this.previewLen = 0;
        this.processing = false;
        this.audioContext = null;
        this.analyser = null;
        this.levelData = null;
        this.levelRaf = null;

        var self = this;
        this.btn.addEventListener('click', function () { self.toggle(); });
        bindPicker(wrap);
        setState(wrap, 'idle');
    }

    Dictation.prototype.getTarget = function () {
        return document.querySelector(this.targetSelector);
    };

    Dictation.prototype.toggle = function () {
        if (!hasRecorderSupport()) {
            setState(this.wrap, 'error');
            alert('Dictation is not supported in this browser.');
            return;
        }
        if (this.processing) return;
        if (this.recording) this.stop();
        else this.start();
    };

    /**
     * Replace the tracked preview range [previewStart, previewStart + previewLen)
     * with `text`. Inserts a single leading space when joining to adjacent words
     * so dictation doesn't produce "helloworld". Dispatches an `input` event so
     * existing auto-save listeners fire.
     */
    Dictation.prototype.writePreview = function (text) {
        var target = this.getTarget();
        if (!target || this.previewStart == null) return;
        text = text || '';
        var val = target.value;
        var before = val.slice(0, this.previewStart);
        var after = val.slice(this.previewStart + this.previewLen);
        var needsSpace = text && before.length > 0 && !/\s$/.test(before) && !/^\s/.test(text);
        var injected = (needsSpace ? ' ' : '') + text;
        target.value = before + injected + after;
        this.previewLen = injected.length;
        var pos = this.previewStart + this.previewLen;
        try { target.setSelectionRange(pos, pos); } catch (e) { /* non-text inputs */ }
        target.dispatchEvent(new Event('input', { bubbles: true }));
    };

    Dictation.prototype.startLivePreview = function () {
        var SR = getSpeechRecognitionCtor();
        if (!SR) {
            setState(this.wrap, 'recording', 'Recording - stop for transcript');
            return false;
        }
        var target = this.getTarget();
        if (!target) return false;

        var start = (typeof target.selectionStart === 'number') ? target.selectionStart : target.value.length;
        this.previewStart = start;
        this.previewLen = 0;

        var self = this;
        var rec = new SR();
        rec.continuous = true;
        rec.interimResults = true;
        rec.lang = 'en-US';

        rec.onresult = function (e) {
            var text = '';
            for (var i = 0; i < e.results.length; i++) {
                text += e.results[i][0].transcript;
            }
            setState(self.wrap, 'recording', 'Live text ready');
            self.writePreview(text);
        };

        rec.onerror = function (e) {
            // Don't alert — live preview is best-effort. Whisper still runs on the audio.
            console.warn('dictation: SpeechRecognition error', e.error);
            if (self.recording) setState(self.wrap, 'recording', 'Recording - stop for transcript');
        };

        rec.onend = function () {
            // Safari tends to cut off on pauses; reopen if we're still recording.
            if (self.recording && self.recognition === rec) {
                try { rec.start(); } catch (err) { /* already started / stopped */ }
            }
        };

        try {
            rec.start();
            this.recognition = rec;
            setState(this.wrap, 'recording', 'Live text ready');
            return true;
        } catch (err) {
            console.warn('dictation: SpeechRecognition.start failed', err);
            this.recognition = null;
            setState(this.wrap, 'recording', 'Recording - stop for transcript');
            return false;
        }
    };

    Dictation.prototype.stopLivePreview = function () {
        if (!this.recognition) return;
        try {
            this.recognition.onend = null;
            this.recognition.stop();
        } catch (e) { /* ignore */ }
        this.recognition = null;
    };

    Dictation.prototype.startLevelMeter = function (stream) {
        this.stopLevelMeter();
        var AC = window.AudioContext || window.webkitAudioContext;
        if (!AC) {
            setLevel(this.wrap, 0);
            return;
        }

        try {
            var ctx = new AC();
            var analyser = ctx.createAnalyser();
            analyser.fftSize = 256;
            ctx.createMediaStreamSource(stream).connect(analyser);
            this.audioContext = ctx;
            this.analyser = analyser;
            this.levelData = new Uint8Array(analyser.frequencyBinCount);
            if (ctx.state === 'suspended' && ctx.resume) ctx.resume();
            this.tickLevelMeter();
        } catch (err) {
            console.warn('dictation: audio level meter failed', err);
            setLevel(this.wrap, 0);
        }
    };

    Dictation.prototype.tickLevelMeter = function () {
        if (!this.analyser || !this.levelData) return;
        this.analyser.getByteTimeDomainData(this.levelData);
        var sum = 0;
        for (var i = 0; i < this.levelData.length; i++) {
            var centered = this.levelData[i] - 128;
            sum += centered * centered;
        }
        var rms = Math.sqrt(sum / this.levelData.length) / 128;
        setLevel(this.wrap, Math.min(1, rms * 8));

        var self = this;
        this.levelRaf = window.requestAnimationFrame(function () {
            self.tickLevelMeter();
        });
    };

    Dictation.prototype.stopLevelMeter = function () {
        if (this.levelRaf) {
            window.cancelAnimationFrame(this.levelRaf);
            this.levelRaf = null;
        }
        if (this.audioContext) {
            try { this.audioContext.close(); } catch (e) { /* ignore */ }
        }
        this.audioContext = null;
        this.analyser = null;
        this.levelData = null;
        setLevel(this.wrap, 0);
    };

    Dictation.prototype.start = function () {
        var self = this;
        var deviceId = localStorage.getItem(STORAGE_KEY) || '';
        setState(this.wrap, 'starting', 'Starting...');
        setLevel(this.wrap, 0);

        // Seed the preview range from the current cursor position even if Web
        // Speech is unavailable — Whisper's writePreview() call still needs it.
        var tgt = this.getTarget();
        this.previewStart = tgt ? ((typeof tgt.selectionStart === 'number') ? tgt.selectionStart : tgt.value.length) : 0;
        this.previewLen = 0;

        function openMic(constraints) {
            return navigator.mediaDevices.getUserMedia(constraints);
        }

        openMic(getAudioConstraints(deviceId)).catch(function (err) {
            if (!deviceId || !shouldRetryWithDefaultMic(err)) throw err;
            console.warn('dictation: selected microphone failed, retrying with system default', err);
            localStorage.removeItem(STORAGE_KEY);
            return openMic(getAudioConstraints(''));
        }).then(function (stream) {
            populatePicker(self.wrap);

            var mime = pickMimeType();
            self.stream = stream;
            self.chunks = [];
            self.recorder = mime ? new MediaRecorder(stream, { mimeType: mime }) : new MediaRecorder(stream);

            self.recorder.ondataavailable = function (e) {
                if (e.data && e.data.size > 0) self.chunks.push(e.data);
            };
            self.recorder.onstop = function () { self.finalize(); };
            self.recorder.onerror = function (e) { console.warn('dictation: MediaRecorder error', e); };

            self.recorder.start();
            self.recording = true;
            self.processing = false;
            setState(self.wrap, 'recording', 'Recording - click mic to stop');
            self.startLevelMeter(stream);

            self.startLivePreview();
        }).catch(function (err) {
            console.error('dictation: getUserMedia failed', err);
            setState(self.wrap, 'error');
            alert('Microphone access was denied or unavailable: ' + err.message);
        });
    };

    Dictation.prototype.stop = function () {
        this.stopLivePreview();
        if (this.recorder && this.recording) {
            try { this.recorder.stop(); } catch (e) { /* already stopped */ }
            this.recording = false;
            this.processing = true;
            setState(this.wrap, 'processing', 'Transcribing...');
        }
        this.stopLevelMeter();
        if (this.stream) {
            this.stream.getTracks().forEach(function (t) { t.stop(); });
            this.stream = null;
        }
    };

    Dictation.prototype.finalize = function () {
        var self = this;
        var blob = new Blob(this.chunks, { type: (this.recorder && this.recorder.mimeType) || 'audio/webm' });
        this.chunks = [];
        if (!blob.size) {
            this.processing = false;
            setState(this.wrap, 'error', 'No audio captured');
            return;
        }

        var form = new FormData();
        var ext = (blob.type.indexOf('mp4') >= 0) ? 'mp4' : (blob.type.indexOf('ogg') >= 0) ? 'ogg' : 'webm';
        form.append('audio', blob, 'dictation.' + ext);

        var url = '/study/session/' + this.sessionId + '/transcribe';
        fetch(url, { method: 'POST', body: form })
            .then(function (r) {
                if (!r.ok) return r.json().then(function (j) { throw new Error(j.error || ('HTTP ' + r.status)); });
                return r.json();
            })
            .then(function (data) {
                var text = (data.text || '').trim();
                if (!text) {
                    var seconds = Number(data.duration_sec || 0);
                    var detail = seconds ? ('No words recognized (' + seconds.toFixed(1) + 's audio)') : 'No words recognized';
                    console.warn('dictation: empty transcript', {
                        blobSize: blob.size,
                        blobType: blob.type,
                        durationSec: data.duration_sec,
                        language: data.language
                    });
                    self.previewStart = null;
                    self.previewLen = 0;
                    self.processing = false;
                    setState(self.wrap, 'error', detail);
                    return;
                }
                self.writePreview(text);
                self.previewStart = null;
                self.previewLen = 0;
                self.processing = false;
                setState(self.wrap, 'idle');
            })
            .catch(function (err) {
                console.error('dictation: Whisper transcription failed', err);
                // Keep whatever live-preview text landed — it's still useful.
                self.previewStart = null;
                self.previewLen = 0;
                self.processing = false;
                setState(self.wrap, 'error');
                alert('Whisper cleanup failed (live preview text was kept): ' + err.message);
            });
    };

    function init() {
        if (!hasRecorderSupport()) return;
        var wraps = document.querySelectorAll('[data-mic-button]');
        wraps.forEach(function (w) { new Dictation(w); });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
