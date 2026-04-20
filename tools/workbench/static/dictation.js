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
        var candidates = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/ogg'];
        for (var i = 0; i < candidates.length; i++) {
            if (MediaRecorder.isTypeSupported(candidates[i])) return candidates[i];
        }
        return '';
    }

    function setState(wrap, state) {
        wrap.classList.remove('state-idle', 'state-recording', 'state-processing', 'state-error');
        wrap.classList.add('state-' + state);
        var statusEl = wrap.querySelector('.mic-status');
        if (!statusEl) return;
        if (state === 'recording') statusEl.textContent = '● REC';
        else if (state === 'processing') statusEl.textContent = '…';
        else if (state === 'error') statusEl.textContent = '!';
        else statusEl.textContent = '';
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
            wrap.classList.add('picker-open');
        }
        function closePicker() {
            picker.hidden = true;
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
        if (!SR) return;
        var target = this.getTarget();
        if (!target) return;

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
            self.writePreview(text);
        };

        rec.onerror = function (e) {
            // Don't alert — live preview is best-effort. Whisper still runs on the audio.
            console.warn('dictation: SpeechRecognition error', e.error);
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
        } catch (err) {
            console.warn('dictation: SpeechRecognition.start failed', err);
            this.recognition = null;
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

    Dictation.prototype.start = function () {
        var self = this;
        var deviceId = localStorage.getItem(STORAGE_KEY) || '';
        var constraints = { audio: deviceId ? { deviceId: { exact: deviceId } } : true };

        // Seed the preview range from the current cursor position even if Web
        // Speech is unavailable — Whisper's writePreview() call still needs it.
        var tgt = this.getTarget();
        this.previewStart = tgt ? ((typeof tgt.selectionStart === 'number') ? tgt.selectionStart : tgt.value.length) : 0;
        this.previewLen = 0;

        navigator.mediaDevices.getUserMedia(constraints).then(function (stream) {
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
            setState(self.wrap, 'recording');

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
            setState(this.wrap, 'processing');
        }
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
            setState(this.wrap, 'idle');
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
                self.writePreview(data.text || '');
                self.previewStart = null;
                self.previewLen = 0;
                setState(self.wrap, 'idle');
            })
            .catch(function (err) {
                console.error('dictation: Whisper transcription failed', err);
                // Keep whatever live-preview text landed — it's still useful.
                self.previewStart = null;
                self.previewLen = 0;
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
