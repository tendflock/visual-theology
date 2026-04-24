#!/usr/bin/env python3
"""
Logos Bible Study Builder
Extracts and compiles study material from a Logos 4 library.

Usage:
    python3 study.py "John 3:16-18"
    python3 study.py "Romans 8:1-11" --bibles ESV,NASB,KJV --commentaries 5
    python3 study.py "Genesis 1:1-3" --all
    python3 study.py --list-bibles
    python3 study.py --list-commentaries "John"
"""

import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

# Batch reader and cache (optional; fall back to run_reader if unavailable)
try:
    from logos_batch import LogosBatchReader
except ImportError:
    LogosBatchReader = None

try:
    from logos_cache import LogosCache
except ImportError:
    LogosCache = None

# ── Configuration ──────────────────────────────────────────────────────────

LOGOS_DATA = "/Volumes/External/Logos4/Data/e3txalek.5iq"
CATALOG_DB = f"{LOGOS_DATA}/LibraryCatalog/catalog.db"
RESOURCE_MGR_DB = f"{LOGOS_DATA}/ResourceManager/ResourceManager.db"
RESOURCES_DIR = f"{LOGOS_DATA}/ResourceManager/Resources"
READER_DIR = "/Volumes/External/Logos4/tools/LogosReader"

DOTNET_ENV = {
    **os.environ,
    "PATH": f"/opt/homebrew/opt/dotnet@8/bin:/usr/bin:/bin:{os.environ.get('PATH', '')}",
    "DOTNET_ROOT": "/opt/homebrew/opt/dotnet@8/libexec",
}

# Old path prefix stored in ResourceManager.db → actual path
PATH_REMAP = (
    "/Users/family/Library/Application Support/Logos4/",
    "/Volumes/External/Logos4/",
)

# ── Batch Reader Singleton ────────────────────────────────────────────────

_batch_reader = None


def init_batch_reader():
    """Initialize the module-level batch reader singleton.

    Safe to call multiple times; subsequent calls are no-ops if already alive.
    Returns True if the batch reader is available.
    """
    global _batch_reader
    if _batch_reader is not None and _batch_reader.is_alive():
        return True
    if LogosBatchReader is None:
        return False
    try:
        print("  Starting batch reader...", file=sys.stderr)
        _batch_reader = LogosBatchReader()
        print("  Batch reader ready.", file=sys.stderr)
        return True
    except Exception as e:
        print(f"  Batch reader unavailable ({e}), using subprocess mode.", file=sys.stderr)
        _batch_reader = None
        return False


def shutdown_batch_reader():
    """Shut down the module-level batch reader singleton."""
    global _batch_reader
    if _batch_reader is not None:
        try:
            _batch_reader.close()
        except Exception:
            pass
        _batch_reader = None


# ── Cache Singleton ───────────────────────────────────────────────────────

_logos_cache = None

def _get_logos_cache():
    """Get or create the LogosCache singleton."""
    global _logos_cache
    if _logos_cache is not None:
        return _logos_cache
    cache_cls = LogosCache
    if cache_cls is None:
        try:
            # Ensure tools directory is on sys.path for sibling imports
            _tools_dir = str(Path(__file__).parent)
            if _tools_dir not in sys.path:
                sys.path.insert(0, _tools_dir)
            from logos_cache import LogosCache as _LC
            cache_cls = _LC
        except ImportError:
            return None
    try:
        _logos_cache = cache_cls()
        return _logos_cache
    except Exception:
        return None


# ── Bible Book Mapping ─────────────────────────────────────────────────────

BOOK_NAMES = {
    # OT
    "genesis": 1, "gen": 1, "ge": 1,
    "exodus": 2, "exod": 2, "ex": 2,
    "leviticus": 3, "lev": 3, "le": 3,
    "numbers": 4, "num": 4, "nu": 4,
    "deuteronomy": 5, "deut": 5, "dt": 5, "de": 5,
    "joshua": 6, "josh": 6, "jos": 6,
    "judges": 7, "judg": 7, "jdg": 7,
    "ruth": 8, "ru": 8,
    "1 samuel": 9, "1samuel": 9, "1sam": 9, "1sa": 9,
    "2 samuel": 10, "2samuel": 10, "2sam": 10, "2sa": 10,
    "1 kings": 11, "1kings": 11, "1ki": 11, "1kgs": 11,
    "2 kings": 12, "2kings": 12, "2ki": 12, "2kgs": 12,
    "1 chronicles": 13, "1chronicles": 13, "1chr": 13, "1ch": 13,
    "2 chronicles": 14, "2chronicles": 14, "2chr": 14, "2ch": 14,
    "ezra": 15, "ezr": 15,
    "nehemiah": 16, "neh": 16, "ne": 16,
    "esther": 17, "est": 17, "es": 17,
    "job": 18, "jb": 18,
    "psalms": 19, "psalm": 19, "ps": 19, "psa": 19,
    "proverbs": 20, "prov": 20, "pr": 20,
    "ecclesiastes": 21, "eccl": 21, "ecc": 21, "ec": 21,
    "song of solomon": 22, "song": 22, "sos": 22, "ss": 22,
    "isaiah": 23, "isa": 23, "is": 23,
    "jeremiah": 24, "jer": 24, "je": 24,
    "lamentations": 25, "lam": 25, "la": 25,
    "ezekiel": 26, "ezek": 26, "eze": 26,
    "daniel": 27, "dan": 27, "da": 27,
    "hosea": 28, "hos": 28, "ho": 28,
    "joel": 29, "joe": 29, "jl": 29,
    "amos": 30, "am": 30,
    "obadiah": 31, "obad": 31, "ob": 31,
    "jonah": 32, "jon": 32, "jnh": 32,
    "micah": 33, "mic": 33,
    "nahum": 34, "nah": 34, "na": 34,
    "habakkuk": 35, "hab": 35,
    "zephaniah": 36, "zeph": 36, "zep": 36,
    "haggai": 37, "hag": 37,
    "zechariah": 38, "zech": 38, "zec": 38,
    "malachi": 39, "mal": 39,
    # NT
    "matthew": 61, "matt": 61, "mt": 61, "mat": 61,
    "mark": 62, "mk": 62, "mr": 62,
    "luke": 63, "lk": 63, "lu": 63,
    "john": 64, "jn": 64, "joh": 64,
    "acts": 65, "ac": 65,
    "romans": 66, "rom": 66, "ro": 66,
    "1 corinthians": 67, "1corinthians": 67, "1cor": 67, "1co": 67,
    "2 corinthians": 68, "2corinthians": 68, "2cor": 68, "2co": 68,
    "galatians": 69, "gal": 69, "ga": 69,
    "ephesians": 70, "eph": 70,
    "philippians": 71, "phil": 71, "php": 71,
    "colossians": 72, "col": 72,
    "1 thessalonians": 73, "1thessalonians": 73, "1thess": 73, "1th": 73,
    "2 thessalonians": 74, "2thessalonians": 74, "2thess": 74, "2th": 74,
    "1 timothy": 75, "1timothy": 75, "1tim": 75, "1ti": 75,
    "2 timothy": 76, "2timothy": 76, "2tim": 76, "2ti": 76,
    "titus": 77, "tit": 77,
    "philemon": 78, "phlm": 78, "phm": 78,
    "hebrews": 79, "heb": 79,
    "james": 80, "jas": 80,
    "1 peter": 81, "1peter": 81, "1pet": 81, "1pe": 81,
    "2 peter": 82, "2peter": 82, "2pet": 82, "2pe": 82,
    "1 john": 83, "1john": 83, "1jn": 83, "1jo": 83,
    "2 john": 84, "2john": 84, "2jn": 84, "2jo": 84,
    "3 john": 85, "3john": 85, "3jn": 85, "3jo": 85,
    "jude": 86, "jud": 86,
    "revelation": 87, "rev": 87, "re": 87,
}

BOOK_NUM_TO_NAME = {
    1: "Genesis", 2: "Exodus", 3: "Leviticus", 4: "Numbers", 5: "Deuteronomy",
    6: "Joshua", 7: "Judges", 8: "Ruth", 9: "1 Samuel", 10: "2 Samuel",
    11: "1 Kings", 12: "2 Kings", 13: "1 Chronicles", 14: "2 Chronicles",
    15: "Ezra", 16: "Nehemiah", 17: "Esther", 18: "Job", 19: "Psalms",
    20: "Proverbs", 21: "Ecclesiastes", 22: "Song of Solomon", 23: "Isaiah",
    24: "Jeremiah", 25: "Lamentations", 26: "Ezekiel", 27: "Daniel",
    28: "Hosea", 29: "Joel", 30: "Amos", 31: "Obadiah", 32: "Jonah",
    33: "Micah", 34: "Nahum", 35: "Habakkuk", 36: "Zephaniah", 37: "Haggai",
    38: "Zechariah", 39: "Malachi",
    61: "Matthew", 62: "Mark", 63: "Luke", 64: "John", 65: "Acts",
    66: "Romans", 67: "1 Corinthians", 68: "2 Corinthians", 69: "Galatians",
    70: "Ephesians", 71: "Philippians", 72: "Colossians",
    73: "1 Thessalonians", 74: "2 Thessalonians", 75: "1 Timothy",
    76: "2 Timothy", 77: "Titus", 78: "Philemon", 79: "Hebrews",
    80: "James", 81: "1 Peter", 82: "2 Peter", 83: "1 John",
    84: "2 John", 85: "3 John", 86: "Jude", 87: "Revelation",
}

# Default Bibles to use
DEFAULT_BIBLES = ["ESV.logos4", "NASB95.logos4", "KJV1900.logos4"]

# ── Reference Parsing ──────────────────────────────────────────────────────

def parse_reference(ref_str):
    """Parse 'John 3:16-18' → {book: 64, chapter: 3, verse_start: 16, verse_end: 18}"""
    ref_str = ref_str.strip()

    # Match patterns like "John 3:16", "John 3:16-18", "John 3", "1 John 2:1-5"
    m = re.match(
        r'^(\d?\s*[A-Za-z ]+?)\s+(\d+)(?::(\d+)(?:\s*[-–]\s*(\d+))?)?$',
        ref_str
    )
    if not m:
        raise ValueError(f"Could not parse reference: {ref_str}")

    book_name = m.group(1).strip().lower()
    chapter = int(m.group(2))
    verse_start = int(m.group(3)) if m.group(3) else None
    verse_end = int(m.group(4)) if m.group(4) else verse_start

    book_num = BOOK_NAMES.get(book_name)
    if book_num is None:
        # Try without spaces for numbered books
        book_name_nospace = book_name.replace(" ", "")
        book_num = BOOK_NAMES.get(book_name_nospace)

    if book_num is None:
        raise ValueError(f"Could not parse reference: {ref_str}")

    return {
        "book": book_num,
        "book_name": BOOK_NUM_TO_NAME[book_num],
        "chapter": chapter,
        "verse_start": verse_start,
        "verse_end": verse_end,
        "ref_str": ref_str,
    }


def parse_reference_multi(ref_str):
    """Parse a reference string that may contain multiple ranges.

    Returns a list of dicts, each with:
        book, chapter_start, verse_start, chapter_end, verse_end, raw_text

    Handles:
      - Single range: "Romans 8:1-11" -> 1 row
      - Multi-range: "Romans 8:1-11; Romans 9:1-5" -> 2 rows
      - Chapter span: "Psalm 1-2" -> 1 row, chapter_start=1, chapter_end=2, verses=None
      - Whole chapter: "Romans 8" -> 1 row, verses=None
      - Unparseable: returns []
    """
    if not ref_str or not isinstance(ref_str, str):
        return []

    parts = [p.strip() for p in ref_str.split(';') if p.strip()]
    results = []
    for part in parts:
        for sub in _expand_comma_verses(part):
            parsed = _parse_single_range(sub)
            if parsed:
                parsed['raw_text'] = sub
                results.append(parsed)
    return results


def _expand_comma_verses(segment):
    """Expand 'Romans 8:1-11,16' into ['Romans 8:1-11', 'Romans 8:16'].

    If the segment has a colon and the after-colon portion contains commas,
    split into multiple segments sharing the same book+chapter prefix.
    """
    m = re.match(r'^(.+?\s+\d+:)(\S+)$', segment)
    if not m:
        return [segment]
    prefix, after = m.groups()
    if ',' not in after:
        return [segment]
    parts = [p.strip() for p in after.split(',') if p.strip()]
    return [f"{prefix}{p}" for p in parts]


def _parse_single_range(part):
    """Parse one range segment. Returns dict or None."""
    # Cross-chapter range: "Ecclesiastes 7:15-8:1"
    m_cross = re.match(r'^(.+?)\s+(\d+):(\d+)-(\d+):(\d+)$', part)
    if m_cross:
        book_name, c1, v1, c2, v2 = m_cross.groups()
        try:
            base = parse_reference(f"{book_name} {c1}:1")
        except Exception:
            return None
        return {
            'book': base['book'],
            'chapter_start': int(c1),
            'verse_start': int(v1),
            'chapter_end': int(c2),
            'verse_end': int(v2),
        }
    # Extract book name (everything before the first digit), then the first number,
    # then optional verse range OR chapter range.
    m = re.match(r'^(.+?)\s+(\d+)(?::(\d+)(?:-(\d+))?|(?:-(\d+)))?$', part)
    if not m:
        return None
    book_name, first_num, v_start, v_end, chap_end = m.groups()
    try:
        base = parse_reference(f"{book_name} {first_num}:1")
    except Exception:
        return None
    book = base['book']
    chapter_start = int(first_num)
    if v_start is not None:
        # "Romans 8:1" or "Romans 8:1-11"
        vs = int(v_start)
        ve = int(v_end) if v_end else vs
        return {
            'book': book,
            'chapter_start': chapter_start,
            'verse_start': vs,
            'chapter_end': chapter_start,
            'verse_end': ve,
        }
    if chap_end is not None:
        # "Psalm 1-2"
        return {
            'book': book,
            'chapter_start': chapter_start,
            'verse_start': None,
            'chapter_end': int(chap_end),
            'verse_end': None,
        }
    # "Romans 8" (whole chapter)
    return {
        'book': book,
        'chapter_start': chapter_start,
        'verse_start': None,
        'chapter_end': chapter_start,
        'verse_end': None,
    }


def ref_to_logos_superset_pattern(ref):
    """Convert parsed ref to SQL LIKE pattern for ReferenceSupersets matching.

    Uses ``bible%.{book}%`` so we pick up every reference-flavor prefix — not
    only the unqualified ``bible.`` one. Collins Hermeneia (Daniel) stores its
    superset as ``bible+bhs.27``; other resources use ``bible+lxx.``,
    ``bible+sblgnt.``, ``bible+nrsv.``, ``bible+na27.``, ``bible+gnt.``, etc.
    The looser LIKE can admit false positives: for example, when the caller
    asks about Daniel (book 27), the pattern ``bible%.27%`` also matches
    supersets like ``bible.66.1.1-66.16.27`` where ``27`` happens to be a
    verse number in Romans. Downstream ``ref_covers_passage`` rejects those
    false positives.
    """
    return f"bible%.{ref['book']}%"


def ref_covers_passage(superset_str, ref):
    """Check if a ReferenceSupersets string covers the given passage."""
    if not superset_str:
        return False
    book = ref["book"]
    ch = ref["chapter"]

    for part in superset_str.split("\t"):
        part = part.strip()
        if not part.startswith("bible"):
            continue

        # Parse ranges like "bible.64.1.1-64.21.25" or "bible.64"
        m = re.match(r'bible(?:\+\w+)?\.(\d+)(?:\.(\d+)(?:\.(\d+))?)?(?:-(\d+)(?:\.(\d+)(?:\.(\d+))?)?)?', part)
        if not m:
            continue

        start_book = int(m.group(1))
        start_ch = int(m.group(2)) if m.group(2) else 1
        end_book = int(m.group(4)) if m.group(4) else start_book
        end_ch = int(m.group(5)) if m.group(5) else 999

        if start_book <= book <= end_book:
            if book == start_book and book == end_book:
                if start_ch <= ch <= end_ch:
                    return True
            elif book == start_book:
                if ch >= start_ch:
                    return True
            elif book == end_book:
                if ch <= end_ch:
                    return True
            else:
                return True

    return False


# ── Database Queries ───────────────────────────────────────────────────────

def remap_path(stored_path):
    """Convert stored path to actual path on disk."""
    if stored_path and stored_path.startswith(PATH_REMAP[0]):
        return stored_path.replace(PATH_REMAP[0], PATH_REMAP[1], 1)
    return stored_path


def get_resource_file(resource_id):
    """Get the file path for a resource ID."""
    conn = sqlite3.connect(RESOURCE_MGR_DB)
    row = conn.execute(
        "SELECT Location FROM Resources WHERE ResourceId = ?", (resource_id,)
    ).fetchone()
    conn.close()
    if row:
        return remap_path(row[0])
    return None


def find_bibles():
    """Find all available Bible text resources."""
    conn = sqlite3.connect(CATALOG_DB)
    conn.execute(f"ATTACH '{RESOURCE_MGR_DB}' AS rm")
    rows = conn.execute("""
        SELECT c.ResourceId, c.AbbreviatedTitle, c.Title,
               rm.Resources.Location
        FROM Records c
        INNER JOIN rm.Resources ON c.ResourceId = rm.Resources.ResourceId
        WHERE c.Type = 'text.monograph.bible' AND c.Availability = 2
        ORDER BY c.AbbreviatedTitle
    """).fetchall()
    conn.close()
    return [
        {
            "resource_id": r[0],
            "abbrev": r[1] or "",
            "title": r[2],
            "file": remap_path(r[3]),
            "filename": os.path.basename(remap_path(r[3])),
        }
        for r in rows
    ]


def find_commentaries_for_ref(ref, limit=10):
    """Find commentaries that cover the given Bible reference."""
    conn = sqlite3.connect(CATALOG_DB)
    conn.execute(f"ATTACH '{RESOURCE_MGR_DB}' AS rm")
    rows = conn.execute("""
        SELECT c.ResourceId, c.AbbreviatedTitle, c.Title,
               c.ReferenceSupersets, rm.Resources.Location
        FROM Records c
        INNER JOIN rm.Resources ON c.ResourceId = rm.Resources.ResourceId
        WHERE c.Type = 'text.monograph.commentary.bible'
        AND c.Availability = 2
        AND c.ReferenceSupersets LIKE ?
        ORDER BY c.AbbreviatedTitle
    """, (ref_to_logos_superset_pattern(ref),)).fetchall()
    conn.close()

    results = []
    for r in rows:
        if ref_covers_passage(r[3], ref):
            results.append({
                "resource_id": r[0],
                "abbrev": r[1] or "",
                "title": r[2],
                "supersets": r[3],
                "file": remap_path(r[4]),
                "filename": os.path.basename(remap_path(r[4])),
            })
    return results[:limit]


# ── Study Bibles ──────────────────────────────────────────────────────────

STUDY_BIBLES = [
    {"resource_id": "LLS:ESVSB", "abbrev": "ESV SB", "title": "ESV Study Bible", "file": "ESVSB.logos4"},
    {"resource_id": "LLS:CSBANCIENTFAITHSB", "abbrev": "Ancient Faith", "title": "Ancient Faith Study Bible: Notes", "file": "CSBANCIENTFAITHSB.logos4"},
    {"resource_id": "LLS:ESVREFSTBBL", "abbrev": "Reformation SB", "title": "The Reformation Study Bible", "file": "ESVREFSTBBL.logos4"},
    {"resource_id": "LLS:FSB", "abbrev": "FSB", "title": "Faithlife Study Bible", "file": "FSB.logos4"},
    {"resource_id": "LLS:GENEVABBL1560NOTE", "abbrev": "Geneva Notes", "title": "Geneva Bible: Notes", "file": "GENEVABBL1560NOTE.logos4"},
    {"resource_id": "LLS:NVCLTRLBCBBLNTS", "abbrev": "NIV Cultural BG", "title": "NIV Cultural Backgrounds Study Bible", "file": "NVCLTRLBCBBLNTS.logos4"},
    {"resource_id": "LLS:NIVZNDRVNSTBBL", "abbrev": "NIVBT SB", "title": "NIV Biblical Theology Study Bible", "file": "NIVZNDRVNSTBBL.logos4"},
]


def find_study_bible_notes(ref, max_chars=20000):
    """Look up notes for a passage across all 7 study bibles.

    Returns list of dicts: [{"title", "abbrev", "text"}, ...]
    Only includes study bibles that returned content.
    """
    results = []
    for sb in STUDY_BIBLES:
        fpath = os.path.join(RESOURCES_DIR, sb["file"])
        if not os.path.isfile(fpath):
            continue
        try:
            text = find_commentary_section(fpath, ref)
            if text:
                if len(text) > max_chars:
                    text = text[:max_chars] + "\n\n[... truncated ...]"
                results.append({
                    "title": sb["title"],
                    "abbrev": sb["abbrev"],
                    "text": text,
                })
        except Exception:
            continue
    return results


def find_lexicons():
    """Find available lexicon resources."""
    conn = sqlite3.connect(CATALOG_DB)
    conn.execute(f"ATTACH '{RESOURCE_MGR_DB}' AS rm")
    rows = conn.execute("""
        SELECT c.ResourceId, c.AbbreviatedTitle, c.Title,
               rm.Resources.Location
        FROM Records c
        INNER JOIN rm.Resources ON c.ResourceId = rm.Resources.ResourceId
        WHERE c.Type LIKE '%lexicon%' AND c.Availability = 2
        ORDER BY c.AbbreviatedTitle
    """).fetchall()
    conn.close()
    return [
        {
            "resource_id": r[0],
            "abbrev": r[1] or "",
            "title": r[2],
            "file": remap_path(r[3]),
            "filename": os.path.basename(remap_path(r[3])),
        }
        for r in rows
    ]


# ── LogosReader Interface ──────────────────────────────────────────────────

def _run_via_batch(args):
    """Try to execute a run_reader call via the batch reader singleton.

    Translates run_reader argument patterns to LogosBatchReader method calls.
    Returns (stdout, stderr) on success, or None if batch reader can't handle it.
    """
    global _batch_reader
    if _batch_reader is None:
        return None
    if not _batch_reader.is_alive():
        # Batch reader died (e.g., from a crashing command); try to restart
        try:
            _batch_reader.close()
        except Exception:
            pass
        _batch_reader = None
        init_batch_reader()
        if _batch_reader is None or not _batch_reader.is_alive():
            return None

    args = list(args)
    try:
        if len(args) >= 2 and args[0] == "--list":
            result = _batch_reader.list_articles(args[1])
            if result:
                lines = ["Article#\tArticleId"]
                for num, aid in result:
                    lines.append(f"{num}\t{aid}")
                return "\n".join(lines), ""
            return "", ""

        if len(args) >= 2 and args[0] == "--toc":
            result = _batch_reader.get_toc(args[1])
            return (result or "", "")

        if len(args) >= 2 and args[0] == "--info":
            info = _batch_reader.get_info(args[1])
            if info:
                lines = [f"{k}: {v}" for k, v in info.items()]
                return "\n".join(lines), ""
            return "", ""

        if len(args) >= 3 and args[0] == "--find-article":
            result = _batch_reader.find_article(args[1], args[2])
            if result:
                lines = []
                for num, aid in result:
                    lines.append(f"{num}\t{aid}")
                return "\n".join(lines), ""
            return "", ""

        if len(args) >= 2 and args[0] == "--interlinear":
            # Interlinear crashes the batch reader (NativeLogosResourceIndexer
            # conflicts with open resources). Always use subprocess for this.
            return None

        # Positional args: resource_file article_num [max_chars]
        if len(args) >= 2 and not args[0].startswith("--"):
            resource_file = args[0]
            article_num = int(args[1])
            max_chars = int(args[2]) if len(args) >= 3 else 10000
            result = _batch_reader.read_article(resource_file, article_num, max_chars)
            return (result or "", "")
    except Exception:
        return None  # Fall back to subprocess

    return None


def run_reader(*args, timeout=30):
    """Run LogosReader and return stdout.

    Tries the batch reader singleton first for speed, falls back to subprocess.
    """
    # Try batch reader first
    batch_result = _run_via_batch(args)
    if batch_result is not None:
        return batch_result

    # Fall back to subprocess
    cmd = ["dotnet", "run", "--no-build", "--"] + list(args)
    try:
        result = subprocess.run(
            cmd,
            cwd=READER_DIR,
            env=DOTNET_ENV,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT"
    except Exception as e:
        return "", str(e)


BOOK_ABBREVS = {
    1: ["GE", "GEN"], 2: ["EX", "EXO", "EXOD"], 3: ["LE", "LEV"],
    4: ["NU", "NUM"], 5: ["DT", "DEU", "DEUT"], 6: ["JOS", "JOSH"],
    7: ["JDG", "JUDG"], 8: ["RU", "RUTH"], 9: ["1SA", "1SAM"],
    10: ["2SA", "2SAM"], 11: ["1KI", "1KGS"], 12: ["2KI", "2KGS"],
    13: ["1CH", "1CHR"], 14: ["2CH", "2CHR"], 15: ["EZR", "EZRA"],
    16: ["NE", "NEH"], 17: ["ES", "EST"], 18: ["JOB", "JB"],
    19: ["PS", "PSA"], 20: ["PR", "PRO", "PROV"], 21: ["EC", "ECC", "ECCL"],
    22: ["SS", "SOS", "SONG"], 23: ["IS", "ISA"], 24: ["JE", "JER"],
    25: ["LA", "LAM"], 26: ["EZE", "EZEK"], 27: ["DA", "DAN"],
    28: ["HO", "HOS"], 29: ["JOE", "JOEL"], 30: ["AM", "AMOS"],
    31: ["OB", "OBAD"], 32: ["JON", "JONAH"], 33: ["MIC"],
    34: ["NA", "NAH"], 35: ["HAB"], 36: ["ZEP", "ZEPH"],
    37: ["HAG"], 38: ["ZEC", "ZECH"], 39: ["MAL"],
    61: ["MT", "MAT", "MATT"], 62: ["MK", "MAR", "MARK"],
    63: ["LK", "LU", "LUKE"], 64: ["JN", "JOH", "JOHN"],
    65: ["AC", "ACT", "ACTS"], 66: ["RO", "ROM"],
    67: ["1CO", "1COR"], 68: ["2CO", "2COR"], 69: ["GA", "GAL"],
    70: ["EPH"], 71: ["PHP", "PHIL"], 72: ["COL"],
    73: ["1TH", "1THESS"], 74: ["2TH", "2THESS"],
    75: ["1TI", "1TIM"], 76: ["2TI", "2TIM"],
    77: ["TIT"], 78: ["PHM", "PHLM"], 79: ["HEB"],
    80: ["JAS"], 81: ["1PE", "1PET"], 82: ["2PE", "2PET"],
    83: ["1JN", "1JO"], 84: ["2JN", "2JO"], 85: ["3JN", "3JO"],
    86: ["JUD", "JUDE"], 87: ["RE", "REV"],
}


def get_article_list_cached(bible_file, _cache={}, _sqlite_cache=None):
    """Get article list for a Bible file, cached across calls.

    Checks in order: in-memory cache, SQLite cache, then LogosReader.
    Results are stored back into all cache layers.
    """
    if bible_file in _cache:
        return _cache[bible_file]

    # Try SQLite cache
    if LogosCache is not None:
        if _sqlite_cache is None:
            try:
                _sqlite_cache = LogosCache()
            except Exception:
                _sqlite_cache = False  # mark as unavailable
        if _sqlite_cache:
            cached = _sqlite_cache.get_article_list(bible_file)
            if cached is not None:
                # Reconstruct the tab-separated text from the cached list
                lines = ["Article#\tArticleId"]
                for art_num, art_id in cached:
                    lines.append(f"{art_num}\t{art_id}")
                text = "\n".join(lines)
                _cache[bible_file] = text
                return text

    # Fall back to LogosReader
    stdout, stderr = run_reader("--list", bible_file, timeout=120)
    text = stdout or ""
    _cache[bible_file] = text

    # Store in SQLite cache for next time
    if LogosCache is not None and text:
        try:
            if not _sqlite_cache:
                _sqlite_cache = LogosCache()
            articles = []
            for line in text.split("\n"):
                parts = line.split("\t")
                if len(parts) == 2 and parts[0].isdigit():
                    articles.append((int(parts[0]), parts[1]))
            if articles:
                _sqlite_cache.put_article_list(bible_file, articles)
        except Exception:
            pass  # Cache write failure is non-fatal

    return text


def find_chapter_article(bible_file, book_num, chapter):
    """Find the article number for a given book+chapter in a Bible.

    Checks the SQLite bible_verse_index cache first; if not found,
    searches the article list and caches the result.
    """
    # Check SQLite verse index cache
    if LogosCache is not None:
        try:
            cache = LogosCache()
            cached = cache.get_bible_verse_index(bible_file, book_num, chapter)
            if cached is not None:
                return str(cached[0]), cached[1]
        except Exception:
            pass

    stdout = get_article_list_cached(bible_file)
    if not stdout:
        return None, None

    # Build candidate article ID patterns for this book+chapter
    abbrevs = BOOK_ABBREVS.get(book_num, [])
    bible_prefix = bible_file.replace(".logos4", "").replace(".lbxlls", "")
    candidates = [f"BOOK.{book_num}.{chapter}"]  # KJV style
    for ab in abbrevs:
        candidates.append(f"{ab}.{chapter}")  # NASB style: JN.3
        candidates.append(f"{bible_prefix}.{ab}.{chapter}")  # ESV.JN.3

    article_num = None
    matched_id = None
    for line in stdout.split("\n"):
        parts = line.split("\t")
        if len(parts) == 2:
            aid = parts[1].upper()
            for cand in candidates:
                if aid == cand.upper():
                    article_num = parts[0]
                    matched_id = parts[1]
                    break
            if article_num:
                break

    if article_num is None:
        # Fallback: search for any article ending with book_abbrev.chapter
        for line in stdout.split("\n"):
            parts = line.split("\t")
            if len(parts) == 2:
                aid = parts[1].upper()
                for ab in abbrevs:
                    if aid.endswith(f".{ab}.{chapter}") or aid == f"{ab}.{chapter}":
                        article_num = parts[0]
                        matched_id = parts[1]
                        break
                    if article_num:
                        break

    # Cache the result in SQLite for next time
    if article_num is not None and LogosCache is not None:
        try:
            cache = LogosCache()
            cache.put_bible_verse_index(
                bible_file, book_num, chapter, int(article_num), matched_id
            )
        except Exception:
            pass  # Cache write failure is non-fatal

    return article_num, matched_id


def clean_bible_text(text):
    """Strip inline cross-ref/footnote markers, leaving clean readable text.

    Logos uses:
    - U+FEFF before a letter for cross-reference markers
    - U+FEFF before a digit for footnote markers
    - U+00A0 (NBSP) after verse numbers
    """
    if not text:
        return text

    # Strip FEFF + adjacent marker character (letter or digit)
    # Pattern: FEFF followed by a lowercase letter (cross-ref marker, single letter)
    text = re.sub(r'\ufeff[a-z]', '', text)
    # Pattern: FEFF followed by digits (footnote)
    text = re.sub(r'\ufeff\d+', '', text)
    # Pattern: standalone letter before FEFF (cross-ref marker before text)
    text = re.sub(r'(?<=\s)[a-z]\ufeff', '', text)
    text = re.sub(r'^[a-z]\ufeff', '', text, flags=re.MULTILINE)

    # Remove any remaining stray FEFF characters
    text = text.replace('\ufeff', '')

    # Replace NBSP with regular space
    text = text.replace('\xa0', ' ')

    # Clean up any double spaces left behind
    text = re.sub(r'  +', ' ', text)

    return text.strip()


def read_annotations(bible_file, book_num, chapter, verses=None):
    """Read cross-reference and footnote articles for given verses.

    Returns dict with:
      'xrefs': {letter: text, ...}
      'footnotes': {num: text, ...}
    """
    stdout = get_article_list_cached(bible_file)
    if not stdout:
        return {"xrefs": {}, "footnotes": {}}

    abbrevs = BOOK_ABBREVS.get(book_num, [])
    bible_prefix = bible_file.replace(".logos4", "").replace(".lbxlls", "")

    # Build book abbreviation patterns for matching article IDs
    book_patterns = set()
    for ab in abbrevs:
        book_patterns.add(ab.upper())
        # Also try without digits for numbered books (1JN → 1JN)
        book_patterns.add(f"{bible_prefix}.{ab}".upper())

    xrefs = {}
    footnotes = {}

    # Find XREF articles: XREF.BOOK_ABBREV+CHAPTER.VERSE.LETTER
    # e.g., XREF.JN3.16.H, XREF.GE1.1.A
    xref_articles = []
    ftn_articles = []

    for line in stdout.split("\n"):
        parts = line.split("\t")
        if len(parts) != 2:
            continue
        aid = parts[1]

        # Match XREF articles for this chapter
        if aid.startswith("XREF."):
            for ab in abbrevs:
                # Pattern: XREF.AB+CHAPTER.VERSE.LETTER
                prefix = f"XREF.{ab}{chapter}."
                if aid.upper().startswith(prefix.upper()):
                    # Extract verse and letter
                    rest = aid[len(prefix):]
                    m = re.match(r'(\d+)\.([A-Za-z]+)', rest)
                    if m:
                        verse_num = int(m.group(1))
                        letter = m.group(2)
                        if verses is None or verse_num in verses:
                            xref_articles.append((parts[0], verse_num, letter))
                    break

        # Match FTN articles for this chapter
        # Pattern: FTN.BOOK_ABBREV.CHAPTER.NUM
        elif aid.startswith("FTN."):
            for ab in abbrevs:
                prefix = f"FTN.{ab}.{chapter}."
                if aid.upper().startswith(prefix.upper()):
                    rest = aid[len(prefix):]
                    if rest.isdigit():
                        ftn_articles.append((parts[0], int(rest)))
                    break

    # Read XREF articles
    for art_num, verse_num, letter in xref_articles:
        text, _ = run_reader(bible_file, art_num, "1000", timeout=15)
        if text:
            key = letter.lower()
            xrefs[key] = f"v{verse_num} [{key}] {text.strip()}"

    # Read FTN articles
    for art_num, ftn_num in ftn_articles:
        text, _ = run_reader(bible_file, art_num, "1000", timeout=15)
        if text:
            footnotes[ftn_num] = text.strip()

    return {"xrefs": xrefs, "footnotes": footnotes}


def read_bible_chapter(bible_file, book_num, chapter):
    """Read a full chapter from a Bible resource.

    Returns (text, annotations) where annotations has xrefs and footnotes.
    """
    article_num, matched_id = find_chapter_article(bible_file, book_num, chapter)
    if article_num is None:
        return None, None

    stdout, stderr = run_reader(bible_file, article_num, "50000", timeout=30)
    if not stdout:
        return None, None

    return stdout, {"article_num": article_num, "article_id": matched_id}


def read_article_text(resource_file, article_num, max_chars=20000):
    """Read text from a specific article number."""
    stdout, _ = run_reader(resource_file, str(article_num), str(max_chars), timeout=30)
    return stdout if stdout else None


def get_interlinear_data(bible_file, article_num):
    """Get interlinear data for a Bible article.

    Returns list of dicts, each representing a word with keys like:
      Surface, Manuscript, Lemma, Morphology, Strong's, etc.
    Returns empty list on failure.
    """
    stdout, stderr = run_reader("--interlinear", bible_file, str(article_num), timeout=60)
    if not stdout:
        return []
    return _parse_interlinear_tsv(stdout)


def _parse_interlinear_tsv(tsv_text):
    """Parse TSV interlinear output into list of dicts."""
    if not tsv_text:
        return []
    lines = tsv_text.strip().split("\n")
    if not lines:
        return []

    # First line is header
    headers = lines[0].split("\t")
    words = []
    for line in lines[1:]:
        fields = line.split("\t")
        entry = {}
        for i, header in enumerate(headers):
            entry[header] = fields[i] if i < len(fields) else ""
        words.append(entry)
    return words


def get_interlinear_for_chapter(bible_file, book_num, chapter):
    """Get interlinear data for a Bible chapter.

    Finds the chapter article, extracts interlinear data.
    Returns list of word dicts or empty list.
    """
    article_num, matched_id = find_chapter_article(bible_file, book_num, chapter)
    if article_num is None:
        return []
    return get_interlinear_data(bible_file, int(article_num))


def find_word_in_interlinear(interlinear_data, english_word):
    """Filter interlinear entries matching an English word.

    Searches the 'Surface' and 'Word' columns (case-insensitive).
    Returns matching entries.
    """
    if not interlinear_data or not english_word:
        return []
    word_lower = english_word.lower()
    matches = []
    for entry in interlinear_data:
        surface = (entry.get("Surface") or entry.get("Word") or "").lower()
        if word_lower in surface:
            matches.append(entry)
    return matches


def get_resource_articles(resource_file, timeout=120):
    """List all articles in a resource."""
    stdout, stderr = run_reader("--list", resource_file, timeout=timeout)
    if not stdout:
        return []
    articles = []
    for line in stdout.split("\n"):
        parts = line.split("\t")
        if len(parts) == 2 and parts[0].isdigit():
            articles.append({"num": int(parts[0]), "id": parts[1]})
    return articles


def extract_verses(chapter_text, verse_start, verse_end):
    """Extract specific verses from chapter text by finding verse number markers."""
    if not chapter_text or verse_start is None:
        return chapter_text

    lines = chapter_text
    # Find verse markers - they appear as numbers at start of sentences
    # Pattern: verse number followed by text
    result_parts = []
    collecting = False

    # Split on verse number patterns
    # Verses appear like: "16 For God so loved..."
    parts = re.split(r'(?<=[.?!"\u201d\s])(\d+)\s+', lines)

    # Rebuild with verse tracking
    current_verse = 0
    full_text = chapter_text

    # Simple approach: find "16 " pattern and collect until verse_end+1
    verse_pattern_start = re.search(rf'(?:^|\s){verse_start}\s+', full_text)
    if not verse_pattern_start:
        # Try at beginning of text
        verse_pattern_start = re.search(rf'^{verse_start}\s+', full_text)

    if not verse_pattern_start:
        return chapter_text  # Can't find verse, return full chapter

    start_pos = verse_pattern_start.start()

    # Find end - look for verse_end+1
    if verse_end:
        end_pattern = re.search(rf'(?:^|\s){verse_end + 1}\s+', full_text[start_pos + 1:])
        if end_pattern:
            end_pos = start_pos + 1 + end_pattern.start()
        else:
            end_pos = len(full_text)
    else:
        # Single verse - find next verse number
        next_verse = re.search(rf'(?:^|\s){verse_start + 1}\s+', full_text[start_pos + 1:])
        if next_verse:
            end_pos = start_pos + 1 + next_verse.start()
        else:
            end_pos = len(full_text)

    return full_text[start_pos:end_pos].strip()


def parse_toc_output(toc_output):
    """Parse LogosReader --toc output into structured entries.

    Each line has format:
      {indent}{label} [article={article}, offset={offset}]
    where indent is depth*2 spaces.

    Returns list of dicts: {label, article, offset, depth}
    """
    entries = []
    if not toc_output:
        return entries

    toc_pattern = re.compile(
        r'^( *)(.+?) \[article=(-?\d+), offset=(-?\d+)\]$'
    )
    for line in toc_output.split("\n"):
        m = toc_pattern.match(line)
        if m:
            indent = len(m.group(1))
            depth = indent // 2
            label = m.group(2)
            article = int(m.group(3))
            offset = int(m.group(4))
            entries.append({
                "label": label,
                "article": article,
                "offset": offset,
                "depth": depth,
            })
    return entries


# Cache for parsed TOC entries, keyed by resource filename
_toc_cache = {}


def get_toc_cached(resource_file):
    """Get parsed TOC for a resource, cached across calls."""
    if resource_file not in _toc_cache:
        stdout, stderr = run_reader("--toc", resource_file, timeout=60)
        _toc_cache[resource_file] = parse_toc_output(stdout)
    return _toc_cache[resource_file]


def _build_book_forms(book_num):
    """Build a set of lowercase name/abbreviation forms for a Bible book number."""
    forms = set()
    book_name = BOOK_NUM_TO_NAME.get(book_num, "")
    forms.add(book_name.lower())
    for name, num in BOOK_NAMES.items():
        if num == book_num:
            forms.add(name.lower())
    for ab in BOOK_ABBREVS.get(book_num, []):
        forms.add(ab.lower())
    return forms


def _parse_ref_from_label(label, target_book_num):
    """Parse a Bible reference from a TOC entry label.

    Tries to extract chapter and verse range info from labels like:
      "John 3:16-18", "3:16-18", "Chapter 3", "John 3",
      "Jn 3:16", "3:1-21", "III. John 3:1-21 (Comment)", etc.

    Returns dict {chapter, verse_start, verse_end} or None if no match.
    Only matches if the book matches target_book_num (when book name present).
    """
    if not label:
        return None

    book_forms = _build_book_forms(target_book_num)

    # Pattern 1: "BookName Chapter:VerseStart-VerseEnd" (full reference)
    # Handles: "John 3:16-18", "Jn 3:16", "1 John 2:1-5", "Jn. 3:16-18"
    ref_pat = re.compile(
        r'(\d?\s*[A-Za-z]+\.?)\s+(\d+):(\d+)(?:\s*[-\u2013]\s*(\d+))?'
    )
    for m in ref_pat.finditer(label):
        book_part = m.group(1).strip().rstrip('.').lower()
        if book_part in book_forms:
            ch = int(m.group(2))
            vs = int(m.group(3))
            ve = int(m.group(4)) if m.group(4) else vs
            return {"chapter": ch, "verse_start": vs, "verse_end": ve}

    # Pattern 2: "BookName Chapter" (chapter-level, no verse)
    # Handles: "John 3", "Jn 3", "1 John 2"
    ch_pat = re.compile(
        r'(\d?\s*[A-Za-z]+\.?)\s+(\d+)\b'
    )
    for m in ch_pat.finditer(label):
        book_part = m.group(1).strip().rstrip('.').lower()
        if book_part in book_forms:
            ch = int(m.group(2))
            return {"chapter": ch, "verse_start": None, "verse_end": None}

    # Pattern 3: Bare "Chapter:Verse-Verse" (no book name, common in sub-entries)
    # Handles: "3:16-18", "3:16", "  3:1-21"
    bare_cv = re.compile(r'^\s*(\d+):(\d+)(?:\s*[-\u2013]\s*(\d+))?\s*')
    m = bare_cv.match(label)
    if m:
        ch = int(m.group(1))
        vs = int(m.group(2))
        ve = int(m.group(3)) if m.group(3) else vs
        return {"chapter": ch, "verse_start": vs, "verse_end": ve}

    # Pattern 4: "Chapter N" or "Ch. N" or "Ch N"
    ch_word = re.compile(r'\bch(?:apter|\.?)?\s+(\d+)\b', re.IGNORECASE)
    m = ch_word.search(label)
    if m:
        ch = int(m.group(1))
        return {"chapter": ch, "verse_start": None, "verse_end": None}

    return None


def _verse_overlap(entry_ref, target_ch, target_vs, target_ve):
    """Score how well a TOC entry's parsed reference matches the target passage.

    Returns (priority, specificity) where:
      priority: 1=exact range, 2=containing range, 3=chapter match, 4=book-level
      specificity: smaller range = higher specificity (lower number)
    Returns None if no match at all.
    """
    if entry_ref is None:
        return None

    e_ch = entry_ref["chapter"]
    e_vs = entry_ref["verse_start"]
    e_ve = entry_ref["verse_end"]

    if e_ch != target_ch:
        return None

    # Chapter-only match (no verse info in TOC entry)
    if e_vs is None:
        return (3, 999)

    # Both have verse info - check overlap
    if target_vs is None:
        # Target is whole chapter; any entry in this chapter matches
        return (3, 999)

    # Exact range match
    if e_vs == target_vs and e_ve == target_ve:
        return (1, e_ve - e_vs)

    # Entry contains target range
    if e_vs <= target_vs and e_ve >= target_ve:
        range_size = e_ve - e_vs
        return (2, range_size)

    # Entry overlaps target range (partial)
    if e_vs <= target_ve and e_ve >= target_vs:
        range_size = e_ve - e_vs
        return (2, range_size + 100)  # penalize partial overlap

    return None


def find_commentary_section_via_toc(resource_file, ref):
    """Find relevant commentary section using TOC-based navigation.

    Parses the resource's table of contents, matches TOC labels to the
    target Bible reference, and reads the best-matching article.

    Returns text string or None if TOC navigation fails.
    """
    toc_entries = get_toc_cached(resource_file)
    if not toc_entries:
        return None

    book_num = ref["book"]
    chapter = ref["chapter"]
    verse_start = ref["verse_start"]
    verse_end = ref["verse_end"] or verse_start

    # Parse all TOC entries for Bible references and score them
    scored = []
    for entry in toc_entries:
        if entry["article"] < 0:
            continue  # skip entries with no valid article

        parsed = _parse_ref_from_label(entry["label"], book_num)
        if parsed is None:
            continue

        score = _verse_overlap(parsed, chapter, verse_start, verse_end)
        if score is not None:
            scored.append((score, entry, parsed))

    if not scored:
        return None

    # Sort by priority (lower=better), then specificity (lower=better)
    scored.sort(key=lambda x: x[0])
    best_score, best_entry, best_parsed = scored[0]

    # Read the article at the TOC location
    article_num = best_entry["article"]
    offset = best_entry["offset"]

    # Read the article text
    text = read_article_text(resource_file, article_num, max_chars=30000)
    if not text:
        return None

    # If the TOC entry has a non-zero offset, the relevant section starts
    # partway through the article. Trim to start near the offset.
    # The offset is in character positions within the article.
    if offset > 0 and offset < len(text):
        # Start a bit before the offset to avoid cutting mid-sentence
        start = max(0, offset - 200)
        text = text[start:]

    # If we matched a chapter-level entry but have a verse-level target,
    # try to narrow down to the verse range within the text
    if best_score[0] >= 3 and verse_start is not None:
        narrowed = _narrow_to_verses(text, verse_start, verse_end)
        if narrowed:
            text = narrowed

    return text


def _narrow_to_verses(text, verse_start, verse_end):
    """Try to narrow chapter-level text to specific verses.

    Looks for verse markers like 'v. 16', 'verse 16', '16 ', '3:16', etc.
    Returns narrowed text or None if can't find verse boundaries.
    """
    if not text or verse_start is None:
        return None

    # Try common verse-start patterns
    patterns = [
        rf'(?:^|\n)\s*{verse_start}\s',              # "16 For God..."
        rf'\b[Vv](?:\.|erse)\s*{verse_start}\b',     # "v. 16" or "verse 16"
        rf'\b\d+:{verse_start}\b',                    # "3:16"
    ]

    best_start = None
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            pos = m.start()
            if best_start is None or pos < best_start:
                best_start = pos

    if best_start is None:
        return None

    # Find end (next verse after verse_end)
    end_verse = (verse_end or verse_start) + 1
    best_end = len(text)

    end_patterns = [
        rf'(?:^|\n)\s*{end_verse}\s',
        rf'\b[Vv](?:\.|erse)\s*{end_verse}\b',
        rf'\b\d+:{end_verse}\b',
    ]
    for pat in end_patterns:
        m = re.search(pat, text[best_start + 1:])
        if m:
            pos = best_start + 1 + m.start()
            if pos < best_end:
                best_end = pos

    result = text[best_start:best_end].strip()
    # Only return if we found something substantial
    return result if len(result) > 50 else None


def _find_commentary_section_heuristic(resource_file, ref, articles=None):
    """Find commentary section using article-ID + text-content navigation.

    Scans commentary body articles for verse-range headings, caches the
    mapping, and returns the best matching article text.
    """
    if articles is None:
        articles = get_resource_articles(resource_file)

    if not articles:
        return None

    chapter = ref["chapter"]
    verse_start = ref["verse_start"]
    verse_end = ref["verse_end"] or verse_start

    # ── Collect commentary-body articles ──
    body_articles = []
    for art in articles:
        aid = art["id"].upper()
        if any(aid.startswith(p) for p in ("FN", "FTN.", "ABBR", "BIB.",
                                            "TITLE", "TOC", "COPY", "DED",
                                            "PREF.", "GENPREFACE", "AUTHPREFACE",
                                            "INTRO", "OUTLINE", "SUMM")):
            continue
        if re.match(r'^(CH|C\d|COMM|BH|CL|SECT|DS)', aid):
            body_articles.append(art)

    if not body_articles:
        for art in articles:
            aid = art["id"].upper()
            if not any(aid.startswith(p) for p in ("FN", "FTN.", "ABBR",
                                                     "BIB.", "TITLE", "TOC",
                                                     "COPY", "DED", "PREF.")):
                body_articles.append(art)

    if not body_articles:
        return None

    # ── Scan articles, extract verse ranges, build index, cache ──
    cache = _get_logos_cache()
    index_entries = []  # for caching
    best_score = -1
    best_art = None

    scan_limit = min(len(body_articles), 60)
    for art in body_articles[:scan_limit]:
        text = read_article_text(resource_file, art["num"], max_chars=600)
        if not text:
            continue

        # Extract and cache verse range from heading
        vr = _extract_verse_range_from_heading(text)
        if vr:
            e_ch, e_vs, e_ve, heading = vr
            index_entries.append((art["num"], art["id"], heading, e_ch, e_vs, e_ve))

        score = _score_verse_match(text, chapter, verse_start, verse_end)
        if score > best_score:
            best_score = score
            best_art = art

    # Cache the index for future use
    if cache and index_entries:
        try:
            cache.put_commentary_articles_batch(resource_file, index_entries)
        except Exception:
            pass

    if best_art and best_score > 0:
        text = read_article_text(resource_file, best_art["num"], max_chars=30000)
        if text:
            return text

    # ── Fallback: ID-based chapter match + text narrowing ──
    ch_str = str(chapter)
    ch_pattern = re.compile(
        rf'(?:^|[.])(?:CH|C)({re.escape(ch_str)})(?:\.(\d+))?$', re.IGNORECASE
    )
    for art in articles:
        m = ch_pattern.search(art["id"])
        if m:
            text = read_article_text(resource_file, art["num"], max_chars=30000)
            if text and verse_start is not None:
                narrowed = _narrow_to_verses(text, verse_start, verse_end)
                if narrowed:
                    return narrowed
            if text:
                return text

    return None


def _extract_verse_range_from_heading(text):
    """Extract chapter:verse range from article heading/opening text.

    Looks for patterns like '1:16-17', '(1:1–16)', '3:16–18', etc.
    in the first 500 chars of the text.

    Returns (chapter, verse_start, verse_end, heading_text) or None.
    """
    if not text:
        return None

    heading = text[:500]
    # Pattern: chapter:verse_start–verse_end (most common in commentary headings)
    m = re.search(r'(\d+):(\d+)\s*[-\u2013]\s*(\d+)', heading)
    if m:
        ch = int(m.group(1))
        vs = int(m.group(2))
        ve = int(m.group(3))
        # Get the heading line
        first_line = text.split('\n')[0][:200] if '\n' in text else text[:200]
        return (ch, vs, ve, first_line.strip())

    # Pattern: chapter:verse (single verse)
    m = re.search(r'(\d+):(\d+)', heading)
    if m:
        ch = int(m.group(1))
        vs = int(m.group(2))
        first_line = text.split('\n')[0][:200] if '\n' in text else text[:200]
        return (ch, vs, vs, first_line.strip())

    return None


def _score_verse_match(text, chapter, verse_start, verse_end):
    """Score how well a text block matches a target verse range.

    Looks for patterns like '1:16-17', '1:16–17', 'vv. 16-17',
    '(1:16-17)', 'verses 16-17', etc. in the text.
    Returns score >= 0 (higher = better match).
    """
    if not text or verse_start is None:
        return 0

    score = 0
    text_lower = text[:2000].lower()  # focus on headings/opening
    ch = str(chapter)
    vs = str(verse_start)
    ve = str(verse_end) if verse_end else vs

    # Exact range match: "1:16-17" or "1:16–17"
    if re.search(rf'{ch}:{vs}\s*[-\u2013]\s*{ve}', text_lower):
        score += 10

    # Chapter:verse mention: "1:16"
    if f'{ch}:{vs}' in text_lower:
        score += 5

    # Verse-only patterns: "v. 16", "verse 16", "vv. 16-17"
    if re.search(rf'\bv(?:v|erse)?\.?\s*{vs}\b', text_lower):
        score += 3

    # Heading-style: starts with verse range
    first_500 = text[:500]
    if re.search(rf'{ch}:{vs}', first_500):
        score += 3  # bonus for appearing near the top

    return score


def _parse_verse_from_navref(ref_key, book_num, chapter):
    """Parse a navindex ref key to extract verse range for a specific chapter.

    Handles formats:
      bible.66.1.24           -> (24, 24)
      bible+esv.66.1.24       -> (24, 24)
      bible+esv.66.1.26-66.1.27 -> (26, 27)
      bible+esv.66.1.18-66.3.20 -> (18, None)  cross-chapter
      page.2157               -> None
      bible+esv.66.2.1        -> None  (wrong chapter)

    Returns (verse_start, verse_end) or None if ref doesn't match book+chapter.
    """
    if not ref_key.startswith("bible"):
        return None

    # Normalize: strip version prefix (bible+esv.X -> bible.X)
    if ref_key.startswith("bible+"):
        dot_idx = ref_key.index(".")
        ref_key = "bible" + ref_key[dot_idx:]

    # Split on hyphen for ranges: "bible.66.1.26-66.1.27"
    parts = ref_key.split("-", 1)
    start_part = parts[0]  # "bible.66.1.26"

    # Parse start: bible.{book}.{chapter}.{verse}
    segs = start_part.split(".")
    if len(segs) < 4:
        return None  # Chapter-only ref like bible.66.1
    try:
        ref_book = int(segs[1])
        ref_ch = int(segs[2])
        ref_vs = int(segs[3])
    except (ValueError, IndexError):
        return None

    if ref_book != book_num or ref_ch != chapter:
        return None

    # Single verse (no range)
    if len(parts) == 1:
        return (ref_vs, ref_vs)

    # Parse end of range
    end_part = parts[1]  # "66.1.27" or "66.3.20"
    end_segs = end_part.split(".")
    try:
        end_book = int(end_segs[0])
        end_ch = int(end_segs[1])
        end_vs = int(end_segs[2])
    except (ValueError, IndexError):
        return (ref_vs, None)

    # Cross-chapter range
    if end_book != book_num or end_ch != chapter:
        return (ref_vs, None)

    return (ref_vs, end_vs)


def _slice_article_by_offsets(text, navindex_refs, book_num, chapter,
                               verse_start, verse_end):
    """Slice article text to target verse range using navindex offsets.

    When a broad section header exists (e.g. 3:1-21 for studying 3:16),
    extracts just the section header paragraph + the target verse notes,
    skipping intermediate verse notes the user didn't ask for.

    Args:
        text: full article text
        navindex_refs: list of {"ref_key", "offset"} dicts, sorted by offset
        book_num: target book number
        chapter: target chapter number
        verse_start: first target verse
        verse_end: last target verse

    Returns:
        Sliced text covering the target verse range, or full text as fallback.
    """
    if not text or not navindex_refs:
        return text

    # Parse all refs into (verse_start, verse_end, offset) tuples
    parsed = []
    for r in navindex_refs:
        vrange = _parse_verse_from_navref(r["ref_key"], book_num, chapter)
        if vrange is not None:
            vs, ve = vrange
            parsed.append((vs, ve, r["offset"]))

    if not parsed:
        return text

    # Sort by offset (should already be sorted, but ensure)
    parsed.sort(key=lambda x: x[2])

    # ── Find section header containing verse_start ──
    best_section = None  # (vs, ve, offset)
    best_section_span = float('inf')
    for vs, ve, offset in parsed:
        if ve is not None and vs != ve and vs <= verse_start and ve >= verse_start:
            span = ve - vs
            if span < best_section_span:
                best_section_span = span
                best_section = (vs, ve, offset)

    # ── Find exact verse match ──
    exact_offset = None
    for vs, ve, offset in parsed:
        if vs == verse_start and ve == verse_start:
            exact_offset = offset
            break

    # ── Find nearest preceding verse ──
    preceding_offset = None
    for vs, ve, offset in parsed:
        if vs is not None and vs <= verse_start:
            preceding_offset = offset

    # ── Find end offset ──
    end_offset = len(text)
    for vs, ve, offset in parsed:
        if vs is not None and vs > verse_end:
            end_offset = offset
            break

    # ── Determine the best target verse start offset ──
    # This is where the verse notes for the target begin
    target_offset = exact_offset or preceding_offset

    # ── Decide whether section header is "close" or "broad" ──
    range_size = verse_end - verse_start + 1
    section_gap_threshold = max(3, range_size)

    if best_section is not None:
        section_vs, section_ve, section_offset = best_section
        gap = verse_start - section_vs

        if gap <= section_gap_threshold:
            # Section starts close to target — include it fully
            start_offset = section_offset
            result = text[start_offset:end_offset].strip()
        elif target_offset is not None:
            # Section starts far before target — extract header + target verse
            # Header = from section start to the first verse note after it
            header_end = section_offset
            for vs, ve, offset in parsed:
                if offset > section_offset:
                    header_end = offset
                    break
            header = text[section_offset:header_end].strip()
            verse_notes = text[target_offset:end_offset].strip()
            if header and verse_notes:
                result = header + "\n\n" + verse_notes
            else:
                result = verse_notes or header or text[section_offset:end_offset].strip()
        else:
            # No target offset, use section fully
            result = text[section_offset:end_offset].strip()
    elif target_offset is not None:
        result = text[target_offset:end_offset].strip()
    else:
        return text  # No usable refs

    # Fallback if slicing produced very little
    if len(result) < 20:
        return text

    return result


def _find_via_navindex(resource_file, ref):
    """Find commentary section using the native navigation index.

    The navigation index maps Bible references (e.g. 'bible.66.1.16')
    to article numbers. This is instant compared to scanning article text.

    Returns article text string, or None if navindex unavailable.
    """
    cache = _get_logos_cache()
    book_num = ref["book"]
    chapter = ref["chapter"]
    verse_start = ref["verse_start"]
    verse_end = ref.get("verse_end") or verse_start

    def _apply_verse_slicing(text, article_num):
        """Apply offset-based slicing if we have verse-level targeting."""
        if not text or not verse_start or not cache:
            return text
        article_refs = cache.get_article_navindex_refs(resource_file, article_num)
        if article_refs:
            return _slice_article_by_offsets(
                text, article_refs, book_num, chapter,
                verse_start, verse_end
            )
        return text

    # Build Logos reference format: bible.{book}.{chapter}.{verse}
    if verse_start:
        bible_ref = f"bible.{book_num}.{chapter}.{verse_start}"
    else:
        bible_ref = f"bible.{book_num}.{chapter}"

    # Check cache first
    if cache:
        result = cache.find_article_for_reference(resource_file, bible_ref)
        if result:
            article_num, offset = result
            text = read_article_text(resource_file, article_num, max_chars=30000)
            return _apply_verse_slicing(text, article_num)

    # Not cached — try to build navindex via batch reader
    global _batch_reader
    nav_data = None

    if _batch_reader and _batch_reader.is_alive():
        try:
            nav_data = _batch_reader.get_navigation_index(resource_file)
        except Exception:
            pass

    if nav_data is None:
        # Fallback to subprocess
        stdout, stderr = run_reader("--navindex", resource_file, timeout=120)
        if stdout:
            refs = []
            topics = []
            for line in stdout.split("\n"):
                parts = line.split("\t")
                if len(parts) >= 4 and parts[0] == "REF":
                    try:
                        refs.append({"ref": parts[1], "article": int(parts[2]), "offset": int(parts[3])})
                    except ValueError:
                        pass
                elif len(parts) >= 5 and parts[0] == "TOPIC":
                    try:
                        topics.append({"key": parts[1], "name": parts[2], "article": int(parts[3]), "offset": int(parts[4])})
                    except ValueError:
                        pass
            nav_data = {"references": refs, "topics": topics}

    if not nav_data or not nav_data["references"]:
        return None

    # Cache for future use
    if cache:
        try:
            cache.put_navindex(resource_file, nav_data["references"], nav_data.get("topics", []))
        except Exception:
            pass

    # Find best matching reference
    # Some resources use 'bible+esv.66.1.1' format instead of 'bible.66.1.1'
    # Normalize by extracting the book.chapter.verse portion after 'bible' prefix
    def _ref_matches(nav_ref, target_ref, prefix):
        """Check if nav_ref matches target, handling bible+version prefix."""
        if nav_ref == target_ref or nav_ref.startswith(target_ref):
            return True
        # Handle 'bible+esv.66.1.1' format — strip version suffix from 'bible+xxx'
        if nav_ref.startswith("bible+"):
            normalized = "bible" + nav_ref[nav_ref.index("."):]
            return normalized == target_ref or normalized.startswith(target_ref) or normalized.startswith(prefix)
        return False

    best_article = None
    best_offset = 0
    chapter_prefix = f"bible.{book_num}.{chapter}."
    for r in nav_data["references"]:
        ref_str = r["ref"]
        if ref_str == bible_ref:
            best_article = r["article"]
            best_offset = r["offset"]
            break
        # Handle bible+version prefix
        if ref_str.startswith("bible+"):
            normalized = "bible" + ref_str[ref_str.index("."):]
            if normalized == bible_ref or normalized.startswith(bible_ref):
                best_article = r["article"]
                best_offset = r["offset"]
                break
            if best_article is None and normalized.startswith(chapter_prefix):
                best_article = r["article"]
                best_offset = r["offset"]
                continue
        # Range match: 'bible.66.1.16-66.1.17' contains 'bible.66.1.16'
        if ref_str.startswith(bible_ref):
            best_article = r["article"]
            best_offset = r["offset"]
            break
        # Chapter match fallback
        if best_article is None and ref_str.startswith(chapter_prefix):
            best_article = r["article"]
            best_offset = r["offset"]

    if best_article is not None:
        text = read_article_text(resource_file, best_article, max_chars=30000)
        return _apply_verse_slicing(text, best_article)

    return None


def find_commentary_section(resource_file, ref, articles=None):
    """Find the relevant section in a commentary for a Bible reference.

    Priority:
    1. Navigation index (native API, instant via cache)
    2. Commentary verse index cache (from prior scans)
    3. TOC-based navigation
    4. Article-ID + text scanning (slow fallback)
    """
    # ── Try navigation index (fastest — native reference→article mapping) ──
    navindex_text = _find_via_navindex(resource_file, ref)
    if navindex_text:
        return navindex_text

    chapter = ref["chapter"]
    verse_start = ref["verse_start"]
    verse_end = ref["verse_end"] or verse_start

    # ── Check commentary verse index cache (from prior heuristic scans) ──
    cache = _get_logos_cache()
    if cache:
        cached_arts = cache.get_commentary_articles(resource_file, chapter, verse_start)
        if cached_arts:
            best = cached_arts[0]
            text = read_article_text(resource_file, best["article_num"], max_chars=30000)
            if text and verse_start:
                narrowed = _narrow_to_verses(text, verse_start, verse_end)
                if narrowed:
                    return narrowed
            if text:
                return text

    # ── Try TOC-based navigation ──
    toc_text = find_commentary_section_via_toc(resource_file, ref)
    if toc_text and verse_start:
        narrowed = _narrow_to_verses(toc_text, verse_start, verse_end)
        if narrowed:
            return narrowed
    if toc_text:
        return toc_text

    # ── Fallback: article-ID + text scanning (slow, but caches results) ──
    return _find_commentary_section_heuristic(resource_file, ref, articles)


# ── Output Formatting ──────────────────────────────────────────────────────

def format_study_output(ref, bible_texts, commentary_texts):
    """Format the compiled study material as markdown."""
    lines = []
    book_name = ref["book_name"]
    ch = ref["chapter"]

    if ref["verse_start"] and ref["verse_end"] and ref["verse_start"] != ref["verse_end"]:
        title = f"{book_name} {ch}:{ref['verse_start']}-{ref['verse_end']}"
    elif ref["verse_start"]:
        title = f"{book_name} {ch}:{ref['verse_start']}"
    else:
        title = f"{book_name} {ch}"

    lines.append(f"# Bible Study: {title}")
    lines.append("")

    # Bible texts
    lines.append("## Scripture Texts")
    lines.append("")
    for bt in bible_texts:
        lines.append(f"### {bt['label']}")
        lines.append("")
        lines.append(bt["text"])
        # Render annotations if present
        annotations = bt.get("annotations", {})
        if annotations.get("xrefs"):
            lines.append("")
            lines.append("**Cross-References:**")
            for key in sorted(annotations["xrefs"]):
                lines.append(f"- {annotations['xrefs'][key]}")
        if annotations.get("footnotes"):
            lines.append("")
            lines.append("**Footnotes:**")
            for key in sorted(annotations["footnotes"]):
                lines.append(f"- [{key}] {annotations['footnotes'][key]}")
        lines.append("")

    # Commentary texts
    if commentary_texts:
        lines.append("## Commentary")
        lines.append("")
        for ct in commentary_texts:
            lines.append(f"### {ct['label']}")
            lines.append("")
            text = ct["text"]
            if len(text) > 5000:
                text = text[:5000] + "\n\n[... truncated ...]"
            lines.append(text)
            lines.append("")

    return "\n".join(lines)


# ── Main ───────────────────────────────────────────────────────────────────

def resolve_bible_files(bible_names):
    """Resolve bible names to filenames."""
    if not bible_names:
        return DEFAULT_BIBLES

    all_bibles = find_bibles()
    resolved = []
    for name in bible_names:
        name_lower = name.lower().replace(".logos4", "").replace(".lbxlls", "")
        found = False
        for b in all_bibles:
            fn = b["filename"].lower().replace(".logos4", "").replace(".lbxlls", "")
            abbrev = b["abbrev"].lower()
            if name_lower == fn or name_lower == abbrev or name_lower in b["title"].lower():
                resolved.append(b["filename"])
                found = True
                break
        if not found:
            # Path contains a ".", use as-is; otherwise resolve the bare stem
            # via ResourceManager.
            if "." in name:
                resolved.append(name)
            else:
                try:
                    resolved.append(_resolve_bare_stem(name))
                except FileNotFoundError as e:
                    # Preserve historical behavior for unknown stems so
                    # callers that intentionally pass through arbitrary names
                    # still get a ".logos4" path, but emit a warning so the
                    # failure is observable rather than silent.
                    sys.stderr.write(f"[warn] resolve_bible_files: {e}\n")
                    resolved.append(name + ".logos4")
    return resolved


def _resolve_bare_stem(stem):
    """Map a bare resource stem to its actual filename (extension included).

    Consults ResourceManager.Resources.Location via a case-insensitive basename
    match so lowercase-ResourceId / uppercase-filename mismatches resolve
    (e.g. Walvoord's `LLS:gs_walv_daniel` → `GS_WALV_DANIEL.lbxlls`). Falls
    back to a filesystem probe for `.logos4` / `.lbxlls`. Raises
    ``FileNotFoundError`` if no candidate is found so callers can decide how
    to handle unknown stems — silent fabrication masked downstream failures.
    """
    if not stem:
        raise ValueError("_resolve_bare_stem: empty stem")
    # Backslash-escape must run first; later replaces add their own
    # backslashes that must not be re-escaped.
    escaped = stem.lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    # LIKE pattern hugs the basename boundary (`/stem.`), but Logos paths
    # include `.../e3txalek.5iq/...` so `/e3txalek.%` still admits rows where
    # the stem appears as a directory segment. The Python post-filter below
    # anchors the match to the actual basename (stem + extension).
    pattern = f"%/{escaped}.%"
    conn = sqlite3.connect(RESOURCE_MGR_DB)
    try:
        # Shortest-Location tiebreaker favors the tightest filename match
        # (avoids compound-path false positives from .lbxcllctn / container
        # entries). Fetch 2 so we can log if multiple candidates tie.
        rows = conn.execute(
            "SELECT Location FROM Resources "
            "WHERE lower(Location) LIKE ? ESCAPE '\\' "
            "ORDER BY length(Location) LIMIT 2",
            (pattern,),
        ).fetchall()
    finally:
        conn.close()

    # Post-filter to rows whose basename (without extension) actually equals
    # the requested stem, case-insensitively. This rejects directory-segment
    # matches like `/Data/e3txalek.5iq/.../CT.lbsct` for stem `e3txalek`.
    stem_lower = stem.lower()
    matches = []
    for r in rows:
        full_path = remap_path(r[0])
        basename = os.path.basename(full_path)
        base_stem = os.path.splitext(basename)[0]
        if base_stem.lower() == stem_lower:
            matches.append(full_path)

    if matches:
        # Warn when multiple distinct candidates share a basename stem so
        # observers can spot base-resource-vs-sidecar tie-breaks.
        if len(matches) > 1:
            sys.stderr.write(
                f"[warn] _resolve_bare_stem: multiple candidates for stem {stem!r}: "
                f"{matches}; choosing shortest ({matches[0]})\n"
            )
        chosen = matches[0]
        # F1: verify the resolved row still points to a real file before
        # trusting it — a stale ResourceManager row would silently yield an
        # empty article list downstream. Fall through to the filesystem
        # probe if the file has moved or been deleted.
        if os.path.exists(chosen):
            return os.path.basename(chosen)
    for ext in (".logos4", ".lbxlls"):
        if os.path.exists(os.path.join(RESOURCES_DIR, stem + ext)):
            return stem + ext
    raise FileNotFoundError(
        f"_resolve_bare_stem: no resource matches stem {stem!r}"
    )


def main():
    parser = argparse.ArgumentParser(description="Logos Bible Study Builder")
    parser.add_argument("reference", nargs="?", help="Bible reference (e.g., 'John 3:16-18')")
    parser.add_argument("--bibles", help="Comma-separated Bible versions (e.g., ESV,NASB,KJV)")
    parser.add_argument("--commentaries", type=int, default=5, help="Max commentaries to include")
    parser.add_argument("--all", action="store_true", help="Include all available commentaries")
    parser.add_argument("--list-bibles", action="store_true", help="List available Bibles")
    parser.add_argument("--list-commentaries", metavar="BOOK", help="List commentaries for a book")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if args.list_bibles:
        bibles = find_bibles()
        print(f"{'Abbrev':<12} {'Filename':<30} {'Title'}")
        print("-" * 80)
        for b in bibles:
            print(f"{b['abbrev']:<12} {b['filename']:<30} {b['title']}")
        return

    if args.list_commentaries:
        fake_ref = parse_reference(f"{args.list_commentaries} 1")
        comms = find_commentaries_for_ref(fake_ref, limit=100)
        print(f"Commentaries covering {fake_ref['book_name']}:")
        print(f"{'Abbrev':<16} {'Filename':<40} {'Coverage'}")
        print("-" * 100)
        for c in comms:
            print(f"{c['abbrev']:<16} {c['filename']:<40} {c['supersets']}")
        return

    if not args.reference:
        parser.print_help()
        return

    ref = parse_reference(args.reference)
    print(f"📖 Studying: {ref['book_name']} {ref['chapter']}"
          + (f":{ref['verse_start']}" if ref['verse_start'] else "")
          + (f"-{ref['verse_end']}" if ref['verse_end'] and ref['verse_end'] != ref['verse_start'] else ""),
          file=sys.stderr)

    # ── Initialize batch reader singleton for efficient reads ──
    init_batch_reader()

    try:
        bible_texts, commentary_texts = _run_study(ref, args)
    finally:
        shutdown_batch_reader()

    # ── Output ──
    if args.json:
        output = json.dumps({
            "reference": ref,
            "bibles": bible_texts,
            "commentaries": commentary_texts,
        }, indent=2, ensure_ascii=False)
    else:
        output = format_study_output(ref, bible_texts, commentary_texts)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"  ✅ Written to {args.output}", file=sys.stderr)
    else:
        print(output)


def _run_study(ref, args):
    """Core study logic. Uses batch reader singleton via run_reader() automatically."""

    # ── Gather Bible texts ──
    bible_files = resolve_bible_files(args.bibles.split(",") if args.bibles else None)
    bible_texts = []

    for bf in bible_files:
        print(f"  Reading {bf}...", file=sys.stderr)
        chapter_text, metadata = read_bible_chapter(bf, ref["book"], ref["chapter"])
        if chapter_text:
            if ref["verse_start"]:
                verse_text = extract_verses(chapter_text, ref["verse_start"], ref["verse_end"])
            else:
                verse_text = chapter_text
            verse_text = clean_bible_text(verse_text)
            # Read cross-references and footnotes
            annotations = read_annotations(bf, ref["book"], ref["chapter"],
                set(range(ref["verse_start"], (ref["verse_end"] or ref["verse_start"]) + 1)) if ref["verse_start"] else None)
            bible_texts.append({
                "label": bf.replace(".logos4", "").replace(".lbxlls", ""),
                "file": bf,
                "text": verse_text,
                "annotations": annotations,
            })
        else:
            print(f"  ⚠ Could not read {bf}", file=sys.stderr)

    # ── Gather commentary texts ──
    max_comms = 100 if args.all else args.commentaries
    commentaries = find_commentaries_for_ref(ref, limit=max_comms)
    print(f"  Found {len(commentaries)} commentaries covering this passage", file=sys.stderr)

    commentary_texts = []
    for comm in commentaries:
        print(f"  Reading {comm['abbrev'] or comm['filename']}...", file=sys.stderr)
        text = find_commentary_section(comm["filename"], ref)
        if text:
            commentary_texts.append({
                "label": f"{comm['abbrev'] or comm['title']} ({comm['filename']})",
                "resource_id": comm["resource_id"],
                "file": comm["filename"],
                "text": text,
            })

    return bible_texts, commentary_texts


if __name__ == "__main__":
    main()
