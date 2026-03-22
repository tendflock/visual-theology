"""
SQLite cache for extracted Logos content.

Caches article text, article lists, TOC data, and bible verse-to-article
mappings so that repeated reads don't require re-extracting from the
native Logos library.

Usage:
    cache = LogosCache()
    text = cache.get_article("ESV.logos4", 42)
    if text is None:
        text = reader.read_article("ESV.logos4", 42)
        cache.put_article("ESV.logos4", 42, "JN.3", text)
"""

import json
import os
import sqlite3
import sys


class LogosCache:
    """SQLite cache for extracted Logos content.

    All data is stored in a single SQLite database. Tables are created
    automatically on first use.
    """

    DB_PATH = "/Volumes/External/Logos4/tools/logos_cache.db"

    def __init__(self, db_path=None):
        """Initialize cache database and create tables if needed.

        Args:
            db_path: path to the SQLite database file. Defaults to DB_PATH.
        """
        self._db_path = db_path or self.DB_PATH
        self._conn = sqlite3.connect(self._db_path)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._create_tables()

    def _create_tables(self):
        """Create cache tables if they don't exist."""
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS articles (
                resource_file TEXT,
                article_num INTEGER,
                article_id TEXT,
                text TEXT,
                char_count INTEGER,
                cached_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (resource_file, article_num)
            );

            CREATE TABLE IF NOT EXISTS article_lists (
                resource_file TEXT PRIMARY KEY,
                articles_json TEXT,
                cached_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS toc_cache (
                resource_file TEXT PRIMARY KEY,
                toc_json TEXT,
                cached_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS bible_verse_index (
                resource_file TEXT,
                book_num INTEGER,
                chapter INTEGER,
                article_num INTEGER,
                article_id TEXT,
                cached_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (resource_file, book_num, chapter)
            );

            CREATE TABLE IF NOT EXISTS commentary_verse_index (
                resource_file TEXT,
                article_num INTEGER,
                article_id TEXT,
                heading TEXT,
                chapter INTEGER,
                verse_start INTEGER,
                verse_end INTEGER,
                cached_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (resource_file, article_num)
            );
            CREATE INDEX IF NOT EXISTS idx_comm_verse
                ON commentary_verse_index(resource_file, chapter, verse_start);

            CREATE TABLE IF NOT EXISTS navindex_cache (
                resource_file TEXT,
                entry_type TEXT,
                ref_key TEXT,
                article_num INTEGER,
                offset INTEGER,
                name TEXT,
                cached_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_navindex_ref
                ON navindex_cache(resource_file, ref_key);
            CREATE INDEX IF NOT EXISTS idx_navindex_file
                ON navindex_cache(resource_file, entry_type);
        """)
        self._conn.commit()

    # ── Articles ──────────────────────────────────────────────────────────

    def get_article(self, resource_file, article_num):
        """Get cached article text, or None if not cached.

        Args:
            resource_file: resource filename (e.g. "ESV.logos4")
            article_num: integer article number

        Returns:
            Cached text string, or None if not in cache.
        """
        row = self._conn.execute(
            "SELECT text FROM articles WHERE resource_file = ? AND article_num = ?",
            (resource_file, article_num),
        ).fetchone()
        return row[0] if row else None

    def put_article(self, resource_file, article_num, article_id, text):
        """Cache an article's text.

        Args:
            resource_file: resource filename
            article_num: integer article number
            article_id: the article's string ID
            text: full text content
        """
        char_count = len(text) if text else 0
        self._conn.execute(
            """INSERT OR REPLACE INTO articles
               (resource_file, article_num, article_id, text, char_count, cached_at)
               VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
            (resource_file, article_num, article_id, text, char_count),
        )
        self._conn.commit()

    # ── Article Lists ─────────────────────────────────────────────────────

    def get_article_list(self, resource_file):
        """Get cached article list, or None.

        Returns:
            List of [article_num, article_id] pairs, or None if not cached.
        """
        row = self._conn.execute(
            "SELECT articles_json FROM article_lists WHERE resource_file = ?",
            (resource_file,),
        ).fetchone()
        if row is None:
            return None
        try:
            return json.loads(row[0])
        except (json.JSONDecodeError, TypeError):
            return None

    def put_article_list(self, resource_file, articles):
        """Cache an article list.

        Args:
            resource_file: resource filename
            articles: list of (article_num, article_id) tuples or lists
        """
        articles_json = json.dumps(articles, ensure_ascii=False)
        self._conn.execute(
            """INSERT OR REPLACE INTO article_lists
               (resource_file, articles_json, cached_at)
               VALUES (?, ?, CURRENT_TIMESTAMP)""",
            (resource_file, articles_json),
        )
        self._conn.commit()

    # ── TOC ───────────────────────────────────────────────────────────────

    def get_toc(self, resource_file):
        """Get cached TOC data, or None.

        Returns:
            TOC data as a string, or None if not cached.
        """
        row = self._conn.execute(
            "SELECT toc_json FROM toc_cache WHERE resource_file = ?",
            (resource_file,),
        ).fetchone()
        if row is None:
            return None
        return row[0]

    def put_toc(self, resource_file, toc_data):
        """Cache TOC data.

        Args:
            resource_file: resource filename
            toc_data: TOC content (raw text or JSON string)
        """
        self._conn.execute(
            """INSERT OR REPLACE INTO toc_cache
               (resource_file, toc_json, cached_at)
               VALUES (?, ?, CURRENT_TIMESTAMP)""",
            (resource_file, toc_data),
        )
        self._conn.commit()

    # ── Bible Verse Index ─────────────────────────────────────────────────

    def get_bible_verse_index(self, resource_file, book_num, chapter):
        """Get cached verse-to-article mapping.

        Args:
            resource_file: Bible resource filename
            book_num: book number (e.g. 64 for John)
            chapter: chapter number

        Returns:
            Tuple of (article_num, article_id), or None if not cached.
        """
        row = self._conn.execute(
            """SELECT article_num, article_id FROM bible_verse_index
               WHERE resource_file = ? AND book_num = ? AND chapter = ?""",
            (resource_file, book_num, chapter),
        ).fetchone()
        if row is None:
            return None
        return (row[0], row[1])

    def put_bible_verse_index(self, resource_file, book_num, chapter, article_num, article_id):
        """Cache verse-to-article mapping.

        Args:
            resource_file: Bible resource filename
            book_num: book number
            chapter: chapter number
            article_num: the article number containing this chapter
            article_id: the article's string ID
        """
        self._conn.execute(
            """INSERT OR REPLACE INTO bible_verse_index
               (resource_file, book_num, chapter, article_num, article_id, cached_at)
               VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
            (resource_file, book_num, chapter, article_num, article_id),
        )
        self._conn.commit()

    # ── Commentary Verse Index ─────────────────────────────────────────

    def get_commentary_articles(self, resource_file, chapter, verse_start=None):
        """Find cached commentary articles for a chapter/verse.

        Returns list of dicts: {article_num, article_id, heading, chapter,
                                verse_start, verse_end}
        """
        if verse_start is not None:
            rows = self._conn.execute(
                """SELECT article_num, article_id, heading, chapter,
                          verse_start, verse_end
                   FROM commentary_verse_index
                   WHERE resource_file = ? AND chapter = ?
                     AND verse_start <= ? AND verse_end >= ?
                   ORDER BY (verse_end - verse_start) ASC""",
                (resource_file, chapter, verse_start, verse_start),
            ).fetchall()
        else:
            rows = self._conn.execute(
                """SELECT article_num, article_id, heading, chapter,
                          verse_start, verse_end
                   FROM commentary_verse_index
                   WHERE resource_file = ? AND chapter = ?
                   ORDER BY verse_start ASC""",
                (resource_file, chapter),
            ).fetchall()
        return [
            {"article_num": r[0], "article_id": r[1], "heading": r[2],
             "chapter": r[3], "verse_start": r[4], "verse_end": r[5]}
            for r in rows
        ]

    def is_commentary_indexed(self, resource_file):
        """Check if a commentary has been indexed."""
        row = self._conn.execute(
            "SELECT 1 FROM commentary_verse_index WHERE resource_file = ? LIMIT 1",
            (resource_file,),
        ).fetchone()
        return row is not None

    def put_commentary_article(self, resource_file, article_num, article_id,
                                heading, chapter, verse_start, verse_end):
        """Cache a commentary article's verse mapping."""
        self._conn.execute(
            """INSERT OR REPLACE INTO commentary_verse_index
               (resource_file, article_num, article_id, heading,
                chapter, verse_start, verse_end, cached_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
            (resource_file, article_num, article_id, heading,
             chapter, verse_start, verse_end),
        )
        self._conn.commit()

    def put_commentary_articles_batch(self, resource_file, entries):
        """Cache multiple commentary article verse mappings at once.

        entries: list of (article_num, article_id, heading, chapter,
                          verse_start, verse_end) tuples
        """
        self._conn.executemany(
            """INSERT OR REPLACE INTO commentary_verse_index
               (resource_file, article_num, article_id, heading,
                chapter, verse_start, verse_end, cached_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
            [(resource_file, *e) for e in entries],
        )
        self._conn.commit()

    # ── Navigation Index Cache ─────────────────────────────────────────

    def get_navindex(self, resource_file):
        """Get cached navigation index for a resource, or None."""
        rows = self._conn.execute(
            "SELECT entry_type, ref_key, article_num, offset, name FROM navindex_cache WHERE resource_file = ?",
            (resource_file,),
        ).fetchall()
        if not rows:
            return None
        refs = []
        topics = []
        for r in rows:
            if r[0] == "REF":
                refs.append({"ref": r[1], "article": r[2], "offset": r[3]})
            else:
                topics.append({"key": r[1], "name": r[4], "article": r[2], "offset": r[3]})
        return {"references": refs, "topics": topics}

    def put_navindex(self, resource_file, references, topics):
        """Cache a navigation index."""
        self._conn.execute("DELETE FROM navindex_cache WHERE resource_file = ?", (resource_file,))
        for r in references:
            self._conn.execute(
                "INSERT INTO navindex_cache (resource_file, entry_type, ref_key, article_num, offset) VALUES (?, 'REF', ?, ?, ?)",
                (resource_file, r["ref"], r["article"], r["offset"]),
            )
        for t in topics:
            self._conn.execute(
                "INSERT INTO navindex_cache (resource_file, entry_type, ref_key, article_num, offset, name) VALUES (?, 'TOPIC', ?, ?, ?, ?)",
                (resource_file, t["key"], t["article"], t["offset"], t.get("name")),
            )
        self._conn.commit()

    def find_article_for_reference(self, resource_file, bible_ref):
        """Find which article contains a Bible reference.

        bible_ref: e.g. 'bible.66.1.16' for Romans 1:16
        Returns (article_num, offset) or None.
        """
        # Try exact match first
        row = self._conn.execute(
            "SELECT article_num, offset FROM navindex_cache WHERE resource_file = ? AND ref_key = ?",
            (resource_file, bible_ref),
        ).fetchone()
        if row:
            return (row[0], row[1])
        # Try range match: 'bible.66.1.16' matches 'bible.66.1.16-66.1.17'
        row = self._conn.execute(
            "SELECT article_num, offset FROM navindex_cache WHERE resource_file = ? AND ref_key LIKE ? AND entry_type = 'REF' ORDER BY ref_key LIMIT 1",
            (resource_file, bible_ref + "%"),
        ).fetchone()
        if row:
            return (row[0], row[1])
        # Try chapter-level match
        chapter_ref = ".".join(bible_ref.split(".")[:4])  # bible.66.1
        row = self._conn.execute(
            "SELECT article_num, offset FROM navindex_cache WHERE resource_file = ? AND ref_key LIKE ? AND entry_type = 'REF' ORDER BY ref_key LIMIT 1",
            (resource_file, chapter_ref + "%"),
        ).fetchone()
        if row:
            return (row[0], row[1])
        return None

    # ── Utilities ─────────────────────────────────────────────────────────

    def stats(self):
        """Return a dict of cache statistics."""
        stats = {}
        for table in ("articles", "article_lists", "toc_cache", "bible_verse_index"):
            row = self._conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
            stats[table] = row[0]
        return stats

    def clear(self, table=None):
        """Clear cached data.

        Args:
            table: specific table to clear, or None to clear all tables.
        """
        if table:
            self._conn.execute(f"DELETE FROM {table}")
        else:
            for t in ("articles", "article_lists", "toc_cache", "bible_verse_index"):
                self._conn.execute(f"DELETE FROM {t}")
        self._conn.commit()

    def close(self):
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


# ── CLI ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    cache = LogosCache()
    stats = cache.stats()
    print("Logos Cache Statistics:")
    for table, count in stats.items():
        print(f"  {table}: {count} entries")
    cache.close()
