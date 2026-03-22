#!/usr/bin/env python3
"""
Logos Sermon Research Agent

Provides tool functions for AI-assisted sermon research and preparation.
Tools can be used standalone or orchestrated by a Claude agent.

Usage:
    # Standalone research
    python3 sermon_agent.py research "John 3:16-18" --theme "God's love"

    # Just exegesis
    python3 sermon_agent.py exegesis "Romans 8:28-30"

    # Word study
    python3 sermon_agent.py word-study "John 3:16" "loved"

    # Commentary survey
    python3 sermon_agent.py commentaries "Ephesians 2:8-9" --max 10

    # Full agent mode (requires ANTHROPIC_API_KEY)
    python3 sermon_agent.py agent "Prepare a sermon on John 3:16-18 about God's love"
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Add tools directory to path
TOOLS_DIR = Path(__file__).parent
sys.path.insert(0, str(TOOLS_DIR))

from study import (
    parse_reference, find_bibles, find_commentaries_for_ref, find_lexicons,
    read_bible_chapter, extract_verses, clean_bible_text, read_annotations,
    find_commentary_section, get_resource_articles, read_article_text,
    run_reader, resolve_bible_files, CATALOG_DB, RESOURCE_MGR_DB,
    BOOK_NUM_TO_NAME, BOOK_ABBREVS,
    init_batch_reader, shutdown_batch_reader,
    get_interlinear_for_chapter, find_word_in_interlinear,
)

# Optional anthropic import
try:
    import anthropic
except ImportError:
    anthropic = None


# ── Tool Definitions (for Claude tool_use) ──────────────────────────────

TOOL_DEFINITIONS = [
    {
        "name": "read_bible_passage",
        "description": "Read a Bible passage in one or more translations. Returns the text with verse numbers.",
        "input_schema": {
            "type": "object",
            "properties": {
                "reference": {"type": "string", "description": "Bible reference, e.g. 'John 3:16-18'"},
                "versions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Bible versions to read, e.g. ['ESV', 'NASB95', 'KJV']. Defaults to ESV, NASB95, KJV.",
                },
            },
            "required": ["reference"],
        },
    },
    {
        "name": "get_cross_references",
        "description": "Get cross-references for a Bible passage. Returns references to related passages.",
        "input_schema": {
            "type": "object",
            "properties": {
                "reference": {"type": "string", "description": "Bible reference"},
                "version": {"type": "string", "description": "Bible version for cross-refs. Default: ESV"},
            },
            "required": ["reference"],
        },
    },
    {
        "name": "survey_commentaries",
        "description": "Read commentary excerpts on a passage from multiple commentaries.",
        "input_schema": {
            "type": "object",
            "properties": {
                "reference": {"type": "string", "description": "Bible reference"},
                "max_commentaries": {"type": "integer", "description": "Max commentaries to read. Default: 5"},
                "focus": {"type": "string", "description": "Optional focus area: 'exegetical', 'devotional', 'homiletical'"},
            },
            "required": ["reference"],
        },
    },
    {
        "name": "read_specific_commentary",
        "description": "Read a specific commentary on a passage.",
        "input_schema": {
            "type": "object",
            "properties": {
                "reference": {"type": "string", "description": "Bible reference"},
                "commentary_abbrev": {"type": "string", "description": "Commentary abbreviation or filename"},
            },
            "required": ["reference", "commentary_abbrev"],
        },
    },
    {
        "name": "word_study",
        "description": "Do a word study on a specific word in a Bible passage. Returns original language data (lemma, morphology, Strong's number) from interlinear analysis.",
        "input_schema": {
            "type": "object",
            "properties": {
                "reference": {"type": "string", "description": "Bible reference where the word appears"},
                "word": {"type": "string", "description": "English word to study"},
                "language": {"type": "string", "enum": ["greek", "hebrew", "auto"], "description": "Original language. Default: auto"},
            },
            "required": ["reference", "word"],
        },
    },
    {
        "name": "search_library",
        "description": "Search across the entire Logos library for a topic or keyword.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "resource_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Types to search: 'bible', 'commentary', 'lexicon', 'theology', 'sermons', 'all'",
                },
                "max_results": {"type": "integer", "description": "Max results. Default: 10"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "find_parallel_passages",
        "description": "Find parallel passages (e.g., Synoptic Gospel parallels, OT/NT connections).",
        "input_schema": {
            "type": "object",
            "properties": {
                "reference": {"type": "string", "description": "Bible reference"},
            },
            "required": ["reference"],
        },
    },
    {
        "name": "list_available_resources",
        "description": "List available resources of a given type.",
        "input_schema": {
            "type": "object",
            "properties": {
                "resource_type": {"type": "string", "enum": ["bibles", "commentaries", "lexicons", "all"]},
                "for_passage": {"type": "string", "description": "Optional: filter to resources covering this passage"},
            },
            "required": ["resource_type"],
        },
    },
]


# ── Tool Implementations ─────────────────────────────────────────────────

def tool_read_bible_passage(reference, versions=None):
    """Read a Bible passage in specified translations."""
    ref = parse_reference(reference)
    bible_files = resolve_bible_files(versions or ["ESV", "NASB95", "KJV"])

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
                "text": text,
                "metadata": metadata,
            })

    return {"reference": reference, "translations": results}


def tool_get_cross_references(reference, version="ESV"):
    """Get cross-references for a passage."""
    ref = parse_reference(reference)
    bible_files = resolve_bible_files([version])
    if not bible_files:
        return {"error": f"Bible version '{version}' not found"}

    bf = bible_files[0]
    verse_set = None
    if ref["verse_start"]:
        verse_set = set(range(ref["verse_start"], (ref["verse_end"] or ref["verse_start"]) + 1))

    annotations = read_annotations(bf, ref["book"], ref["chapter"], verse_set)
    return {
        "reference": reference,
        "version": version,
        "cross_references": annotations.get("xrefs", {}),
        "footnotes": annotations.get("footnotes", {}),
    }


def tool_survey_commentaries(reference, max_commentaries=3, focus=None):
    """Survey multiple commentaries on a passage."""
    ref = parse_reference(reference)
    commentaries = find_commentaries_for_ref(ref, limit=max_commentaries)

    results = []
    for comm in commentaries:
        text = find_commentary_section(comm["filename"], ref)
        if text:
            if len(text) > 1500:
                text = text[:1500] + "\n[... truncated — use read_specific_commentary for full text ...]"
            results.append({
                "commentary": comm["abbrev"] or comm["title"],
                "resource_id": comm["resource_id"],
                "text": text,
            })

    return {"reference": reference, "commentaries": results}


def tool_read_specific_commentary(reference, commentary_abbrev):
    """Read a specific commentary on a passage."""
    ref = parse_reference(reference)
    commentaries = find_commentaries_for_ref(ref, limit=100)

    target = None
    abbrev_lower = commentary_abbrev.lower()
    for comm in commentaries:
        if (abbrev_lower in (comm["abbrev"] or "").lower() or
            abbrev_lower in comm["filename"].lower() or
            abbrev_lower in (comm["title"] or "").lower()):
            target = comm
            break

    if not target:
        return {"error": f"Commentary '{commentary_abbrev}' not found for {reference}"}

    text = find_commentary_section(target["filename"], ref)
    if text and len(text) > 3000:
        text = text[:3000] + "\n[... truncated ...]"
    return {
        "reference": reference,
        "commentary": target["abbrev"] or target["title"],
        "resource_id": target["resource_id"],
        "text": text or "(section not found)",
    }


def tool_word_study(reference, word, language="auto"):
    """Do a word study using interlinear data from the Logos library."""
    ref = parse_reference(reference)

    # Determine if NT (Greek) or OT (Hebrew)
    if language == "auto":
        language = "greek" if ref["book"] >= 61 else "hebrew"

    # Read the passage to confirm the word appears
    bible_files = resolve_bible_files(["ESV"])
    passage_text = None
    if bible_files:
        chapter_text, _ = read_bible_chapter(bible_files[0], ref["book"], ref["chapter"])
        if chapter_text and ref["verse_start"]:
            passage_text = extract_verses(chapter_text, ref["verse_start"], ref["verse_end"])
            passage_text = clean_bible_text(passage_text)

    result = {
        "reference": reference,
        "word": word,
        "language": language,
        "passage_text": passage_text,
    }

    # Try interlinear extraction
    if bible_files:
        interlinear = get_interlinear_for_chapter(bible_files[0], ref["book"], ref["chapter"])
        if interlinear:
            matches = find_word_in_interlinear(interlinear, word)
            if matches:
                result["interlinear_matches"] = matches[:10]  # Limit to 10 entries
                result["total_matches"] = len(matches)
            else:
                result["interlinear_note"] = f"Word '{word}' not found in interlinear surface forms. Try a different form."
            result["interlinear_available"] = True
            result["total_words_in_chapter"] = len(interlinear)
        else:
            result["interlinear_available"] = False
            result["interlinear_note"] = "Interlinear data not available for this resource."

    # List available lexicons for further study
    lexicons = find_lexicons()
    if lexicons:
        result["available_lexicons"] = [
            {"abbrev": l["abbrev"], "title": l["title"], "file": l["filename"]}
            for l in lexicons[:10]
        ]

    return result


def tool_search_library(query, resource_types=None, max_results=10):
    """Search the library catalog for resources matching a query."""
    import sqlite3

    types = resource_types or ["all"]
    type_filter = ""
    if "all" not in types:
        type_clauses = []
        type_map = {
            "bible": "text.monograph.bible",
            "commentary": "text.monograph.commentary%",
            "lexicon": "%lexicon%",
            "theology": "%systematic-theology%",
            "sermons": "%sermons%",
        }
        for t in types:
            if t in type_map:
                type_clauses.append(f"c.Type LIKE '{type_map[t]}'")
        if type_clauses:
            type_filter = f"AND ({' OR '.join(type_clauses)})"

    conn = sqlite3.connect(CATALOG_DB)
    conn.execute(f"ATTACH '{RESOURCE_MGR_DB}' AS rm")
    rows = conn.execute(f"""
        SELECT c.ResourceId, c.AbbreviatedTitle, c.Title, c.Type,
               rm.Resources.Location
        FROM Records c
        INNER JOIN rm.Resources ON c.ResourceId = rm.Resources.ResourceId
        WHERE c.Availability = 2
        AND (c.Title LIKE ? OR c.AbbreviatedTitle LIKE ?)
        {type_filter}
        ORDER BY c.AbbreviatedTitle
        LIMIT ?
    """, (f"%{query}%", f"%{query}%", max_results)).fetchall()
    conn.close()

    return {
        "query": query,
        "results": [
            {
                "resource_id": r[0],
                "abbrev": r[1] or "",
                "title": r[2],
                "type": r[3],
                "filename": os.path.basename(r[4]) if r[4] else "",
            }
            for r in rows
        ],
    }


def tool_find_parallel_passages(reference):
    """Find parallel passages using cross-references."""
    xrefs = tool_get_cross_references(reference, version="ESV")
    return {
        "reference": reference,
        "parallel_passages": xrefs.get("cross_references", {}),
        "note": "Parallel passages derived from ESV cross-reference annotations.",
    }


def tool_list_available_resources(resource_type, for_passage=None):
    """List available resources of a given type."""
    if resource_type == "bibles":
        resources = find_bibles()
        return {"type": "bibles", "count": len(resources), "resources": resources}
    elif resource_type == "lexicons":
        resources = find_lexicons()
        return {"type": "lexicons", "count": len(resources), "resources": resources}
    elif resource_type == "commentaries":
        if for_passage:
            ref = parse_reference(for_passage)
            resources = find_commentaries_for_ref(ref, limit=100)
        else:
            resources = []
        return {"type": "commentaries", "count": len(resources), "resources": resources}
    else:
        return {"error": f"Unknown resource type: {resource_type}"}


# ── Tool Dispatcher ──────────────────────────────────────────────────────

TOOL_HANDLERS = {
    "read_bible_passage": lambda args: tool_read_bible_passage(**args),
    "get_cross_references": lambda args: tool_get_cross_references(**args),
    "survey_commentaries": lambda args: tool_survey_commentaries(**args),
    "read_specific_commentary": lambda args: tool_read_specific_commentary(**args),
    "word_study": lambda args: tool_word_study(**args),
    "search_library": lambda args: tool_search_library(**args),
    "find_parallel_passages": lambda args: tool_find_parallel_passages(**args),
    "list_available_resources": lambda args: tool_list_available_resources(**args),
}


def execute_tool(tool_name, tool_input):
    """Execute a tool by name with given input."""
    handler = TOOL_HANDLERS.get(tool_name)
    if not handler:
        return {"error": f"Unknown tool: {tool_name}"}
    try:
        return handler(tool_input)
    except Exception as e:
        return {"error": f"{type(e).__name__}: {str(e)}"}


# ── Result Truncation ────────────────────────────────────────────────────

MAX_RESULT_CHARS = 15000


def _truncate_result(result_str):
    """Smart truncation of tool results to stay within context limits.

    Tries to truncate at logical boundaries (per-commentary, per-translation)
    rather than cutting mid-sentence.
    """
    if len(result_str) <= MAX_RESULT_CHARS:
        return result_str

    # Try to parse as JSON and truncate intelligently
    try:
        data = json.loads(result_str)
    except (json.JSONDecodeError, TypeError):
        return result_str[:MAX_RESULT_CHARS] + "\n[... truncated ...]"

    # Truncate list-heavy results
    for key in ("commentaries", "translations", "results", "resources"):
        if key in data and isinstance(data[key], list):
            while len(json.dumps(data, ensure_ascii=False)) > MAX_RESULT_CHARS and len(data[key]) > 1:
                data[key] = data[key][:-1]
            data[f"{key}_truncated"] = True

    # Truncate text fields within nested objects
    truncated = json.dumps(data, ensure_ascii=False)
    if len(truncated) > MAX_RESULT_CHARS:
        return truncated[:MAX_RESULT_CHARS] + "\n[... truncated ...]"
    return truncated


# ── Claude Agent Loop ────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a biblical scholar and sermon research assistant with access to a \
large Logos 4 theological library containing 302 Bibles, 1025 commentaries, 49 lexicons, \
and thousands of other resources.

Your job is to help prepare thorough, well-researched sermon briefs and Bible study materials.

## Research Methodology
1. **Read the passage** in multiple translations (ESV, NASB95, KJV at minimum) to understand the text
2. **Check cross-references** to see how the passage connects to the rest of Scripture
3. **Do word studies** on key theological terms to understand the original Greek/Hebrew
4. **Survey commentaries** to see how scholars have interpreted the passage
5. **Find parallel passages** that illuminate the text
6. **Synthesize** your findings into a clear, organized research brief

## Guidelines
- Always cite which translation or commentary you're drawing from
- Note where scholars disagree and present multiple views fairly
- Highlight the original language insights that are most relevant for preaching
- Structure your output with clear markdown headings
- Be thorough but focused — don't pad with generic information you could produce without the library
- When a tool returns an error or empty result, note it briefly and move on
- Aim for depth over breadth — 3 good commentaries analyzed well beats 10 skimmed superficially
"""


def run_agent(user_query, max_turns=25, model="claude-sonnet-4-20250514"):
    """Run the Claude agentic loop with library tools.

    Args:
        user_query: The user's research question or sermon prep request.
        max_turns: Maximum number of API round-trips.
        model: Claude model to use.

    Returns:
        Final text response from Claude.
    """
    if anthropic is None:
        print("Error: 'anthropic' package not installed. Run: pip3 install anthropic", file=sys.stderr)
        sys.exit(1)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    # Initialize batch reader for speed
    init_batch_reader()

    messages = [{"role": "user", "content": user_query}]

    try:
        for turn in range(max_turns):
            print(f"\n--- Turn {turn + 1}/{max_turns} ---", file=sys.stderr)

            response = client.messages.create(
                model=model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOL_DEFINITIONS,
                messages=messages,
            )

            # Check stop reason
            if response.stop_reason == "end_turn":
                # Extract final text
                text_parts = []
                for block in response.content:
                    if block.type == "text":
                        text_parts.append(block.text)
                return "\n".join(text_parts)

            # Process tool use blocks
            if response.stop_reason == "tool_use":
                # Add assistant's response to messages
                messages.append({"role": "assistant", "content": response.content})

                # Execute each tool call
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        tool_name = block.name
                        tool_input = block.input
                        tool_id = block.id

                        print(f"  Tool: {tool_name}({json.dumps(tool_input, ensure_ascii=False)[:100]})", file=sys.stderr)

                        result = execute_tool(tool_name, tool_input)
                        result_str = json.dumps(result, indent=2, ensure_ascii=False)

                        # Truncate large results
                        result_str = _truncate_result(result_str)

                        print(f"    -> {len(result_str)} chars", file=sys.stderr)

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": result_str,
                        })

                messages.append({"role": "user", "content": tool_results})
            else:
                # Unexpected stop reason
                print(f"  Unexpected stop_reason: {response.stop_reason}", file=sys.stderr)
                text_parts = []
                for block in response.content:
                    if block.type == "text":
                        text_parts.append(block.text)
                return "\n".join(text_parts) if text_parts else "(no response)"

        print(f"  Reached max turns ({max_turns})", file=sys.stderr)
        return "(Agent reached maximum turns without completing)"

    finally:
        shutdown_batch_reader()


# ── Research Workflows ───────────────────────────────────────────────────

def run_exegesis(reference):
    """Run a complete exegesis workflow for a passage."""
    print(f"=== Exegesis: {reference} ===\n", file=sys.stderr)

    results = {}

    print("  Reading translations...", file=sys.stderr)
    results["translations"] = tool_read_bible_passage(reference)

    print("  Getting cross-references...", file=sys.stderr)
    results["cross_references"] = tool_get_cross_references(reference)

    print("  Checking word study resources...", file=sys.stderr)
    results["word_study_info"] = tool_word_study(reference, "(overview)", "auto")

    print("  Surveying commentaries...", file=sys.stderr)
    results["commentaries"] = tool_survey_commentaries(reference, max_commentaries=5)

    return results


def run_full_research(reference, theme=None):
    """Run comprehensive sermon research workflow."""
    print(f"=== Full Research: {reference} ===", file=sys.stderr)
    if theme:
        print(f"  Theme: {theme}", file=sys.stderr)
    print(file=sys.stderr)

    results = {"reference": reference, "theme": theme}

    print("Phase 1: Exegesis", file=sys.stderr)
    results["exegesis"] = run_exegesis(reference)

    print("\nPhase 2: Parallel Passages", file=sys.stderr)
    results["parallels"] = tool_find_parallel_passages(reference)

    print("\nPhase 3: Extended Commentary Survey", file=sys.stderr)
    results["extended_commentaries"] = tool_survey_commentaries(reference, max_commentaries=10)

    if theme:
        print(f"\nPhase 4: Theme Search ({theme})", file=sys.stderr)
        results["theme_resources"] = tool_search_library(theme, resource_types=["theology", "sermons"])

    return results


def format_research_output(results):
    """Format research results as readable markdown."""
    lines = []
    ref = results.get("reference", "Unknown")
    theme = results.get("theme", "")

    lines.append(f"# Sermon Research: {ref}")
    if theme:
        lines.append(f"**Theme:** {theme}")
    lines.append("")

    # Translations
    exegesis = results.get("exegesis", {})
    translations = exegesis.get("translations", {}).get("translations", [])
    if translations:
        lines.append("## Scripture Text")
        lines.append("")
        for t in translations:
            lines.append(f"### {t['version']}")
            lines.append(t.get("text", "(no text)"))
            lines.append("")

    # Cross-references
    xrefs = exegesis.get("cross_references", {})
    if xrefs.get("cross_references"):
        lines.append("## Cross-References")
        lines.append("")
        for key, text in sorted(xrefs["cross_references"].items()):
            lines.append(f"- {text}")
        lines.append("")

    # Commentaries
    comms = results.get("extended_commentaries", results.get("exegesis", {}).get("commentaries", {}))
    comm_list = comms.get("commentaries", [])
    if comm_list:
        lines.append("## Commentary Insights")
        lines.append("")
        for c in comm_list:
            lines.append(f"### {c['commentary']}")
            lines.append(c.get("text", "(no text)"))
            lines.append("")

    # Parallels
    parallels = results.get("parallels", {})
    if parallels.get("parallel_passages"):
        lines.append("## Parallel Passages")
        lines.append("")
        for key, text in sorted(parallels["parallel_passages"].items()):
            lines.append(f"- {text}")
        lines.append("")

    return "\n".join(lines)


def format_exegesis_output(results):
    """Format exegesis results as readable markdown."""
    lines = []

    # Translations
    translations = results.get("translations", {}).get("translations", [])
    if translations:
        ref_str = results.get("translations", {}).get("reference", "")
        lines.append(f"# Exegesis: {ref_str}")
        lines.append("")
        lines.append("## Scripture Text")
        lines.append("")
        for t in translations:
            lines.append(f"### {t['version']}")
            lines.append(t.get("text", "(no text)"))
            lines.append("")

    # Cross-references
    xrefs = results.get("cross_references", {})
    if xrefs.get("cross_references"):
        lines.append("## Cross-References")
        lines.append("")
        for key, text in sorted(xrefs["cross_references"].items()):
            lines.append(f"- {text}")
        lines.append("")

    # Word study info
    ws = results.get("word_study_info", {})
    if ws.get("interlinear_matches"):
        lines.append("## Word Study Data")
        lines.append("")
        for m in ws["interlinear_matches"][:5]:
            word = m.get("Surface") or m.get("Word", "?")
            lemma = m.get("Lemma", "")
            morph = m.get("Morphology", "")
            strongs = m.get("Strong's", "")
            lines.append(f"- **{word}** — lemma: {lemma}, morph: {morph}, Strong's: {strongs}")
        lines.append("")

    # Commentaries
    comms = results.get("commentaries", {})
    comm_list = comms.get("commentaries", [])
    if comm_list:
        lines.append("## Commentary Insights")
        lines.append("")
        for c in comm_list:
            lines.append(f"### {c['commentary']}")
            text = c.get("text", "(no text)")
            if len(text) > 3000:
                text = text[:3000] + "\n[... truncated ...]"
            lines.append(text)
            lines.append("")

    return "\n".join(lines) if lines else json.dumps(results, indent=2, ensure_ascii=False)


# ── CLI ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Logos Sermon Research Agent")
    subparsers = parser.add_subparsers(dest="command")

    # research command
    p_research = subparsers.add_parser("research", help="Full sermon research")
    p_research.add_argument("reference", help="Bible reference")
    p_research.add_argument("--theme", help="Sermon theme")
    p_research.add_argument("-o", "--output", help="Output file")
    p_research.add_argument("--json", action="store_true", help="JSON output")

    # exegesis command
    p_exeg = subparsers.add_parser("exegesis", help="Exegetical analysis")
    p_exeg.add_argument("reference", help="Bible reference")
    p_exeg.add_argument("-o", "--output", help="Output file")
    p_exeg.add_argument("--json", action="store_true", help="JSON output")

    # word-study command
    p_word = subparsers.add_parser("word-study", help="Word study")
    p_word.add_argument("reference", help="Bible reference")
    p_word.add_argument("word", help="Word to study")
    p_word.add_argument("--language", choices=["greek", "hebrew", "auto"], default="auto")
    p_word.add_argument("--json", action="store_true", help="JSON output")

    # commentaries command
    p_comm = subparsers.add_parser("commentaries", help="Commentary survey")
    p_comm.add_argument("reference", help="Bible reference")
    p_comm.add_argument("--max", type=int, default=5, help="Max commentaries")
    p_comm.add_argument("--json", action="store_true", help="JSON output")

    # tool command (for direct tool execution)
    p_tool = subparsers.add_parser("tool", help="Execute a single tool")
    p_tool.add_argument("tool_name", help="Tool name")
    p_tool.add_argument("tool_input", help="Tool input as JSON string")

    # tools command (list available tools)
    subparsers.add_parser("tools", help="List available tools")

    # agent command
    p_agent = subparsers.add_parser("agent", help="Run Claude agent for sermon research")
    p_agent.add_argument("query", help="Research query or sermon prep request")
    p_agent.add_argument("--model", default="claude-sonnet-4-20250514", help="Claude model to use")
    p_agent.add_argument("--max-turns", type=int, default=25, help="Max agent turns")
    p_agent.add_argument("-o", "--output", help="Output file")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "tools":
        for tool in TOOL_DEFINITIONS:
            print(f"  {tool['name']}: {tool['description']}")
        return

    if args.command == "tool":
        init_batch_reader()
        try:
            result = execute_tool(args.tool_name, json.loads(args.tool_input))
            print(json.dumps(result, indent=2, ensure_ascii=False))
        finally:
            shutdown_batch_reader()
        return

    if args.command == "agent":
        output = run_agent(args.query, max_turns=args.max_turns, model=args.model)
        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
            print(f"Written to {args.output}", file=sys.stderr)
        else:
            print(output)
        return

    # All remaining commands benefit from batch reader
    init_batch_reader()
    try:
        if args.command == "research":
            results = run_full_research(args.reference, args.theme)
            if args.json:
                output = json.dumps(results, indent=2, ensure_ascii=False)
            else:
                output = format_research_output(results)
            if args.output:
                with open(args.output, "w") as f:
                    f.write(output)
                print(f"Written to {args.output}", file=sys.stderr)
            else:
                print(output)

        elif args.command == "exegesis":
            results = run_exegesis(args.reference)
            if args.json:
                output = json.dumps(results, indent=2, ensure_ascii=False)
            else:
                output = format_exegesis_output(results)
            if args.output:
                with open(args.output, "w") as f:
                    f.write(output)
            else:
                print(output)

        elif args.command == "word-study":
            result = tool_word_study(args.reference, args.word, args.language)
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.command == "commentaries":
            result = tool_survey_commentaries(args.reference, max_commentaries=args.max)
            if args.json:
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                for c in result.get("commentaries", []):
                    print(f"### {c['commentary']}")
                    print(c.get("text", "")[:2000])
                    print()
    finally:
        shutdown_batch_reader()


if __name__ == "__main__":
    main()
