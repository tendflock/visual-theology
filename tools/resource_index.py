"""One-time index builder for lexicon and grammar resources.

Reads article headwords (first line of each article) and builds a SQLite
index mapping searchable terms → article numbers. This replaces the broken
content-sampling search in companion_tools.py.

Usage:
    idx = ResourceIndex("path/to/index.db")
    idx.build_index_for_resource("EXGDCTNT.logos4", resource_type="lexicon")
    results = idx.lookup("ματαιόω", "EXGDCTNT.logos4")
"""
import os
import re
import sqlite3
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(__file__))
from logos_batch import LogosBatchReader

# Wallace chapter structure: chapter prefix → topic
# Derived from manual inspection of article ID patterns and content
WALLACE_CHAPTERS = {
    "G01": "Introduction to Syntax",
    "G02": "The Cases: Overview",
    "G03": "Nominative Case",
    "G04": "Vocative Case",
    "G05": "Genitive Case",
    "G06": "Dative Case",
    "G07": "Accusative Case",
    "G08": "The Article: Overview",
    "G09": "The Article: Special Uses and Non-Uses",
    "G10": "Adjectives",
    "G11": "Pronouns",
    "G12": "Prepositions",
    "G13": "Person and Number",
    "G14": "Voice: Active, Middle, Passive",
    "G15": "Mood: Overview, Indicative, Subjunctive, Optative, Imperative",
    "G16": "The Tenses: Overview, Present, Imperfect",
    "G17": "Aorist, Future, Perfect, Pluperfect",
    "G18A": "Infinitive",
    "G18B": "Infinitive continued",
    "G18C": "Participle: Adverbial",
    "G18D": "Participle: Adjectival",
    "G18E": "Participle: Substantival, Independent, Genitive Absolute",
    "G18F": "Participle: Periphrastic, Redundant",
    "G19": "Clauses: Relative, Conditional, Causal, Temporal, Result, Purpose",
    "G20": "Word Order, Sentences",
    "G21A": "Discourse Analysis: Cohesion",
    "G21B": "Discourse Analysis: Prominence",
    "G21C": "Discourse Analysis continued",
    "G21D": "Discourse Analysis continued",
}

WALLACE_TOPICS = {
    "G03": ["nominative", "subject", "predicate nominative", "nominative absolute"],
    "G05": ["genitive", "possessive", "subjective genitive", "objective genitive",
             "partitive", "genitive absolute", "ablative"],
    "G06": ["dative", "indirect object", "instrumental", "locative", "dative of advantage"],
    "G07": ["accusative", "direct object", "double accusative"],
    "G08": ["article", "definite article", "anarthrous"],
    "G14": ["voice", "active voice", "middle voice", "passive voice", "deponent",
             "middle passive", "reflexive", "causative"],
    "G15": ["mood", "indicative", "subjunctive", "optative", "imperative",
             "prohibition", "hortatory", "deliberative"],
    "G16": ["tense", "present tense", "imperfect", "progressive", "iterative",
             "gnomic", "historical present", "conative", "customary"],
    "G17": ["aorist", "future", "perfect", "pluperfect", "constative",
             "ingressive", "consummative", "gnomic aorist", "epistolary aorist",
             "proleptic", "intensive perfect", "dramatic aorist"],
    "G18A": ["infinitive", "purpose", "result", "complementary", "substantival infinitive"],
    "G18C": ["participle", "adverbial participle", "temporal", "causal", "conditional",
              "concessive", "purpose participle", "result participle", "attendant circumstance"],
    "G18D": ["adjectival participle", "attributive", "predicate"],
    "G18E": ["substantival participle", "genitive absolute", "independent participle",
              "periphrastic"],
    "G19": ["clause", "relative clause", "conditional", "first class condition",
             "second class condition", "third class condition", "fourth class condition",
             "causal clause", "temporal clause", "result clause", "purpose clause",
             "concessive clause"],
}


class ResourceIndex:
    """SQLite-backed index for fast lexicon/grammar lookups."""

    def __init__(self, db_path):
        self.db_path = db_path
        self._ensure_tables()

    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_tables(self):
        conn = self._conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS resource_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resource_file TEXT NOT NULL,
                article_num INTEGER NOT NULL,
                article_id TEXT NOT NULL,
                headword TEXT,
                headword_translit TEXT,
                gloss TEXT,
                entry_type TEXT,
                UNIQUE(resource_file, article_num, headword)
            );
            CREATE INDEX IF NOT EXISTS idx_headword ON resource_entries(headword);
            CREATE INDEX IF NOT EXISTS idx_translit ON resource_entries(headword_translit);
            CREATE INDEX IF NOT EXISTS idx_gloss ON resource_entries(gloss);
            CREATE INDEX IF NOT EXISTS idx_resource ON resource_entries(resource_file);
        """)
        conn.commit()
        conn.close()

    def build_index_for_resource(self, resource_file, resource_type="lexicon"):
        if resource_type == "grammar":
            return self._build_grammar_index(resource_file)
        return self._build_lexicon_index(resource_file)

    def _build_lexicon_index(self, resource_file):
        reader = LogosBatchReader()
        try:
            articles = reader.list_articles(resource_file)
            if not articles:
                return 0

            conn = self._conn()
            conn.execute("DELETE FROM resource_entries WHERE resource_file = ?",
                         (resource_file,))

            count = 0
            batch = []
            for art_num, art_id in articles:
                if art_id.startswith("ABBR") or art_id.startswith("FTN"):
                    continue
                # BDAG: only index R.xxx lexicon entries (skip A.xxx abbreviations,
                # NOTE, TITLE, FOREWORD, LET, DIV, etc.)
                if resource_file.startswith("BDAG") and not art_id.startswith("R."):
                    continue

                text = reader.read_article(resource_file, art_num, max_chars=300)
                if not text or len(text.strip()) < 3:
                    continue

                headword, translit, gloss = self._extract_headword(text)
                if not headword and not translit:
                    translit = art_id.lower()

                # Normalize Unicode to NFC for consistent matching
                if headword:
                    headword = unicodedata.normalize('NFC', headword)

                batch.append((
                    resource_file, art_num, art_id,
                    headword, translit, gloss, "lemma"
                ))
                count += 1

                if len(batch) >= 500:
                    conn.executemany(
                        """INSERT OR REPLACE INTO resource_entries
                           (resource_file, article_num, article_id, headword,
                            headword_translit, gloss, entry_type)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        batch
                    )
                    conn.commit()
                    batch = []

            if batch:
                conn.executemany(
                    """INSERT OR REPLACE INTO resource_entries
                       (resource_file, article_num, article_id, headword,
                        headword_translit, gloss, entry_type)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    batch
                )
                conn.commit()

            conn.close()
            return count
        finally:
            reader.close()

    def _extract_headword(self, text):
        first_line = text.split('\n')[0].strip()

        greek_match = re.search(
            r'([\u0370-\u03FF\u1F00-\u1FFF][\u0370-\u03FF\u1F00-\u1FFF\u0300-\u036F,\s]*)',
            first_line)
        hebrew_match = re.search(
            r'([\u0590-\u05FF][\u0590-\u05FF\u0300-\u036F\s]*)',
            first_line)

        headword = None
        if greek_match:
            headword = greek_match.group(1).split(',')[0].split()[0].strip()
        elif hebrew_match:
            headword = hebrew_match.group(1).split()[0].strip()

        translit = None
        parts = re.split(r'\s{2,}', first_line)
        if len(parts) >= 2:
            for part in parts[1:]:
                part = part.strip().rstrip('*\ufeff')
                if part and re.match(r'^[a-zA-Z\u0101\u0113\u012B\u014D\u016B\u00E0-\u00FC\-\u02BE\u02BF]+$', part):
                    translit = part.lower()
                    break

        gloss = None
        if len(parts) >= 3:
            for part in reversed(parts):
                part = part.strip().rstrip('*\ufeff')
                if part and re.match(r'^[a-zA-Z]', part) and not re.match(
                        r'^[a-zA-Z\u0101\u0113\u012B\u014D\u016B\u00E0-\u00FC\-\u02BE\u02BF]+$', part):
                    gloss = part.lower()
                    break

        if headword:
            nfkd = unicodedata.normalize('NFKD', headword)
            translit_from_greek = ''.join(c for c in nfkd if not unicodedata.combining(c)).lower()
            if not translit:
                translit = translit_from_greek

        return headword, translit, gloss

    def _build_grammar_index(self, resource_file):
        reader = LogosBatchReader()
        try:
            articles = reader.list_articles(resource_file)
            if not articles:
                return 0

            conn = self._conn()
            conn.execute("DELETE FROM resource_entries WHERE resource_file = ?",
                         (resource_file,))

            count = 0
            chapter_ranges = {}
            for art_num, art_id in articles:
                match = re.match(r'(G\d+[A-F]?|CH\d+|PT\d+|SSC|IDX|SYN)', art_id)
                if match:
                    prefix = match.group(1)
                    if prefix not in chapter_ranges:
                        chapter_ranges[prefix] = {"start": art_num, "end": art_num, "art_id_start": art_id}
                    chapter_ranges[prefix]["end"] = art_num

            for prefix, info in chapter_ranges.items():
                topic = WALLACE_CHAPTERS.get(prefix, prefix)
                keywords = WALLACE_TOPICS.get(prefix, [])

                conn.execute(
                    """INSERT OR REPLACE INTO resource_entries
                       (resource_file, article_num, article_id, headword,
                        headword_translit, gloss, entry_type)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (resource_file, info["start"], info["art_id_start"],
                     topic, prefix.lower(), topic.lower(), "chapter")
                )
                count += 1

                for kw in keywords:
                    conn.execute(
                        """INSERT INTO resource_entries
                           (resource_file, article_num, article_id, headword,
                            headword_translit, gloss, entry_type)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (resource_file, info["start"], info["art_id_start"],
                         kw, kw.lower(), topic.lower(), "topic")
                    )
                    count += 1

            conn.commit()
            conn.close()
            return count
        finally:
            reader.close()

    def lookup(self, query, resource_file, limit=5):
        conn = self._conn()
        # Normalize query to NFC for consistent matching against stored headwords
        query = unicodedata.normalize('NFC', query)
        query_lower = query.lower().strip()
        query_norm = unicodedata.normalize('NFKD', query_lower)
        query_norm = ''.join(c for c in query_norm if not unicodedata.combining(c))

        results = []

        # 1. Exact headword match
        rows = conn.execute(
            "SELECT article_num, article_id, headword, gloss, entry_type "
            "FROM resource_entries WHERE resource_file = ? AND headword = ? LIMIT ?",
            (resource_file, query.strip(), limit)
        ).fetchall()
        for r in rows:
            results.append({**dict(r), "score": 100})

        # 2. Headword prefix match
        if len(results) < limit:
            rows = conn.execute(
                "SELECT article_num, article_id, headword, gloss, entry_type "
                "FROM resource_entries WHERE resource_file = ? AND headword LIKE ? AND headword != ? LIMIT ?",
                (resource_file, query.strip() + '%', query.strip(), limit - len(results))
            ).fetchall()
            for r in rows:
                results.append({**dict(r), "score": 80})

        # 3. Transliterated match
        if len(results) < limit:
            rows = conn.execute(
                "SELECT article_num, article_id, headword, gloss, entry_type "
                "FROM resource_entries WHERE resource_file = ? AND headword_translit LIKE ? LIMIT ?",
                (resource_file, '%' + query_norm + '%', limit - len(results))
            ).fetchall()
            for r in rows:
                if not any(e["article_num"] == r["article_num"] for e in results):
                    results.append({**dict(r), "score": 60})

        # 4. Gloss match
        if len(results) < limit:
            rows = conn.execute(
                "SELECT article_num, article_id, headword, gloss, entry_type "
                "FROM resource_entries WHERE resource_file = ? AND gloss LIKE ? LIMIT ?",
                (resource_file, '%' + query_lower + '%', limit - len(results))
            ).fetchall()
            for r in rows:
                if not any(e["article_num"] == r["article_num"] for e in results):
                    results.append({**dict(r), "score": 40})

        # 5. Article ID match
        if len(results) < limit:
            rows = conn.execute(
                "SELECT article_num, article_id, headword, gloss, entry_type "
                "FROM resource_entries WHERE resource_file = ? AND article_id LIKE ? LIMIT ?",
                (resource_file, '%' + query_lower.upper() + '%', limit - len(results))
            ).fetchall()
            for r in rows:
                if not any(e["article_num"] == r["article_num"] for e in results):
                    results.append({**dict(r), "score": 20})

        conn.close()
        return sorted(results, key=lambda x: -x["score"])[:limit]

    def is_indexed(self, resource_file):
        conn = self._conn()
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM resource_entries WHERE resource_file = ?",
            (resource_file,)
        ).fetchone()
        conn.close()
        return row["cnt"] > 0
