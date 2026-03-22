import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from companion_agent import build_system_prompt

def test_system_prompt_includes_identity():
    prompt = build_system_prompt(
        phase='text_work', passage='Romans 1:18-23', genre='epistle',
        timer_remaining=3600, card_responses=[], outline_summary='',
        conversation_summary=''
    )
    assert 'Reformed' in prompt
    assert 'study partner' in prompt.lower() or 'companion' in prompt.lower()

def test_system_prompt_includes_phase():
    prompt = build_system_prompt(
        phase='text_work', passage='Romans 1:18-23', genre='epistle',
        timer_remaining=3600, card_responses=[], outline_summary='',
        conversation_summary=''
    )
    assert 'text' in prompt.lower() or 'translation' in prompt.lower()

def test_system_prompt_includes_homiletical_guardrails():
    prompt = build_system_prompt(
        phase='sermon_construction', passage='Romans 1:18-23', genre='epistle',
        timer_remaining=3600, card_responses=[], outline_summary='',
        conversation_summary=''
    )
    assert 'so what' in prompt.lower() or 'So What' in prompt
    assert 'Christ' in prompt
    assert 'wife' in prompt.lower() or 'congregation' in prompt.lower()

def test_system_prompt_includes_timer():
    prompt = build_system_prompt(
        phase='text_work', passage='Romans 1:18-23', genre='epistle',
        timer_remaining=1200, card_responses=[], outline_summary='',
        conversation_summary=''
    )
    assert '20 minutes' in prompt or '1200' in prompt
