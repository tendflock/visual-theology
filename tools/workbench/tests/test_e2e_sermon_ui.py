"""Minimal Playwright tests for the sermon review UI.

Requires: playwright, pytest-playwright. Server must be running on http://localhost:5111.
Marked @pytest.mark.e2e to skip in normal runs.
"""
import pytest

pytest.importorskip('playwright')


BASE_URL = 'http://localhost:5111'


@pytest.mark.e2e
def test_sermons_list_loads():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f'{BASE_URL}/sermons/')
        assert page.title().lower().startswith('sermon')
        browser.close()


@pytest.mark.e2e
def test_sermon_detail_renders_four_cards_when_review_ready():
    """Requires a seeded sermon with a review."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f'{BASE_URL}/sermons/1')
        if page.locator('text=Impact').is_visible():
            assert page.locator('text=Faithfulness').is_visible()
            assert page.locator('text=Diagnostic').is_visible()
            assert page.locator('text=For Next Sunday').is_visible()
        browser.close()
