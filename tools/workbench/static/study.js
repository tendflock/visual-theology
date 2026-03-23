/**
 * study.js — Hybrid card + conversation sermon study UI
 * Vanilla JS. No framework. SSE streaming. Outline sidebar. Session clock.
 */

'use strict';

/* ── Session Clock (counts UP) ──────────────────────────────────────────── */

var studyClock = {
    startTime: null,
    interval: null,
    elapsed: 0,
    paused: false,
    nudge2hShown: false,
    nudge4hShown: false,

    start: function(initialElapsed) {
        this.elapsed = initialElapsed || 0;
        this.startTime = Date.now() - (this.elapsed * 1000);
        if (this.interval) return;
        var self = this;
        this.interval = setInterval(function() {
            if (!self.paused) {
                self.elapsed = Math.floor((Date.now() - self.startTime) / 1000);
                self.checkWellbeing();
            }
            self.updateDisplay();
        }, 1000);
        this.updateDisplay();
    },

    toggle: function() {
        if (this.paused) {
            // Resume — adjust startTime so elapsed stays correct
            this.startTime = Date.now() - (this.elapsed * 1000);
            this.paused = false;
        } else {
            this.paused = true;
        }
        this.updateDisplay();
    },

    updateDisplay: function() {
        var el = document.getElementById('session-clock');
        if (!el) return;
        var text = this.formatDuration(this.elapsed);
        if (this.paused) text += ' (paused)';
        el.textContent = text;
        el.classList.toggle('paused', this.paused);
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

/* ── Card Functions ─────────────────────────────────────────────────────── */

function switchTab(btn) {
    var tabIndex = btn.getAttribute('data-tab');
    var container = btn.closest('.study-bible-container');
    if (!container) return;

    // Toggle tab active state
    var allTabs = container.querySelectorAll('.sb-tab');
    for (var i = 0; i < allTabs.length; i++) {
        allTabs[i].classList.remove('active');
    }
    btn.classList.add('active');

    // Toggle panel visibility
    var allPanels = container.querySelectorAll('.sb-panel');
    for (var j = 0; j < allPanels.length; j++) {
        if (allPanels[j].getAttribute('data-tab') === tabIndex) {
            allPanels[j].classList.add('active');
        } else {
            allPanels[j].classList.remove('active');
        }
    }
}

function copyCardResponse() {
    var textarea = document.getElementById('card-response');
    var hidden = document.getElementById('hidden-response');
    if (textarea && hidden) {
        hidden.value = textarea.value;
    }
}

/* ── Card Auto-Save ────────────────────────────────────────────────────── */

var _cardSaveTimer = null;

function setupCardAutosave() {
    var textarea = document.getElementById('card-response');
    if (!textarea || !window.studySessionId) return;
    textarea.addEventListener('input', function() {
        clearTimeout(_cardSaveTimer);
        _cardSaveTimer = setTimeout(function() {
            fetch('/study/session/' + window.studySessionId + '/card/autosave', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({content: textarea.value})
            });
        }, 1500);
    });
}

/* ── Star Annotations ───────────────────────────────────────────────────── */

var starPopup = null;

function setupStarAnnotations() {
    var sbTextElements = document.querySelectorAll('.sb-text');
    if (sbTextElements.length === 0) return;

    document.addEventListener('mouseup', function(e) {
        var selection = window.getSelection();
        var text = selection ? selection.toString().trim() : '';

        // Remove existing popup
        if (starPopup) {
            starPopup.remove();
            starPopup = null;
        }

        if (!text || text.length < 3) return;

        // Check if selection is inside a .sb-text element
        var anchor = selection.anchorNode;
        var insideSbText = false;
        var sourceAbbrev = '';
        var node = anchor;
        while (node) {
            if (node.nodeType === 1 && node.classList && node.classList.contains('sb-text')) {
                insideSbText = true;
                sourceAbbrev = node.getAttribute('data-source') || '';
                break;
            }
            node = node.parentNode;
        }
        if (!insideSbText) return;

        // Show star popup near selection
        var range = selection.getRangeAt(0);
        var rect = range.getBoundingClientRect();

        starPopup = document.createElement('div');
        starPopup.id = 'star-popup';
        starPopup.textContent = '\u2605';
        starPopup.title = 'Star this selection';
        starPopup.style.left = (rect.left + rect.width / 2 - 16) + 'px';
        starPopup.style.top = (rect.top - 36) + 'px';

        var selectedText = text;
        var source = sourceAbbrev;

        starPopup.addEventListener('mousedown', function(ev) {
            ev.preventDefault();
            ev.stopPropagation();

            var note = prompt('Add a note (optional):') || '';

            fetch('/study/session/' + window.studySessionId + '/annotate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    source: source,
                    starred_text: selectedText,
                    note: note
                })
            }).then(function() {
                window.location.reload();
            }).catch(function() {});

            if (starPopup) {
                starPopup.remove();
                starPopup = null;
            }
        });

        document.body.appendChild(starPopup);
    });

    // Remove popup on click elsewhere
    document.addEventListener('mousedown', function(e) {
        if (starPopup && e.target !== starPopup) {
            starPopup.remove();
            starPopup = null;
        }
    });
}

/* ── Notepad Auto-save ──────────────────────────────────────────────────── */

var notepadTimer = null;
function debouncedSaveNotepad(content) {
    clearTimeout(notepadTimer);
    notepadTimer = setTimeout(function() {
        fetch('/study/session/' + window.studySessionId + '/notepad', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phase: 'study_bibles', content: content })
        }).catch(function() {});
    }, 1000);
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
        refreshOutline();

    } else if (data.type === 'error') {
        var errContent = assistantEl.querySelector('.msg-content');
        if (errContent) errContent.textContent += '\n[Error: ' + (data.message || 'unknown') + ']';
    }
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

/* ── Word Popup (click Greek/Hebrew word for parsing) ──────────────────── */

var _wordPopup = null;
var _wordCache = {};

function setupWordPopups() {
    var textEl = document.getElementById('clickable-text');
    if (!textEl) return;

    // Wrap each Greek/Hebrew word in a clickable span using DOM methods
    var walker = document.createTreeWalker(textEl, NodeFilter.SHOW_TEXT, null, false);
    var textNodes = [];
    var node;
    while ((node = walker.nextNode())) textNodes.push(node);

    var greekOrHebrew = /[\u0370-\u03FF\u1F00-\u1FFF\u0590-\u05FF\uFB1D-\uFB4F][\u0300-\u036F\u0370-\u03FF\u1F00-\u1FFF\u0590-\u05FF]*/;
    textNodes.forEach(function(tn) {
        var text = tn.textContent;
        if (!greekOrHebrew.test(text)) return;
        var frag = document.createDocumentFragment();
        // Split into words and non-words
        var parts = text.split(/([\u0370-\u03FF\u1F00-\u1FFF\u0590-\u05FF\uFB1D-\uFB4F][\u0300-\u036F\u0370-\u03FF\u1F00-\u1FFF\u0590-\u05FF\uFB1D-\uFB4F]*)/);
        parts.forEach(function(part) {
            if (greekOrHebrew.test(part)) {
                var span = document.createElement('span');
                span.className = 'clickable-word';
                span.textContent = part;
                frag.appendChild(span);
            } else {
                frag.appendChild(document.createTextNode(part));
            }
        });
        tn.parentNode.replaceChild(frag, tn);
    });

    // Add click handler
    textEl.addEventListener('click', function(e) {
        var wordEl = e.target.closest('.clickable-word');
        if (!wordEl) {
            dismissWordPopup();
            return;
        }
        var word = wordEl.textContent.trim();
        if (word) showWordInfo(word, wordEl);
    });

    // Dismiss on click outside
    document.addEventListener('click', function(e) {
        if (_wordPopup && !e.target.closest('.clickable-word') && !e.target.closest('.word-popup')) {
            dismissWordPopup();
        }
    });
}

function showWordInfo(word, anchorEl) {
    dismissWordPopup();

    // Check cache first
    if (_wordCache[word]) {
        renderWordPopup(_wordCache[word], anchorEl);
        return;
    }

    // Show loading state
    renderWordPopup({lemma: '...', gloss: 'loading...', parsing: '', root: ''}, anchorEl);

    fetch('/study/session/' + window.studySessionId + '/word-info', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({word: word})
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.error) {
            renderWordPopup({lemma: word, gloss: 'lookup failed', parsing: '', root: ''}, anchorEl);
        } else {
            _wordCache[word] = data;
            renderWordPopup(data, anchorEl);
        }
    })
    .catch(function() {
        renderWordPopup({lemma: word, gloss: 'error', parsing: '', root: ''}, anchorEl);
    });
}

function renderWordPopup(info, anchorEl) {
    dismissWordPopup();
    var popup = document.createElement('div');
    popup.className = 'word-popup';

    var lemmaDiv = document.createElement('div');
    lemmaDiv.className = 'wp-lemma';
    lemmaDiv.textContent = info.lemma || '';
    popup.appendChild(lemmaDiv);

    var glossDiv = document.createElement('div');
    glossDiv.className = 'wp-gloss';
    glossDiv.textContent = info.gloss || '';
    popup.appendChild(glossDiv);

    var parseDiv = document.createElement('div');
    parseDiv.className = 'wp-parsing';
    parseDiv.textContent = info.parsing || '';
    popup.appendChild(parseDiv);

    if (info.root && info.root !== info.lemma) {
        var rootDiv = document.createElement('div');
        rootDiv.className = 'wp-root';
        rootDiv.textContent = 'Root: ' + info.root;
        popup.appendChild(rootDiv);
    }

    // Position below the clicked word
    document.body.appendChild(popup);
    var rect = anchorEl.getBoundingClientRect();
    popup.style.left = Math.max(8, rect.left) + 'px';
    popup.style.top = (rect.bottom + window.scrollY + 6) + 'px';
    _wordPopup = popup;
}

function dismissWordPopup() {
    if (_wordPopup) {
        _wordPopup.remove();
        _wordPopup = null;
    }
}

/* ── DOMContentLoaded ───────────────────────────────────────────────────── */

document.addEventListener('DOMContentLoaded', function() {

    // Conversation mode: wire input and send button
    if (window.studyMode === 'conversation') {
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

        var sendBtn = document.getElementById('btn-study-send');
        if (sendBtn) {
            sendBtn.addEventListener('click', function() {
                var msg = inputEl ? inputEl.value.trim() : '';
                if (msg && window.studySessionId) {
                    sendStudyMessage(window.studySessionId, msg);
                }
            });
        }

        // Scroll conversation to bottom
        scrollConversation();
    }

    // Card mode: set up star annotations, word popups, and auto-save
    if (window.studyMode === 'card') {
        setupStarAnnotations();
        setupWordPopups();
        setupCardAutosave();
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
    addOutlineNote: addOutlineNote,
    switchTab: switchTab,
    copyCardResponse: copyCardResponse,
    debouncedSaveNotepad: debouncedSaveNotepad
});
