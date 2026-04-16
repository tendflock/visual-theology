"""Sermon tagger taxonomy constants and LLM output parser.

Defines the closed enums for dimension keys, section roles, and homiletic
moves used by the tagger prompt (Task 11).  parse_tagger_output() validates
and filters the raw JSON that the LLM returns into a clean moment list.
"""

# ── Taxonomy constants ──────────────────────────────────────────────

DIMENSION_KEYS = frozenset({
    'burden_clarity', 'movement_clarity', 'application_specificity',
    'ethos_rating', 'concreteness_score', 'christ_thread_score',
    'exegetical_grounding',
})

SECTION_ROLES = frozenset({
    'intro', 'setup', 'exposition', 'illustration_section', 'application',
    'transition', 'recap', 'appeal', 'conclusion', 'prayer', 'reading',
})

HOMILETIC_MOVES = frozenset({
    'big_idea_statement', 'structure_signpost', 'textual_observation',
    'doctrinal_claim', 'illustration', 'exhortation', 'application',
    'christ_connection', 'gospel_implication', 'objection_handling',
    'direct_address', 'diagnostic_question', 'pastoral_comfort',
    'warning', 'summary_restatement', 'contextualization',
})

CONFIDENCE_FLOOR = 0.65
MAX_MOMENTS_PER_SERMON = 18
TAGGER_PROMPT_VERSION = '1.0.0'

_VALID_VALENCES = {'positive', 'negative'}
_VALID_IMPACTS = {'minor', 'moderate', 'major'}


# ── Output parser ───────────────────────────────────────────────────

def parse_tagger_output(raw: dict) -> list[dict]:
    """Validate, fix up, and filter moments from the tagger LLM response.

    *raw* is the parsed JSON dict the LLM returned.  Expected shape::

        {"moments": [ {dimension_key, valence, ...}, ... ]}

    Returns a list of validated moment dicts, sorted by confidence
    descending and capped at MAX_MOMENTS_PER_SERMON.
    """
    moments = raw.get('moments')
    if not isinstance(moments, list):
        return []

    accepted: list[dict] = []
    for m in moments:
        if not isinstance(m, dict):
            continue

        # ── Hard-drop checks ────────────────────────────────────
        if m.get('dimension_key') not in DIMENSION_KEYS:
            continue
        if m.get('valence') not in _VALID_VALENCES:
            continue
        if m.get('section_role') not in SECTION_ROLES:
            continue
        if m.get('impact') not in _VALID_IMPACTS:
            continue

        conf = m.get('confidence')
        if not isinstance(conf, (int, float)):
            continue
        if conf < CONFIDENCE_FLOOR:
            continue

        excerpt = m.get('excerpt_text')
        if not isinstance(excerpt, str) or not excerpt.strip():
            continue

        rationale = m.get('rationale')
        if not isinstance(rationale, str) or not rationale.strip():
            continue

        if not isinstance(m.get('start_segment_index'), int):
            continue
        if not isinstance(m.get('end_segment_index'), int):
            continue

        # ── Fixup rules (repair, don't drop) ────────────────────
        if m.get('homiletic_move') not in HOMILETIC_MOVES:
            m['homiletic_move'] = None

        if conf > 1.0:
            conf = 1.0
            m['confidence'] = conf

        accepted.append(m)

    # Sort by confidence descending, then cap.
    accepted.sort(key=lambda x: x['confidence'], reverse=True)
    return accepted[:MAX_MOMENTS_PER_SERMON]
