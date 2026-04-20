"""MorphGNT cache — authoritative morphological data for the Greek NT.

Loads MorphGNT SBLGNT data into SQLite for fast lookups.
Source: https://github.com/morphgnt/sblgnt

Book numbering: stored as Logos numbers (Matthew=40 .. Revelation=66).
MorphGNT internal numbers (1-27) are converted on load via offset +39.
"""

import os
import sqlite3
import unicodedata
from pathlib import Path

MORPHGNT_DATA_DIR = Path(__file__).parent / "morphgnt_data"
MORPHGNT_DB_PATH = Path(__file__).parent / "morphgnt_cache.db"

# MorphGNT file prefix → internal book number (1-27)
_BOOK_ABBREVS = [
    "Mt", "Mk", "Lk", "Jn", "Ac",
    "Ro", "1Co", "2Co", "Ga", "Eph",
    "Php", "Col", "1Th", "2Th", "1Ti",
    "2Ti", "Tit", "Phm", "Heb", "Jas",
    "1Pe", "2Pe", "1Jn", "2Jn", "3Jn",
    "Jud", "Re",
]

# File naming: 61-Mt-morphgnt.txt .. 87-Re-morphgnt.txt
BOOK_FILES = {
    i + 1: f"{i + 61}-{abbrev}-morphgnt.txt"
    for i, abbrev in enumerate(_BOOK_ABBREVS)
}

LOGOS_OFFSET = 39  # logos_book = morphgnt_book + 39

# ── Human-readable parsing ──────────────────────────────────────────────

POS_NAMES = {
    "N-": "Noun", "V-": "Verb", "RA": "Article",
    "A-": "Adjective", "C-": "Conjunction", "D-": "Adverb",
    "P-": "Preposition", "RP": "Personal Pronoun",
    "RR": "Relative Pronoun", "RD": "Demonstrative Pronoun",
    "RI": "Interrogative Pronoun", "RX": "Indefinite Pronoun",
    "X-": "Particle", "I-": "Interjection",
}

_PERSON = {"1": "1st Person", "2": "2nd Person", "3": "3rd Person"}
_TENSE = {
    "P": "Present", "I": "Imperfect", "F": "Future",
    "A": "Aorist", "X": "Perfect", "Y": "Pluperfect",
}
_VOICE = {"A": "Active", "M": "Middle", "P": "Passive"}
_MOOD = {
    "I": "Indicative", "S": "Subjunctive", "O": "Optative",
    "D": "Imperative", "N": "Infinitive", "P": "Participle",
}
_CASE = {
    "N": "Nominative", "G": "Genitive", "D": "Dative",
    "A": "Accusative", "V": "Vocative",
}
_NUMBER = {"S": "Singular", "P": "Plural"}
_GENDER = {"M": "Masculine", "F": "Feminine", "N": "Neuter"}
_DEGREE = {"C": "Comparative", "S": "Superlative"}


def human_readable_parsing(pos_code, morph_code):
    """Convert MorphGNT pos + morph codes to human-readable string.

    Example: ('V-', '3AAI-S--') → 'Verb, Aorist Active Indicative, 3rd Person Singular'
    """
    parts = [POS_NAMES.get(pos_code, pos_code)]

    if len(morph_code) >= 8:
        person = morph_code[0]
        tense = morph_code[1]
        voice = morph_code[2]
        mood = morph_code[3]
        case = morph_code[4]
        number = morph_code[5]
        gender = morph_code[6]
        degree = morph_code[7]

        # Tense-voice-mood group (for verbs)
        tvm = []
        if tense != "-":
            tvm.append(_TENSE.get(tense, tense))
        if voice != "-":
            tvm.append(_VOICE.get(voice, voice))
        if mood != "-":
            tvm.append(_MOOD.get(mood, mood))
        if tvm:
            parts.append(" ".join(tvm))

        # Person
        if person != "-":
            parts.append(_PERSON.get(person, person))

        # Case-number-gender group (for nouns/adjectives/participles)
        cng = []
        if case != "-":
            cng.append(_CASE.get(case, case))
        if number != "-":
            cng.append(_NUMBER.get(number, number))
        if gender != "-":
            cng.append(_GENDER.get(gender, gender))
        if cng:
            parts.append(" ".join(cng))

        if degree != "-":
            parts.append(_DEGREE.get(degree, degree))

    return ", ".join(parts)


# ── Database loading ────────────────────────────────────────────────────

def _parse_line(line):
    """Parse one MorphGNT line into a dict.

    Format: BBCCVV POS MORPH text wordform normalized lemma
    """
    cols = line.strip().split()
    if len(cols) < 7:
        return None

    ref = cols[0]
    book_internal = int(ref[0:2])
    chapter = int(ref[2:4])
    verse = int(ref[4:6])

    return {
        "book_internal": book_internal,
        "chapter": chapter,
        "verse": verse,
        "text": cols[3],           # surface form with punctuation
        "wordform": cols[4],       # without punctuation
        "normalized": cols[5],     # normalized spelling
        "lemma": cols[6],          # dictionary headword
        "pos": cols[1],            # part of speech code
        "parsing": cols[2],        # 8-char morphology code
    }


def _normalize_greek(text):
    """NFC-normalize Greek text for consistent matching."""
    return unicodedata.normalize("NFC", text)


def build_db(db_path=None, data_dir=None):
    """Parse all MorphGNT files and load into SQLite. Returns word count."""
    db_path = db_path or MORPHGNT_DB_PATH
    data_dir = data_dir or MORPHGNT_DATA_DIR

    conn = sqlite3.connect(str(db_path))
    conn.execute("DROP TABLE IF EXISTS morphgnt")
    conn.execute("DROP TABLE IF EXISTS glosses")
    conn.executescript("""
        CREATE TABLE morphgnt (
            book INTEGER,
            chapter INTEGER,
            verse INTEGER,
            word_num INTEGER,
            text TEXT,
            normalized TEXT,
            lemma TEXT,
            pos TEXT,
            parsing TEXT,
            PRIMARY KEY (book, chapter, verse, word_num)
        );
        CREATE TABLE glosses (
            lemma TEXT PRIMARY KEY,
            gloss TEXT NOT NULL,
            source TEXT NOT NULL
        );
        CREATE INDEX idx_morphgnt_lemma ON morphgnt(lemma);
        CREATE INDEX idx_morphgnt_text ON morphgnt(text);
        CREATE INDEX idx_morphgnt_normalized ON morphgnt(normalized);
    """)

    total = 0
    for morphgnt_book, filename in sorted(BOOK_FILES.items()):
        filepath = Path(data_dir) / filename
        if not filepath.exists():
            continue

        logos_book = morphgnt_book + LOGOS_OFFSET
        prev_ref = None
        word_num = 0
        rows = []

        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                parsed = _parse_line(line)
                if not parsed:
                    continue

                ref_key = (parsed["chapter"], parsed["verse"])
                if ref_key != prev_ref:
                    word_num = 1
                    prev_ref = ref_key
                else:
                    word_num += 1

                rows.append((
                    logos_book,
                    parsed["chapter"],
                    parsed["verse"],
                    word_num,
                    _normalize_greek(parsed["wordform"]),
                    _normalize_greek(parsed["normalized"]),
                    _normalize_greek(parsed["lemma"]),
                    parsed["pos"],
                    parsed["parsing"],
                ))

        conn.executemany(
            "INSERT INTO morphgnt VALUES (?,?,?,?,?,?,?,?,?)", rows
        )
        total += len(rows)

    conn.commit()
    conn.close()
    return total


# ── Query interface ─────────────────────────────────────────────────────

class MorphGNTCache:
    """Query interface for MorphGNT data."""

    def __init__(self, db_path=None):
        self.db_path = str(db_path or MORPHGNT_DB_PATH)
        self._conn = None

    def _get_conn(self):
        if self._conn is None:
            if not os.path.exists(self.db_path):
                return None
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def is_nt_book(self, logos_book):
        """Check if a Logos book number is in the NT (40-66)."""
        return 40 <= logos_book <= 66

    def lookup_word(self, word, book=None, chapter=None, verse=None):
        """Look up a Greek word form. Returns dict with morphological data or None.

        Searches by normalized form first, then text form.
        Optionally narrow by book/chapter/verse (Logos numbering).
        """
        conn = self._get_conn()
        if not conn:
            return None

        word_nfc = _normalize_greek(word.strip())
        # Strip trailing punctuation for matching
        word_clean = word_nfc.rstrip(".,;·")

        for search_col in ("normalized", "text"):
            sql = f"SELECT * FROM morphgnt WHERE {search_col} = ?"
            params = [word_clean]

            if book is not None:
                sql += " AND book = ?"
                params.append(book)
            if chapter is not None:
                sql += " AND chapter = ?"
                params.append(chapter)
            if verse is not None:
                sql += " AND verse = ?"
                params.append(verse)

            sql += " LIMIT 1"
            row = conn.execute(sql, params).fetchone()
            if row:
                return self._row_to_dict(row)

        return None

    def lookup_verse(self, book, chapter, verse):
        """Get all words in a verse. Returns list of dicts (Logos book numbering)."""
        conn = self._get_conn()
        if not conn:
            return []

        rows = conn.execute(
            "SELECT * FROM morphgnt WHERE book=? AND chapter=? AND verse=? ORDER BY word_num",
            (book, chapter, verse),
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def search_lemma(self, lemma, limit=50):
        """Find all occurrences of a lemma. Returns list of dicts."""
        conn = self._get_conn()
        if not conn:
            return []

        lemma_nfc = _normalize_greek(lemma.strip())
        rows = conn.execute(
            "SELECT * FROM morphgnt WHERE lemma=? ORDER BY book, chapter, verse, word_num LIMIT ?",
            (lemma_nfc, limit),
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def lookup_gloss(self, lemma):
        """Look up English gloss for a lemma. Returns string or None."""
        conn = self._get_conn()
        if not conn:
            return None
        lemma_nfc = _normalize_greek(lemma.strip())
        try:
            row = conn.execute(
                "SELECT gloss FROM glosses WHERE lemma=?", (lemma_nfc,)
            ).fetchone()
            return row[0] if row else None
        except sqlite3.OperationalError:
            return None

    def _row_to_dict(self, row):
        d = dict(row)
        d["parsing_human"] = human_readable_parsing(d["pos"], d["parsing"])
        d["gloss"] = self.lookup_gloss(d["lemma"]) or ""
        return d


# ── Gloss building ──────────────────────────────────────────────────────

# High-frequency function words with manual glosses.
# These are common words whose BDAG articles are too complex for auto-extraction.
_MANUAL_GLOSSES = {
    "ὁ": "the (article)",
    "καί": "and, also, even",
    "αὐτός": "he, she, it; self; same",
    "σύ": "you (singular)",
    "δέ": "but, and, now",
    "ἐν": "in, on, among (+ dat.)",
    "ἐγώ": "I, me",
    "οὐ": "not",
    "εἰμί": "to be, exist",
    "λέγω": "to say, speak, tell",
    "εἰς": "into, to, for (+ acc.)",
    "ἐκ": "out of, from (+ gen.)",
    "ὅς": "who, which, that (rel. pron.)",
    "οὗτος": "this, this one",
    "μή": "not (w/ non-indicative)",
    "ἐπί": "on, upon, over",
    "ὅτι": "that, because",
    "πρός": "to, toward, with (+ acc.)",
    "γάρ": "for, because",
    "διά": "through (+ gen.), because of (+ acc.)",
    "ἀπό": "from, away from (+ gen.)",
    "ἀλλά": "but, rather",
    "πᾶς": "all, every, each",
    "κατά": "down from (+ gen.), according to (+ acc.)",
    "ὡς": "as, like, when",
    "μετά": "with (+ gen.), after (+ acc.)",
    "τίς": "who? which? what?",
    "τις": "someone, something, a certain",
    "περί": "about, concerning (+ gen.)",
    "ὑπό": "by (+ gen.), under (+ acc.)",
    "ἐάν": "if (+ subjunctive)",
    "ἵνα": "in order that, so that",
    "ἤ": "or, than",
    "ἄν": "particle of contingency",
    "οὖν": "therefore, then",
    "μέν": "on the one hand, indeed",
    "τε": "and, both",
    "οὐδέ": "and not, neither, not even",
    "ὅστις": "whoever, whichever",
    "εἰ": "if",
    "ἄρα": "then, therefore",
    "ὅπως": "how, in order that",
    "οὔτε": "neither, nor",
    "ὥστε": "so that, therefore",
    "μηδέ": "and not, nor, not even",
    "ἕως": "until, as far as",
    "ὅπου": "where",
    "ὅτε": "when",
    "ἕκαστος": "each, every",
    "πόθεν": "from where? whence?",
    "πῶς": "how?",
    "ποῦ": "where?",
    "θεός": "God, god, deity",
    "Ἰησοῦς": "Jesus",
    "κύριος": "lord, master, the Lord",
    "Χριστός": "Christ, Anointed One",
    "ἄνθρωπος": "human being, person",
    "πατήρ": "father",
    "υἱός": "son",
    "πνεῦμα": "spirit, wind, breath",
    "ἀδελφός": "brother, fellow believer",
    "γυνή": "woman, wife",
    "ἀνήρ": "man, husband",
    "ὄνομα": "name",
    "λόγος": "word, message, reason",
    "οὐρανός": "heaven, sky",
    "ἔργον": "work, deed, action",
    "γῆ": "earth, land, ground",
    "ὕδωρ": "water",
    "αἷμα": "blood",
    "σῶμα": "body",
    "ὀφθαλμός": "eye",
    "χείρ": "hand",
    "πρόσωπον": "face, presence",
    "ψυχή": "soul, life, self",
    "καρδία": "heart",
    "ἡμέρα": "day",
    "ἔτος": "year",
    "ὥρα": "hour, time",
    "οἶκος": "house, household",
    "πόλις": "city",
    "ὁδός": "way, road, path",
    "ἔθνος": "nation; (pl.) Gentiles",
    "λαός": "people",
    "βασιλεία": "kingdom, reign",
    "ἐκκλησία": "church, assembly",
    "κόσμος": "world, creation, order",
    "νόμος": "law",
    "πίστις": "faith, trust, faithfulness",
    "ἁμαρτία": "sin",
    "δικαιοσύνη": "righteousness, justice",
    "χάρις": "grace, favor, thanks",
    "ἀγάπη": "love",
    "ζωή": "life",
    "θάνατος": "death",
    "ἀλήθεια": "truth",
    "εἰρήνη": "peace",
    "δόξα": "glory, splendor, opinion",
    "δύναμις": "power, ability, miracle",
    "ἐξουσία": "authority, power, right",
    "σοφία": "wisdom",
    "γνῶσις": "knowledge",
    "ἐλπίς": "hope, expectation",
    "σάρξ": "flesh, body",
    "σταυρός": "cross",
    "εὐαγγέλιον": "gospel, good news",
    "ἱερόν": "temple",
    "ἁμαρτωλός": "sinner, sinful",
    "μαθητής": "disciple, learner",
    "ἀπόστολος": "apostle, messenger",
    "προφήτης": "prophet",
    "γραφή": "writing, Scripture",
    "Μωϋσῆς": "Moses",
    "Πέτρος": "Peter",
    "Παῦλος": "Paul",
    "Ἀβραάμ": "Abraham",
    "Δαυίδ": "David",
    "Ἰωάννης": "John",
    "Σίμων": "Simon",
    "Ἰάκωβος": "James",
    "Ἰσραήλ": "Israel",
    "Ἱερουσαλήμ": "Jerusalem",
    "γίνομαι": "to become, be, happen",
    "ἔχω": "to have, hold",
    "ποιέω": "to do, make",
    "ἔρχομαι": "to come, go",
    "δίδωμι": "to give",
    "γινώσκω": "to know, understand",
    "ἀκούω": "to hear, listen",
    "ὁράω": "to see, perceive",
    "βλέπω": "to see, look at",
    "πιστεύω": "to believe, trust",
    "λαμβάνω": "to take, receive",
    "ἐσθίω": "to eat",
    "πίνω": "to drink",
    "γράφω": "to write",
    "ἀγαπάω": "to love",
    "ζάω": "to live",
    "θέλω": "to wish, want, will",
    "δύναμαι": "to be able, can",
    "ζητέω": "to seek, look for",
    "καλέω": "to call, name, invite",
    "κρίνω": "to judge, decide",
    "βαπτίζω": "to baptize, wash",
    "ἀποθνῄσκω": "to die",
    "ἐγείρω": "to raise, wake up",
    "σῴζω": "to save, deliver, heal",
    "ἀποκτείνω": "to kill",
    "ἀποστέλλω": "to send, commission",
    "κηρύσσω": "to preach, proclaim",
    "διδάσκω": "to teach",
    "προσεύχομαι": "to pray",
    "περιπατέω": "to walk, live, conduct oneself",
    "αἴρω": "to lift up, take away",
    "βάλλω": "to throw, cast, put",
    "ἄγω": "to lead, bring, go",
    "μέγας": "great, large",
    "πολύς": "much, many",
    "ἀγαθός": "good",
    "κακός": "bad, evil",
    "καλός": "good, beautiful, noble",
    "δίκαιος": "righteous, just",
    "πιστός": "faithful, trustworthy, believing",
    "ἅγιος": "holy, saint",
    "ἀληθής": "true, genuine",
    "νεκρός": "dead",
    "ἕτερος": "other, another, different",
    "ἄλλος": "other, another",
    "πρῶτος": "first",
    "ἔσχατος": "last, final",
    "νέος": "new, young",
    "μόνος": "alone, only",
    "ὅλος": "whole, entire, complete",
}


def _extract_gloss_from_bdag(text):
    """Extract short English gloss from BDAG article text."""
    import re
    if not text:
        return None

    first_line = text.split("\n")[0]

    # Strategy 1: Scan each ')' for a gloss after reference parentheticals.
    # The gloss is English text between the last ref paren and Greek examples.
    for m in re.finditer(r"\)", first_line):
        after = first_line[m.end() :].strip().lstrip(".;,— ")
        if not after or not re.match(r"[a-z]", after):
            continue
        # Extract text up to first Greek character
        gloss = re.split(r"[\u0370-\u03FF\u1F00-\u1FFF]", after)[0]
        # Remove Bible references (e.g. "Ro 2:17")
        gloss = re.sub(r"\s+[A-Z][a-z]{0,2}\s+\d+[,:]\d+.*$", "", gloss)
        gloss = re.sub(r"\s*\(.*$", "", gloss)
        # Strip leading/trailing grammatical abbreviations (aor., pass., etc.)
        words = gloss.strip().split()
        while words and words[0].endswith(".") and len(words[0]) <= 6:
            words.pop(0)
        while words and words[-1].endswith(".") and len(words[-1]) <= 6:
            words.pop()
        gloss = " ".join(words).strip().rstrip(",;.—: ")
        if len(gloss.split()) < 1 or len(gloss) <= 2:
            continue
        if len(gloss) > 60:
            gloss = gloss[:60].rsplit(" ", 1)[0].rstrip(",;.")
        if len(gloss) > 2:
            return gloss

    # Strategy 2: Numbered definition ①
    m = re.search(r"①\s*(.+?)(?:\n|$)", text)
    if m:
        defn = m.group(1).strip()
        defn = re.sub(r"\([^)]{0,200}\)", "", defn)
        defn = re.sub(r"\s+[A-Z][a-z]{0,2}\s+\d+[,:]\d+.*$", "", defn)
        defn = re.sub(r",?\s*as (?:gener|class)\.\s.*$", "", defn)
        defn = defn.strip().rstrip(",;.—")
        if defn.startswith("w.") or defn.startswith("in our lit"):
            defn = None
        if defn and len(defn) > 60:
            defn = defn[:60].rsplit(" ", 1)[0].rstrip(",;.")
        if defn and len(defn) > 2:
            return defn

    # Strategy 3: 'indecl.' proper noun
    m = re.search(
        r"indecl\.\s+([A-Z][a-z].+?)(?:\s+[A-Z][a-z]{0,2}\s+\d|[.;]|$)",
        first_line,
    )
    if m:
        defn = m.group(1).strip().rstrip(",;.")
        if len(defn) > 60:
            defn = defn[:60].rsplit(" ", 1)[0].rstrip(",;.")
        if len(defn) > 2:
            return defn

    return None


def build_glosses(db_path=None):
    """Build lemma→gloss table from BDAG articles + manual overrides.

    Requires: resource_index.db and LogosBatchReader (for BDAG access).
    Returns number of glosses stored.
    """
    import re
    db_path = db_path or MORPHGNT_DB_PATH
    conn = sqlite3.connect(str(db_path))

    conn.execute("DROP TABLE IF EXISTS glosses")
    conn.execute("""
        CREATE TABLE glosses (
            lemma TEXT PRIMARY KEY,
            gloss TEXT NOT NULL,
            source TEXT NOT NULL
        )
    """)

    # Step 1: Manual glosses for function words and common terms
    for lemma, gloss in _MANUAL_GLOSSES.items():
        conn.execute(
            "INSERT OR REPLACE INTO glosses VALUES (?,?,?)",
            (_normalize_greek(lemma), gloss, "manual"),
        )

    # Step 2: BDAG extraction for remaining lemmas
    lemmas = [
        r[0] for r in conn.execute("SELECT DISTINCT lemma FROM morphgnt").fetchall()
    ]

    try:
        from resource_index import ResourceIndex
        from logos_batch import LogosBatchReader

        idx = ResourceIndex(
            str(Path(__file__).parent / "resource_index.db")
        )
        reader = LogosBatchReader()

        for lemma in lemmas:
            # Skip if already has a manual gloss
            existing = conn.execute(
                "SELECT 1 FROM glosses WHERE lemma=?", (lemma,)
            ).fetchone()
            if existing:
                continue

            results = idx.lookup(lemma, "BDAG.logos4", limit=1)
            if results and results[0]["score"] == 100:
                text = reader.read_article(
                    "BDAG.logos4", results[0]["article_num"], max_chars=2000
                )
                gloss = _extract_gloss_from_bdag(text)
                if gloss:
                    conn.execute(
                        "INSERT OR REPLACE INTO glosses VALUES (?,?,?)",
                        (lemma, gloss, "bdag"),
                    )

        reader.close()
    except Exception as e:
        print(f"BDAG extraction skipped: {e}")

    conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM glosses").fetchone()[0]
    conn.close()
    return total


# ── Singleton for app use ───────────────────────────────────────────────

_cache_instance = None


def get_cache(db_path=None):
    """Get or create the singleton MorphGNT cache."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = MorphGNTCache(db_path)
    return _cache_instance


def ensure_db(db_path=None, data_dir=None):
    """Build the DB if it doesn't exist. Returns word count or 0 if already built."""
    db_path = db_path or MORPHGNT_DB_PATH
    if os.path.exists(str(db_path)):
        return 0
    return build_db(db_path, data_dir)


# ── CLI ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "build":
        print(f"Building MorphGNT cache from {MORPHGNT_DATA_DIR} ...")
        count = build_db()
        print(f"Loaded {count} words into {MORPHGNT_DB_PATH}")
    elif cmd == "glosses":
        print("Building glosses from BDAG + manual table ...")
        count = build_glosses()
        print(f"Stored {count} glosses in {MORPHGNT_DB_PATH}")
    elif cmd == "test":
        ensure_db()
        cache = get_cache()
        result = cache.lookup_word("ἠγάπησεν", book=43, chapter=3, verse=16)
        if result:
            print(f"Found: {result['lemma']} — {result['parsing_human']}")
            print(f"Gloss: {result.get('gloss', '(none)')}")
        else:
            print("Not found (DB may be empty)")
    else:
        print("Usage: python3 morphgnt_cache.py build|glosses|test")
