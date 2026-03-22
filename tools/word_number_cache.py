"""Word-number-to-verse mapping cache.

Extracts word number → Bible verse mappings from WordSenses.lbswsd
(an encrypted Logos database) and caches them in a local SQLite database.
This enables SupplementalData tools to query by passage.

Usage:
    cache = WordNumberCache("path/to/cache.db")
    if not cache.is_built():
        cache.build()  # One-time, ~5 minutes
    word_refs = cache.get_word_numbers(45, 1)  # Romans 1
"""
import binascii
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(__file__))
from logos_batch import LogosBatchReader


def _protestant_to_logos(book):
    """Convert Protestant book number (1-66) to Logos canonical number."""
    if book <= 39:
        return book
    return book + 21


class WordNumberCache:
    """SQLite-backed cache mapping word numbers to Bible verses."""

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
            CREATE TABLE IF NOT EXISTS word_verse_map (
                word_ref TEXT PRIMARY KEY,
                logos_book INTEGER NOT NULL,
                chapter INTEGER NOT NULL,
                verse INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_book_chapter
                ON word_verse_map(logos_book, chapter);
            CREATE INDEX IF NOT EXISTS idx_book_chapter_verse
                ON word_verse_map(logos_book, chapter, verse);
        """)
        conn.commit()
        conn.close()

    def is_built(self):
        conn = self._conn()
        row = conn.execute("SELECT COUNT(*) as cnt FROM word_verse_map").fetchone()
        conn.close()
        return row["cnt"] > 0

    def count(self):
        conn = self._conn()
        row = conn.execute("SELECT COUNT(*) as cnt FROM word_verse_map").fetchone()
        conn.close()
        return row["cnt"]

    def build(self):
        """One-time build: extract all mappings from WordSenses.lbswsd."""
        reader = LogosBatchReader()
        conn = self._conn()
        try:
            conn.execute("DELETE FROM word_verse_map")
            conn.commit()

            batch_size = 1000
            total_inserted = 0
            offset = 0

            while True:
                rows = reader.query_dataset(
                    "WordSenses.lbswsd", "WordSenses.db",
                    f"SELECT DISTINCT hex(wn.Reference) as wn_ref, "
                    f"hex(br.Reference) as bible_ref "
                    f"FROM WordNumbers wn "
                    f"JOIN OccurrenceWordNumbers own ON wn.WordNumberId = own.WordNumberId "
                    f"JOIN Occurrences o ON own.OccurrenceId = o.OccurrenceId "
                    f"JOIN BibleReferences br ON o.BibleReferenceId = br.BibleReferenceId "
                    f"LIMIT {batch_size} OFFSET {offset}",
                    max_rows=batch_size
                )

                if not rows:
                    break

                batch = []
                for r in rows:
                    wn_hex = r.get("wn_ref", "")
                    br_hex = r.get("bible_ref", "")
                    if not wn_hex or not br_hex:
                        continue

                    try:
                        wn_bytes = binascii.unhexlify(wn_hex)
                        word_ref = wn_bytes[1:].decode("utf-8", errors="replace")
                    except Exception:
                        continue

                    if not word_ref or "/" not in word_ref:
                        continue

                    try:
                        br_bytes = binascii.unhexlify(br_hex)
                        if len(br_bytes) < 4 or br_bytes[0] != 0x60:
                            continue
                        logos_book = br_bytes[1]
                        chapter = br_bytes[2]
                        verse = br_bytes[3]
                    except Exception:
                        continue

                    batch.append((word_ref, logos_book, chapter, verse))

                if batch:
                    conn.executemany(
                        "INSERT OR IGNORE INTO word_verse_map "
                        "(word_ref, logos_book, chapter, verse) VALUES (?, ?, ?, ?)",
                        batch
                    )
                    conn.commit()
                    total_inserted += len(batch)

                offset += batch_size
                if offset > 500000:
                    break

            return total_inserted
        finally:
            conn.close()
            reader.close()

    def get_word_numbers(self, protestant_book, chapter,
                         verse_start=None, verse_end=None):
        """Get word number references for a passage.

        Args:
            protestant_book: Protestant book number (1-66)
            chapter: Chapter number
            verse_start: Optional start verse (inclusive)
            verse_end: Optional end verse (inclusive)

        Returns:
            List of word reference strings like ["gnt/83219", ...]
        """
        logos_book = _protestant_to_logos(protestant_book)
        conn = self._conn()

        if verse_start and verse_end:
            rows = conn.execute(
                "SELECT word_ref FROM word_verse_map "
                "WHERE logos_book = ? AND chapter = ? "
                "AND verse >= ? AND verse <= ?",
                (logos_book, chapter, verse_start, verse_end)
            ).fetchall()
        elif verse_start:
            rows = conn.execute(
                "SELECT word_ref FROM word_verse_map "
                "WHERE logos_book = ? AND chapter = ? AND verse = ?",
                (logos_book, chapter, verse_start)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT word_ref FROM word_verse_map "
                "WHERE logos_book = ? AND chapter = ?",
                (logos_book, chapter)
            ).fetchall()

        conn.close()
        return [r["word_ref"] for r in rows]
