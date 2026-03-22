import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from genre_map import get_genre

def test_epistle():
    assert get_genre(66) == 'epistle'   # Romans
    assert get_genre(70) == 'epistle'   # Ephesians

def test_narrative():
    assert get_genre(1) == 'narrative'   # Genesis
    assert get_genre(9) == 'narrative'   # 1 Samuel
    assert get_genre(63) == 'narrative'  # Luke
    assert get_genre(64) == 'narrative'  # John (Gospel)

def test_poetry():
    assert get_genre(19) == 'poetry'     # Psalms
    assert get_genre(22) == 'poetry'     # Song of Solomon

def test_prophecy():
    assert get_genre(23) == 'prophecy'   # Isaiah

def test_apocalyptic():
    assert get_genre(27) == 'apocalyptic' # Daniel

def test_law():
    assert get_genre(3) == 'law'         # Leviticus

def test_wisdom():
    assert get_genre(20) == 'wisdom'     # Proverbs
    assert get_genre(21) == 'wisdom'     # Ecclesiastes
