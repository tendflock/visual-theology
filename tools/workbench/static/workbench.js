/* Sermon Research Workbench — client-side JS */

// ── Tab Switching ────────────────────────────────────────────────────────

function switchTab(btn, tabId) {
    const panel = btn.closest('.center-panel');
    panel.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    panel.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    btn.classList.add('active');
    const tab = document.getElementById(tabId);
    if (tab) tab.classList.add('active');
}

// ── Phase Selection ─────────────────────────────────────────────────────

const PHASE_PROMPTS = {
    exegesis: {
        icon: "📖",
        guidance: "Establish what the text says. Read in multiple translations, note differences, identify structure and flow of thought.",
        prompts: [
            "Read this passage in ESV, NASB95, and KJV and compare the translations",
            "What is the literary structure and flow of thought in this passage?",
            "Identify the key textual variants and translation differences",
            "What is the historical and literary context of this passage?",
        ],
    },
    languages: {
        icon: "🔤",
        guidance: "Analyze the Greek/Hebrew text. Identify theologically significant terms, morphological details, wordplay, and literary devices.",
        prompts: [
            "Do a word study on the key terms in this passage",
            "What are the important Greek/Hebrew words and their semantic range?",
            "Analyze the verb tenses and moods — what is significant?",
            "Are there any wordplay, chiasm, or literary devices in the original?",
        ],
    },
    crossrefs: {
        icon: "🔗",
        guidance: "Find intertextual connections, parallel passages, OT quotations in NT texts, and trace themes across Scripture.",
        prompts: [
            "Find the cross-references for this passage",
            "Are there OT quotations or allusions in this text?",
            "What parallel passages illuminate the meaning here?",
            "Trace the key themes of this passage across Scripture",
        ],
    },
    commentary: {
        icon: "📚",
        guidance: "Survey scholarly commentary. Where do commentators agree and disagree? What are the live exegetical questions?",
        prompts: [
            "Survey the commentaries on this passage",
            "What are the main interpretive questions scholars debate here?",
            "What historical and cultural background is important?",
            "Summarize the key insights from the commentaries",
        ],
    },
    synthesis: {
        icon: "🧠",
        guidance: "Draw together your findings. What are the main theological claims? How do exegetical details support the theological message?",
        prompts: [
            "What are the main theological claims of this text?",
            "How do the exegetical details support the theological message?",
            "How does this text fit into the book's overall argument?",
            "What systematic theological loci does this passage address?",
        ],
    },
    homiletics: {
        icon: "🎤",
        guidance: "Structure the sermon. Develop an outline faithful to the text. Consider illustrations and specific applications.",
        prompts: [
            "Suggest a sermon outline based on the text's structure",
            "What are the main points of application for a congregation?",
            "Suggest illustrations that illuminate the theological claims",
            "Critique my sermon outline for faithfulness to the text",
        ],
    },
};

function setActivePhase(btn) {
    btn.closest('.phase-list').querySelectorAll('.phase-item').forEach(p => {
        p.classList.remove('active');
    });
    btn.classList.add('active');
}

function activatePhase(btn, phaseId, phaseName, phaseDesc) {
    setActivePhase(btn);

    const phase = PHASE_PROMPTS[phaseId];
    if (!phase) return;

    // Build phase guidance banner using safe DOM methods
    let banner = document.getElementById('phase-banner');
    if (!banner) {
        banner = document.createElement('div');
        banner.id = 'phase-banner';
        const centerPanel = document.querySelector('.center-panel');
        const tabBar = centerPanel.querySelector('.tab-bar');
        tabBar.insertAdjacentElement('afterend', banner);
    }

    banner.className = 'phase-banner';
    // Clear previous content
    banner.textContent = '';

    // Header row
    const header = document.createElement('div');
    header.className = 'phase-banner-header';

    const icon = document.createElement('span');
    icon.className = 'phase-banner-icon';
    icon.textContent = phase.icon;
    header.appendChild(icon);

    const info = document.createElement('div');
    const nameEl = document.createElement('strong');
    nameEl.textContent = phaseName;
    info.appendChild(nameEl);
    const descEl = document.createElement('p');
    descEl.className = 'phase-banner-desc';
    descEl.textContent = phase.guidance;
    info.appendChild(descEl);
    header.appendChild(info);

    const closeBtn = document.createElement('button');
    closeBtn.className = 'phase-banner-close';
    closeBtn.textContent = '\u00d7';
    closeBtn.addEventListener('click', () => banner.remove());
    header.appendChild(closeBtn);

    banner.appendChild(header);

    // Prompt buttons
    const promptsDiv = document.createElement('div');
    promptsDiv.className = 'phase-prompts';
    for (const p of phase.prompts) {
        const promptBtn = document.createElement('button');
        promptBtn.className = 'phase-prompt-btn';
        promptBtn.textContent = p;
        promptBtn.addEventListener('click', () => sendPhasePrompt(p));
        promptsDiv.appendChild(promptBtn);
    }
    banner.appendChild(promptsDiv);
}

function sendPhasePrompt(text) {
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
        chatInput.value = text;
        chatInput.style.height = 'auto';
        chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
        chatInput.focus();
        sendMessage();
    }
}

// ── Notes Auto-Save ─────────────────────────────────────────────────────

let _notesSaveTimer = null;

function debounceSaveNotes(textarea) {
    clearTimeout(_notesSaveTimer);
    const status = document.getElementById('notes-status');
    if (status) status.textContent = 'Unsaved changes...';

    _notesSaveTimer = setTimeout(() => {
        const projectId = document.querySelector('.workspace')?.dataset?.projectId;
        if (!projectId) return;

        fetch(`/api/projects/${projectId}/notes`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ section: 'general', content: textarea.value }),
        }).then(r => {
            if (r.ok && status) status.textContent = 'Saved';
        }).catch(() => {
            if (status) status.textContent = 'Save failed';
        });
    }, 1000);
}

// ── Chat ─────────────────────────────────────────────────────────────────

let _chatBusy = false;

function sendMessage() {
    if (_chatBusy) return;

    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    if (!message) return;

    const projectId = typeof PROJECT_ID !== 'undefined' ? PROJECT_ID : null;
    if (!projectId) return;

    const model = document.getElementById('model-select')?.value || 'claude-sonnet-4-20250514';
    const messagesDiv = document.getElementById('chat-messages');
    const sendBtn = document.getElementById('chat-send');

    // Add user message bubble
    appendChatMessage('user', message);
    input.value = '';
    input.style.height = 'auto';

    // Create streaming assistant bubble
    const assistantDiv = appendChatMessage('assistant', '', true);
    const contentDiv = assistantDiv.querySelector('.msg-content');

    _chatBusy = true;
    sendBtn.disabled = true;

    // Stream via fetch + ReadableStream (SSE)
    fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project_id: projectId, message, model }),
    }).then(response => {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        function read() {
            reader.read().then(({ done, value }) => {
                if (done) {
                    finishStreaming(assistantDiv);
                    return;
                }

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop(); // keep incomplete line

                for (const line of lines) {
                    if (!line.startsWith('data: ')) continue;
                    try {
                        const event = JSON.parse(line.slice(6));
                        handleSSE(event, contentDiv, messagesDiv);
                    } catch (e) {
                        // skip malformed events
                    }
                }

                read();
            }).catch(err => {
                contentDiv.textContent += '\n[Connection error]';
                finishStreaming(assistantDiv);
            });
        }

        read();
    }).catch(err => {
        contentDiv.textContent = '[Failed to connect to server]';
        finishStreaming(assistantDiv);
    });
}

function handleSSE(event, contentDiv, messagesDiv) {
    switch (event.type) {
        case 'text':
            contentDiv.textContent += event.content;
            scrollChat();
            break;

        case 'tool_start':
            const toolDiv = document.createElement('div');
            toolDiv.className = 'chat-msg tool';
            toolDiv.innerHTML = `<details open>
                <summary>Calling: ${escapeHtml(event.name)}</summary>
                <pre class="tool-output">${escapeHtml(JSON.stringify(event.input, null, 2).slice(0, 200))}</pre>
            </details>`;
            messagesDiv.appendChild(toolDiv);
            scrollChat();
            break;

        case 'tool_result':
            // Update the last tool details with result
            const lastTool = messagesDiv.querySelector('.chat-msg.tool:last-of-type details');
            if (lastTool) {
                const resultPre = document.createElement('pre');
                resultPre.className = 'tool-output';
                resultPre.textContent = event.result;
                lastTool.appendChild(resultPre);
                lastTool.removeAttribute('open');
            }
            scrollChat();
            // Refresh research sidebar
            htmx.trigger(document.body, 'refreshResearch');
            break;

        case 'done':
            // Final content already streamed via 'text' events
            break;

        case 'error':
            contentDiv.textContent += '\n[Error: ' + event.message + ']';
            break;
    }
}

function appendChatMessage(role, content, streaming = false) {
    const messagesDiv = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = `chat-msg ${role}` + (streaming ? ' streaming' : '');
    div.innerHTML = `<div class="msg-content">${escapeHtml(content)}</div>`;
    messagesDiv.appendChild(div);
    scrollChat();
    return div;
}

function finishStreaming(div) {
    div.classList.remove('streaming');
    _chatBusy = false;
    const sendBtn = document.getElementById('chat-send');
    if (sendBtn) sendBtn.disabled = false;
    scrollChat();
}

function scrollChat() {
    const messagesDiv = document.getElementById('chat-messages');
    if (messagesDiv) {
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ── Library Browser ─────────────────────────────────────────────────────

function openResource(filename, title, abbrev, rtype) {
    const slot = document.getElementById('resource-detail-slot');
    if (!slot) return;

    slot.innerHTML = '<p class="loading">Loading table of contents...</p>';
    const params = new URLSearchParams({ title, abbrev, type: rtype });

    fetch(`/api/resource/${encodeURIComponent(filename)}/toc?${params}`)
        .then(r => r.text())
        .then(html => { slot.innerHTML = html; slot.scrollIntoView({ behavior: 'smooth' }); })
        .catch(() => { slot.innerHTML = '<p>Failed to load resource.</p>'; });
}

function readArticle(filename, articleNum, el) {
    // Find the article slot for this resource
    const safeFilename = filename.replace(/\./g, '-');
    const slot = document.getElementById('article-slot-' + safeFilename);
    if (!slot) return;

    // Highlight the clicked entry
    const parent = el.closest('.resource-toc');
    if (parent) parent.querySelectorAll('.toc-entry').forEach(e => e.style.fontWeight = '');
    el.style.fontWeight = '700';

    slot.innerHTML = '<p class="loading">Reading article...</p>';

    fetch(`/api/resource/${encodeURIComponent(filename)}/article/${articleNum}`)
        .then(r => r.text())
        .then(html => { slot.innerHTML = html; })
        .catch(() => { slot.innerHTML = '<p>Failed to read article.</p>'; });
}

// ── Interlinear Suggestions ─────────────────────────────────────────────

function suggestWordStudy(reference) {
    // Switch to the project view's chat tab and pre-fill the input
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
        chatInput.value = `Do a word study on the key terms in ${reference}`;
        chatInput.style.height = 'auto';
        chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
        chatInput.focus();
    }
}

// ── Keyboard Shortcuts ──────────────────────────────────────────────────

document.addEventListener('keydown', function(e) {
    // Cmd/Ctrl + Enter to send message
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
        const input = document.getElementById('chat-input');
        if (input && document.activeElement === input) {
            e.preventDefault();
            sendMessage();
        }
    }
});

// Auto-resize chat textarea
document.addEventListener('input', function(e) {
    if (e.target.id === 'chat-input') {
        e.target.style.height = 'auto';
        e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
    }
});
