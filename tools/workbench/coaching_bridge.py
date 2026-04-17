"""Coaching bridge helpers — load commitment, insights, exposure tracking.

Connects the sermon coaching system's data into the study companion so that
during sermon prep, the AI can reference Bryan's historical patterns and
coaching agreements without nagging.
"""

import json
from datetime import datetime, timezone
from typing import Optional


def load_active_commitment(db) -> Optional[dict]:
    """Load the single active coaching commitment, if any.

    Returns dict with dimension_key, practice_experiment, target_sermons,
    created_at — or None if no active commitment exists.
    """
    conn = db._conn()
    row = conn.execute(
        "SELECT dimension_key, practice_experiment, target_sermons, created_at "
        "FROM coaching_commitments WHERE status = 'active'"
    ).fetchone()
    conn.close()
    if row is None:
        return None
    return {
        'dimension_key': row[0],
        'practice_experiment': row[1],
        'target_sermons': row[2],
        'created_at': row[3],
    }


def load_coaching_insights(db, limit=5) -> list:
    """Load recent non-superseded coaching insights.

    Returns list of dicts with id, dimension_key, summary, applies_when
    (parsed JSON list), avoid_when (parsed JSON list), source_sermon_id,
    created_at.
    """
    conn = db._conn()
    rows = conn.execute(
        "SELECT id, dimension_key, summary, applies_when, avoid_when, "
        "source_sermon_id, created_at "
        "FROM coaching_insights "
        "WHERE superseded_by IS NULL "
        "ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    results = []
    for row in rows:
        results.append({
            'id': row[0],
            'dimension_key': row[1],
            'summary': row[2],
            'applies_when': _parse_json_list(row[3]),
            'avoid_when': _parse_json_list(row[4]),
            'source_sermon_id': row[5],
            'created_at': row[6],
        })
    return results


def record_coaching_exposure(db, session_id, dimension_key, escalation_level, response='pending'):
    """Record or update coaching exposure for a session+dimension.

    escalation_level: 1-5 (silent shaping through concrete intervention)
    response: 'accepted', 'declined', 'deferred', or 'pending'
    """
    if not 1 <= escalation_level <= 5:
        raise ValueError(f"escalation_level must be 1-5, got {escalation_level}")
    valid_responses = ('accepted', 'declined', 'deferred', 'pending')
    if response not in valid_responses:
        raise ValueError(f"response must be one of {valid_responses}, got {response!r}")

    now = datetime.now(timezone.utc).isoformat()
    conn = db._conn()
    # Check if already exists — don't overwrite declined/accepted state
    existing = conn.execute(
        "SELECT response FROM session_coaching_exposure "
        "WHERE session_id = ? AND dimension_key = ?",
        (session_id, dimension_key),
    ).fetchone()
    if existing and existing[0] in ('declined', 'accepted'):
        conn.close()
        return  # Don't resurface — anti-nagging guard
    conn.execute(
        "INSERT INTO session_coaching_exposure "
        "(session_id, dimension_key, escalation_level, response, created_at) "
        "VALUES (?, ?, ?, ?, ?) "
        "ON CONFLICT(session_id, dimension_key) DO UPDATE SET "
        "escalation_level = excluded.escalation_level, "
        "response = excluded.response, "
        "created_at = excluded.created_at",
        (session_id, dimension_key, escalation_level, response, now),
    )
    conn.commit()
    conn.close()


def check_coaching_exposure(db, session_id, dimension_key) -> Optional[dict]:
    """Check if a coaching dimension has been surfaced this session.

    Returns dict with escalation_level, response — or None.
    """
    conn = db._conn()
    row = conn.execute(
        "SELECT escalation_level, response "
        "FROM session_coaching_exposure "
        "WHERE session_id = ? AND dimension_key = ?",
        (session_id, dimension_key),
    ).fetchone()
    conn.close()
    if row is None:
        return None
    return {
        'escalation_level': row[0],
        'response': row[1],
    }


def build_coaching_prompt_section(commitment, insights) -> str:
    """Build the coaching context section for the system prompt.

    Returns empty string if no commitment and no insights.
    When data exists, includes active commitment, recent insights,
    retrieval policy, escalation ladder, and anti-nagging rules.
    """
    if commitment is None and not insights:
        return ''

    parts = []

    # Active commitment
    if commitment is not None:
        parts.append(
            "## Active Coaching Commitment (background — do not recite verbatim)\n"
            "\n"
            f"Dimension: {commitment['dimension_key']}\n"
            f"Practice: {commitment['practice_experiment']}\n"
            f"Target: {commitment['target_sermons']} sermons\n"
            "\n"
            "Rules:\n"
            "- Never recite the commitment back verbatim\n"
            "- Use it as a lens that shapes guidance — e.g., when Bryan reaches "
            "application work, naturally ask questions aligned with the practice "
            "rather than saying \"your commitment says...\"\n"
            "- Active commitment is a bias, not a straitjacket — if today's text "
            "demands something different, follow the text"
        )

    # Recent coaching insights
    if insights:
        insight_lines = ["## Recent Coaching Insights\n"]
        for i, ins in enumerate(insights[:3], 1):
            applies = ', '.join(ins['applies_when']) if ins['applies_when'] else 'any'
            avoids = ', '.join(ins['avoid_when']) if ins['avoid_when'] else 'none'
            insight_lines.append(
                f"{i}. [{ins['dimension_key']}] {ins['summary']}\n"
                f"   Applies when: {applies}\n"
                f"   Avoid when: {avoids}"
            )
        parts.append('\n'.join(insight_lines))

    # Retrieval policy
    parts.append(
        "## Coaching Memory — Retrieval Policy\n"
        "\n"
        "You have access to Bryan's longitudinal sermon coaching data. Use it to sharpen\n"
        "your homiletical guidance — never to nag, lecture, or constantly reference the past.\n"
        "\n"
        "WHEN TO CONSULT:\n"
        "- During textual work (observation, word study, context, commentaries): Do NOT\n"
        "  consult coaching tools. Your job here is discovery. The only exception is if\n"
        "  Bryan explicitly asks about past sermons.\n"
        "- When transitioning to sermon shaping: Ask \"Are we still exploring the text,\n"
        "  or are we shaping the sermon now?\" That question is the gate. Once Bryan says\n"
        "  \"let's shape it,\" coaching tools activate.\n"
        "- During sermon construction: Check get_active_commitment. Consult other tools\n"
        "  when you detect sprawling outline, deferred application, unclear burden, or\n"
        "  Bryan asks for examples.\n"
        "\n"
        "TOOL PRECEDENCE (when coaching data conflicts):\n"
        "1. Active commitment (most specific, Bryan-approved)\n"
        "2. Stable sermon pattern aggregates (strongest evidence base)\n"
        "3. Counterexamples (what worked differently)\n"
        "4. Coaching insights (recent, but may have recency bias)\n"
        "5. Representative moments (evidence, not guidance)\n"
        "\n"
        "NO SERMON TITLES/DATES UNPROMPTED:\n"
        "Do not reference specific sermon titles or dates unless Bryan asks for evidence\n"
        "or disputes a pattern claim.\n"
        "\n"
        "GRACEFUL DEGRADATION:\n"
        "If coaching data is sparse, stale, or doesn't apply to the current sermon type,\n"
        "do not pretend confidence. Say nothing rather than force irrelevant coaching."
    )

    # Escalation ladder
    parts.append(
        "## ESCALATION LADDER (never skip levels)\n"
        "\n"
        "1. SILENT SHAPING\n"
        "   Guide toward clarity without any coaching reference.\n"
        "   \"Let's tighten this to one governing idea.\"\n"
        "\n"
        "2. DIAGNOSTIC CHECK\n"
        "   Ask a targeted question that tests whether the issue is present.\n"
        "   \"What's the one burden you want them to carry out of the room?\"\n"
        "   Do NOT reference history yet. Let Bryan's answer reveal the state.\n"
        "\n"
        "3. PATTERN REFERENCE\n"
        "   Only if the diagnostic confirms drift or confusion.\n"
        "   \"A recurring pattern in your recent sermons is that the burden emerges late.\n"
        "   Want to state it now before we build the outline?\"\n"
        "\n"
        "4. SPECIFIC EXAMPLE\n"
        "   Only if Bryan asks, disputes the pattern, or seems stuck.\n"
        "   \"In your Romans 2 sermon, you found the application at minute 10 by naming\n"
        "   a specific person — 'the coworker you've been avoiding.' That landed.\"\n"
        "\n"
        "5. CONCRETE INTERVENTION\n"
        "   Offer one action, not more analysis.\n"
        "   \"Let's write the burden sentence right now: 'God teaches us that ___.'\n"
        "   We'll test each movement against it.\""
    )

    # Anti-nagging rules
    parts.append(
        "## ANTI-NAGGING RULES\n"
        "\n"
        "RELEVANCE GATE — before ANY coaching callback, ALL must be true:\n"
        "1. Prep mode is sermon-shaping (not textual discovery)\n"
        "2. Active commitment or pattern is plausibly relevant to this passage/genre\n"
        "3. Current work actually exhibits the risk (not hypothetical)\n"
        "4. The issue has not already been surfaced and addressed this session\n"
        "\n"
        "BACKING OFF:\n"
        "- If Bryan declines or redirects (\"I know, but this passage needs the density\"),\n"
        "  record response='declined' and do not resurface that dimension this session\n"
        "  unless Bryan reopens it\n"
        "- If Bryan accepts and acts on it, record response='accepted' and move on\n"
        "- Maximum one explicit pattern reference per coaching dimension per session\n"
        "\n"
        "FRAMING:\n"
        "- Frame as allyship: \"To help this land more clearly...\" not \"Because you usually...\"\n"
        "- Prefer simplification choices over reflective warnings\n"
        "- Brief, binary or comparative when possible (ADHD-friendly)\n"
        "\n"
        "HEALTHY DEVIATION:\n"
        "- If Bryan is doing a typically weak area WELL in the current prep, stay silent.\n"
        "  Counterexamples should prevent false positives, not just support escalation.\n"
        "- Do not force the commitment lens onto a sermon that doesn't need it."
    )

    return '\n\n'.join(parts)


def _parse_json_list(value):
    """Parse a JSON string as a list of strings. Coerces non-string elements."""
    if not value:
        return []
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
        return [str(parsed)]
    except (json.JSONDecodeError, TypeError):
        return [value]
