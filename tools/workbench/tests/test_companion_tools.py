import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from companion_tools import TOOL_DEFINITIONS, get_tool_names

def test_tool_definitions_exist():
    names = get_tool_names()
    assert 'read_bible_passage' in names
    assert 'find_commentary_paragraph' in names
    assert 'word_study_lookup' in names
    assert 'expand_cross_references' in names

def test_tool_definitions_have_required_fields():
    for tool in TOOL_DEFINITIONS:
        assert 'name' in tool
        assert 'description' in tool
        assert 'input_schema' in tool
