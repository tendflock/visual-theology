/**
 * companion.js - Client-side state for sermon study companion
 * Vanilla JS, no framework. ADHD-friendly: timer, mode toggle, SSE streaming.
 */

'use strict';

/* ── Timer ────────────────────────────────────────────────────────────────── */

class CompanionTimer {
    constructor(sessionId, initialSeconds) {
        this.sessionId = sessionId;
        this.remaining = initialSeconds;
        this.paused = false;
        this.manuallyPaused = false;
        this.interval = null;
        this.lastInteraction = Date.now();
        this.inactivityWarned = false;
        this._syncEvery = 30; // seconds between server syncs
        this._syncCounter = 0;
    }

    start() {
        if (this.interval) return; // already running
        this.paused = false;
        this.interval = setInterval(() => {
            if (this.remaining > 0) {
                this.remaining -= 1;
            }
            this._syncCounter += 1;
            if (this._syncCounter >= this._syncEvery) {
                this._syncCounter = 0;
                this.sync();
            }
            this.checkInactivity();
            this.updateDisplay();
        }, 1000);
    }

    pause(manual) {
        if (!this.interval) return;
        clearInterval(this.interval);
        this.interval = null;
        this.paused = true;
        if (manual) this.manuallyPaused = true;
        this.sync();
        this.updateDisplay();
        this._updatePauseButton();
    }

    resume() {
        if (this.interval) return;
        this.paused = false;
        this.manuallyPaused = false;
        this.start();
        this.sync();
        this._updatePauseButton();
    }

    toggle() {
        if (this.paused) {
            this.resume();
        } else {
            this.pause(true);
        }
    }

    sync() {
        fetch('/companion/session/' + this.sessionId + '/timer', {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                remaining: this.remaining,
                paused: this.paused
            })
        }).catch(function() {
            // Silently ignore network errors - timer keeps running locally
        });
    }

    formatTime(seconds) {
        if (seconds < 0) seconds = 0;
        var h = Math.floor(seconds / 3600);
        var m = Math.floor((seconds % 3600) / 60);
        var s = seconds % 60;
        var pad = function(n) { return String(n).padStart(2, '0'); };
        if (h > 0) {
            return h + ':' + pad(m) + ':' + pad(s);
        }
        return pad(m) + ':' + pad(s);
    }

    checkInactivity() {
        var idle = (Date.now() - this.lastInteraction) / 1000;
        if (idle > 300 && !this.paused) {
            this.pause();
        }
        if (idle > 600 && !this.inactivityWarned) {
            this.inactivityWarned = true;
            sendNudge();
        }
    }

    onInteraction() {
        this.lastInteraction = Date.now();
        this.inactivityWarned = false;
        // Resume on any interaction — whether auto-paused or manually paused
        if (this.paused) {
            this.resume();
        }
    }

    updateDisplay() {
        var el = document.getElementById('timer-display');
        if (!el) return;
        var prefix = this.paused ? 'II ' : '';
        el.textContent = prefix + this.formatTime(this.remaining);
        el.classList.remove('warning', 'urgent');
        if (this.remaining < 60) {
            el.classList.add('urgent');
        } else if (this.remaining < 300) {
            el.classList.add('warning');
        }
    }

    _updatePauseButton() {
        var btn = document.getElementById('btn-timer-toggle');
        if (!btn) return;
        btn.textContent = this.paused ? 'Resume' : 'Pause';
    }
}

/* ── Global timer instance ───────────────────────────────────────────────── */

var timer = null;

/**
 * Called from session.html template to boot the timer.
 * @param {string} sessionId
 * @param {number} seconds - remaining seconds
 * @param {boolean} paused
 */
function initTimer(sessionId, seconds, paused) {
    timer = new CompanionTimer(sessionId, seconds);
    if (!paused) {
        timer.start();
    } else {
        timer.paused = true;
    }
    timer.updateDisplay();
    timer._updatePauseButton();
}

/* ── Mode Toggle ──────────────────────────────────────────────────────────── */

/**
 * Switch to discussion mode: card stays visible, discussion panel opens beside it.
 */
function enterDiscussionMode() {
    var mainContent = document.getElementById('main-content');
    var discussionArea = document.getElementById('discussion-area');
    if (mainContent) mainContent.classList.add('split-view');
    if (discussionArea) {
        discussionArea.classList.remove('hidden');
        scrollDiscussion();
    }
    var input = document.getElementById('discussion-input');
    if (input) input.focus();
}

/**
 * Close discussion panel, card goes back to full width.
 */
function enterCardMode() {
    var mainContent = document.getElementById('main-content');
    var discussionArea = document.getElementById('discussion-area');
    if (discussionArea) discussionArea.classList.add('hidden');
    if (mainContent) mainContent.classList.remove('split-view');
}

/* ── Outline Drawer ───────────────────────────────────────────────────────── */

function toggleOutlineDrawer() {
    var drawer = document.getElementById('outline-drawer');
    if (!drawer) return;
    drawer.classList.toggle('open');
}

function openOutlineDrawer() {
    var drawer = document.getElementById('outline-drawer');
    if (drawer) drawer.classList.add('open');
}

function closeOutlineDrawer() {
    var drawer = document.getElementById('outline-drawer');
    if (drawer) drawer.classList.remove('open');
}

/* ── Discussion / SSE Streaming ──────────────────────────────────────────── */

/**
 * Send a message and stream the assistant reply via SSE-over-fetch.
 * @param {string} sessionId
 * @param {string} message
 */
async function sendDiscussionMessage(sessionId, message) {
    if (!message.trim()) return;

    var inputEl = document.getElementById('discussion-input');
    var sendBtn = document.getElementById('btn-send');
    if (inputEl) inputEl.disabled = true;
    if (sendBtn) sendBtn.disabled = true;

    appendMessage('user', message);
    if (inputEl) inputEl.value = '';

    // Placeholder assistant bubble filled as tokens stream in
    var assistantEl = appendMessage('assistant', '');

    var buffer = '';

    try {
        var response = await fetch('/companion/session/' + sessionId + '/discuss', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message })
        });

        if (!response.ok) {
            var bubble = assistantEl.querySelector('.msg-bubble');
            if (bubble) {
                bubble.textContent = '[Error ' + response.status + ': ' + response.statusText + ']';
            }
            return;
        }

        var reader = response.body.getReader();
        var decoder = new TextDecoder();

        while (true) {
            var chunk = await reader.read();
            if (chunk.done) break;

            buffer += decoder.decode(chunk.value, { stream: true });

            // Parse SSE lines; keep last incomplete line in buffer
            var lines = buffer.split('\n');
            buffer = lines.pop();

            for (var i = 0; i < lines.length; i++) {
                var line = lines[i];
                if (!line.startsWith('data: ')) continue;
                var payload = line.slice(6).trim();
                if (!payload || payload === '[DONE]') continue;

                var data;
                try {
                    data = JSON.parse(payload);
                } catch (parseErr) {
                    continue;
                }

                if (data.type === 'text_delta') {
                    var msgBubble = assistantEl.querySelector('.msg-bubble');
                    if (msgBubble) {
                        msgBubble.textContent += data.text;
                    }
                    scrollDiscussion();
                } else if (data.type === 'tool_start') {
                    appendToolStart(data.name);
                    scrollDiscussion();
                } else if (data.type === 'tool_result') {
                    appendToolResult(data.name, data.result);
                    scrollDiscussion();
                } else if (data.type === 'error') {
                    var errBubble = assistantEl.querySelector('.msg-bubble');
                    if (errBubble) {
                        errBubble.textContent += '\n[Error: ' + (data.message || 'unknown') + ']';
                    }
                }
                // 'done' type: fall through, re-enable happens in finally
            }
        }
    } catch (err) {
        var errBubble2 = assistantEl ? assistantEl.querySelector('.msg-bubble') : null;
        if (errBubble2) {
            errBubble2.textContent = '[Connection error: ' + err.message + ']';
        }
    } finally {
        if (inputEl) {
            inputEl.disabled = false;
            inputEl.focus();
        }
        if (sendBtn) sendBtn.disabled = false;
        scrollDiscussion();
    }
}

/* ── Helper: append a message bubble ────────────────────────────────────── */

/**
 * Append a user or assistant message to the discussion thread.
 * Returns the wrapper element so the caller can update it for streaming.
 * @param {'user'|'assistant'} role
 * @param {string} text
 * @returns {HTMLElement}
 */
function appendMessage(role, text) {
    var thread = document.getElementById('discussion-thread');
    if (!thread) return null;

    var wrapper = document.createElement('div');
    wrapper.className = 'msg ' + role;

    var bubble = document.createElement('div');
    bubble.className = 'msg-bubble';
    bubble.textContent = text;

    wrapper.appendChild(bubble);
    thread.appendChild(wrapper);
    scrollDiscussion();
    return wrapper;
}

/* ── Helper: tool start indicator ───────────────────────────────────────── */

/**
 * Show "Using: tool_name..." indicator in the thread.
 * @param {string} name
 */
function appendToolStart(name) {
    var thread = document.getElementById('discussion-thread');
    if (!thread) return;

    var el = document.createElement('div');
    el.className = 'msg-tool-start';
    el.textContent = 'Using: ' + name + '\u2026';
    thread.appendChild(el);
}

/* ── Helper: collapsible tool result ─────────────────────────────────────── */

/**
 * Append a collapsible details block with tool output.
 * @param {string} name
 * @param {*} result
 */
function appendToolResult(name, result) {
    var thread = document.getElementById('discussion-thread');
    if (!thread) return;

    // Remove matching pending tool-start lines
    var pending = thread.querySelectorAll('.msg-tool-start');
    var needle = 'Using: ' + name + '\u2026';
    for (var i = 0; i < pending.length; i++) {
        if (pending[i].textContent === needle) {
            pending[i].remove();
        }
    }

    var wrapper = document.createElement('div');
    wrapper.className = 'msg-tool-result';

    var details = document.createElement('details');

    var summary = document.createElement('summary');
    summary.textContent = 'Result: ' + name;

    var content = document.createElement('div');
    content.className = 'tool-content';

    if (typeof result === 'string') {
        content.textContent = result;
    } else {
        try {
            content.textContent = JSON.stringify(result, null, 2);
        } catch (e) {
            content.textContent = String(result);
        }
    }

    details.appendChild(summary);
    details.appendChild(content);
    wrapper.appendChild(details);
    thread.appendChild(wrapper);
}

/* ── Helper: scroll discussion to bottom ─────────────────────────────────── */

function scrollDiscussion() {
    var thread = document.getElementById('discussion-thread');
    if (thread) {
        thread.scrollTop = thread.scrollHeight;
    }
}

/* ── Nudge ────────────────────────────────────────────────────────────────── */

/**
 * Called when user has been idle >10 minutes.
 */
function sendNudge() {
    if (!window.sessionId) return;

    var banner = document.getElementById('nudge-banner');
    if (banner) banner.classList.remove('hidden');

    fetch('/companion/session/' + window.sessionId + '/nudge', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
    }).catch(function() {});
}

function dismissNudge() {
    var banner = document.getElementById('nudge-banner');
    if (banner) banner.classList.add('hidden');
}

/* ── Outline item interactions ───────────────────────────────────────────── */

/**
 * Delete an outline item.
 * @param {string|number} itemId
 * @param {HTMLElement} rowEl
 */
function deleteOutlineItem(itemId, rowEl) {
    if (!window.sessionId) return;
    fetch('/companion/session/' + window.sessionId + '/outline/' + itemId, {
        method: 'DELETE'
    }).then(function(r) {
        if (r.ok) {
            var li = rowEl.closest('li');
            if (li) li.remove();
        }
    }).catch(function() {});
}

/**
 * Make an outline item text editable inline.
 * @param {string|number} itemId
 * @param {HTMLElement} textEl
 */
function editOutlineItem(itemId, textEl) {
    if (!textEl) return;
    var original = textEl.textContent;

    var input = document.createElement('input');
    input.type = 'text';
    input.value = original;
    input.style.cssText = [
        'background:var(--bg-input)',
        'border:1px solid var(--border-focus)',
        'border-radius:3px',
        'color:var(--text)',
        'font-size:13px',
        'padding:1px 6px',
        'width:100%',
        'outline:none'
    ].join(';');

    textEl.replaceWith(input);
    input.focus();
    input.select();

    function save() {
        var newText = input.value.trim() || original;
        var span = document.createElement('span');
        span.className = 'outline-item-text';
        span.textContent = newText;
        input.replaceWith(span);

        if (newText !== original && window.sessionId) {
            fetch('/companion/session/' + window.sessionId + '/outline/' + itemId, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: newText })
            }).catch(function() {});
        }
    }

    input.addEventListener('blur', save);
    input.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') { e.preventDefault(); input.blur(); }
        if (e.key === 'Escape') { input.value = original; input.blur(); }
    });
}

/* ── Outline: add a point via API ────────────────────────────────────────── */

/**
 * POST a new top-level outline point to the server.
 * @param {string} text
 */
function addOutlinePoint(text) {
    if (!window.sessionId) return;
    fetch('/companion/session/' + window.sessionId + '/outline', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text, level: 0 })
    }).then(function(r) { return r.json(); }).then(function(data) {
        if (data.id) {
            _appendOutlineItemToDOM(data.id, text, 0);
        }
    }).catch(function() {});
}

/**
 * Append a new outline list item to the DOM.
 * @param {string|number} id
 * @param {string} text
 * @param {number} level
 */
function _appendOutlineItemToDOM(id, text, level) {
    var list = document.querySelector('#outline-body > .outline-list');
    if (!list) return;

    var li = document.createElement('li');
    li.className = 'outline-item' + (level === 0 ? ' main-point' : '');
    li.dataset.id = String(id);

    var row = document.createElement('div');
    row.className = 'outline-item-row';

    var textSpan = document.createElement('span');
    textSpan.className = 'outline-item-text';
    textSpan.textContent = text;

    var actions = document.createElement('div');
    actions.className = 'outline-item-actions';

    var editBtn = document.createElement('button');
    editBtn.className = 'outline-btn-icon';
    editBtn.title = 'Edit';
    editBtn.textContent = 'Edit';
    editBtn.addEventListener('click', function() {
        editOutlineItem(id, row.querySelector('.outline-item-text'));
    });

    var delBtn = document.createElement('button');
    delBtn.className = 'outline-btn-icon delete';
    delBtn.title = 'Delete';
    delBtn.textContent = 'Del';
    delBtn.addEventListener('click', function() {
        deleteOutlineItem(id, row);
    });

    actions.appendChild(editBtn);
    actions.appendChild(delBtn);
    row.appendChild(textSpan);
    row.appendChild(actions);
    li.appendChild(row);
    list.appendChild(li);
}

/* ── Progress dots ───────────────────────────────────────────────────────── */

/**
 * Refresh progress dot states given current step index and total.
 * @param {number} currentIndex - 0-based index of active step
 * @param {number} total
 */
function updateProgressDots(currentIndex, total) {
    var container = document.getElementById('progress-dots');
    if (!container) return;

    // Safe DOM removal - no untrusted content via innerHTML
    while (container.firstChild) {
        container.removeChild(container.firstChild);
    }

    for (var i = 0; i < total; i++) {
        var dot = document.createElement('div');
        dot.className = 'progress-dot';
        if (i < currentIndex) {
            dot.classList.add('completed');
            dot.title = 'Step ' + (i + 1) + ': complete';
        } else if (i === currentIndex) {
            dot.classList.add('current');
            dot.title = 'Step ' + (i + 1) + ': current';
        } else {
            dot.classList.add('future');
            dot.title = 'Step ' + (i + 1);
        }
        container.appendChild(dot);
    }
}

/* ── DOMContentLoaded bootstrap ─────────────────────────────────────────── */

document.addEventListener('DOMContentLoaded', function() {

    // Track interactions for inactivity detection
    // Skip clicks on the timer toggle button (handled separately)
    document.addEventListener('click', function(e) {
        if (e.target && e.target.id === 'btn-timer-toggle') return;
        if (timer) timer.onInteraction();
    });
    document.addEventListener('keydown', function() {
        if (timer) timer.onInteraction();
    });

    // Timer pause/resume button — stopPropagation prevents the document
    // click handler from calling onInteraction() which would auto-resume
    var timerToggleBtn = document.getElementById('btn-timer-toggle');
    if (timerToggleBtn) {
        timerToggleBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            if (timer) timer.toggle();
        });
    }

    // Outline drawer toggle
    var outlineToggleBtn = document.getElementById('btn-outline-toggle');
    if (outlineToggleBtn) {
        outlineToggleBtn.addEventListener('click', toggleOutlineDrawer);
    }

    var closeOutlineBtn = document.getElementById('btn-close-outline');
    if (closeOutlineBtn) {
        closeOutlineBtn.addEventListener('click', closeOutlineDrawer);
    }

    // Back to card button in discussion view
    var backToCardBtn = document.getElementById('btn-back-to-card');
    if (backToCardBtn) {
        backToCardBtn.addEventListener('click', enterCardMode);
    }

    // Dismiss nudge banner
    var dismissNudgeBtn = document.getElementById('btn-dismiss-nudge');
    if (dismissNudgeBtn) {
        dismissNudgeBtn.addEventListener('click', dismissNudge);
    }

    // Discussion input - Enter to send (Shift+Enter for newline)
    var inputEl = document.getElementById('discussion-input');
    if (inputEl) {
        inputEl.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                var msg = inputEl.value.trim();
                if (msg && window.sessionId) {
                    sendDiscussionMessage(window.sessionId, msg);
                }
            }
        });

        // Auto-resize textarea as user types
        inputEl.addEventListener('input', function() {
            inputEl.style.height = 'auto';
            inputEl.style.height = Math.min(inputEl.scrollHeight, 120) + 'px';
        });
    }

    // Send button
    var sendBtn = document.getElementById('btn-send');
    if (sendBtn) {
        sendBtn.addEventListener('click', function() {
            var msg = inputEl ? inputEl.value.trim() : '';
            if (msg && window.sessionId) {
                sendDiscussionMessage(window.sessionId, msg);
            }
        });
    }

    // Outline add-point input
    var outlineAddInput = document.getElementById('outline-add-input');
    if (outlineAddInput) {
        outlineAddInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                var text = outlineAddInput.value.trim();
                if (text && window.sessionId) {
                    addOutlinePoint(text);
                    outlineAddInput.value = '';
                }
            }
        });
    }

    // Scroll discussion to bottom on load (may have prior messages)
    scrollDiscussion();
});

/* ── Exports (available on window for inline handlers in templates) ──────── */

Object.assign(window, {
    initTimer: initTimer,
    enterDiscussionMode: enterDiscussionMode,
    enterCardMode: enterCardMode,
    toggleOutlineDrawer: toggleOutlineDrawer,
    openOutlineDrawer: openOutlineDrawer,
    closeOutlineDrawer: closeOutlineDrawer,
    sendDiscussionMessage: sendDiscussionMessage,
    appendMessage: appendMessage,
    appendToolStart: appendToolStart,
    appendToolResult: appendToolResult,
    scrollDiscussion: scrollDiscussion,
    sendNudge: sendNudge,
    dismissNudge: dismissNudge,
    deleteOutlineItem: deleteOutlineItem,
    editOutlineItem: editOutlineItem,
    addOutlinePoint: addOutlinePoint,
    updateProgressDots: updateProgressDots
});
