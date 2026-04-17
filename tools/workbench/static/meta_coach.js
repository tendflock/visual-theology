// Meta-coach — SSE chat handler for patterns page

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('meta-coach-form');
  if (!form) return;

  const messagesDiv = document.getElementById('meta-coach-messages');
  const conversationId = Date.now();

  // Canned prompt buttons
  document.querySelectorAll('.coach-canned').forEach(btn => {
    btn.addEventListener('click', () => {
      sendMessage(btn.dataset.prompt);
    });
  });

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const textarea = form.querySelector('textarea[name=message]');
    const text = textarea.value.trim();
    if (!text) return;
    textarea.value = '';
    sendMessage(text);
  });

  async function sendMessage(text) {
    appendMessage('user', text);

    const response = await fetch('/sermons/patterns/coach/message', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({message: text, conversation_id: conversationId}),
    });

    if (!response.ok) {
      appendMessage('error', `HTTP ${response.status}`);
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    const assistantEl = appendMessage('assistant', '');
    let buffer = '';
    let fullText = '';

    while (true) {
      const {done, value} = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, {stream: true});
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        try {
          const event = JSON.parse(line.slice(6));
          if (event.type === 'text_delta') {
            fullText += event.text;
            assistantEl.textContent = 'Coach: ' + fullText;
          } else if (event.type === 'error') {
            fullText += `\n[error: ${event.error}]`;
            assistantEl.textContent = 'Coach: ' + fullText;
          }
        } catch (err) {
          console.error('parse error', err);
        }
      }
      messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }
    // Final markdown render — renderMarkdown escapes all HTML entities (&, <, >)
    // before applying markdown formatting, so XSS is not possible.
    const rendered = renderMarkdown(fullText);
    assistantEl.textContent = '';
    const strong = document.createElement('strong');
    strong.textContent = 'Coach:';
    assistantEl.appendChild(strong);
    assistantEl.insertAdjacentHTML('beforeend', ' ' + rendered); // eslint-disable-line no-unsanitized/method -- input is HTML-escaped by renderMarkdown
  }

  function renderMarkdown(text) {
    // SECURITY: Escape HTML entities FIRST to prevent XSS — all <, >, & are
    // converted to entities before any markdown processing. The only HTML
    // produced is from markdown syntax (strong, em, p, ul, ol, li, br).
    let html = text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
    html = html.split(/\n{2,}/).map(p => {
      p = p.trim();
      if (!p) return '';
      if (/^[-\u2022]\s/.test(p)) {
        const items = p.split(/\n/).map(l => '<li>' + l.replace(/^[-\u2022]\s*/, '') + '</li>').join('');
        return '<ul>' + items + '</ul>';
      }
      if (/^\d+[.)]\s/.test(p)) {
        const items = p.split(/\n/).map(l => '<li>' + l.replace(/^\d+[.)]\s*/, '') + '</li>').join('');
        return '<ol>' + items + '</ol>';
      }
      return '<p>' + p.replace(/\n/g, '<br>') + '</p>';
    }).join('');
    return html;
  }

  function appendMessage(role, text) {
    const el = document.createElement('div');
    el.className = `msg-${role}`;
    const label = role === 'user' ? 'You: ' : role === 'assistant' ? 'Coach: ' : '';
    if (role === 'assistant' && text) {
      // renderMarkdown escapes HTML entities before formatting — safe from XSS
      const strong = document.createElement('strong');
      strong.textContent = label;
      el.appendChild(strong);
      el.insertAdjacentHTML('beforeend', renderMarkdown(text)); // eslint-disable-line no-unsanitized/method -- input is HTML-escaped by renderMarkdown
    } else {
      el.textContent = label + (text || '');
    }
    messagesDiv.appendChild(el);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    return el;
  }
});
