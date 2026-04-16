import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from llm_client import LLMClient, CannedLLMClient, AnthropicClient


@pytest.fixture(scope="session", autouse=True)
def _verify_url():
    yield


def test_canned_client_returns_fixture_on_match():
    canned = {'hello': {'result': 'world'}}
    client = CannedLLMClient(canned)
    result = client.call(prompt='hello', schema={})
    assert result == {'result': 'world'}


def test_canned_client_returns_error_on_miss():
    client = CannedLLMClient({})
    result = client.call(prompt='unseen', schema={})
    assert 'error' in result


def test_canned_client_hashes_long_prompts():
    canned = {}
    client = CannedLLMClient(canned)
    import hashlib
    long_prompt = 'x' * 5000
    key = hashlib.sha256(long_prompt.encode()).hexdigest()[:16]
    client.fixtures[key] = {'ok': True}
    assert client.call(prompt=long_prompt, schema={}) == {'ok': True}


def test_llm_client_is_a_protocol():
    assert hasattr(AnthropicClient, 'call')


def test_anthropic_client_defaults_to_opus_4_6():
    client = AnthropicClient(api_key='fake-key-for-test')
    assert client.model == 'claude-opus-4-6'
