import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from study import clean_bible_text

def test_strips_crossref_markers():
    text = "For \ufeffhGod so loved \ufeffithe world"
    result = clean_bible_text(text)
    assert '[h]' not in result
    assert '\ufeff' not in result
    assert 'God so loved' in result
    assert 'the world' in result

def test_strips_footnote_markers():
    text = "gave his only Son\ufeff9"
    result = clean_bible_text(text)
    assert '[fn9]' not in result
    assert '\ufeff' not in result
    assert 'gave his only Son' in result

def test_preserves_verse_numbers():
    text = "16 For God so loved the world"
    result = clean_bible_text(text)
    assert '16' in result

def test_clean_text_no_markers():
    text = "The Lord is my shepherd"
    result = clean_bible_text(text)
    assert result == "The Lord is my shepherd"
