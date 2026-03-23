/**
 * study.js — Conversation-first sermon study UI
 * Vanilla JS. No framework. SSE streaming. Outline sidebar. Session clock.
 */

'use strict';

/* ── Session Clock (counts UP) ──────────────────────────────────────────── */

var studyClock = {
    startTime: null,
    interval: null,
    elapsed: 0,        // seconds, restored from server on resume
    nudge2hShown: false,
    nudge4hShown: false,

    start: function(initialElapsed) {
        this.elapsed = initialElapsed || 0;
        this.startTime = Date.now() - (this.elapsed * 1000);
        if (this.interval) return;
        var self = this;
        this.interval = setInterval(function() {
            self.elapsed = Math.floor((Date.now() - self.startTime) / 1000);
            self.updateDisplay();
            self.checkWellbeing();
        }, 1000);
        this.updateDisplay();
    },

    updateDisplay: function() {
        var el = document.getElementById('session-clock');
        if (!el) return;
        el.textContent = this.formatDuration(this.elapsed);
    },

    formatDuration: function(totalSeconds) {
        var h = Math.floor(totalSeconds / 3600);
        var m = Math.floor((totalSeconds % 3600) / 60);
        if (h > 0) return h + 'h ' + m + 'm';
        return m + 'm';
    },

    checkWellbeing: function() {
        if (this.elapsed >= 14400 && !this.nudge4hShown) {
            this.nudge4hShown = true;
            showWellbeingNudge("Seriously, eat something. The Greek will still be here.");
        } else if (this.elapsed >= 7200 && !this.nudge2hShown) {
            this.nudge2hShown = true;
            showWellbeingNudge("You've been locked in for 2 hours \u2014 grab some water?");
        }
    },

    syncToServer: function() {
        if (!window.studySessionId) return;
        fetch('/study/session/' + window.studySessionId + '/clock', {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ elapsed: this.elapsed })
        }).catch(function() {});
    }
};

/* ── Wellbeing Nudge ────────────────────────────────────────────────────── */

function showWellbeingNudge(text) {
    var el = document.getElementById('wellbeing-nudge');
    if (!el) return;
    var msgEl = el.querySelector('.nudge-text');
    if (msgEl) msgEl.textContent = text;
    el.classList.remove('hidden');
}

function dismissWellbeingNudge() {
    var el = document.getElementById('wellbeing-nudge');
    if (el) el.classList.add('hidden');
}

/* ── SSE Streaming ──────────────────────────────────────────────────────── */

var isStreaming = false;

async function sendStudyMessage(sessionId, message) {
    if (!message.trim() || isStreaming) return;
    isStreaming = true;

    var inputEl = document.getElementById('study-input');
    var sendBtn = document.getElementById('btn-study-send');
    if (inputEl) { inputEl.disabled = true; inputEl.value = ''; }
    if (sendBtn) sendBtn.disabled = true;

    appendConvMessage('user', message);

    var assistantEl = appendConvMessage('assistant', '');

    var buffer = '';

    try {
        var response = await fetch('/study/session/' + sessionId + '/discuss', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message })
        });

        if (!response.ok) {
            var bubble = assistantEl.querySelector('.msg-content');
            if (bubble) bubble.textContent = '[Error ' + response.status + ']';
            return;
        }

        var reader = response.body.getReader();
        var decoder = new TextDecoder();

        while (true) {
            var chunk = await reader.read();
            if (chunk.done) break;

            buffer += decoder.decode(chunk.value, { stream: true });

            var lines = buffer.split('\n');
            buffer = lines.pop();

            for (var i = 0; i < lines.length; i++) {
                var line = lines[i];
                if (!line.startsWith('data: ')) continue;
                var payload = line.slice(6).trim();
                if (!payload || payload === '[DONE]') continue;

                var data;
                try { data = JSON.parse(payload); } catch (e) { continue; }

                handleSSEEvent(data, assistantEl);
            }
        }
    } catch (err) {
        var errEl = assistantEl ? assistantEl.querySelector('.msg-content') : null;
        if (errEl) errEl.textContent = '[Connection error: ' + err.message + ']';
    } finally {
        isStreaming = false;
        if (inputEl) { inputEl.disabled = false; inputEl.focus(); }
        if (sendBtn) sendBtn.disabled = false;
        scrollConversation();
        // Sync clock after each exchange
        studyClock.syncToServer();
    }
}

function handleSSEEvent(data, assistantEl) {
    if (data.type === 'text_delta') {
        var msgContent = assistantEl.querySelector('.msg-content');
        if (msgContent) msgContent.textContent += data.text;
        scrollConversation();

    } else if (data.type === 'tool_start') {
        appendToolStart(data.name);
        scrollConversation();

    } else if (data.type === 'tool_result') {
        renderToolResult(data.name, data.result);
        scrollConversation();

    } else if (data.type === 'outline_update') {
        // AI saved something to outline — refresh sidebar
        refreshOutline();

    } else if (data.type === 'error') {
        var errContent = assistantEl.querySelector('.msg-content');
        if (errContent) errContent.textContent += '\n[Error: ' + (data.message || 'unknown') + ']';
    }
    // 'done' — handled by finally block
}

/* ── Message Rendering ──────────────────────────────────────────────────── */

function appendConvMessage(role, text) {
    var thread = document.getElementById('conversation-thread');
    if (!thread) return null;

    var wrapper = document.createElement('div');
    wrapper.className = 'conv-message ' + role;

    var content = document.createElement('div');
    content.className = 'msg-content';
    content.textContent = text;

    wrapper.appendChild(content);
    thread.appendChild(wrapper);
    scrollConversation();
    return wrapper;
}

function appendToolStart(name) {
    var thread = document.getElementById('conversation-thread');
    if (!thread) return;

    var el = document.createElement('div');
    el.className = 'conv-tool-start';
    el.textContent = 'Searching: ' + formatToolName(name) + '\u2026';
    thread.appendChild(el);
}

function formatToolName(name) {
    var names = {
        'read_bible_passage': 'Bible',
        'find_commentary_paragraph': 'commentaries',
        'lookup_lexicon': 'lexicons',
        'lookup_grammar': 'grammars',
        'word_study_lookup': 'interlinear',
        'expand_cross_references': 'cross-references',
        'save_to_outline': 'saving to outline',
        'get_passage_data': 'Logos datasets',
        'get_cross_reference_network': 'cross-reference network',
        'get_passage_context': 'passage context'
    };
    return names[name] || name.replace(/_/g, ' ');
}

/* ── Rich Content Block Rendering ───────────────────────────────────────── */

function renderToolResult(name, result) {
    var thread = document.getElementById('conversation-thread');
    if (!thread) return;

    // Remove matching pending tool-start
    var pending = thread.querySelectorAll('.conv-tool-start');
    var needle = 'Searching: ' + formatToolName(name) + '\u2026';
    for (var i = 0; i < pending.length; i++) {
        if (pending[i].textContent === needle) {
            pending[i].remove();
            break;
        }
    }

    // save_to_outline — show as insight pill
    if (name === 'save_to_outline') {
        var pillText = '';
        if (typeof result === 'object' && result !== null) {
            pillText = result.content || result.message || JSON.stringify(result);
        } else {
            pillText = String(result);
        }
        var pill = document.createElement('div');
        pill.className = 'insight-pill';
        var pillSpan = document.createElement('span');
        pillSpan.textContent = 'Saved: ' + pillText;
        pill.appendChild(pillSpan);
        thread.appendChild(pill);
        refreshOutline();
        return;
    }

    // Default: collapsible tool result
    var wrapper = document.createElement('div');
    wrapper.className = 'conv-tool-result';

    var details = document.createElement('details');
    var summary = document.createElement('summary');
    summary.textContent = formatToolName(name);

    var body = document.createElement('div');
    body.className = 'tool-body';
    if (typeof result === 'string') {
        body.textContent = result;
    } else {
        try { body.textContent = JSON.stringify(result, null, 2); }
        catch (e) { body.textContent = String(result); }
    }

    details.appendChild(summary);
    details.appendChild(body);
    wrapper.appendChild(details);
    thread.appendChild(wrapper);
}

/* ── Scroll ─────────────────────────────────────────────────────────────── */

function scrollConversation() {
    var thread = document.getElementById('conversation-thread');
    if (thread) thread.scrollTop = thread.scrollHeight;
}

/* ── Outline Sidebar ────────────────────────────────────────────────────── */

function refreshOutline() {
    if (!window.studySessionId) return;
    fetch('/study/session/' + window.studySessionId + '/outline')
        .then(function(r) { return r.json(); })
        .then(function(tree) { renderOutlineTree(tree); })
        .catch(function() {});
}

function renderOutlineTree(tree) {
    var body = document.getElementById('outline-tree-container');
    if (!body) return;

    // Clear existing
    while (body.firstChild) body.removeChild(body.firstChild);

    if (!tree || tree.length === 0) {
        var empty = document.createElement('p');
        empty.style.cssText = 'color:var(--text-dim);font-size:13px;font-style:italic;padding:8px 0;';
        empty.textContent = 'Outline builds as you study.';
        body.appendChild(empty);
        return;
    }

    var ul = buildOutlineUL(tree);
    body.appendChild(ul);
}

function buildOutlineUL(nodes) {
    var ul = document.createElement('ul');
    ul.className = 'outline-tree';

    for (var i = 0; i < nodes.length; i++) {
        var node = nodes[i];
        var li = document.createElement('li');
        li.className = 'outline-node';
        if (node.type === 'main_point' || node.type === 'title') li.classList.add('is-main');
        li.dataset.id = String(node.id);

        var row = document.createElement('div');
        row.className = 'outline-node-row';

        var textSpan = document.createElement('span');
        textSpan.className = 'outline-node-text';
        textSpan.textContent = node.content;

        row.appendChild(textSpan);

        if (node.verse_ref) {
            var ref = document.createElement('span');
            ref.className = 'outline-node-ref';
            ref.textContent = node.verse_ref;
            row.appendChild(ref);
        }

        // Actions
        var actions = document.createElement('div');
        actions.className = 'outline-node-actions';

        var editBtn = document.createElement('button');
        editBtn.className = 'outline-btn';
        editBtn.textContent = 'Edit';
        editBtn.title = 'Edit';
        (function(nid, textEl) {
            editBtn.addEventListener('click', function() {
                editOutlineNode(nid, textEl);
            });
        })(node.id, textSpan);

        var delBtn = document.createElement('button');
        delBtn.className = 'outline-btn del';
        delBtn.textContent = 'Del';
        delBtn.title = 'Delete';
        (function(nid) {
            delBtn.addEventListener('click', function() {
                deleteOutlineNode(nid);
            });
        })(node.id);

        actions.appendChild(editBtn);
        actions.appendChild(delBtn);
        row.appendChild(actions);

        li.appendChild(row);

        if (node.children && node.children.length > 0) {
            li.appendChild(buildOutlineUL(node.children));
        }

        ul.appendChild(li);
    }
    return ul;
}

function editOutlineNode(nodeId, textEl) {
    if (!textEl) return;
    var original = textEl.textContent;

    var input = document.createElement('input');
    input.type = 'text';
    input.value = original;
    input.style.cssText = 'background:var(--bg-input);border:1px solid var(--border-focus);border-radius:3px;color:var(--text);font-size:13px;padding:1px 6px;width:100%;outline:none;';

    textEl.replaceWith(input);
    input.focus();
    input.select();

    function save() {
        var newText = input.value.trim() || original;
        var span = document.createElement('span');
        span.className = 'outline-node-text';
        span.textContent = newText;
        input.replaceWith(span);

        if (newText !== original && window.studySessionId) {
            fetch('/study/session/' + window.studySessionId + '/outline/' + nodeId, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: newText })
            }).catch(function() {});
        }
    }

    input.addEventListener('blur', save);
    input.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') { e.preventDefault(); input.blur(); }
        if (e.key === 'Escape') { input.value = original; input.blur(); }
    });
}

function deleteOutlineNode(nodeId) {
    if (!window.studySessionId) return;
    fetch('/study/session/' + window.studySessionId + '/outline/' + nodeId, {
        method: 'DELETE'
    }).then(function(r) {
        if (r.ok) refreshOutline();
    }).catch(function() {});
}

function addOutlineNote(text, nodeType) {
    if (!window.studySessionId || !text.trim()) return;
    fetch('/study/session/' + window.studySessionId + '/outline/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: text, node_type: nodeType || 'note' })
    }).then(function(r) {
        if (r.ok) refreshOutline();
    }).catch(function() {});
}

/* ── DOMContentLoaded ───────────────────────────────────────────────────── */

document.addEventListener('DOMContentLoaded', function() {

    // Study input — Enter to send, Shift+Enter for newline
    var inputEl = document.getElementById('study-input');
    if (inputEl) {
        inputEl.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                var msg = inputEl.value.trim();
                if (msg && window.studySessionId) {
                    sendStudyMessage(window.studySessionId, msg);
                }
            }
        });

        // Auto-resize
        inputEl.addEventListener('input', function() {
            inputEl.style.height = 'auto';
            inputEl.style.height = Math.min(inputEl.scrollHeight, 160) + 'px';
        });
    }

    // Send button
    var sendBtn = document.getElementById('btn-study-send');
    if (sendBtn) {
        sendBtn.addEventListener('click', function() {
            var msg = inputEl ? inputEl.value.trim() : '';
            if (msg && window.studySessionId) {
                sendStudyMessage(window.studySessionId, msg);
            }
        });
    }

    // Dismiss wellbeing nudge
    var nudgeDismiss = document.getElementById('btn-dismiss-nudge');
    if (nudgeDismiss) {
        nudgeDismiss.addEventListener('click', dismissWellbeingNudge);
    }

    // Outline add-note input
    var outlineInput = document.getElementById('outline-add-input');
    var outlineTypeSelect = document.getElementById('outline-add-type');
    if (outlineInput) {
        outlineInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                var text = outlineInput.value.trim();
                var ntype = outlineTypeSelect ? outlineTypeSelect.value : 'note';
                if (text) {
                    addOutlineNote(text, ntype);
                    outlineInput.value = '';
                }
            }
        });
    }

    // Load outline on page load
    refreshOutline();

    // Scroll conversation to bottom
    scrollConversation();

    // Sync clock every 60 seconds
    setInterval(function() { studyClock.syncToServer(); }, 60000);
});

/* ── Exports ────────────────────────────────────────────────────────────── */

Object.assign(window, {
    studyClock: studyClock,
    sendStudyMessage: sendStudyMessage,
    appendConvMessage: appendConvMessage,
    scrollConversation: scrollConversation,
    refreshOutline: refreshOutline,
    showWellbeingNudge: showWellbeingNudge,
    dismissWellbeingNudge: dismissWellbeingNudge,
    addOutlineNote: addOutlineNote
});
