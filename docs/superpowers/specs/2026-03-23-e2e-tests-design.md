# E2E Test Suite — Playwright + pytest

**Date:** 2026-03-23
**Status:** Approved

## Problem

Features break silently. The word-click popup returned "error" for every word because the Flask server was running stale code — the MorphGNT module had been added but the server wasn't restarted. Existing unit tests use Flask's test client (fresh Python process each run), so they can't catch server-level issues. We need tests that boot the real server, open a real browser, and verify the full stack works.

## Approach

Playwright (headless Chromium) + pytest via `pytest-playwright`. Tests start the Flask server as a subprocess, navigate the UI in a browser, and verify everything from session creation through AI conversation with tool calls.

## Dependencies

```
pytest-playwright    # pytest integration
playwright           # browser automation
```

Setup:
```bash
pip install pytest-playwright
playwright install chromium
```

## Architecture

### Server Fixture (session-scoped)

One Flask server per test run. The fixture:

1. Creates a temp SQLite DB for session isolation
2. Picks a random available port
3. Starts `app.py` as a subprocess with env vars:
   - `COMPANION_DB_PATH` → temp DB path
   - `FLASK_PORT` → random port
   - `ANTHROPIC_API_KEY` → inherited from environment
   - `PATH` / `DOTNET_ROOT` → dotnet@8 paths
4. Health-checks `GET /study/` in a retry loop (up to 15s)
5. Yields `base_url` (e.g., `http://localhost:54321`)
6. Kills subprocess with `os.killpg()` (process group kill to include LogosReader grandchild) + cleans up temp DB on teardown

**Important:** The dev server on port 5111 must NOT be running during E2E tests. The LogosReader C# subprocess holds the native `libSinaiInterop.dylib` — two instances can conflict. The fixture should check port 5111 is free before starting, and fail fast with a clear message if it's occupied.

### Production Code Changes (must be implemented before tests)

Two env var overrides in `app.py`. These do NOT exist yet — they must be added.

**DB path (line ~88) — change hardcoded path to env-overridable:**
```diff
- companion_db = CompanionDB(str(TOOLS_DIR / "workbench" / "companion.db"))
+ db_path = os.environ.get("COMPANION_DB_PATH", str(TOOLS_DIR / "workbench" / "companion.db"))
+ companion_db = CompanionDB(db_path)
```

Also apply the same pattern for `study_analytics` (same line area):
```diff
- study_analytics = SessionAnalytics(str(TOOLS_DIR / "workbench" / "companion.db"))
+ study_analytics = SessionAnalytics(db_path)
```

**Port (line ~1131) — change hardcoded port to env-overridable:**
```diff
- app.run(host="127.0.0.1", port=5111, debug=False, threaded=True)
+ port = int(os.environ.get("FLASK_PORT", "5111"))
+ app.run(host="127.0.0.1", port=port, debug=False, threaded=True)
```

### Browser Fixture

`pytest-playwright` provides `page` (Chromium tab). Each test gets a fresh browser context — no cookie/state leakage.

### Helpers

**`advance_to_conversation(page, base_url)`** — Creates a session for "Romans 1:24-32", clicks Next through all 4 card phases, returns the session URL in conversation mode. Used by all tool tests.

Phase-by-phase behavior:
- **prayer** (has textarea): types "Lord, open my eyes" in `#card-response`, clicks Next
- **read_translate** (has textarea): types "Working translation" in `#card-response`, clicks Next
- **digestion** (has textarea): types "Meditation notes" in `#card-response`, clicks Next
- **study_bibles** (NO textarea): just clicks Next — no text input needed

**`send_message_and_wait(page, message, timeout=90000)`** — Types into `#study-input`, clicks `#btn-study-send`, waits for the assistant response to finish streaming (waits for `#btn-study-send` to re-enable), returns the last `.conv-message.assistant` element. After completion, asserts the response does NOT contain error indicators (`[Error`, `[Connection error`, `error`-class elements).

**`get_tool_results(page)`** — Returns all `.conv-tool-result` elements from the conversation thread, parsed into `{name, body}` dicts. Also checks for `.insight-pill` elements (used by `save_to_outline` tool instead of `.conv-tool-result`).

### Markers

```python
@pytest.mark.e2e          # all E2E tests
@pytest.mark.tools        # tool tests (real API calls)
```

Run options:
```bash
pytest -m e2e                    # all 20 tests
pytest -m "e2e and not tools"    # UI-only (12 tests, no API cost)
pytest -m tools                  # tool tests only (8 tests)
```

### Timeouts

| Category | Timeout |
|----------|---------|
| Server startup | 15s (LogosReader subprocess boot) |
| Card/UI tests | 10s default |
| Tool tests | 90s (API call + LogosReader + Claude thinking) |

## Test Scenarios (20 tests)

### Session Creation (2 tests)

**`test_create_session`**
1. Navigate to `/study/`
2. Type "Romans 1:24-32" into `input[name="passage"]`
3. Click submit
4. Assert: redirected to `/study/session/{id}`, `.card-phase-label` contains "Prayer" (CSS may uppercase it), passage "Romans 1:24-32" in `.topbar-passage`

**`test_create_session_invalid`**
1. Navigate to `/study/`
2. Submit empty passage
3. Assert: error message visible, no redirect

### Card Workflow (3 tests)

**`test_card_phase_navigation`**
1. Create session for "Romans 1:24-32"
2. Assert phase label is "PRAYER", first progress dot is active
3. Type prayer text in `#card-response`, click Next
4. Assert phase label is "READ & TRANSLATE"
5. Click Back → assert "PRAYER" with textarea content preserved
6. Click Next → "READ & TRANSLATE", type translation, Next
7. Assert "DIGESTION", Next → "STUDY BIBLE CONSULTATION"
8. Next → conversation mode (assert `#conversation-column` exists in DOM — it's only rendered in conversation mode, not hidden)

**`test_card_autosave`**
1. Create session, land on prayer phase
2. Type "Test prayer content" in `#card-response`
3. Wait for the autosave network request to complete (`page.wait_for_response()` on `/card/autosave`)
4. Reload the page
5. Assert `#card-response` contains "Test prayer content"

**`test_read_translate_greek_text`**
1. Create session for "Romans 1:24-32", advance to read_translate phase
2. Assert `.card-resource-label` shows "THGNT"
3. Assert `.clickable-word` elements exist (Greek words are wrapped in spans)
4. Assert at least 10 clickable words present

### Word Click Popup (2 tests)

**`test_word_popup_shows_parsing`**
1. Create session for "Romans 1:24-32", advance to read_translate
2. Click first `.clickable-word`
3. Wait for `.word-popup` to appear
4. Assert `.wp-lemma` has Greek text (not empty, not "...")
5. Assert `.wp-gloss` has English text (not "loading...", not "error")
6. Assert `.wp-parsing` has content (e.g., "Noun, Genitive Plural Feminine")

**`test_word_popup_dismisses`**
1. Create session for "Romans 1:24-32", advance to read_translate
2. Click first `.clickable-word`, wait for `.word-popup` to appear
3. Click on empty area of the card (e.g., `.card-prompt`)
4. Assert `.word-popup` is gone (element count is 0)

### Study Bible Phase (2 tests)

**`test_study_bible_tabs`**
1. Create session, advance to study_bibles phase
2. Assert `.sb-tab` buttons exist (multiple study bibles)
3. Click second tab
4. Assert second `.sb-panel` is visible, first is hidden

**`test_star_annotation`**
1. At study_bibles phase, programmatically select text in `.sb-text` using `page.evaluate()` to create a DOM Selection range (triple-click is unreliable in headless Chromium). Then dispatch a `mouseup` event on `.sb-text` to trigger the star popup.
2. Assert `#star-popup` appears
3. Click star button (handle the `prompt()` dialog via `page.on('dialog')`)
4. Reload page
5. Assert `.sb-star-item` exists with the starred text

### Outline Sidebar (2 tests)

**`test_outline_add_note`**
1. Create session (any phase)
2. Type "Test main point" in `#outline-add-input`
3. Select "main_point" from `#outline-add-type`
4. Press Enter
5. Assert `.outline-node` appears with text "Test main point"

**`test_outline_delete_note`**
1. Add a note as above
2. Click the delete button (`.outline-btn.del` or similar) on that node
3. Assert `.outline-node` count decremented

### Timer (1 test)

**`test_session_clock`**
1. Create session
2. Assert `#session-clock` displays a time value (e.g., "0m" or "0:00")
3. Wait 2 seconds
4. Assert clock value has incremented
5. Click `#session-clock` (pause)
6. Record value, wait 2s
7. Assert value hasn't changed (paused)
8. Click again (resume), wait 2s, assert incremented

### Conversation + Tool Tests (8 tests)

All require `ANTHROPIC_API_KEY`. Skipped if not set. Each test:
1. Uses `advance_to_conversation()` helper to reach conversation mode
2. Sends a targeted prompt via `send_message_and_wait()`
3. Verifies the SSE stream completes, assistant message appears, and expected tool was called with real data

**`test_tool_read_bible`**
- Prompt: "Read Romans 1:24 in THGNT and ESV"
- Assert: tool result for "Bible" appears, response contains Greek characters

**`test_tool_commentary`**
- Prompt: "What do the commentaries say about Romans 1:24?"
- Assert: tool result for "commentaries" appears, response contains commentary text (length > 50 chars)

**`test_tool_lexicon`**
- Prompt: "Look up παρέδωκεν in BDAG"
- Assert: tool result for "lexicons" appears, response references BDAG

**`test_tool_grammar`**
- Prompt: "Check Wallace's grammar on the aorist indicative"
- Assert: tool result for "grammars" appears, response contains grammar content

**`test_tool_word_study`**
- Prompt: "What's the morphology of παρέδωκεν in Romans 1:24?"
- Assert: tool result for "interlinear" appears, response contains lemma/parsing info

**`test_tool_cross_references`**
- Prompt: "Get cross-references for Romans 1:24"
- Assert: tool result for "cross-references" appears, response contains at least one Bible reference

**`test_tool_save_outline`**
- Prompt: "Save this as a main point in the outline: God gave them over to the sinful desires of their hearts"
- Assert: `.insight-pill` appears (save_to_outline renders as insight pill, not `.conv-tool-result`), outline sidebar `.outline-node` count increases

**`test_tool_datasets`**
- Prompt: "What ancient literature or cultural context relates to idolatry in Romans 1:24-25?"
- Assert: tool result element appears in conversation (`.conv-tool-result`), assistant response contains substantive content (>100 chars)

**Note on tool prompt nondeterminism:** Claude may not always call the expected tool for a given prompt. The prompts above were chosen to strongly target specific tools, but if Claude routes differently, the test should check that *some* tool was called and returned data, then log which tool was actually used. Hard-failing on the wrong tool name would make tests flaky. The key assertion is: the pipeline works end-to-end (message → tool call → tool execution → result displayed).

## File Layout

```
tools/workbench/
  tests/
    conftest.py          # NEW file — server fixture + helpers
    test_e2e.py          # NEW file — all 20 E2E tests
  app.py                 # 2 env var overrides (changes to existing)
  pyproject.toml         # register e2e and tools markers (add or update)
```

### Marker Registration

Add to `pyproject.toml` (or `pytest.ini`):
```toml
[tool.pytest.ini_options]
markers = [
    "e2e: End-to-end browser tests (Playwright)",
    "tools: Tool integration tests (requires ANTHROPIC_API_KEY)",
]
```

## Running

```bash
# Install (one-time)
pip install pytest-playwright
playwright install chromium

# Run all E2E tests
cd tools/workbench && python3 -m pytest tests/test_e2e.py -v

# UI tests only (no API cost)
cd tools/workbench && python3 -m pytest tests/test_e2e.py -v -m "e2e and not tools"

# Tool tests only
cd tools/workbench && python3 -m pytest tests/test_e2e.py -v -m tools

# Run alongside existing unit tests
cd tools/workbench && python3 -m pytest tests/ -v
```
