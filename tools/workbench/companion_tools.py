"""Companion tools — focused implementations for the sermon study companion.

Each tool wraps study.py functions and returns structured data.
The companion agent formats results for display.
"""

import json
import os
import sys

# Add parent tools dir to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from resource_index import ResourceIndex
from study import (
    parse_reference, find_bibles, find_commentaries_for_ref,
    read_bible_chapter, extract_verses, clean_bible_text,
    read_annotations, get_interlinear_for_chapter, find_word_in_interlinear,
    find_commentary_section, resolve_bible_files,
    get_resource_articles, read_article_text,
)

# ── Lexicon/Grammar resource registry ──────────────────────────────────────
# Resources confirmed readable, organized by use case.

NT_LEXICONS = [
    {"abbrev": "EDNT", "file": "EXGDCTNT.logos4", "desc": "Exegetical Dictionary of the NT"},
    {"abbrev": "TDNTA", "file": "TDNTA.logos4", "desc": "Theological Dictionary of the NT (Abridged)"},
    {"abbrev": "Louw-Nida", "file": "LOUWNIDA.logos4", "desc": "Greek-English Lexicon by Semantic Domain"},
    {"abbrev": "TLNT", "file": "TLNT.logos4", "desc": "Theological Lexicon of the NT"},
    {"abbrev": "LSJ", "file": "LSJ.logos4", "desc": "Liddell-Scott-Jones Greek-English Lexicon"},
    {"abbrev": "ANLEX", "file": "ANLEX.logos4", "desc": "Analytical Lexicon of the Greek NT"},
    {"abbrev": "M-M", "file": "MMVGT.logos4", "desc": "Moulton & Milligan Vocabulary of Greek Testament"},
]

OT_LEXICONS = [
    {"abbrev": "BDB", "file": "BDB.logos4", "desc": "Brown-Driver-Briggs Hebrew Lexicon"},
    {"abbrev": "HALOT", "file": "HAL.logos4", "desc": "Hebrew and Aramaic Lexicon of the OT"},
    {"abbrev": "TDOT", "file": "TDOT.logos4", "desc": "Theological Dictionary of the OT"},
    {"abbrev": "TLOT", "file": "TLOT.logos4", "desc": "Theological Lexicon of the OT"},
    {"abbrev": "DCH", "file": "DICHEBREW.logos4", "desc": "Dictionary of Classical Hebrew"},
    {"abbrev": "AnLexHeb", "file": "LXHEBANLEX.logos4", "desc": "Analytical Lexicon of Hebrew"},
]

ALL_LEXICONS = NT_LEXICONS + OT_LEXICONS

NT_GRAMMARS = [
    {"abbrev": "Wallace", "file": "GRKGRAMBBWALLACE.logos4", "desc": "Greek Grammar beyond the Basics (Exegetical Syntax)"},
    {"abbrev": "Robertson", "file": "GGNTLHR.logos4", "desc": "Grammar of the Greek NT in Light of Historical Research"},
    {"abbrev": "Blass-Debrunner", "file": "GRNTGRKBLASS.logos4", "desc": "Grammar of NT Greek (Blass)"},
    {"abbrev": "Discourse", "file": "DISCGRMRGRKNT.logos4", "desc": "Discourse Grammar of the Greek NT"},
    {"abbrev": "Morphology", "file": "MORPHBBCLGRK.logos4", "desc": "Morphology of Biblical Greek"},
    {"abbrev": "Verbal Aspect", "file": "BASVERBALGRK.logos4", "desc": "Basics of Verbal Aspect in Biblical Greek"},
    {"abbrev": "Idioms", "file": "IDIOMGREEKNT.logos4", "desc": "Idioms of the Greek New Testament"},
    {"abbrev": "Intermediate", "file": "NTRMDTGRKGRMMR.logos4", "desc": "Intermediate Greek Grammar: Syntax for NT Students"},
]

OT_GRAMMARS = [
    {"abbrev": "GKC", "file": "GESENGRAM.logos4", "desc": "Gesenius' Hebrew Grammar"},
    {"abbrev": "Waltke-OConnor", "file": "WLTKHEBSYN.logos4", "desc": "Introduction to Biblical Hebrew Syntax"},
]

ALL_GRAMMARS = NT_GRAMMARS + OT_GRAMMARS

# Module-level resource index singleton
_resource_index = None
_INDEX_DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'resource_index.db')


def _get_index():
    global _resource_index
    if _resource_index is None:
        _resource_index = ResourceIndex(_INDEX_DB_PATH)
    return _resource_index


def _ensure_indexed(resource_file, resource_type="lexicon"):
    """Ensure a resource is indexed. Build index on first use."""
    idx = _get_index()
    if not idx.is_indexed(resource_file):
        idx.build_index_for_resource(resource_file, resource_type=resource_type)
    return idx


TOOL_DEFINITIONS = [
    {
        "name": "read_bible_passage",
        "description": "Read a Bible passage in one or more translations. Returns clean text for each version.",
        "input_schema": {
            "type": "object",
            "properties": {
                "reference": {
                    "type": "string",
                    "description": "Bible reference, e.g. 'Romans 1:18-23' or 'John 3:16'"
                },
                "versions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Bible version names, e.g. ['ESV', 'NASB95']. Defaults to ['ESV']."
                }
            },
            "required": ["reference"]
        }
    },
    {
        "name": "find_commentary_paragraph",
        "description": "Find the relevant commentary section for a passage from a specific commentary. Returns the commentary text.",
        "input_schema": {
            "type": "object",
            "properties": {
                "reference": {
                    "type": "string",
                    "description": "Bible reference, e.g. 'Romans 1:18-23'"
                },
                "commentary_title": {
                    "type": "string",
                    "description": "Optional: specific commentary to search. If omitted, searches available commentaries."
                }
            },
            "required": ["reference"]
        }
    },
    {
        "name": "lookup_lexicon",
        "description": "Look up a Greek or Hebrew word in lexical resources from Bryan's library. Searches EDNT, Louw-Nida, TDNTA, TLNT, LSJ, BDB, HALOT, TDOT, and more. Use this for word studies, semantic range, morphological analysis, and theological significance of terms.",
        "input_schema": {
            "type": "object",
            "properties": {
                "word": {
                    "type": "string",
                    "description": "Greek or Hebrew word to look up (in original script or transliterated). Can also be an English gloss to search for."
                },
                "lexicons": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional: specific lexicons to search by abbreviation (e.g. ['EDNT', 'Louw-Nida']). If omitted, searches the most relevant ones."
                },
                "testament": {
                    "type": "string",
                    "enum": ["nt", "ot"],
                    "description": "Whether to search NT lexicons (Greek) or OT lexicons (Hebrew). Defaults based on the word script."
                }
            },
            "required": ["word"]
        }
    },
    {
        "name": "lookup_grammar",
        "description": "Search Greek and Hebrew grammars in Bryan's library. Available: Wallace (Exegetical Syntax), Robertson, Blass-Debrunner, Discourse Grammar, Morphology of Biblical Greek, Verbal Aspect, Idioms of the GNT, GKC (Gesenius Hebrew), Waltke-O'Connor. Use for questions about syntax, morphology, verbal aspect, clause structure, and grammatical constructions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search term — a grammatical concept, Greek/Hebrew form, or construction (e.g. 'middle passive', 'genitive absolute', 'aorist aspect', 'conditional clause')"
                },
                "grammars": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional: specific grammars by abbreviation (e.g. ['Wallace', 'Robertson']). If omitted, searches Wallace first for NT, GKC for OT."
                },
                "testament": {
                    "type": "string",
                    "enum": ["nt", "ot"],
                    "description": "Whether to search NT grammars (Greek) or OT grammars (Hebrew). Defaults to NT."
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "word_study_lookup",
        "description": "Look up interlinear data for a word in the current passage. Returns lemma, morphology, Strong's number. Note: interlinear data may not be available for all passages.",
        "input_schema": {
            "type": "object",
            "properties": {
                "word": {
                    "type": "string",
                    "description": "Word to look up (English, Greek, or Hebrew)"
                },
                "reference": {
                    "type": "string",
                    "description": "Bible reference for context, e.g. 'Romans 1:18'"
                }
            },
            "required": ["word", "reference"]
        }
    },
    {
        "name": "expand_cross_references",
        "description": "Get cross-reference annotations for a passage and fetch the actual text of referenced verses.",
        "input_schema": {
            "type": "object",
            "properties": {
                "reference": {
                    "type": "string",
                    "description": "Bible reference to get cross-references for"
                }
            },
            "required": ["reference"]
        }
    },
    {
        "name": "save_to_outline",
        "description": "Save a node to the sermon outline. Use for main points, sub-points, cross-references, notes, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "node_type": {
                    "type": "string",
                    "enum": ["title", "theme", "main_point", "sub_point", "bullet", "cross_ref", "note"],
                    "description": "Type of outline node"
                },
                "content": {
                    "type": "string",
                    "description": "The text content of the node"
                },
                "parent_id": {
                    "type": "integer",
                    "description": "Optional parent node ID for nesting"
                },
                "verse_ref": {
                    "type": "string",
                    "description": "Optional verse reference for this point"
                }
            },
            "required": ["node_type", "content"]
        }
    },
    # ── Encrypted Volume Dataset Tools ──────────────────────────────────
    {
        "name": "get_passage_data",
        "description": "Get structured study data for a passage from Logos's pre-indexed datasets. Returns figurative language, grammatical constructions, literary typing, wordplay, propositional outlines, important words, preaching themes, and more. Use this proactively when Bryan enters a new passage or phase.",
        "input_schema": {
            "type": "object",
            "properties": {
                "reference": {
                    "type": "string",
                    "description": "Bible reference, e.g. 'Romans 1:18-23'"
                },
                "datasets": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["figurative_language", "greek_constructions", "hebrew_constructions",
                                 "literary_typing", "wordplay", "propositional_outline",
                                 "important_words", "preaching_themes", "nt_use_of_ot",
                                 "cultural_concepts"]
                    },
                    "description": "Which datasets to query. If omitted, queries the most relevant ones for the current phase."
                }
            },
            "required": ["reference"]
        }
    },
    {
        "name": "get_cross_reference_network",
        "description": "Get curated cross-references from Logos's cross-reference databases. Much richer than inline Bible annotations. Can also query theology, biblical theology, confessional, and grammar cross-references.",
        "input_schema": {
            "type": "object",
            "properties": {
                "reference": {
                    "type": "string",
                    "description": "Bible reference"
                },
                "xref_type": {
                    "type": "string",
                    "enum": ["curated", "systematic", "biblical", "confessional", "grammar"],
                    "description": "Type of cross-references. 'curated' = Bible cross-refs, 'systematic' = systematic theology sections, etc."
                }
            },
            "required": ["reference"]
        }
    },
    {
        "name": "get_passage_context",
        "description": "Get contextual data for a passage: biblical places, people, things, events, ancient literature references, and timeline data.",
        "input_schema": {
            "type": "object",
            "properties": {
                "reference": {
                    "type": "string",
                    "description": "Bible reference"
                },
                "context_types": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["places", "people", "things", "ancient_literature"]
                    },
                    "description": "Which context data to retrieve. If omitted, returns all available."
                }
            },
            "required": ["reference"]
        }
    },
]


def get_tool_names():
    """Return list of available tool names."""
    return [t["name"] for t in TOOL_DEFINITIONS]


def execute_tool(tool_name, tool_input, session_context):
    """Dispatch a tool call and return structured result.

    session_context is a dict with: session_id, passage_ref, book, chapter,
    verse_start, verse_end, genre, db (CompanionDB instance)
    """
    try:
        if tool_name == "read_bible_passage":
            return _read_bible_passage(tool_input)
        elif tool_name == "find_commentary_paragraph":
            return _find_commentary_paragraph(tool_input, session_context)
        elif tool_name == "lookup_lexicon":
            return _lookup_lexicon(tool_input, session_context)
        elif tool_name == "lookup_grammar":
            return _lookup_grammar(tool_input, session_context)
        elif tool_name == "word_study_lookup":
            return _word_study_lookup(tool_input, session_context)
        elif tool_name == "expand_cross_references":
            return _expand_cross_references(tool_input, session_context)
        elif tool_name == "save_to_outline":
            return _save_to_outline(tool_input, session_context)
        elif tool_name == "get_passage_data":
            return _get_passage_data(tool_input, session_context)
        elif tool_name == "get_cross_reference_network":
            return _get_cross_reference_network(tool_input, session_context)
        elif tool_name == "get_passage_context":
            return _get_passage_context(tool_input, session_context)
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    except Exception as e:
        return {"error": str(e)}


def _read_bible_passage(tool_input):
    """Read a Bible passage in one or more translations."""
    ref_str = tool_input["reference"]
    versions = tool_input.get("versions", ["ESV"])

    ref = parse_reference(ref_str)
    bible_files = resolve_bible_files(versions)

    results = []
    for bf in bible_files:
        chapter_text, metadata = read_bible_chapter(bf, ref["book"], ref["chapter"])
        if chapter_text:
            if ref["verse_start"]:
                text = extract_verses(chapter_text, ref["verse_start"], ref["verse_end"])
            else:
                text = chapter_text
            text = clean_bible_text(text)
            results.append({
                "version": bf.replace(".logos4", "").replace(".lbxlls", ""),
                "text": text
            })

    return {
        "reference": ref_str,
        "translations": results
    }


def _find_commentary_paragraph(tool_input, session_context):
    """Find relevant commentary section for a passage."""
    ref_str = tool_input["reference"]
    ref = parse_reference(ref_str)

    commentaries = find_commentaries_for_ref(ref, limit=5)

    if not commentaries:
        return {"error": "No commentaries found for this reference"}

    results = []
    for comm in commentaries[:3]:
        resource_file = comm.get("filename") or comm.get("location", "")
        if not resource_file:
            continue
        text = find_commentary_section(resource_file, ref)
        if text:
            if len(text) > 5000:
                text = text[:5000] + "\n\n[... truncated ...]"
            results.append({
                "title": comm.get("abbrev") or comm.get("title", resource_file),
                "text": text
            })

    return {
        "reference": ref_str,
        "commentaries": results
    }


def _lookup_lexicon(tool_input, session_context):
    """Look up a word in lexical resources by searching article IDs and text."""
    word = tool_input["word"]
    requested_lexicons = tool_input.get("lexicons")
    testament = tool_input.get("testament")

    # Auto-detect testament from word script if not specified
    if not testament:
        # Check if word contains Greek characters
        if any('\u0370' <= c <= '\u03FF' or '\u1F00' <= c <= '\u1FFF' for c in word):
            testament = "nt"
        elif any('\u0590' <= c <= '\u05FF' for c in word):
            testament = "ot"
        else:
            # Default based on session context
            book = session_context.get("book", 66)
            testament = "ot" if book and book <= 39 else "nt"

    # Select lexicons to search
    if requested_lexicons:
        lexicons = [l for l in ALL_LEXICONS if l["abbrev"] in requested_lexicons]
        if not lexicons:
            lexicons = NT_LEXICONS[:3] if testament == "nt" else OT_LEXICONS[:3]
    else:
        lexicons = NT_LEXICONS[:4] if testament == "nt" else OT_LEXICONS[:4]

    results = []
    for lex in lexicons:
        entry = _search_lexicon(lex["file"], lex["abbrev"], word)
        if entry:
            results.append(entry)
        if len(results) >= 3:
            break

    return {
        "word": word,
        "testament": testament,
        "entries": results,
        "searched": [l["abbrev"] for l in lexicons],
    }


def _search_lexicon(resource_file, abbrev, word, resource_type="lexicon"):
    """Search a lexicon/grammar using the pre-built index."""
    try:
        idx = _ensure_indexed(resource_file, resource_type=resource_type)
        results = idx.lookup(word, resource_file, limit=3)

        if not results:
            return None

        # Read the best match article
        best = results[0]
        text = read_article_text(resource_file, best["article_num"], max_chars=8000)
        if not text:
            return None

        return {
            "lexicon": abbrev,
            "article_id": best["article_id"],
            "headword": best.get("headword", ""),
            "text": text[:6000] if len(text) > 6000 else text,
        }
    except Exception:
        return None


def _lookup_grammar(tool_input, session_context):
    """Search grammar resources by scanning article IDs for a query term."""
    query = tool_input["query"]
    requested_grammars = tool_input.get("grammars")
    testament = tool_input.get("testament", "nt")

    if requested_grammars:
        grammars = [g for g in ALL_GRAMMARS if g["abbrev"] in requested_grammars]
        if not grammars:
            grammars = NT_GRAMMARS[:2] if testament == "nt" else OT_GRAMMARS[:1]
    else:
        grammars = NT_GRAMMARS[:3] if testament == "nt" else OT_GRAMMARS

    results = []
    for gram in grammars:
        entry = _search_lexicon(gram["file"], gram["abbrev"], query, resource_type="grammar")
        if entry:
            results.append(entry)
        if len(results) >= 2:
            break

    return {
        "query": query,
        "testament": testament,
        "entries": results,
        "searched": [g["abbrev"] for g in grammars],
    }


def _word_study_lookup(tool_input, session_context):
    """Look up interlinear data for a word in the passage."""
    word = tool_input["word"]
    ref_str = tool_input["reference"]
    ref = parse_reference(ref_str)

    bible_files = resolve_bible_files(["ESV"])
    if not bible_files:
        return {"error": "No Bible available for interlinear data"}

    interlinear = get_interlinear_for_chapter(bible_files[0], ref["book"], ref["chapter"])
    if not interlinear:
        return {"note": "Interlinear data not available for this passage. Use lookup_lexicon for word studies."}

    matches = find_word_in_interlinear(interlinear, word)

    if not matches:
        return {
            "word": word,
            "reference": ref_str,
            "matches": [],
            "note": f"No interlinear matches for '{word}'. Use lookup_lexicon for detailed word study."
        }

    structured = []
    for m in matches:
        entry = {
            "surface": m.get("Surface") or m.get("Word", ""),
            "lemma": m.get("Lemma", ""),
            "morphology": m.get("Morphology", ""),
            "strongs": m.get("Strong's", m.get("Strongs", "")),
        }
        for key in ["Manuscript", "Louw-Nida", "Gloss"]:
            if key in m and m[key]:
                entry[key.lower().replace("-", "_")] = m[key]
        structured.append(entry)

    return {
        "word": word,
        "reference": ref_str,
        "matches": structured
    }


def _expand_cross_references(tool_input, session_context):
    """Get cross-reference annotations and fetch referenced verse text."""
    ref_str = tool_input["reference"]
    ref = parse_reference(ref_str)

    bible_files = resolve_bible_files(["ESV"])
    if not bible_files:
        return {"error": "No Bible available"}

    annotations = read_annotations(
        bible_files[0], ref["book"], ref["chapter"],
        verses=list(range(ref["verse_start"] or 1, (ref["verse_end"] or ref["verse_start"] or 1) + 1))
    )

    return {
        "reference": ref_str,
        "cross_references": annotations.get("xrefs", {}),
        "footnotes": annotations.get("footnotes", {})
    }


def _save_to_outline(tool_input, session_context):
    """Save a node to the sermon outline."""
    db = session_context.get("db")
    session_id = session_context.get("session_id")

    if not db or not session_id:
        return {"error": "No active session for outline"}

    node_id = db.add_outline_node(
        session_id=session_id,
        node_type=tool_input["node_type"],
        content=tool_input["content"],
        parent_id=tool_input.get("parent_id"),
        verse_ref=tool_input.get("verse_ref"),
        source_type="companion",
    )

    return {
        "saved": True,
        "node_id": node_id,
        "node_type": tool_input["node_type"],
        "content": tool_input["content"]
    }


# ── Dataset Tool Implementations ─────────────────────────────────────────

def _get_passage_data(tool_input, session_context):
    """Query pre-indexed passage datasets."""
    from dataset_tools import (
        query_figurative_language, query_greek_constructions,
        query_hebrew_constructions, query_literary_typing,
        query_wordplay, query_propositional_outline,
        query_important_words, query_preaching_themes,
        query_nt_use_of_ot, query_cultural_concepts
    )

    ref = parse_reference(tool_input["reference"])
    book, chapter = ref["book"], ref["chapter"]
    testament = "ot" if book <= 39 else "nt"

    requested = tool_input.get("datasets")
    if not requested:
        requested = ["preaching_themes"]
        if testament == "nt":
            requested.append("greek_constructions")
        else:
            requested.append("hebrew_constructions")

    dispatch = {
        "figurative_language": lambda: query_figurative_language(book, chapter),
        "greek_constructions": lambda: query_greek_constructions(book, chapter),
        "hebrew_constructions": lambda: query_hebrew_constructions(book, chapter),
        "literary_typing": lambda: query_literary_typing(book, chapter),
        "wordplay": lambda: query_wordplay(book, chapter),
        "propositional_outline": lambda: query_propositional_outline(book, chapter, testament),
        "important_words": lambda: query_important_words(book, chapter),
        "preaching_themes": lambda: query_preaching_themes(book, chapter),
        "nt_use_of_ot": lambda: query_nt_use_of_ot(book, chapter),
        "cultural_concepts": lambda: query_cultural_concepts(book, chapter),
    }

    results = {}
    for ds in requested:
        if ds in dispatch:
            try:
                data = dispatch[ds]()
                results[ds] = data if data else []
            except Exception:
                results[ds] = []

    return {"reference": tool_input["reference"], "datasets": results}


def _get_cross_reference_network(tool_input, session_context):
    """Query cross-reference databases."""
    from dataset_tools import query_curated_cross_refs, query_theology_xrefs

    ref = parse_reference(tool_input["reference"])
    xref_type = tool_input.get("xref_type", "curated")

    if xref_type == "curated":
        rows = query_curated_cross_refs(ref["book"], ref["chapter"],
                                        ref.get("verse_start"), ref.get("verse_end"))
    else:
        rows = query_theology_xrefs(ref["book"], ref["chapter"], xref_type=xref_type)

    return {
        "reference": tool_input["reference"],
        "xref_type": xref_type,
        "cross_references": rows[:50]
    }


def _get_passage_context(tool_input, session_context):
    """Query contextual data for a passage."""
    from dataset_tools import (
        query_biblical_places, query_biblical_people,
        query_biblical_things, query_ancient_literature
    )

    ref = parse_reference(tool_input["reference"])
    book, chapter = ref["book"], ref["chapter"]

    requested = tool_input.get("context_types")
    if not requested:
        requested = ["places", "people", "things"]

    dispatch = {
        "places": lambda: query_biblical_places(book, chapter),
        "people": lambda: query_biblical_people(book, chapter),
        "things": lambda: query_biblical_things(book, chapter),
        "ancient_literature": lambda: query_ancient_literature(book, chapter),
    }

    results = {}
    for ct in requested:
        if ct in dispatch:
            try:
                data = dispatch[ct]()
                results[ct] = data if data else []
            except Exception:
                results[ct] = []

    return {"reference": tool_input["reference"], "context": results}
