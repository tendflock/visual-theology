// Sermon coach — SSE chat handler

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('coach-form');
  if (!form) return;

  const messagesDiv = document.getElementById('coach-messages');
  const sermonId = form.dataset.sermonId;
  let conversationId = 1;

  // Load existing chat history on page load (disable form until loaded to prevent race)
  const submitBtn = form.querySelector('button[type=submit]');
  submitBtn.disabled = true;
  fetch(`/sermons/${sermonId}/coach/history?conversation_id=${conversationId}`)
    .then(r => r.json())
    .then(messages => {
      for (const msg of messages) {
        appendMessage(msg.role, msg.content);
      }
    })
    .catch(err => console.error('Failed to load coach history:', err))
    .finally(() => { submitBtn.disabled = false; });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const textarea = form.querySelector('textarea[name=message]');
    const userText = textarea.value.trim();
    if (!userText) return;

    appendMessage('user', userText);
    textarea.value = '';

    const response = await fetch(`/sermons/${sermonId}/coach/message`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({message: userText, conversation_id: conversationId}),
    });

    if (!response.ok) {
      appendMessage('error', `HTTP ${response.status}`);
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    const assistantEl = appendMessage('assistant', '');
    let buffer = '';

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
            assistantEl.textContent += event.text;
          } else if (event.type === 'error') {
            assistantEl.textContent += `\n[error: ${event.error}]`;
          }
        } catch (err) {
          console.error('parse error', err);
        }
      }
      messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }
  });

  function appendMessage(role, text) {
    const el = document.createElement('div');
    el.className = `msg-${role}`;
    el.textContent = (role === 'user' ? 'You: ' : role === 'assistant' ? 'Coach: ' : '') + text;
    messagesDiv.appendChild(el);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    return el;
  }

  // Flag click → focused message
  document.querySelectorAll('.flag').forEach(el => {
    el.addEventListener('click', () => {
      const rationale = el.querySelector('.flag-rationale')?.textContent;
      const ts = el.querySelector('.flag-timestamp')?.textContent;
      const type = el.querySelector('.flag-type')?.textContent;
      const textarea = form.querySelector('textarea');
      textarea.value = `Walk me through the ${type} flag ${ts || ''}: ${rationale}`;
      textarea.focus();
    });
  });
});
