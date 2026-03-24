"""
E2E test fixtures — boots Flask server as subprocess, provides Playwright helpers.
"""

import os
import signal
import socket
import subprocess
import sys
import tempfile
import time

import pytest
import requests


def _free_port():
    """Find a free TCP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _port_in_use(port):
    """Check if a port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


@pytest.fixture(scope="session")
def base_url():
    """Start Flask server as subprocess, yield base URL, kill on teardown."""

    # Safety: warn if dev server is running (LogosReader native lib contention)
    if _port_in_use(5111):
        pytest.exit(
            "Port 5111 is in use (dev server running?). "
            "Stop it before running E2E tests — LogosReader native lib cannot be shared.",
            returncode=1,
        )

    # Create temp DB
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    db_path = tmp.name

    port = _free_port()
    app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    app_py = os.path.join(app_dir, "app.py")

    env = os.environ.copy()
    env["COMPANION_DB_PATH"] = db_path
    env["FLASK_PORT"] = str(port)
    env["PATH"] = "/opt/homebrew/opt/dotnet@8/bin:" + env.get("PATH", "")
    env["DOTNET_ROOT"] = "/opt/homebrew/opt/dotnet@8/libexec"

    # Start server in its own process group for clean teardown
    proc = subprocess.Popen(
        [sys.executable, app_py],
        cwd=app_dir,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid,
    )

    url = f"http://127.0.0.1:{port}"

    # Health check — wait up to 15s for server to be ready
    deadline = time.time() + 15
    while time.time() < deadline:
        try:
            r = requests.get(f"{url}/study/", timeout=2)
            if r.status_code == 200:
                break
        except requests.ConnectionError:
            pass
        time.sleep(0.5)
    else:
        # Server didn't start — dump stderr and fail
        proc.terminate()
        _, stderr = proc.communicate(timeout=5)
        pytest.exit(
            f"Flask server failed to start on port {port}.\n"
            f"stderr: {stderr.decode()[-2000:]}",
            returncode=1,
        )

    yield url

    # Teardown: kill entire process group (Flask + LogosReader grandchild)
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        proc.wait(timeout=5)
    except (ProcessLookupError, subprocess.TimeoutExpired):
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except ProcessLookupError:
            pass

    # Clean up temp DB
    try:
        os.unlink(db_path)
    except FileNotFoundError:
        pass


def create_session(page, base_url, passage="Romans 1:24-32"):
    """Create a study session and return the session URL."""
    page.goto(f"{base_url}/study/")
    page.fill('input[name="passage"]', passage)
    page.click('button[type="submit"], .btn-primary')
    page.wait_for_url("**/study/session/*")
    return page.url


def advance_to_conversation(page, base_url, passage="Romans 1:24-32"):
    """Create session and click through all 4 card phases to reach conversation mode.

    Phase behavior:
    - prayer (has textarea): fills text, clicks Next
    - read_translate (has textarea): fills text, clicks Next
    - digestion (has textarea): fills text, clicks Next
    - study_bibles (no textarea): just clicks Next
    """
    create_session(page, base_url, passage)

    # Phase 1: Prayer (has textarea)
    page.fill("#card-response", "Lord, open my eyes to this passage.")
    page.click("#card-next-form button[type='submit']")
    page.wait_for_load_state("networkidle")

    # Phase 2: Read & Translate (has textarea)
    page.fill("#card-response", "Working translation of the passage.")
    page.click("#card-next-form button[type='submit']")
    page.wait_for_load_state("networkidle")

    # Phase 3: Digestion (has textarea)
    page.fill("#card-response", "Meditation notes on the text.")
    page.click("#card-next-form button[type='submit']")
    page.wait_for_load_state("networkidle")

    # Phase 4: Study Bibles (no textarea, just Next)
    page.click("#card-next-form button[type='submit']")
    page.wait_for_load_state("networkidle")

    # Should now be in conversation mode
    assert page.locator("#conversation-column").count() > 0, \
        "Expected conversation mode after advancing through all card phases"

    return page.url


def send_message_and_wait(page, message, timeout=90000):
    """Type a message, send it, wait for assistant response to finish streaming.

    Returns the last .conv-message.assistant element.
    """
    page.fill("#study-input", message)
    page.click("#btn-study-send")

    # Wait for send button to re-enable (streaming finished)
    page.wait_for_function(
        "() => !document.getElementById('btn-study-send').disabled",
        timeout=timeout,
    )

    # Get last assistant message
    msgs = page.locator(".conv-message.assistant")
    assert msgs.count() > 0, "No assistant message appeared"
    last_msg = msgs.last

    # Check for error indicators
    content = last_msg.inner_text()
    assert "[Error" not in content, f"Response contained error: {content[:200]}"
    assert "[Connection error" not in content, f"Response contained connection error: {content[:200]}"

    return last_msg


def get_tool_results(page):
    """Get all tool results from conversation thread.

    Returns list of dicts: {"name": "Bible", "body": "..."}.
    Also checks .insight-pill elements (used by save_to_outline).
    """
    results = []

    # Standard tool results (collapsible <details>)
    tool_els = page.locator(".conv-tool-result")
    for i in range(tool_els.count()):
        el = tool_els.nth(i)
        summary = el.locator("summary")
        body = el.locator(".tool-body")
        results.append({
            "name": summary.inner_text() if summary.count() > 0 else "",
            "body": body.inner_text() if body.count() > 0 else "",
        })

    # Insight pills (save_to_outline renders these instead)
    pills = page.locator(".insight-pill")
    for i in range(pills.count()):
        results.append({
            "name": "saving to outline",
            "body": pills.nth(i).inner_text(),
        })

    return results
