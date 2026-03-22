"""
genre_map.py — Maps Logos Bible book numbers to genre tags.

Book numbers follow Logos convention:
  1=Gen, 2=Exo, ..., 39=Mal, (gap for deuterocanon), 61=Matt, ..., 87=Rev

7 genres: narrative, law, poetry, wisdom, prophecy, apocalyptic, epistle
"""

GENRE_MAP = {
    1: 'narrative',    # Genesis
    2: 'narrative',    # Exodus
    3: 'law',          # Leviticus
    4: 'narrative',    # Numbers
    5: 'law',          # Deuteronomy
    6: 'narrative',    # Joshua
    7: 'narrative',    # Judges
    8: 'narrative',    # Ruth
    9: 'narrative',    # 1 Samuel
    10: 'narrative',   # 2 Samuel
    11: 'narrative',   # 1 Kings
    12: 'narrative',   # 2 Kings
    13: 'narrative',   # 1 Chronicles
    14: 'narrative',   # 2 Chronicles
    15: 'narrative',   # Ezra
    16: 'narrative',   # Nehemiah
    17: 'narrative',   # Esther
    18: 'poetry',      # Job
    19: 'poetry',      # Psalms
    20: 'wisdom',      # Proverbs
    21: 'wisdom',      # Ecclesiastes
    22: 'poetry',      # Song of Solomon
    23: 'prophecy',    # Isaiah
    24: 'prophecy',    # Jeremiah
    25: 'poetry',      # Lamentations
    26: 'prophecy',    # Ezekiel
    27: 'apocalyptic', # Daniel
    28: 'prophecy',    # Hosea
    29: 'prophecy',    # Joel
    30: 'prophecy',    # Amos
    31: 'prophecy',    # Obadiah
    32: 'narrative',   # Jonah
    33: 'prophecy',    # Micah
    34: 'prophecy',    # Nahum
    35: 'prophecy',    # Habakkuk
    36: 'prophecy',    # Zephaniah
    37: 'prophecy',    # Haggai
    38: 'prophecy',    # Zechariah
    39: 'prophecy',    # Malachi
    61: 'narrative',   # Matthew
    62: 'narrative',   # Mark
    63: 'narrative',   # Luke
    64: 'narrative',   # John
    65: 'narrative',   # Acts
    66: 'epistle',     # Romans
    67: 'epistle',     # 1 Corinthians
    68: 'epistle',     # 2 Corinthians
    69: 'epistle',     # Galatians
    70: 'epistle',     # Ephesians
    71: 'epistle',     # Philippians
    72: 'epistle',     # Colossians
    73: 'epistle',     # 1 Thessalonians
    74: 'epistle',     # 2 Thessalonians
    75: 'epistle',     # 1 Timothy
    76: 'epistle',     # 2 Timothy
    77: 'epistle',     # Titus
    78: 'epistle',     # Philemon
    79: 'epistle',     # Hebrews
    80: 'epistle',     # James
    81: 'epistle',     # 1 Peter
    82: 'epistle',     # 2 Peter
    83: 'epistle',     # 1 John
    84: 'epistle',     # 2 John
    85: 'epistle',     # 3 John
    86: 'epistle',     # Jude
    87: 'apocalyptic', # Revelation
}


def get_genre(book_num):
    """Return genre tag for a book number. Defaults to 'narrative' if unknown."""
    return GENRE_MAP.get(book_num, 'narrative')
