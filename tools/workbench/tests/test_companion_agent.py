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


def test_build_study_prompt_includes_16_steps():
    """System prompt should reference the 16-step workflow phases."""
    from companion_agent import build_study_prompt
    prompt = build_study_prompt("Romans 1:1-7", "epistle", 1800)
    assert "FCF" in prompt or "Fallen Condition" in prompt
    assert "EP" in prompt or "Exegetical Point" in prompt
    assert "HP" in prompt or "Homiletical Point" in prompt
    assert "THT" in prompt or "Take Home Truth" in prompt


def test_build_study_prompt_includes_card_summary():
    """System prompt should incorporate Bryan's card-phase work."""
    from companion_agent import build_study_prompt
    card_summary = "[prayer] Lord, open my eyes\n[translation] Paul, slave of Christ Jesus..."
    prompt = build_study_prompt("Romans 1:1-7", "epistle", 3600,
                                card_work_summary=card_summary)
    assert "slave of Christ Jesus" in prompt
