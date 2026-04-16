"""
Enhanced agent for the Sermon Research Workbench.

Wraps the existing sermon_agent.py tool infrastructure with:
- Streaming responses via SSE
- Project-aware system prompt (passage, phase, research history, user notes)
- Conversation history persistence
- Extended tools for project management
"""

import json
import os
import sys
import time
from pathlib import Path

# Add tools directory to path
TOOLS_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(TOOLS_DIR))

from sermon_agent import TOOL_DEFINITIONS, execute_tool
from study import init_batch_reader, shutdown_batch_reader
import workbench_db as db
from app_secrets import anthropic_api_key

try:
    import anthropic
except ImportError:
    anthropic = None

# ── Research Phases ──────────────────────────────────────────────────────

PHASES = [
    ("exegesis", "Exegesis", "Read the text in multiple translations, establish what it says"),
    ("languages", "Original Languages", "Analyze Greek/Hebrew, word studies, morphology"),
    ("crossrefs", "Cross-References", "Find parallel passages and intertextual connections"),
    ("commentary", "Commentary Survey", "Read scholarly commentary and identify key interpretive issues"),
    ("synthesis", "Theological Synthesis", "Draw together findings into a coherent theological reading"),
    ("homiletics", "Homiletics", "Structure the sermon: outline, illustrations, application"),
]

PHASE_IDS = [p[0] for p in PHASES]

# ── Extended Tools ───────────────────────────────────────────────────────

# Project-aware tools that the agent can use to manage the workbench
PROJECT_TOOLS = [
    {
        "name": "save_research_finding",
        "description": "Save an important research finding to the project. Use this to record key insights, "
                       "commentary excerpts, word study results, or cross-reference discoveries as you work.",
        "input_schema": {
            "type": "object",
            "properties": {
                "item_type": {
                    "type": "string",
                    "enum": ["translation", "interlinear", "cross_ref", "commentary",
                             "word_study", "theological", "historical", "application", "other"],
                    "description": "Type of research finding",
                },
                "title": {"type": "string", "description": "Short title for this finding"},
                "content": {"type": "string", "description": "The finding content (markdown)"},
                "source": {"type": "string", "description": "Source (e.g., commentary name, Bible version)"},
            },
            "required": ["item_type", "title", "content"],
        },
    },
    {
        "name": "read_user_notes",
        "description": "Read the user's notes for the current project. Use this to understand what the "
                       "preacher has already observed, questioned, or planned.",
        "input_schema": {
            "type": "object",
            "properties": {
                "section": {
                    "type": "string",
                    "enum": ["general", "exegesis", "application", "illustrations", "outline"],
                    "description": "Note section to read. Omit to read all notes.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "suggest_next_research",
        "description": "Analyze what has been researched so far and suggest productive next steps.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]

# ── System Prompt ────────────────────────────────────────────────────────

BASE_SYSTEM_PROMPT = """\
You are a biblical scholar, exegete, and homiletician serving as a research assistant \
for sermon preparation. You have access to a large Logos 4 theological library containing \
302 Bibles, 1,025 commentaries, 49 lexicons, and thousands of other resources including \
ancient literature, confessional documents, and systematic theologies.

## Your Roles
1. **Research Assistant** — Systematically gather materials: read texts in multiple translations, \
extract interlinear data, survey commentaries, find cross-references, locate relevant resources.
2. **Interlocutor** — Engage in substantive dialogue about the text. Push back on shallow readings. \
Raise alternative interpretations. Ask clarifying questions about the preacher's theological commitments \
and homiletical intent.
3. **Homiletician** — Help structure sermons. Critique outlines for coherence, faithfulness to the text, \
and applicability. Suggest illustrations. Review manuscript drafts for clarity and theological precision.

## Research Methodology
1. **Read the passage** in multiple translations (ESV, NASB95, KJV minimum)
2. **Analyze original languages** — interlinear data, key word studies, morphological analysis
3. **Check cross-references** — how does this passage connect to the rest of Scripture?
4. **Survey commentaries** — what do scholars say? Where do they agree/disagree?
5. **Theological synthesis** — what are the main theological claims of this text?
6. **Homiletical application** — how does this text address the congregation?

## Available Greek/Hebrew Texts
- **SBLGNT** — SBL Greek New Testament (use `read_bible_passage` with version "SBLGNT")
- **NA28** — Nestle-Aland 28th Edition
- **Westcott-Hort** — WH 1881
- **Scrivener 1881** — Textus Receptus
- **Tregelles** — Critical text
- Note: THGNT is in the catalog but cannot be opened (version incompatible with this library)
- For Greek text, use `search_library` to find resources, then `read_specific_commentary` to read them

## Guidelines
- Always cite which translation or commentary you're drawing from
- When scholars disagree, present multiple views fairly before offering assessment
- Use `save_research_finding` to record important discoveries as you work
- Use `read_user_notes` to check what the preacher has already observed
- Be thorough but focused — depth over breadth
- When a tool returns an error, note it briefly and move on
- Format output in clean markdown
"""

PHASE_INSTRUCTIONS = {
    "exegesis": """
## Current Phase: Exegesis
Focus on establishing what the text says. Read in multiple translations. Note textual \
variants and translation differences. Identify the literary genre, structure, and flow \
of thought. Pay attention to conjunctions, particles, and discourse markers.""",

    "languages": """
## Current Phase: Original Languages
Focus on Greek/Hebrew analysis. Use the word_study tool and get_full_interlinear. \
Identify theologically significant terms. Note morphological details that affect meaning \
(tense, voice, mood for Greek; stem, binyan for Hebrew). Look for wordplay, chiasm, \
or other literary devices in the original.""",

    "crossrefs": """
## Current Phase: Cross-References
Focus on intertextual connections. Use cross-references and parallel passages. \
Trace key themes across Scripture. Identify OT quotations or allusions in NT texts. \
Note how the broader biblical narrative illuminates this passage.""",

    "commentary": """
## Current Phase: Commentary Survey
Focus on scholarly interpretation. Survey multiple commentaries for diverse perspectives. \
Note where commentators agree (likely settled interpretation) and where they disagree \
(live exegetical questions). Pay special attention to historical and cultural background.""",

    "synthesis": """
## Current Phase: Theological Synthesis
Draw together your findings. What are the main theological claims of this text? \
How do the exegetical details support the theological message? What is the text's \
contribution to biblical theology? How does it relate to systematic theological loci?""",

    "homiletics": """
## Current Phase: Homiletics
Focus on sermon structure and application. Help develop an outline that is faithful \
to the text's structure and theology. Suggest illustrations that illuminate without \
distracting. Consider specific applications for different audiences. Critique proposed \
outlines for coherence and faithfulness to the text.""",
}


def build_system_prompt(project):
    """Build a dynamic system prompt with project context."""
    parts = [BASE_SYSTEM_PROMPT]

    # Phase instructions
    phase = project.get("current_phase", "exegesis")
    if phase in PHASE_INSTRUCTIONS:
        parts.append(PHASE_INSTRUCTIONS[phase])

    # Project context
    parts.append(f"\n## Current Project")
    parts.append(f"**Passage:** {project['passage']}")
    if project.get("theme"):
        parts.append(f"**Theme:** {project['theme']}")
    parts.append(f"**Phase:** {phase}")

    # Research summary
    items = db.get_research_items(project["id"])
    if items:
        parts.append(f"\n## Research Completed So Far ({len(items)} items)")
        by_type = {}
        for item in items:
            t = item["item_type"]
            by_type.setdefault(t, []).append(item["title"] or item["source"] or "untitled")
        for item_type, titles in by_type.items():
            parts.append(f"- **{item_type}**: {', '.join(titles[:5])}"
                         + (f" (+{len(titles)-5} more)" if len(titles) > 5 else ""))

    # User notes summary
    notes = db.get_notes(project["id"])
    if notes:
        parts.append("\n## User's Notes")
        for note in notes:
            content = note["content"]
            if len(content) > 500:
                content = content[:500] + "..."
            parts.append(f"### {note['section'].title()}\n{content}")

    return "\n".join(parts)


# ── Project-Aware Tool Execution ─────────────────────────────────────────

def execute_project_tool(tool_name, tool_input, project_id):
    """Execute a tool, handling both library tools and project tools."""

    # Project-specific tools
    if tool_name == "save_research_finding":
        project = db.get_project(project_id)
        item_id = db.add_research_item(
            project_id,
            item_type=tool_input["item_type"],
            title=tool_input.get("title"),
            content=tool_input["content"],
            source=tool_input.get("source"),
            phase=project.get("current_phase") if project else None,
        )
        return {"saved": True, "item_id": item_id}

    if tool_name == "read_user_notes":
        section = tool_input.get("section")
        notes = db.get_notes(project_id, section)
        if not notes:
            return {"notes": [], "message": "No notes found for this project."}
        return {"notes": [{"section": n["section"], "content": n["content"]} for n in notes]}

    if tool_name == "suggest_next_research":
        return _suggest_next(project_id)

    # Library tools (existing sermon_agent tools)
    return execute_tool(tool_name, tool_input)


def _suggest_next(project_id):
    """Analyze project state and suggest next research steps."""
    project = db.get_project(project_id)
    if not project:
        return {"error": "Project not found"}

    items = db.get_research_items(project_id)
    types_done = {item["item_type"] for item in items}
    phase = project.get("current_phase", "exegesis")

    suggestions = []

    if "translation" not in types_done:
        suggestions.append("Read the passage in multiple translations (ESV, NASB95, KJV)")
    if "cross_ref" not in types_done:
        suggestions.append("Check cross-references for intertextual connections")
    if "interlinear" not in types_done and "word_study" not in types_done:
        suggestions.append("Analyze key terms in the original Greek/Hebrew")
    if "commentary" not in types_done:
        suggestions.append("Survey commentaries for scholarly interpretation")
    if len([i for i in items if i["item_type"] == "commentary"]) < 3:
        suggestions.append("Read additional commentaries for broader perspective")
    if "theological" not in types_done and len(items) > 5:
        suggestions.append("Synthesize findings into theological themes")

    # Phase-specific suggestions
    next_phase_idx = PHASE_IDS.index(phase) + 1 if phase in PHASE_IDS else 0
    if next_phase_idx < len(PHASES):
        nid, name, desc = PHASES[next_phase_idx]
        suggestions.append(f"Consider moving to the next phase: {name} — {desc}")

    return {
        "current_phase": phase,
        "items_completed": len(items),
        "types_covered": sorted(types_done),
        "suggestions": suggestions,
    }


# ── Streaming Agent ──────────────────────────────────────────────────────

MAX_RESULT_CHARS = 4000


def _truncate_result(result_str):
    """Truncate large tool results."""
    if len(result_str) <= MAX_RESULT_CHARS:
        return result_str
    try:
        data = json.loads(result_str)
    except (json.JSONDecodeError, TypeError):
        return result_str[:MAX_RESULT_CHARS] + "\n[... truncated ...]"

    for key in ("commentaries", "translations", "results", "resources"):
        if key in data and isinstance(data[key], list):
            while len(json.dumps(data, ensure_ascii=False)) > MAX_RESULT_CHARS and len(data[key]) > 1:
                data[key] = data[key][:-1]
            data[f"{key}_note"] = "truncated to fit context"

    truncated = json.dumps(data, ensure_ascii=False)
    if len(truncated) > MAX_RESULT_CHARS:
        return truncated[:MAX_RESULT_CHARS] + "\n[... truncated ...]"
    return truncated


def stream_agent_response(project_id, user_message, model="claude-sonnet-4-20250514", max_turns=8):
    """Generator yielding SSE events as the agent works.

    Events:
        {"type": "text", "content": "..."}         — streaming text chunk
        {"type": "tool_start", "name": "...", "input": {...}}
        {"type": "tool_result", "name": "...", "result": "..."}
        {"type": "done", "content": "..."}          — full final text
        {"type": "error", "message": "..."}
    """
    if anthropic is None:
        yield _sse({"type": "error", "message": "anthropic package not installed"})
        return

    api_key = anthropic_api_key()
    if not api_key:
        yield _sse({"type": "error", "message": "ANTHROPIC_API_KEY not set"})
        return

    project = db.get_project(project_id)
    if not project:
        yield _sse({"type": "error", "message": f"Project {project_id} not found"})
        return

    # Save user message
    db.add_message(project_id, "user", user_message)

    client = anthropic.Anthropic(api_key=api_key)
    system_prompt = build_system_prompt(project)
    all_tools = TOOL_DEFINITIONS + PROJECT_TOOLS

    # Build messages from history — trim to recent messages to control costs
    history = db.get_messages_for_api(project_id)
    if len(history) > 20:
        # Take last N messages, find a clean cut point starting at a plain user text message
        tail = history[-18:]
        while tail:
            msg = tail[0]
            if msg["role"] == "user" and isinstance(msg["content"], str):
                break
            tail = tail[1:]
        history = tail if tail else history[-2:]

    full_response_text = ""

    try:
        for turn in range(max_turns):
            response = client.messages.create(
                model=model,
                max_tokens=2048,
                system=system_prompt,
                tools=all_tools,
                messages=history,
            )

            # Process response content blocks
            assistant_content = []
            text_parts = []

            for block in response.content:
                if block.type == "text":
                    text_parts.append(block.text)
                    yield _sse({"type": "text", "content": block.text})
                    assistant_content.append({"type": "text", "text": block.text})
                elif block.type == "tool_use":
                    assistant_content.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    })

            # Save assistant message
            db.add_message(project_id, "assistant", json.dumps(assistant_content))

            if response.stop_reason == "end_turn":
                full_response_text = "\n".join(text_parts)
                yield _sse({"type": "done", "content": full_response_text})
                return

            if response.stop_reason == "tool_use":
                # Add assistant response to history
                history.append({"role": "assistant", "content": assistant_content})

                # Execute tools
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        yield _sse({
                            "type": "tool_start",
                            "name": block.name,
                            "input": block.input,
                        })

                        result = execute_project_tool(block.name, block.input, project_id)
                        result_str = json.dumps(result, indent=2, ensure_ascii=False)
                        result_str = _truncate_result(result_str)

                        yield _sse({
                            "type": "tool_result",
                            "name": block.name,
                            "result": result_str[:2000],  # Send abbreviated to browser
                        })

                        # Save to conversation
                        db.add_message(
                            project_id, "tool_result", result_str,
                            tool_name=block.id, tool_input=block.input,
                        )

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result_str,
                        })

                history.append({"role": "user", "content": tool_results})
            else:
                full_response_text = "\n".join(text_parts)
                yield _sse({"type": "done", "content": full_response_text})
                return

        yield _sse({"type": "done", "content": "(Reached maximum turns)"})

    except Exception as e:
        yield _sse({"type": "error", "message": f"{type(e).__name__}: {str(e)}"})


def _sse(data):
    """Format a dict as an SSE event string."""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
