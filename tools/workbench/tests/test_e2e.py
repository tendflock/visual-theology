"""
E2E tests — Playwright + real Flask server.

Run: cd tools/workbench && python3 -m pytest tests/test_e2e.py -v
UI only: python3 -m pytest tests/test_e2e.py -v -m "e2e and not tools"
Tool tests: python3 -m pytest tests/test_e2e.py -v -m tools
"""

import os
import sys
import pytest

# Load .env file so ANTHROPIC_API_KEY is available for skipif checks
_env_file = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(_env_file):
    with open(_env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, _, val = line.partition('=')
                os.environ.setdefault(key.strip(), val.strip())

# conftest.py helpers are in the same directory
sys.path.insert(0, os.path.dirname(__file__))
from conftest import (
    create_session,
    advance_to_conversation,
    send_message_and_wait,
    get_tool_results,
)

pytestmark = pytest.mark.e2e

# ── Session Creation ──────────────────────────────────────────────────────


def test_create_session(page, base_url):
    """Create a study session from the start page."""
    create_session(page, base_url, "Romans 1:24-32")

    # Should be on session page with prayer phase
    assert "/study/session/" in page.url
    assert page.locator(".card-phase-label").inner_text().strip().lower() == "prayer"
    assert "Romans 1:24-32" in page.locator(".topbar-passage").inner_text()


def test_create_session_invalid(page, base_url):
    """Invalid passage shows server-side error, does not create session."""
    page.goto(f"{base_url}/study/")

    # Type a non-parseable passage (bypasses HTML required attribute)
    page.fill('input[name="passage"]', "xyzzy not a real passage")
    page.click('button[type="submit"], .btn-primary')
    page.wait_for_load_state("networkidle")

    # Should stay on start page with error visible
    assert "/study/session/" not in page.url
    assert page.locator(".error-msg").count() > 0, \
        "Expected .error-msg element for invalid passage"


# ── Card Workflow ─────────────────────────────────────────────────────────


def test_card_phase_navigation(page, base_url):
    """Walk through all 4 card phases forward and back."""
    create_session(page, base_url, "Romans 1:24-32")

    # Phase 1: Prayer
    label = page.locator(".card-phase-label")
    assert "prayer" in label.inner_text().lower()
    dots = page.locator(".phase-dot")
    assert dots.count() >= 4

    # Fill textarea and advance
    page.fill("#card-response", "My prayer for this study")
    page.click("#card-next-form button[type='submit']")
    page.wait_for_load_state("networkidle")

    # Phase 2: Read & Translate
    assert "read" in page.locator(".card-phase-label").inner_text().lower()

    # Go back — prayer text should be preserved
    page.click(".btn-secondary")
    page.wait_for_load_state("networkidle")
    assert "prayer" in page.locator(".card-phase-label").inner_text().lower()
    assert "My prayer for this study" in page.locator("#card-response").input_value()

    # Advance through all remaining phases
    page.click("#card-next-form button[type='submit']")
    page.wait_for_load_state("networkidle")
    # Phase 2: Read & Translate
    page.fill("#card-response", "Working translation")
    page.click("#card-next-form button[type='submit']")
    page.wait_for_load_state("networkidle")

    # Phase 3: Digestion
    assert "digestion" in page.locator(".card-phase-label").inner_text().lower()
    page.fill("#card-response", "Meditation notes")
    page.click("#card-next-form button[type='submit']")
    page.wait_for_load_state("networkidle")

    # Phase 4: Study Bibles (no textarea)
    assert "study bible" in page.locator(".card-phase-label").inner_text().lower()
    page.click("#card-next-form button[type='submit']")
    page.wait_for_load_state("networkidle")

    # Should be in conversation mode
    assert page.locator("#conversation-column").count() > 0


def test_card_autosave(page, base_url):
    """Textarea content auto-saves and persists across page reload."""
    create_session(page, base_url, "Romans 1:24-32")

    # Set up response listener BEFORE triggering the input (avoids race condition)
    with page.expect_response("**/card/autosave", timeout=5000) as resp_info:
        page.fill("#card-response", "Autosave test content here")
        # Wait for debounce (1500ms) + network round-trip
        page.wait_for_timeout(2500)
    response = resp_info.value
    assert response.status == 200

    # Reload and check content persisted
    page.reload()
    page.wait_for_load_state("networkidle")
    assert "Autosave test content here" in page.locator("#card-response").input_value()


def test_read_translate_greek_text(page, base_url):
    """Read & Translate phase shows THGNT Greek text with clickable words."""
    create_session(page, base_url, "Romans 1:24-32")

    # Advance to read_translate
    page.fill("#card-response", "prayer")
    page.click("#card-next-form button[type='submit']")
    page.wait_for_load_state("networkidle")

    # Check THGNT label (use .first — side_by_side layout has two .card-resource-label)
    assert "THGNT" in page.locator(".card-resource-label").first.inner_text()

    # Check clickable Greek words exist
    words = page.locator(".clickable-word")
    assert words.count() >= 10, f"Expected >=10 clickable words, got {words.count()}"

    # Verify first word contains Greek characters
    first_word = words.first.inner_text()
    assert any("\u0370" <= c <= "\u03FF" or "\u1F00" <= c <= "\u1FFF" for c in first_word), \
        f"First clickable word '{first_word}' doesn't contain Greek characters"


# ── Word Click Popup ──────────────────────────────────────────────────────


def _go_to_read_translate(page, base_url):
    """Helper: create session and advance to read_translate phase."""
    create_session(page, base_url, "Romans 1:24-32")
    page.fill("#card-response", "prayer")
    page.click("#card-next-form button[type='submit']")
    page.wait_for_load_state("networkidle")


def test_word_popup_shows_parsing(page, base_url):
    """Click a Greek word — popup shows lemma, gloss, parsing."""
    _go_to_read_translate(page, base_url)

    # Click first clickable word
    word_el = page.locator(".clickable-word").first
    word_text = word_el.inner_text()
    word_el.click()

    # Wait for popup to appear with real data (not "loading...")
    popup = page.locator(".word-popup")
    popup.wait_for(state="visible", timeout=10000)

    # Wait for content to load (lemma changes from "..." to real text)
    page.wait_for_function(
        """() => {
            var lemma = document.querySelector('.wp-lemma');
            return lemma && lemma.textContent !== '...' && lemma.textContent !== '';
        }""",
        timeout=10000,
    )

    lemma = page.locator(".wp-lemma").inner_text()
    gloss = page.locator(".wp-gloss").inner_text()
    parsing = page.locator(".wp-parsing").inner_text()

    assert lemma, "Lemma should not be empty"
    assert gloss not in ("loading...", "error", "lookup failed"), \
        f"Gloss should be a real value, got '{gloss}'"
    # Gloss can be empty for some words without BDAG entries
    assert parsing, "Parsing should not be empty"


def test_word_popup_dismisses(page, base_url):
    """Click elsewhere dismisses the word popup."""
    _go_to_read_translate(page, base_url)

    # Open popup
    page.locator(".clickable-word").first.click()
    page.locator(".word-popup").wait_for(state="visible", timeout=10000)
    assert page.locator(".word-popup").count() == 1

    # Click on the card prompt area (outside popup and word)
    page.locator(".card-prompt").click()
    page.wait_for_timeout(500)

    assert page.locator(".word-popup").count() == 0, "Popup should dismiss on outside click"


# ── Study Bible Phase ─────────────────────────────────────────────────────


def _go_to_study_bibles(page, base_url):
    """Helper: create session and advance to study_bibles phase."""
    create_session(page, base_url, "Romans 1:24-32")
    # Prayer
    page.fill("#card-response", "prayer")
    page.click("#card-next-form button[type='submit']")
    page.wait_for_load_state("networkidle")
    # Read & Translate
    page.fill("#card-response", "translation")
    page.click("#card-next-form button[type='submit']")
    page.wait_for_load_state("networkidle")
    # Digestion
    page.fill("#card-response", "meditation")
    page.click("#card-next-form button[type='submit']")
    page.wait_for_load_state("networkidle")
    # Now on study_bibles


def test_study_bible_tabs(page, base_url):
    """Tab switching between study bibles works."""
    _go_to_study_bibles(page, base_url)

    tabs = page.locator(".sb-tab")
    panels = page.locator(".sb-panel")

    assert tabs.count() >= 2, f"Expected >=2 study bible tabs, got {tabs.count()}"

    # First tab should be active, first panel visible
    assert "active" in tabs.first.get_attribute("class")
    assert "active" in panels.first.get_attribute("class")

    # Click second tab
    tabs.nth(1).click()
    page.wait_for_timeout(300)

    # Second panel should now be active
    assert "active" in tabs.nth(1).get_attribute("class")
    assert "active" in panels.nth(1).get_attribute("class")
    # First panel should no longer be active
    assert "active" not in panels.first.get_attribute("class")


def test_star_annotation(page, base_url):
    """Select text in study bible, star it, verify it persists after reload."""
    _go_to_study_bibles(page, base_url)

    # Set up dialog handler for the prompt("Add a note:")
    page.on("dialog", lambda dialog: dialog.accept("Test annotation note"))

    sb_text = page.locator(".sb-text").first
    sb_text.wait_for(state="visible", timeout=10000)

    # Programmatically select text and trigger mouseup (triple-click is unreliable)
    page.evaluate("""() => {
        var el = document.querySelector('.sb-text');
        var range = document.createRange();
        // Select the first 30 chars of the first text node
        var walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
        var textNode = walker.nextNode();
        if (!textNode) return;
        var end = Math.min(textNode.length, 30);
        range.setStart(textNode, 0);
        range.setEnd(textNode, end);
        var sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(range);
        // Dispatch mouseup to trigger star popup
        el.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
    }""")

    # Wait for star popup
    star = page.locator("#star-popup")
    star.wait_for(state="visible", timeout=5000)

    # Click star (uses mousedown handler)
    star.dispatch_event("mousedown")
    page.wait_for_load_state("networkidle")

    # Reload and check annotation persisted
    page.reload()
    page.wait_for_load_state("networkidle")

    stars = page.locator(".sb-star-item")
    assert stars.count() > 0, "Expected at least one starred annotation after reload"


# ── Outline Sidebar ───────────────────────────────────────────────────────


def test_outline_add_note(page, base_url):
    """Add a note to the outline sidebar."""
    create_session(page, base_url, "Romans 1:24-32")

    # Select node type and type note text
    page.select_option("#outline-add-type", "main_point")
    page.fill("#outline-add-input", "Test main point")
    page.keyboard.press("Enter")

    # Wait for outline to refresh
    page.wait_for_timeout(1000)

    nodes = page.locator(".outline-node")
    assert nodes.count() > 0, "Expected at least one outline node"
    assert "Test main point" in page.locator("#outline-tree-container").inner_text()


def test_outline_delete_note(page, base_url):
    """Delete a note from the outline sidebar."""
    create_session(page, base_url, "Romans 1:24-32")

    # Add a note first
    page.select_option("#outline-add-type", "note")
    page.fill("#outline-add-input", "Note to delete")
    page.keyboard.press("Enter")
    page.wait_for_timeout(1000)

    initial_count = page.locator(".outline-node").count()
    assert initial_count > 0

    # Delete button is hidden until hover — use dispatch_event to bypass visibility
    del_btn = page.locator(".outline-node").first.locator("button.del")
    del_btn.dispatch_event("click")
    page.wait_for_timeout(1000)

    final_count = page.locator(".outline-node").count()
    assert final_count < initial_count, \
        f"Expected node count to decrease: {initial_count} -> {final_count}"


# ── Timer ─────────────────────────────────────────────────────────────────


def test_session_clock(page, base_url):
    """Clock displays, increments, and toggles pause."""
    create_session(page, base_url, "Romans 1:24-32")

    clock = page.locator("#session-clock")
    clock.wait_for(state="visible")

    # Get initial value
    initial = clock.inner_text()

    # Wait for clock to tick
    page.wait_for_timeout(2500)
    after_tick = clock.inner_text()

    # Clock should have changed (either seconds or minutes format)
    # Note: might still show "0m" if < 1 minute, so check the internal counter
    elapsed = page.evaluate("() => window.studyClock ? studyClock.elapsed : -1")
    assert elapsed > 0, f"Clock should have elapsed time > 0, got {elapsed}"

    # Pause
    clock.click()
    page.wait_for_timeout(500)
    paused_value = page.evaluate("() => window.studyClock ? studyClock.elapsed : -1")

    page.wait_for_timeout(2000)
    still_paused = page.evaluate("() => window.studyClock ? studyClock.elapsed : -1")

    # Elapsed should not have changed significantly while paused (allow 1s tolerance)
    assert abs(still_paused - paused_value) <= 1, \
        f"Clock should be paused: {paused_value} -> {still_paused}"

    # Resume
    clock.click()
    page.wait_for_timeout(2500)
    after_resume = page.evaluate("() => window.studyClock ? studyClock.elapsed : -1")
    assert after_resume > still_paused, \
        f"Clock should resume: {still_paused} -> {after_resume}"


# ── Conversation + Tool Tests ─────────────────────────────────────────────

needs_api_key = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set — skipping tool tests",
)


@needs_api_key
@pytest.mark.tools
def test_tool_read_bible(page, base_url):
    """Conversation triggers read_bible_passage tool with real data."""
    advance_to_conversation(page, base_url)
    send_message_and_wait(page, "Read Romans 1:24 in THGNT and ESV. Use the read_bible_passage tool.")

    results = get_tool_results(page)
    tool_names = [r["name"] for r in results]
    assert any("Bible" in n or "bible" in n.lower() for n in tool_names), \
        f"Expected Bible tool result, got tools: {tool_names}"

    # Response should contain Greek characters (from THGNT)
    full_text = page.locator("#conversation-thread").inner_text()
    assert any("\u0370" <= c <= "\u03FF" or "\u1F00" <= c <= "\u1FFF" for c in full_text), \
        "Expected Greek characters in response from THGNT"


@needs_api_key
@pytest.mark.tools
def test_tool_commentary(page, base_url):
    """Conversation triggers find_commentary_paragraph tool."""
    advance_to_conversation(page, base_url)
    send_message_and_wait(page, "What do the commentaries say about Romans 1:24? Use find_commentary_paragraph.")

    results = get_tool_results(page)
    tool_names = [r["name"] for r in results]
    assert any("commentar" in n.lower() for n in tool_names), \
        f"Expected commentary tool result, got tools: {tool_names}"

    # Verify the assistant produced a substantive response about the commentary
    full_text = page.locator("#conversation-thread").inner_text()
    assert len(full_text) > 100, f"Expected substantive commentary response, got {len(full_text)} chars"


@needs_api_key
@pytest.mark.tools
def test_tool_lexicon(page, base_url):
    """Conversation triggers lookup_lexicon tool with BDAG."""
    advance_to_conversation(page, base_url)
    send_message_and_wait(page, "Look up παρέδωκεν in BDAG using the lookup_lexicon tool.")

    results = get_tool_results(page)
    tool_names = [r["name"] for r in results]
    assert any("lexicon" in n.lower() for n in tool_names), \
        f"Expected lexicon tool result, got tools: {tool_names}"


@needs_api_key
@pytest.mark.tools
def test_tool_grammar(page, base_url):
    """Conversation triggers lookup_grammar tool."""
    advance_to_conversation(page, base_url)
    send_message_and_wait(page, "Check Wallace's grammar on the aorist indicative using lookup_grammar.")

    results = get_tool_results(page)
    tool_names = [r["name"] for r in results]
    assert any("grammar" in n.lower() for n in tool_names), \
        f"Expected grammar tool result, got tools: {tool_names}"


@needs_api_key
@pytest.mark.tools
def test_tool_word_study(page, base_url):
    """Conversation triggers word_study_lookup tool."""
    advance_to_conversation(page, base_url)
    send_message_and_wait(page, "What is the morphology of παρέδωκεν in Romans 1:24? Use word_study_lookup.")

    results = get_tool_results(page)
    tool_names = [r["name"] for r in results]
    assert any("interlinear" in n.lower() for n in tool_names), \
        f"Expected interlinear tool result, got tools: {tool_names}"


@needs_api_key
@pytest.mark.tools
def test_tool_cross_references(page, base_url):
    """Conversation triggers expand_cross_references tool."""
    advance_to_conversation(page, base_url)
    send_message_and_wait(page, "Get cross-references for Romans 1:24 using expand_cross_references.")

    results = get_tool_results(page)
    tool_names = [r["name"] for r in results]
    assert any("cross" in n.lower() or "ref" in n.lower() for n in tool_names), \
        f"Expected cross-references tool result, got tools: {tool_names}"


@needs_api_key
@pytest.mark.tools
def test_tool_save_outline(page, base_url):
    """Conversation triggers save_to_outline tool."""
    advance_to_conversation(page, base_url)

    initial_nodes = page.locator(".outline-node").count()

    send_message_and_wait(
        page,
        "Save this as a main point in the outline using save_to_outline: "
        "God gave them over to the sinful desires of their hearts"
    )

    # save_to_outline renders as .insight-pill, and outline refreshes
    page.wait_for_timeout(2000)  # wait for outline refresh

    results = get_tool_results(page)
    has_outline_tool = any("outline" in r["name"].lower() or "saving" in r["name"].lower()
                          for r in results)
    new_nodes = page.locator(".outline-node").count()

    # Either tool result appeared OR outline grew (Claude may save without showing pill)
    assert has_outline_tool or new_nodes > initial_nodes, \
        f"Expected outline save: tool results={[r['name'] for r in results]}, " \
        f"nodes {initial_nodes}->{new_nodes}"


@needs_api_key
@pytest.mark.tools
def test_tool_datasets(page, base_url):
    """Conversation triggers dataset/context tools."""
    advance_to_conversation(page, base_url)
    send_message_and_wait(
        page,
        "What ancient literature or cultural context relates to idolatry in Romans 1:24-25? "
        "Use get_passage_context or get_passage_data tools."
    )

    results = get_tool_results(page)
    assert len(results) > 0, "Expected at least one tool result for dataset query"

    # Response should have substantive content
    full_text = page.locator("#conversation-thread").inner_text()
    assert len(full_text) > 100, f"Expected substantive response, got {len(full_text)} chars"
