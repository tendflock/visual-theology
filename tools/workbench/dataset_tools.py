"""Encrypted volume dataset tools for the sermon study companion.

Each function queries a specific encrypted dataset file via LogosBatchReader.
The batch reader sends query-db commands to LogosReader which uses the
EncryptedVolume API to open encrypted SQLite databases.

Reference encoding:
- BIBLEXREFS uses text: "bible.{book}.{chapter}.{verse}" (Protestant numbering 1-66)
- All binary databases use Logos canonical numbering:
  - OT 1-39: same as Protestant
  - NT: Protestant + 21 (Matthew=61, Romans=66, Revelation=87)
- Binary format: 60{book}{chapter}{verse} (single) or 61{b}{c}{v}60{b}{c}{v} (range)

Schema details: docs/research/encrypted-volume-schemas.md
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from logos_batch import LogosBatchReader

# Singleton batch reader — reuse across calls
_reader = None


def _get_reader():
    """Get or create a batch reader singleton."""
    global _reader
    if _reader is None or not _reader.is_alive():
        _reader = LogosBatchReader()
    return _reader


def _protestant_to_logos(book):
    """Convert Protestant book number (1-66) to Logos canonical number."""
    if book <= 39:
        return book
    return book + 21


def _ref_hex_clause(book, chapter):
    """Build SQL WHERE clause for binary reference matching by book/chapter.

    Returns a clause like:
      (hex(Reference) LIKE '604201%' OR hex(Reference) LIKE '614201%')
    for Romans chapter 1 (Protestant book 45 → Logos 66 = 0x42).
    """
    logos_book = _protestant_to_logos(book)
    prefix = f"{logos_book:02X}{chapter:02X}"
    return f"(hex(Reference) LIKE '60{prefix}%' OR hex(Reference) LIKE '61{prefix}%')"


def _ref_hex_clause_for_col(col, book, chapter):
    """Same as _ref_hex_clause but for a named column."""
    logos_book = _protestant_to_logos(book)
    prefix = f"{logos_book:02X}{chapter:02X}"
    return f"(hex({col}) LIKE '60{prefix}%' OR hex({col}) LIKE '61{prefix}%')"


# ── Cross-Reference Tools ─────────────────────────────────────────────

def query_curated_cross_refs(book, chapter, verse_start=None, verse_end=None):
    """Query curated Bible cross-references from BIBLEXREFS.

    Uses text reference format: bible.{logos_book}.{chapter}.{verse}
    BIBLEXREFS uses Logos canonical numbering (same as binary databases).
    Returns list of dicts with source, target, score, and reason.
    """
    reader = _get_reader()
    logos_book = _protestant_to_logos(book)
    ref_pattern = f"bible.{logos_book}.{chapter}."
    if verse_start and verse_end:
        # For verse range, we query all in chapter and filter
        pass
    rows = reader.query_dataset(
        "BIBLEXREFS.lbslcr", "bxrefs.db",
        f"SELECT cr.Score, src.Reference as Source, tgt.Reference as Target "
        f"FROM CrossReferences cr "
        f"JOIN BibleReferences src ON cr.SourceReferenceId = src.ReferenceId "
        f"JOIN BibleReferences tgt ON cr.TargetReferenceId = tgt.ReferenceId "
        f"WHERE src.Reference LIKE '{ref_pattern}%' "
        f"ORDER BY cr.Score DESC LIMIT 50"
    )
    if verse_start:
        # Filter to verse range
        filtered = []
        for r in rows:
            src = r.get("Source", "")
            parts = src.split(".")
            if len(parts) >= 4:
                try:
                    v = int(parts[3].split("-")[0])
                    if verse_start <= v <= (verse_end or verse_start):
                        filtered.append(r)
                except ValueError:
                    filtered.append(r)
            else:
                filtered.append(r)
        rows = filtered
    return rows


def query_theology_xrefs(book, chapter, xref_type="systematic"):
    """Query theology cross-references for a passage.

    xref_type: "systematic", "biblical", "confessional", "grammar"
    Returns list of dicts with article, resource, tradition, topic.
    """
    file_map = {
        "systematic": "THEOLOGY-XREFS.lbsxrf",
        "biblical": "BIBLICAL-THEOLOGY-XREFS.lbsxrf",
        "confessional": "CREEDS-COUNCILS-XREFS.lbsxrf",
        "grammar": "GRAMMAR-XREFS.lbsxrf",
    }
    resource_file = file_map.get(xref_type, "THEOLOGY-XREFS.lbsxrf")
    reader = _get_reader()
    ref_clause = _ref_hex_clause_for_col("dtr.Reference", book, chapter)

    rows = reader.query_dataset(
        resource_file, "CrossReferences.db",
        f"SELECT cr.ArticleName, cr.ArticleTitle, cr.ResourceId, "
        f"ge.Label as Tradition, te.Label as Topic "
        f"FROM CrossReferences cr "
        f"JOIN DataTypeReferences dtr ON cr.CanonReferenceId = dtr.DataTypeReferenceId "
        f"LEFT JOIN GroupExpressions ge ON cr.GroupId = ge.GroupId AND ge.Language = 'en' "
        f"LEFT JOIN TypeExpressions te ON cr.TypeId = te.TypeId AND te.Language = 'en' "
        f"WHERE {ref_clause} LIMIT 50"
    )
    return rows


# ── Preaching & Thematic Tools ────────────────────────────────────────

def query_preaching_themes(book, chapter):
    """Query preaching themes for a passage.

    Returns list of dicts with pericope title and theme labels.
    """
    reader = _get_reader()
    ref_clause = _ref_hex_clause_for_col("r.Reference", book, chapter)

    rows = reader.query_dataset(
        "PreachingThemes.lbsptd", "preachingthemes.db",
        f"SELECT pt.Title as Pericope, tt.Label as Theme, tt.Description "
        f"FROM Pericope p "
        f"JOIN Reference r ON p.ReferenceId = r.ReferenceId "
        f"JOIN PericopeTitle pt ON p.PericopeId = pt.PericopeId "
        f"JOIN PericopeTheme pth ON p.PericopeId = pth.PericopeId "
        f"JOIN ThemeTitle tt ON pth.ThemeId = tt.ThemeId "
        f"WHERE pt.Language='en' AND tt.Language='en' "
        f"AND {ref_clause} LIMIT 50"
    )
    return rows


def query_thematic_outlines(book, chapter):
    """Query thematic outlines for a passage.

    Source: ThematicOutlines.lbstod → thematicoutlines.db
    """
    reader = _get_reader()
    # First check what tables exist
    tables = reader.query_dataset(
        "ThematicOutlines.lbstod", "thematicoutlines.db",
        "SELECT name FROM sqlite_master WHERE type='table'"
    )
    table_names = [r.get("name", "") for r in tables]
    if not table_names:
        return []

    # Try to query with reference matching
    ref_clause = _ref_hex_clause_for_col("Reference", book, chapter)
    for table in table_names:
        if "Reference" in table or "Pericope" in table:
            rows = reader.query_dataset(
                "ThematicOutlines.lbstod", "thematicoutlines.db",
                f"SELECT * FROM [{table}] WHERE {ref_clause} LIMIT 20"
            )
            if rows:
                return rows
    return []


# ── Entity Tools (Places, People, Things) ─────────────────────────────

def _query_entity_db(resource_file, db_name, book, chapter):
    """Generic query for entity databases (places, people, things)."""
    reader = _get_reader()
    ref_clause = _ref_hex_clause_for_col("br.Reference", book, chapter)

    rows = reader.query_dataset(
        resource_file, db_name,
        f"SELECT DISTINCT et.Title, et.Description, e.Kind, e.EntityReference "
        f"FROM EntityLemmaPhraseReferences elpr "
        f"JOIN EntityLemmaPhrases elp ON elpr.EntityId = elp.EntityId "
        f"  AND elpr.LemmaPhraseId = elp.LemmaPhraseId "
        f"JOIN Entities e ON elp.EntityId = e.EntityId "
        f"JOIN EntityTitles et ON e.EntityId = et.EntityId "
        f"JOIN BibleReferences br ON elpr.BibleReferenceId = br.BibleReferenceId "
        f"WHERE et.LanguageId = 2 AND {ref_clause} LIMIT 30"
    )
    return rows


def query_biblical_places(book, chapter):
    """Query biblical places mentioned in a passage."""
    return _query_entity_db("BiblicalPlaces.lbsplc", "biblicalplaces.db", book, chapter)


def query_biblical_people(book, chapter):
    """Query biblical people mentioned in a passage."""
    return _query_entity_db("BiblicalPeople.lbsbpd", "biblicalpeople.db", book, chapter)


def query_biblical_things(book, chapter):
    """Query biblical things/objects mentioned in a passage."""
    return _query_entity_db("BiblicalThings.lbsthg", "biblicalthings.db", book, chapter)


# ── SupplementalData Tools (word-number based) ────────────────────────
# These datasets use GNT/BHS word numbers to link to Bible passages.
# Full word-number-to-passage mapping is deferred to v2.
# For now, provide table listing and raw query capabilities.

def query_dataset_tables(resource_file, db_name):
    """List tables in an encrypted volume's database."""
    reader = _get_reader()
    rows = reader.query_dataset(
        resource_file, db_name,
        "SELECT name FROM sqlite_master WHERE type='table'"
    )
    return [r.get("name", "") for r in rows]


def query_figurative_language(book, chapter, verse_start=None, verse_end=None):
    """Query figurative language labels from the dataset.

    NOTE: SupplementalData uses word-number-based indexing. This function
    returns all distinct figurative language labels (types/categories)
    from the dataset. Passage-specific filtering requires word number
    mapping (v2).
    """
    reader = _get_reader()
    rows = reader.query_dataset(
        "FIGURATIVE-LANGUAGE.lbssd", "SupplementalData.db",
        "SELECT DISTINCT ls.Text as Label, lsk_prop.StringKey as Property "
        "FROM LabelStrings ls "
        "JOIN LocalizedStringKeys lsk_prop ON ls.PropertyValueStringId = lsk_prop.LocalizedStringKeyId "
        "WHERE ls.Language = 'en' AND ls.PropertyValueStringId IS NOT NULL "
        "AND ls.PropertyValueStringId != '' "
        "LIMIT 100"
    )
    return rows


def query_greek_constructions(book, chapter, verse_start=None, verse_end=None):
    """Query Greek grammatical constructions. V2: passage-specific via word numbers."""
    return []  # Deferred to v2 — requires word number mapping


def query_hebrew_constructions(book, chapter, verse_start=None, verse_end=None):
    """Query Hebrew grammatical constructions. V2: passage-specific via word numbers."""
    return []  # Deferred to v2 — requires word number mapping


def query_literary_typing(book, chapter):
    """Query literary type classification. V2: passage-specific via word numbers."""
    return []  # Deferred to v2


def query_propositional_outline(book, chapter, testament="nt"):
    """Query propositional outline. V2: passage-specific via word numbers."""
    return []  # Deferred to v2


def query_nt_use_of_ot(book, chapter):
    """Query NT use of OT passages. V2: passage-specific via word numbers."""
    return []  # Deferred to v2


def query_wordplay(book, chapter):
    """Query wordplay instances. V2: passage-specific via word numbers."""
    return []  # Deferred to v2


def query_cultural_concepts(book, chapter):
    """Query Lexham Cultural Ontology. V2: passage-specific."""
    return []  # Deferred to v2


def query_ancient_literature(book, chapter):
    """Query ancient literature cross-references. V2: passage-specific."""
    return []  # Deferred to v2


def query_important_words(book, chapter):
    """Query important words tagged for a passage. V2: passage-specific."""
    return []  # Deferred to v2
