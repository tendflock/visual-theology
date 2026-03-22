"""
Resource type registry for Logos library.
Maps catalog resource types to extraction strategies and metadata.

Each resource in the Logos catalog has a Type string (e.g.,
"text.monograph.commentary.bible") that determines how its content is
structured and how it should be queried.  This module centralizes that
knowledge so that higher-level tools can ask "what kind of thing is
this?" and "how do I look something up in it?" without hard-coding
type strings everywhere.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Lookup strategies
# ---------------------------------------------------------------------------

class LookupStrategy(Enum):
    """How to find content in a resource."""
    CHAPTER_VERSE = "chapter_verse"       # Bible texts: navigate by book/chapter/verse
    PASSAGE_REFERENCE = "passage_ref"     # Commentaries: find section by Bible reference
    LEMMA_WORD = "lemma_word"             # Lexicons: look up by Greek/Hebrew word
    TOPIC = "topic"                        # Encyclopedias, theologies: search by topic
    TOC_NAVIGATION = "toc_nav"            # Generic: navigate by table of contents
    SEQUENTIAL = "sequential"             # Read articles in order
    SEARCH = "search"                     # Full-text search only
    MEDIA = "media"                       # Audio/video/image content
    INTERACTIVE = "interactive"           # Interactive datasets (syntax trees, etc.)
    CALENDAR = "calendar"                 # Date-based daily readings
    DATA_LOOKUP = "data_lookup"           # Supplemental data keyed by reference/lemma


# ---------------------------------------------------------------------------
# ResourceTypeInfo
# ---------------------------------------------------------------------------

@dataclass
class ResourceTypeInfo:
    """Metadata and behavior for a resource type."""
    type_key: str                          # Logos catalog type string
    display_name: str                      # Human-readable name
    category: str                          # Grouping: bible, commentary, reference,
                                           #   language, sermons, academic, media, data, other
    lookup_strategy: LookupStrategy        # Primary way to find content
    secondary_strategies: list[LookupStrategy] = field(default_factory=list)
    description: str = ""
    priority: int = 0                      # Higher = more important for study output
    max_article_chars: int = 30000         # Default max chars to read per article
    passage_aware: bool = False            # True if ReferenceSupersets is meaningful


# ---------------------------------------------------------------------------
# Registry of all known resource types
# ---------------------------------------------------------------------------

RESOURCE_TYPES: dict[str, ResourceTypeInfo] = {

    # ── Bible texts ───────────────────────────────────────────────────────
    "text.monograph.bible": ResourceTypeInfo(
        type_key="text.monograph.bible",
        display_name="Bible Text",
        category="bible",
        lookup_strategy=LookupStrategy.CHAPTER_VERSE,
        priority=100,
        max_article_chars=50000,
        passage_aware=True,
        description="Bible translation text with chapter/verse navigation",
    ),
    "text.monograph.study.bible": ResourceTypeInfo(
        type_key="text.monograph.study.bible",
        display_name="Study Bible",
        category="bible",
        lookup_strategy=LookupStrategy.CHAPTER_VERSE,
        secondary_strategies=[LookupStrategy.PASSAGE_REFERENCE, LookupStrategy.TOC_NAVIGATION],
        priority=95,
        max_article_chars=60000,
        passage_aware=True,
        description="Study Bible with text, notes, and articles keyed by passage",
    ),
    "text.monograph.harmony.bible": ResourceTypeInfo(
        type_key="text.monograph.harmony.bible",
        display_name="Bible Harmony",
        category="bible",
        lookup_strategy=LookupStrategy.PASSAGE_REFERENCE,
        secondary_strategies=[LookupStrategy.TOC_NAVIGATION],
        priority=60,
        max_article_chars=40000,
        passage_aware=True,
        description="Parallel/harmony arrangement of Bible passages (e.g. Gospel harmony)",
    ),
    "text.monograph.lectionary.bible": ResourceTypeInfo(
        type_key="text.monograph.lectionary.bible",
        display_name="Bible Lectionary",
        category="bible",
        lookup_strategy=LookupStrategy.CALENDAR,
        secondary_strategies=[LookupStrategy.PASSAGE_REFERENCE],
        priority=30,
        max_article_chars=20000,
        passage_aware=True,
        description="Lectionary readings organized by liturgical calendar date",
    ),
    "text.monograph.notes.bible": ResourceTypeInfo(
        type_key="text.monograph.notes.bible",
        display_name="Bible Notes",
        category="bible",
        lookup_strategy=LookupStrategy.PASSAGE_REFERENCE,
        secondary_strategies=[LookupStrategy.CHAPTER_VERSE],
        priority=70,
        max_article_chars=30000,
        passage_aware=True,
        description="Notes keyed to Bible passages (e.g. NET Bible notes)",
    ),

    # ── Commentaries ──────────────────────────────────────────────────────
    "text.monograph.commentary.bible": ResourceTypeInfo(
        type_key="text.monograph.commentary.bible",
        display_name="Bible Commentary",
        category="commentary",
        lookup_strategy=LookupStrategy.PASSAGE_REFERENCE,
        secondary_strategies=[LookupStrategy.TOC_NAVIGATION],
        priority=90,
        max_article_chars=50000,
        passage_aware=True,
        description="Verse-by-verse or section commentary on biblical text",
    ),
    "text.monograph.commentary": ResourceTypeInfo(
        type_key="text.monograph.commentary",
        display_name="Commentary (General)",
        category="commentary",
        lookup_strategy=LookupStrategy.TOC_NAVIGATION,
        secondary_strategies=[LookupStrategy.PASSAGE_REFERENCE, LookupStrategy.SEARCH],
        priority=75,
        max_article_chars=40000,
        passage_aware=False,
        description="General commentary not keyed to specific Bible passages",
    ),
    "text.monograph.critical-apparatus.bible": ResourceTypeInfo(
        type_key="text.monograph.critical-apparatus.bible",
        display_name="Critical Apparatus (Bible)",
        category="commentary",
        lookup_strategy=LookupStrategy.PASSAGE_REFERENCE,
        secondary_strategies=[LookupStrategy.CHAPTER_VERSE],
        priority=65,
        max_article_chars=30000,
        passage_aware=True,
        description="Textual-critical apparatus noting manuscript variants for Bible passages",
    ),
    "text.monograph.critical-apparatus": ResourceTypeInfo(
        type_key="text.monograph.critical-apparatus",
        display_name="Critical Apparatus",
        category="commentary",
        lookup_strategy=LookupStrategy.TOC_NAVIGATION,
        secondary_strategies=[LookupStrategy.SEARCH],
        priority=55,
        max_article_chars=30000,
        passage_aware=False,
        description="Textual-critical apparatus for non-biblical texts",
    ),
    "text.monograph.concordance.bible": ResourceTypeInfo(
        type_key="text.monograph.concordance.bible",
        display_name="Bible Concordance",
        category="commentary",
        lookup_strategy=LookupStrategy.LEMMA_WORD,
        secondary_strategies=[LookupStrategy.PASSAGE_REFERENCE, LookupStrategy.SEARCH],
        priority=60,
        max_article_chars=20000,
        passage_aware=True,
        description="Word concordance keyed to Bible passages and original-language terms",
    ),
    "text.monograph.cross-references.bible": ResourceTypeInfo(
        type_key="text.monograph.cross-references.bible",
        display_name="Cross-References (Bible)",
        category="commentary",
        lookup_strategy=LookupStrategy.PASSAGE_REFERENCE,
        priority=50,
        max_article_chars=15000,
        passage_aware=True,
        description="Cross-reference lists keyed to Bible passages",
    ),
    "text.monograph.cross-references": ResourceTypeInfo(
        type_key="text.monograph.cross-references",
        display_name="Cross-References",
        category="commentary",
        lookup_strategy=LookupStrategy.PASSAGE_REFERENCE,
        secondary_strategies=[LookupStrategy.SEARCH],
        priority=45,
        max_article_chars=15000,
        passage_aware=False,
        description="Cross-reference material (general)",
    ),

    # ── Language / Lexical ────────────────────────────────────────────────
    "text.monograph.lexicon": ResourceTypeInfo(
        type_key="text.monograph.lexicon",
        display_name="Lexicon",
        category="language",
        lookup_strategy=LookupStrategy.LEMMA_WORD,
        secondary_strategies=[LookupStrategy.SEARCH],
        priority=85,
        max_article_chars=30000,
        passage_aware=False,
        description="Greek/Hebrew lexicon with entries keyed by lemma",
    ),
    "text.monograph.grammar": ResourceTypeInfo(
        type_key="text.monograph.grammar",
        display_name="Grammar",
        category="language",
        lookup_strategy=LookupStrategy.TOC_NAVIGATION,
        secondary_strategies=[LookupStrategy.SEARCH, LookupStrategy.TOPIC],
        priority=70,
        max_article_chars=40000,
        passage_aware=False,
        description="Greek/Hebrew grammar reference (e.g., BDF, Wallace, Joüon-Muraoka)",
    ),
    "text.monograph.glossary": ResourceTypeInfo(
        type_key="text.monograph.glossary",
        display_name="Glossary",
        category="language",
        lookup_strategy=LookupStrategy.LEMMA_WORD,
        secondary_strategies=[LookupStrategy.SEARCH],
        priority=50,
        max_article_chars=15000,
        passage_aware=False,
        description="Word list or glossary of terms",
    ),
    "text.monograph.dictionary": ResourceTypeInfo(
        type_key="text.monograph.dictionary",
        display_name="Dictionary",
        category="language",
        lookup_strategy=LookupStrategy.LEMMA_WORD,
        secondary_strategies=[LookupStrategy.SEARCH],
        priority=65,
        max_article_chars=25000,
        passage_aware=False,
        description="General or specialized dictionary",
    ),
    "text.monograph.thesaurus": ResourceTypeInfo(
        type_key="text.monograph.thesaurus",
        display_name="Thesaurus",
        category="language",
        lookup_strategy=LookupStrategy.LEMMA_WORD,
        secondary_strategies=[LookupStrategy.SEARCH],
        priority=40,
        max_article_chars=15000,
        passage_aware=False,
        description="Thesaurus of theological or linguistic terms",
    ),

    # ── Reference / Encyclopedic ──────────────────────────────────────────
    "text.monograph.encyclopedia": ResourceTypeInfo(
        type_key="text.monograph.encyclopedia",
        display_name="Encyclopedia",
        category="reference",
        lookup_strategy=LookupStrategy.TOPIC,
        secondary_strategies=[LookupStrategy.SEARCH],
        priority=80,
        max_article_chars=40000,
        passage_aware=False,
        description="Bible encyclopedia or dictionary with topical articles",
    ),
    "text.monograph.systematic-theology": ResourceTypeInfo(
        type_key="text.monograph.systematic-theology",
        display_name="Systematic Theology",
        category="reference",
        lookup_strategy=LookupStrategy.TOPIC,
        secondary_strategies=[LookupStrategy.TOC_NAVIGATION, LookupStrategy.SEARCH],
        priority=80,
        max_article_chars=50000,
        passage_aware=False,
        description="Systematic theology treatise organized by doctrinal topic",
    ),
    "text.monograph.biblical-theology": ResourceTypeInfo(
        type_key="text.monograph.biblical-theology",
        display_name="Biblical Theology",
        category="reference",
        lookup_strategy=LookupStrategy.TOPIC,
        secondary_strategies=[LookupStrategy.PASSAGE_REFERENCE, LookupStrategy.TOC_NAVIGATION],
        priority=78,
        max_article_chars=50000,
        passage_aware=False,
        description="Biblical theology tracing themes through the Bible's own structure",
    ),
    "text.monograph.handbook": ResourceTypeInfo(
        type_key="text.monograph.handbook",
        display_name="Handbook",
        category="reference",
        lookup_strategy=LookupStrategy.TOC_NAVIGATION,
        secondary_strategies=[LookupStrategy.TOPIC, LookupStrategy.SEARCH],
        priority=60,
        max_article_chars=30000,
        passage_aware=False,
        description="Reference handbook (exegetical, pastoral, etc.)",
    ),
    "text.monograph.atlas": ResourceTypeInfo(
        type_key="text.monograph.atlas",
        display_name="Bible Atlas",
        category="reference",
        lookup_strategy=LookupStrategy.TOPIC,
        secondary_strategies=[LookupStrategy.SEARCH],
        priority=40,
        max_article_chars=20000,
        passage_aware=False,
        description="Geographic atlas with maps and place descriptions",
    ),
    "text.monograph.quotations": ResourceTypeInfo(
        type_key="text.monograph.quotations",
        display_name="Quotations",
        category="reference",
        lookup_strategy=LookupStrategy.TOPIC,
        secondary_strategies=[LookupStrategy.SEARCH],
        priority=30,
        max_article_chars=15000,
        passage_aware=False,
        description="Collections of quotations organized by topic or author",
    ),
    "text.monograph.illustrations": ResourceTypeInfo(
        type_key="text.monograph.illustrations",
        display_name="Illustrations",
        category="reference",
        lookup_strategy=LookupStrategy.TOPIC,
        secondary_strategies=[LookupStrategy.SEARCH],
        priority=30,
        max_article_chars=15000,
        passage_aware=False,
        description="Sermon illustrations and anecdotes organized by topic",
    ),
    "text.monograph.confessional-document": ResourceTypeInfo(
        type_key="text.monograph.confessional-document",
        display_name="Confessional Document",
        category="reference",
        lookup_strategy=LookupStrategy.TOC_NAVIGATION,
        secondary_strategies=[LookupStrategy.TOPIC, LookupStrategy.SEARCH],
        priority=55,
        max_article_chars=30000,
        passage_aware=False,
        description="Creed, confession, or catechism (e.g., Westminster, Augsburg)",
    ),
    "text.monograph.catechism": ResourceTypeInfo(
        type_key="text.monograph.catechism",
        display_name="Catechism",
        category="reference",
        lookup_strategy=LookupStrategy.TOC_NAVIGATION,
        secondary_strategies=[LookupStrategy.SEQUENTIAL],
        priority=50,
        max_article_chars=20000,
        passage_aware=False,
        description="Question-and-answer catechism",
    ),

    # ── NT / OT Introductions ────────────────────────────────────────────
    "text.monograph.introduction.new-testament": ResourceTypeInfo(
        type_key="text.monograph.introduction.new-testament",
        display_name="NT Introduction",
        category="reference",
        lookup_strategy=LookupStrategy.TOC_NAVIGATION,
        secondary_strategies=[LookupStrategy.TOPIC, LookupStrategy.SEARCH],
        priority=65,
        max_article_chars=40000,
        passage_aware=False,
        description="Introduction to the New Testament (authorship, date, background)",
    ),
    "text.monograph.introduction.old-testament": ResourceTypeInfo(
        type_key="text.monograph.introduction.old-testament",
        display_name="OT Introduction",
        category="reference",
        lookup_strategy=LookupStrategy.TOC_NAVIGATION,
        secondary_strategies=[LookupStrategy.TOPIC, LookupStrategy.SEARCH],
        priority=65,
        max_article_chars=40000,
        passage_aware=False,
        description="Introduction to the Old Testament (authorship, date, background)",
    ),
    "text.monograph.survey.new-testament": ResourceTypeInfo(
        type_key="text.monograph.survey.new-testament",
        display_name="NT Survey",
        category="reference",
        lookup_strategy=LookupStrategy.TOC_NAVIGATION,
        secondary_strategies=[LookupStrategy.SEARCH],
        priority=55,
        max_article_chars=40000,
        passage_aware=False,
        description="Survey of the New Testament books",
    ),

    # ── Sermons / Preaching ───────────────────────────────────────────────
    "text.monograph.sermons": ResourceTypeInfo(
        type_key="text.monograph.sermons",
        display_name="Sermons",
        category="sermons",
        lookup_strategy=LookupStrategy.PASSAGE_REFERENCE,
        secondary_strategies=[LookupStrategy.TOPIC, LookupStrategy.SEQUENTIAL],
        priority=50,
        max_article_chars=30000,
        passage_aware=True,
        description="Sermon collections, often keyed by Bible passage or topic",
    ),
    "text.monograph.sermon-outlines": ResourceTypeInfo(
        type_key="text.monograph.sermon-outlines",
        display_name="Sermon Outlines",
        category="sermons",
        lookup_strategy=LookupStrategy.PASSAGE_REFERENCE,
        secondary_strategies=[LookupStrategy.TOPIC],
        priority=40,
        max_article_chars=15000,
        passage_aware=True,
        description="Sermon outlines and skeletons organized by passage or topic",
    ),

    # ── History ───────────────────────────────────────────────────────────
    "text.monograph.church-history": ResourceTypeInfo(
        type_key="text.monograph.church-history",
        display_name="Church History",
        category="academic",
        lookup_strategy=LookupStrategy.TOC_NAVIGATION,
        secondary_strategies=[LookupStrategy.TOPIC, LookupStrategy.SEARCH],
        priority=55,
        max_article_chars=40000,
        passage_aware=False,
        description="Church history text, organized chronologically or thematically",
    ),
    "text.monograph.biography": ResourceTypeInfo(
        type_key="text.monograph.biography",
        display_name="Biography",
        category="academic",
        lookup_strategy=LookupStrategy.TOC_NAVIGATION,
        secondary_strategies=[LookupStrategy.SEQUENTIAL],
        priority=35,
        max_article_chars=30000,
        passage_aware=False,
        description="Biographical work about a historical or biblical figure",
    ),
    "text.monograph.autobiography": ResourceTypeInfo(
        type_key="text.monograph.autobiography",
        display_name="Autobiography",
        category="academic",
        lookup_strategy=LookupStrategy.TOC_NAVIGATION,
        secondary_strategies=[LookupStrategy.SEQUENTIAL],
        priority=30,
        max_article_chars=30000,
        passage_aware=False,
        description="First-person autobiographical text",
    ),

    # ── Ancient manuscripts ───────────────────────────────────────────────
    "text.monograph.ancient-manuscript": ResourceTypeInfo(
        type_key="text.monograph.ancient-manuscript",
        display_name="Ancient Manuscript",
        category="academic",
        lookup_strategy=LookupStrategy.TOC_NAVIGATION,
        secondary_strategies=[LookupStrategy.PASSAGE_REFERENCE, LookupStrategy.SEARCH],
        priority=50,
        max_article_chars=40000,
        passage_aware=False,
        description="Primary-source ancient manuscript (church fathers, ANF/NPNF, etc.)",
    ),
    "text.monograph.ancient-manuscript.translation": ResourceTypeInfo(
        type_key="text.monograph.ancient-manuscript.translation",
        display_name="Ancient Manuscript (Translation)",
        category="academic",
        lookup_strategy=LookupStrategy.TOC_NAVIGATION,
        secondary_strategies=[LookupStrategy.PASSAGE_REFERENCE, LookupStrategy.SEARCH],
        priority=48,
        max_article_chars=40000,
        passage_aware=False,
        description="English translation of an ancient manuscript or patristic text",
    ),

    # ── Study / Devotional ────────────────────────────────────────────────
    "text.monograph.study-guide": ResourceTypeInfo(
        type_key="text.monograph.study-guide",
        display_name="Study Guide",
        category="academic",
        lookup_strategy=LookupStrategy.TOC_NAVIGATION,
        secondary_strategies=[LookupStrategy.PASSAGE_REFERENCE, LookupStrategy.SEQUENTIAL],
        priority=45,
        max_article_chars=25000,
        passage_aware=False,
        description="Study guide with questions, exercises, or outlines",
    ),
    "text.monograph.bible-study": ResourceTypeInfo(
        type_key="text.monograph.bible-study",
        display_name="Bible Study",
        category="academic",
        lookup_strategy=LookupStrategy.PASSAGE_REFERENCE,
        secondary_strategies=[LookupStrategy.TOC_NAVIGATION],
        priority=50,
        max_article_chars=25000,
        passage_aware=True,
        description="Bible-study curriculum or workbook keyed to passages",
    ),
    "text.monograph.workbook": ResourceTypeInfo(
        type_key="text.monograph.workbook",
        display_name="Workbook",
        category="academic",
        lookup_strategy=LookupStrategy.SEQUENTIAL,
        secondary_strategies=[LookupStrategy.TOC_NAVIGATION],
        priority=30,
        max_article_chars=20000,
        passage_aware=False,
        description="Interactive workbook with exercises",
    ),
    "text.monograph.devotional": ResourceTypeInfo(
        type_key="text.monograph.devotional",
        display_name="Devotional",
        category="other",
        lookup_strategy=LookupStrategy.CALENDAR,
        secondary_strategies=[LookupStrategy.SEQUENTIAL, LookupStrategy.TOPIC],
        priority=35,
        max_article_chars=15000,
        passage_aware=False,
        description="Daily or topical devotional readings",
    ),
    "text.monograph.prayers": ResourceTypeInfo(
        type_key="text.monograph.prayers",
        display_name="Prayers",
        category="other",
        lookup_strategy=LookupStrategy.TOPIC,
        secondary_strategies=[LookupStrategy.SEQUENTIAL],
        priority=25,
        max_article_chars=10000,
        passage_aware=False,
        description="Collection of prayers",
    ),
    "text.monograph.poetry": ResourceTypeInfo(
        type_key="text.monograph.poetry",
        display_name="Poetry",
        category="other",
        lookup_strategy=LookupStrategy.SEQUENTIAL,
        secondary_strategies=[LookupStrategy.TOPIC],
        priority=20,
        max_article_chars=10000,
        passage_aware=False,
        description="Poetry collection",
    ),
    "text.monograph.hymnal": ResourceTypeInfo(
        type_key="text.monograph.hymnal",
        display_name="Hymnal",
        category="other",
        lookup_strategy=LookupStrategy.SEQUENTIAL,
        secondary_strategies=[LookupStrategy.TOPIC, LookupStrategy.SEARCH],
        priority=20,
        max_article_chars=10000,
        passage_aware=False,
        description="Hymnal or songbook",
    ),
    "text.monograph.service-book": ResourceTypeInfo(
        type_key="text.monograph.service-book",
        display_name="Service Book",
        category="other",
        lookup_strategy=LookupStrategy.TOC_NAVIGATION,
        secondary_strategies=[LookupStrategy.CALENDAR],
        priority=25,
        max_article_chars=15000,
        passage_aware=False,
        description="Liturgical service book or book of common worship",
    ),
    "text.monograph.letters": ResourceTypeInfo(
        type_key="text.monograph.letters",
        display_name="Letters",
        category="academic",
        lookup_strategy=LookupStrategy.SEQUENTIAL,
        secondary_strategies=[LookupStrategy.TOC_NAVIGATION],
        priority=30,
        max_article_chars=25000,
        passage_aware=False,
        description="Collected correspondence or epistolary works",
    ),

    # ── Generic monograph / collected works ───────────────────────────────
    "text.monograph.collected-work": ResourceTypeInfo(
        type_key="text.monograph.collected-work",
        display_name="Collected Work",
        category="academic",
        lookup_strategy=LookupStrategy.TOC_NAVIGATION,
        secondary_strategies=[LookupStrategy.SEARCH, LookupStrategy.TOPIC],
        priority=40,
        max_article_chars=40000,
        passage_aware=False,
        description="Multi-volume or collected works (e.g., complete works of an author)",
    ),
    "text.monograph": ResourceTypeInfo(
        type_key="text.monograph",
        display_name="Monograph",
        category="academic",
        lookup_strategy=LookupStrategy.TOC_NAVIGATION,
        secondary_strategies=[LookupStrategy.SEARCH],
        priority=35,
        max_article_chars=30000,
        passage_aware=False,
        description="General monograph / book without a more specific sub-type",
    ),

    # ── Courseware ─────────────────────────────────────────────────────────
    "text.monograph.courseware": ResourceTypeInfo(
        type_key="text.monograph.courseware",
        display_name="Courseware (Text)",
        category="academic",
        lookup_strategy=LookupStrategy.SEQUENTIAL,
        secondary_strategies=[LookupStrategy.TOC_NAVIGATION],
        priority=40,
        max_article_chars=30000,
        passage_aware=False,
        description="Text-based course material (lessons, lectures)",
    ),
    "lbx.media.courseware": ResourceTypeInfo(
        type_key="lbx.media.courseware",
        display_name="Courseware (Media)",
        category="media",
        lookup_strategy=LookupStrategy.MEDIA,
        secondary_strategies=[LookupStrategy.SEQUENTIAL],
        priority=20,
        max_article_chars=5000,
        passage_aware=False,
        description="Video or audio course lectures",
    ),

    # ── Manual / Visualization ────────────────────────────────────────────
    "text.manual": ResourceTypeInfo(
        type_key="text.manual",
        display_name="Manual",
        category="other",
        lookup_strategy=LookupStrategy.TOC_NAVIGATION,
        secondary_strategies=[LookupStrategy.SEARCH],
        priority=10,
        max_article_chars=20000,
        passage_aware=False,
        description="Software manual or help documentation",
    ),
    "text.visualization.bible": ResourceTypeInfo(
        type_key="text.visualization.bible",
        display_name="Bible Visualization",
        category="bible",
        lookup_strategy=LookupStrategy.PASSAGE_REFERENCE,
        secondary_strategies=[LookupStrategy.INTERACTIVE],
        priority=40,
        max_article_chars=15000,
        passage_aware=True,
        description="Visual / diagrammatic representation of Bible text structure",
    ),

    # ── Serials ───────────────────────────────────────────────────────────
    "text.serial.journal": ResourceTypeInfo(
        type_key="text.serial.journal",
        display_name="Journal",
        category="academic",
        lookup_strategy=LookupStrategy.TOC_NAVIGATION,
        secondary_strategies=[LookupStrategy.SEARCH, LookupStrategy.TOPIC],
        priority=60,
        max_article_chars=40000,
        passage_aware=False,
        description="Academic journal with peer-reviewed articles (e.g., JETS, TynBul)",
    ),
    "text.serial.magazine": ResourceTypeInfo(
        type_key="text.serial.magazine",
        display_name="Magazine",
        category="other",
        lookup_strategy=LookupStrategy.SEQUENTIAL,
        secondary_strategies=[LookupStrategy.TOC_NAVIGATION, LookupStrategy.SEARCH],
        priority=25,
        max_article_chars=20000,
        passage_aware=False,
        description="Popular magazine or periodical",
    ),

    # ── Logos binary resources (lbx.*) ────────────────────────────────────
    "lbx.reverse-interlinear": ResourceTypeInfo(
        type_key="lbx.reverse-interlinear",
        display_name="Reverse Interlinear",
        category="language",
        lookup_strategy=LookupStrategy.CHAPTER_VERSE,
        secondary_strategies=[LookupStrategy.LEMMA_WORD],
        priority=88,
        max_article_chars=50000,
        passage_aware=True,
        description="Reverse interlinear linking translation words to original-language lemmas",
    ),
    "lbx.media": ResourceTypeInfo(
        type_key="lbx.media",
        display_name="Media",
        category="media",
        lookup_strategy=LookupStrategy.MEDIA,
        secondary_strategies=[LookupStrategy.SEARCH],
        priority=15,
        max_article_chars=5000,
        passage_aware=False,
        description="Images, audio, or video resources",
    ),
    "lbx.interactive": ResourceTypeInfo(
        type_key="lbx.interactive",
        display_name="Interactive Dataset",
        category="data",
        lookup_strategy=LookupStrategy.INTERACTIVE,
        secondary_strategies=[LookupStrategy.SEARCH],
        priority=45,
        max_article_chars=20000,
        passage_aware=False,
        description="Interactive dataset (timelines, maps, charts)",
    ),
    "lbx.supplementaldata": ResourceTypeInfo(
        type_key="lbx.supplementaldata",
        display_name="Supplemental Data",
        category="data",
        lookup_strategy=LookupStrategy.DATA_LOOKUP,
        priority=20,
        max_article_chars=10000,
        passage_aware=False,
        description="Supplemental metadata or tagging datasets used by Logos engine",
    ),
    "lbx.calendar-devotional": ResourceTypeInfo(
        type_key="lbx.calendar-devotional",
        display_name="Calendar Devotional",
        category="other",
        lookup_strategy=LookupStrategy.CALENDAR,
        secondary_strategies=[LookupStrategy.SEQUENTIAL],
        priority=25,
        max_article_chars=10000,
        passage_aware=False,
        description="Daily devotional organized by calendar date",
    ),
    "lbx.pronunciations": ResourceTypeInfo(
        type_key="lbx.pronunciations",
        display_name="Pronunciations",
        category="language",
        lookup_strategy=LookupStrategy.LEMMA_WORD,
        priority=30,
        max_article_chars=5000,
        passage_aware=False,
        description="Audio pronunciations of Greek/Hebrew words",
    ),

    # ── Logos linguistic / syntax datasets ─────────────────────────────────
    "lbx.syntaxdatabase": ResourceTypeInfo(
        type_key="lbx.syntaxdatabase",
        display_name="Syntax Database",
        category="data",
        lookup_strategy=LookupStrategy.DATA_LOOKUP,
        secondary_strategies=[LookupStrategy.PASSAGE_REFERENCE],
        priority=55,
        max_article_chars=20000,
        passage_aware=True,
        description="Syntactic analysis database for Greek or Hebrew text",
    ),
    "lbx.grammar": ResourceTypeInfo(
        type_key="lbx.grammar",
        display_name="Grammar Database",
        category="data",
        lookup_strategy=LookupStrategy.DATA_LOOKUP,
        secondary_strategies=[LookupStrategy.LEMMA_WORD],
        priority=50,
        max_article_chars=15000,
        passage_aware=False,
        description="Machine-readable grammatical tagging dataset",
    ),
    "lbx.clauses": ResourceTypeInfo(
        type_key="lbx.clauses",
        display_name="Clause Database",
        category="data",
        lookup_strategy=LookupStrategy.DATA_LOOKUP,
        secondary_strategies=[LookupStrategy.PASSAGE_REFERENCE],
        priority=45,
        max_article_chars=15000,
        passage_aware=True,
        description="Clause-level analysis of Hebrew or Greek text",
    ),
    "lbx.crossreferences": ResourceTypeInfo(
        type_key="lbx.crossreferences",
        display_name="Cross-Reference Dataset",
        category="data",
        lookup_strategy=LookupStrategy.DATA_LOOKUP,
        secondary_strategies=[LookupStrategy.PASSAGE_REFERENCE],
        priority=40,
        max_article_chars=10000,
        passage_aware=True,
        description="Machine-readable cross-reference dataset",
    ),
    "lbx.reportedspeech": ResourceTypeInfo(
        type_key="lbx.reportedspeech",
        display_name="Reported Speech",
        category="data",
        lookup_strategy=LookupStrategy.DATA_LOOKUP,
        secondary_strategies=[LookupStrategy.PASSAGE_REFERENCE],
        priority=35,
        max_article_chars=10000,
        passage_aware=True,
        description="Dataset tagging direct/indirect speech in Bible text",
    ),
    "lbx.wordsenses": ResourceTypeInfo(
        type_key="lbx.wordsenses",
        display_name="Word Senses",
        category="data",
        lookup_strategy=LookupStrategy.DATA_LOOKUP,
        secondary_strategies=[LookupStrategy.LEMMA_WORD],
        priority=45,
        max_article_chars=10000,
        passage_aware=False,
        description="Sense disambiguation data for original-language words",
    ),
    "lbx.lemmas": ResourceTypeInfo(
        type_key="lbx.lemmas",
        display_name="Lemma Database",
        category="data",
        lookup_strategy=LookupStrategy.DATA_LOOKUP,
        secondary_strategies=[LookupStrategy.LEMMA_WORD],
        priority=40,
        max_article_chars=10000,
        passage_aware=False,
        description="Lemmatization data for original-language morphology",
    ),
    "lbx.importantwords": ResourceTypeInfo(
        type_key="lbx.importantwords",
        display_name="Important Words",
        category="data",
        lookup_strategy=LookupStrategy.DATA_LOOKUP,
        secondary_strategies=[LookupStrategy.PASSAGE_REFERENCE],
        priority=35,
        max_article_chars=10000,
        passage_aware=True,
        description="Dataset marking theologically significant words per passage",
    ),
    "lbx.phraseconcordance": ResourceTypeInfo(
        type_key="lbx.phraseconcordance",
        display_name="Phrase Concordance",
        category="data",
        lookup_strategy=LookupStrategy.DATA_LOOKUP,
        secondary_strategies=[LookupStrategy.SEARCH],
        priority=30,
        max_article_chars=15000,
        passage_aware=False,
        description="Concordance of phrases and multi-word expressions",
    ),

    # ── Logos ontology / knowledge-graph datasets ─────────────────────────
    "lbx.biblicalpeople": ResourceTypeInfo(
        type_key="lbx.biblicalpeople",
        display_name="Biblical People",
        category="data",
        lookup_strategy=LookupStrategy.DATA_LOOKUP,
        secondary_strategies=[LookupStrategy.TOPIC],
        priority=35,
        max_article_chars=10000,
        passage_aware=False,
        description="Ontology of people mentioned in the Bible",
    ),
    "lbx.biblicalplaces": ResourceTypeInfo(
        type_key="lbx.biblicalplaces",
        display_name="Biblical Places",
        category="data",
        lookup_strategy=LookupStrategy.DATA_LOOKUP,
        secondary_strategies=[LookupStrategy.TOPIC],
        priority=35,
        max_article_chars=10000,
        passage_aware=False,
        description="Ontology of places mentioned in the Bible",
    ),
    "lbx.biblicalplacesmaps": ResourceTypeInfo(
        type_key="lbx.biblicalplacesmaps",
        display_name="Biblical Places Maps",
        category="data",
        lookup_strategy=LookupStrategy.DATA_LOOKUP,
        secondary_strategies=[LookupStrategy.MEDIA],
        priority=25,
        max_article_chars=5000,
        passage_aware=False,
        description="Map data for biblical locations",
    ),
    "lbx.biblicalevents": ResourceTypeInfo(
        type_key="lbx.biblicalevents",
        display_name="Biblical Events",
        category="data",
        lookup_strategy=LookupStrategy.DATA_LOOKUP,
        secondary_strategies=[LookupStrategy.TOPIC],
        priority=35,
        max_article_chars=10000,
        passage_aware=False,
        description="Ontology of events described in the Bible",
    ),
    "lbx.biblicalpeoplediagrams": ResourceTypeInfo(
        type_key="lbx.biblicalpeoplediagrams",
        display_name="Biblical People Diagrams",
        category="data",
        lookup_strategy=LookupStrategy.DATA_LOOKUP,
        secondary_strategies=[LookupStrategy.MEDIA],
        priority=20,
        max_article_chars=5000,
        passage_aware=False,
        description="Family tree / relationship diagrams for biblical figures",
    ),
    "lbx.biblicalreferents": ResourceTypeInfo(
        type_key="lbx.biblicalreferents",
        display_name="Biblical Referents",
        category="data",
        lookup_strategy=LookupStrategy.DATA_LOOKUP,
        priority=30,
        max_article_chars=10000,
        passage_aware=False,
        description="Co-reference resolution data (who/what pronouns refer to)",
    ),
    "lbx.biblicalthings": ResourceTypeInfo(
        type_key="lbx.biblicalthings",
        display_name="Biblical Things",
        category="data",
        lookup_strategy=LookupStrategy.DATA_LOOKUP,
        secondary_strategies=[LookupStrategy.TOPIC],
        priority=25,
        max_article_chars=10000,
        passage_aware=False,
        description="Ontology of objects and concepts in the Bible",
    ),
    "lbx.biographies": ResourceTypeInfo(
        type_key="lbx.biographies",
        display_name="Biography Database",
        category="data",
        lookup_strategy=LookupStrategy.DATA_LOOKUP,
        secondary_strategies=[LookupStrategy.TOPIC],
        priority=25,
        max_article_chars=10000,
        passage_aware=False,
        description="Structured biographical data for historical figures",
    ),
    "lbx.ancientliterature": ResourceTypeInfo(
        type_key="lbx.ancientliterature",
        display_name="Ancient Literature",
        category="data",
        lookup_strategy=LookupStrategy.DATA_LOOKUP,
        secondary_strategies=[LookupStrategy.SEARCH],
        priority=30,
        max_article_chars=15000,
        passage_aware=False,
        description="Index of ancient literary works and references",
    ),
    "lbx.universaltimeline": ResourceTypeInfo(
        type_key="lbx.universaltimeline",
        display_name="Universal Timeline",
        category="data",
        lookup_strategy=LookupStrategy.DATA_LOOKUP,
        secondary_strategies=[LookupStrategy.INTERACTIVE],
        priority=25,
        max_article_chars=10000,
        passage_aware=False,
        description="Master chronological timeline of biblical and world events",
    ),
    "lbx.pericopesets": ResourceTypeInfo(
        type_key="lbx.pericopesets",
        display_name="Pericope Sets",
        category="data",
        lookup_strategy=LookupStrategy.DATA_LOOKUP,
        secondary_strategies=[LookupStrategy.PASSAGE_REFERENCE],
        priority=35,
        max_article_chars=10000,
        passage_aware=True,
        description="Pericope (passage division) boundary datasets",
    ),
    "lbx.namedtexts": ResourceTypeInfo(
        type_key="lbx.namedtexts",
        display_name="Named Texts",
        category="data",
        lookup_strategy=LookupStrategy.DATA_LOOKUP,
        priority=20,
        max_article_chars=10000,
        passage_aware=False,
        description="Registry of named text identifiers in the Logos system",
    ),
    "lbx.excerpts": ResourceTypeInfo(
        type_key="lbx.excerpts",
        display_name="Excerpts",
        category="data",
        lookup_strategy=LookupStrategy.DATA_LOOKUP,
        secondary_strategies=[LookupStrategy.SEARCH],
        priority=25,
        max_article_chars=15000,
        passage_aware=False,
        description="Pre-extracted excerpts from various resources",
    ),
    "lbx.biblecrossreferences": ResourceTypeInfo(
        type_key="lbx.biblecrossreferences",
        display_name="Bible Cross-References",
        category="data",
        lookup_strategy=LookupStrategy.DATA_LOOKUP,
        secondary_strategies=[LookupStrategy.PASSAGE_REFERENCE],
        priority=40,
        max_article_chars=10000,
        passage_aware=True,
        description="Machine-readable Bible cross-reference links (Treasury, etc.)",
    ),
    "lbx.fbmedia": ResourceTypeInfo(
        type_key="lbx.fbmedia",
        display_name="Faithlife Media",
        category="media",
        lookup_strategy=LookupStrategy.MEDIA,
        priority=10,
        max_article_chars=5000,
        passage_aware=False,
        description="Faithlife media assets (images, presentations)",
    ),

    # ── Logos thematic / pastoral datasets ─────────────────────────────────
    "lbx.thematicoutlines": ResourceTypeInfo(
        type_key="lbx.thematicoutlines",
        display_name="Thematic Outlines",
        category="data",
        lookup_strategy=LookupStrategy.DATA_LOOKUP,
        secondary_strategies=[LookupStrategy.TOPIC],
        priority=30,
        max_article_chars=15000,
        passage_aware=False,
        description="Thematic outlines of Bible books and doctrines",
    ),
    "lbx.preachingthemes": ResourceTypeInfo(
        type_key="lbx.preachingthemes",
        display_name="Preaching Themes",
        category="data",
        lookup_strategy=LookupStrategy.DATA_LOOKUP,
        secondary_strategies=[LookupStrategy.TOPIC, LookupStrategy.PASSAGE_REFERENCE],
        priority=30,
        max_article_chars=10000,
        passage_aware=True,
        description="Preaching theme suggestions keyed to passages",
    ),
    "lbx.counselingthemes": ResourceTypeInfo(
        type_key="lbx.counselingthemes",
        display_name="Counseling Themes",
        category="data",
        lookup_strategy=LookupStrategy.DATA_LOOKUP,
        secondary_strategies=[LookupStrategy.TOPIC],
        priority=25,
        max_article_chars=10000,
        passage_aware=False,
        description="Pastoral counseling topic index with related passages",
    ),
    "lbx.churchhistoryontology": ResourceTypeInfo(
        type_key="lbx.churchhistoryontology",
        display_name="Church History Ontology",
        category="data",
        lookup_strategy=LookupStrategy.DATA_LOOKUP,
        secondary_strategies=[LookupStrategy.TOPIC],
        priority=20,
        max_article_chars=10000,
        passage_aware=False,
        description="Structured ontology of church history persons, events, movements",
    ),
    "lbx.lexhamsystematictheologyontology": ResourceTypeInfo(
        type_key="lbx.lexhamsystematictheologyontology",
        display_name="Systematic Theology Ontology",
        category="data",
        lookup_strategy=LookupStrategy.DATA_LOOKUP,
        secondary_strategies=[LookupStrategy.TOPIC],
        priority=25,
        max_article_chars=10000,
        passage_aware=False,
        description="Ontology of systematic theology concepts and relationships",
    ),
    "lbx.lexhamculturalontology": ResourceTypeInfo(
        type_key="lbx.lexhamculturalontology",
        display_name="Cultural Ontology",
        category="data",
        lookup_strategy=LookupStrategy.DATA_LOOKUP,
        secondary_strategies=[LookupStrategy.TOPIC],
        priority=25,
        max_article_chars=10000,
        passage_aware=False,
        description="Ontology of cultural concepts relevant to biblical studies",
    ),
    "lbx.logoscontrolledvocabulary": ResourceTypeInfo(
        type_key="lbx.logoscontrolledvocabulary",
        display_name="Controlled Vocabulary",
        category="data",
        lookup_strategy=LookupStrategy.DATA_LOOKUP,
        priority=10,
        max_article_chars=5000,
        passage_aware=False,
        description="Master controlled vocabulary / taxonomy for the Logos system",
    ),
    "lbx.unifiedannotationvocabulary": ResourceTypeInfo(
        type_key="lbx.unifiedannotationvocabulary",
        display_name="Annotation Vocabulary",
        category="data",
        lookup_strategy=LookupStrategy.DATA_LOOKUP,
        priority=10,
        max_article_chars=5000,
        passage_aware=False,
        description="Unified vocabulary for text annotations across Logos datasets",
    ),
}


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------

def get_type_info(catalog_type: str) -> ResourceTypeInfo:
    """Get type info, falling back to generic for unknown types.

    Exact match is tried first, then longest-prefix match so that e.g.
    ``text.monograph.commentary.bible.ot`` still resolves to the
    ``text.monograph.commentary.bible`` entry.
    """
    if catalog_type in RESOURCE_TYPES:
        return RESOURCE_TYPES[catalog_type]
    # Try prefix matching for subtypes (longest match first)
    for key in sorted(RESOURCE_TYPES.keys(), key=len, reverse=True):
        if catalog_type.startswith(key):
            return RESOURCE_TYPES[key]
    # Fallback: synthesize a generic entry
    return ResourceTypeInfo(
        type_key=catalog_type,
        display_name=catalog_type.split(".")[-1].replace("-", " ").title(),
        category="other",
        lookup_strategy=LookupStrategy.TOC_NAVIGATION,
    )


def get_types_by_category(category: str) -> list[ResourceTypeInfo]:
    """Get all resource types in a category, sorted by priority descending."""
    return sorted(
        [t for t in RESOURCE_TYPES.values() if t.category == category],
        key=lambda t: t.priority,
        reverse=True,
    )


def get_all_categories() -> list[str]:
    """Return a sorted list of all known category names."""
    return sorted({t.category for t in RESOURCE_TYPES.values()})


def get_passage_aware_types() -> list[ResourceTypeInfo]:
    """Return all types whose resources are keyed to Bible passages."""
    return sorted(
        [t for t in RESOURCE_TYPES.values() if t.passage_aware],
        key=lambda t: t.priority,
        reverse=True,
    )


# ---------------------------------------------------------------------------
# Catalog query helper
# ---------------------------------------------------------------------------

def get_study_resources_for_passage(
    catalog_db_path: str,
    resource_mgr_db_path: str,
    book_num: int,
    chapter: int,
) -> dict[str, list]:
    """Query catalog for all resources relevant to a Bible passage, grouped by category.

    Returns a dict like::

        {
            "bible": [{"resource_id": ..., "abbrev": ..., ...}, ...],
            "commentary": [...],
            "reference": [...],
            "language": [...],
            ...
        }

    Only resources with ``Availability = 2`` (owned/installed) and a valid
    file path in ResourceManager are included.  For passage-aware types the
    resource's ``ReferenceSupersets`` is checked against *book_num*.
    """
    import sqlite3

    conn = sqlite3.connect(catalog_db_path)
    conn.execute(f"ATTACH '{resource_mgr_db_path}' AS rm")

    rows = conn.execute("""
        SELECT c.ResourceId, c.AbbreviatedTitle, c.Title, c.Type,
               c.ReferenceSupersets, rm.Resources.Location
        FROM Records c
        INNER JOIN rm.Resources ON c.ResourceId = rm.Resources.ResourceId
        WHERE c.Availability = 2
        ORDER BY c.Type, c.AbbreviatedTitle
    """).fetchall()
    conn.close()

    results: dict[str, list] = {}
    for r in rows:
        resource_id, abbrev, title, rtype, supersets, location = r
        type_info = get_type_info(rtype)
        cat = type_info.category

        # For passage-aware types, skip resources that clearly don't cover this book
        if type_info.passage_aware and supersets:
            # Quick substring check: the superset should mention this book number
            if f"bible.{book_num}" not in supersets and f"bible+{book_num}" not in supersets:
                # Also check for range-style supersets where book_num falls inside
                # e.g. "bible.1.1.1-39.4.6" covers books 1-39
                import re
                covered = False
                for part in supersets.split("\t"):
                    m = re.match(
                        r'bible(?:\+\w+)?\.(\d+)(?:\.\d+)*(?:-(\d+)(?:\.\d+)*)?',
                        part.strip(),
                    )
                    if m:
                        start_book = int(m.group(1))
                        end_book = int(m.group(2)) if m.group(2) else start_book
                        if start_book <= book_num <= end_book:
                            covered = True
                            break
                if not covered:
                    continue

        if cat not in results:
            results[cat] = []

        results[cat].append({
            "resource_id": resource_id,
            "abbrev": abbrev or "",
            "title": title,
            "type": rtype,
            "type_info": type_info,
            "file": location,
        })

    return results
