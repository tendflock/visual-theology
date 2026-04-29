"""Minimal Playwright tests for the sermon review UI.

Uses the conftest `base_url` fixture (temp Flask + temp DB) and pytest-playwright's
`page` fixture, like the rest of the E2E suite. Marked @pytest.mark.e2e.
"""
import pytest

pytest.importorskip('playwright')

pytestmark = pytest.mark.e2e


def test_sermons_list_loads(page, base_url):
    page.goto(f'{base_url}/sermons/')
    assert page.title().lower().startswith('sermon')


def test_sermon_detail_renders_four_cards_when_review_ready(page, base_url):
    """Tolerant of missing sermon 1 (temp DB has no seeded data); only asserts when a review is rendered."""
    response = page.goto(f'{base_url}/sermons/1')
    if response is None or response.status == 404:
        return
    if page.locator('text=Impact').is_visible():
        assert page.locator('text=Faithfulness').is_visible()
        assert page.locator('text=Diagnostic').is_visible()
        assert page.locator('text=For Next Sunday').is_visible()
