import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from voice_constants import IDENTITY_CORE, HOMILETICAL_TRADITION, VOICE_GUARDRAILS


# Override pytest-base-url's autouse _verify_url fixture so these pure-import
# tests don't trigger conftest.py's Flask-server `base_url` fixture (which
# hard-exits if port 5111 is in use).
@pytest.fixture(scope="session", autouse=True)
def _verify_url():
    yield


def test_constants_are_non_empty_strings():
    for name, value in [
        ('IDENTITY_CORE', IDENTITY_CORE),
        ('HOMILETICAL_TRADITION', HOMILETICAL_TRADITION),
        ('VOICE_GUARDRAILS', VOICE_GUARDRAILS),
    ]:
        assert isinstance(value, str), f"{name} should be str, got {type(value).__name__}"
        assert len(value.strip()) > 50, f"{name} is too short to be a real prompt section"


def test_identity_names_the_tradition():
    assert 'Reformed' in IDENTITY_CORE or 'Presbyterian' in IDENTITY_CORE


def test_homiletical_tradition_cites_chapell_and_robinson():
    assert 'Chapell' in HOMILETICAL_TRADITION
    assert 'Robinson' in HOMILETICAL_TRADITION


def test_voice_guardrails_mention_study_partner():
    assert 'study partner' in VOICE_GUARDRAILS.lower() or 'partner' in VOICE_GUARDRAILS.lower()
