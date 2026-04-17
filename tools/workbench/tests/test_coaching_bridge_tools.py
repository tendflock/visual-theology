import os, sys, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from companion_tools import TOOL_DEFINITIONS

@pytest.fixture(scope="session", autouse=True)
def _verify_url():
    yield

COACHING_TOOL_NAMES = {'get_active_commitment', 'get_sermon_patterns', 'get_representative_moments', 'get_counterexamples', 'get_coaching_insights'}

def test_coaching_tools_present_in_definitions():
    tool_names = {t['name'] for t in TOOL_DEFINITIONS}
    for name in COACHING_TOOL_NAMES:
        assert name in tool_names, f"Missing: {name}"

def test_coaching_tools_have_required_fields():
    for tool in TOOL_DEFINITIONS:
        if tool['name'] in COACHING_TOOL_NAMES:
            assert 'description' in tool
            assert 'input_schema' in tool
            assert tool['input_schema'].get('type') == 'object'
