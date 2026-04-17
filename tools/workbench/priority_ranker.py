"""Priority ranker — ranks sermon dimensions by coaching urgency.

Given a list of tagger moments across multiple sermons, computes a
composite score per dimension and returns them sorted most-urgent-first.
"""

from __future__ import annotations

from sermon_tagger import DIMENSION_KEYS

# ── Impact weights ─────────────────────────────────────────────────

IMPACT_WEIGHTS: dict[str, float] = {
    'minor': 0.3,
    'moderate': 0.6,
    'major': 1.0,
}

# ── Actionability (static per dimension) ───────────────────────────

ACTIONABILITY: dict[str, float] = {
    'application_specificity': 1.0,
    'burden_clarity': 1.0,
    'movement_clarity': 0.7,
    'ethos_rating': 0.7,
    'concreteness_score': 0.7,
    'christ_thread_score': 0.4,
    'exegetical_grounding': 0.4,
}

# ── Overall-score weights ──────────────────────────────────────────

W_IMPACT = 0.35
W_EVIDENCE = 0.25
W_TRAJECTORY = 0.25
W_ACTIONABILITY = 0.15


def compute_priority_ranking(
    moments: list[dict],
    n_sermons: int,
    recent_sermon_ids: list | None = None,
) -> list[dict]:
    """Rank dimensions by coaching urgency.

    Parameters
    ----------
    moments:
        Each dict must have at least ``dimension_key``, ``valence``,
        ``confidence``, ``impact``, and ``sermon_id``.
    n_sermons:
        Total sermons in the corpus (denominator for rate scores).
    recent_sermon_ids:
        Optional list of most-recent sermon IDs (reserved for future
        recency weighting).

    Returns
    -------
    List of dicts sorted by ``overall_rank`` (1 = most urgent), one per
    dimension key.
    """
    # Bucket negative moments by dimension
    negatives: dict[str, list[dict]] = {dk: [] for dk in DIMENSION_KEYS}
    for m in moments:
        dk = m.get('dimension_key')
        if dk not in DIMENSION_KEYS:
            continue
        if m.get('valence') != 'negative':
            continue
        negatives[dk].append(m)

    # Compute per-dimension sub-scores
    rows: list[dict] = []
    safe_n = max(n_sermons, 1)  # avoid division by zero

    for dk in sorted(DIMENSION_KEYS):
        negs = negatives[dk]
        n_neg = len(negs)

        # impact_priority_score
        impact_sum = sum(
            IMPACT_WEIGHTS.get(m.get('impact', 'minor'), 0.3) * m.get('confidence', 0)
            for m in negs
        )
        impact_score = min(1.0, impact_sum / safe_n)

        # evidence_strength_score
        if n_neg > 0:
            avg_conf = sum(m.get('confidence', 0) for m in negs) / n_neg
            evidence_score = min(1.0, n_neg / 10) * avg_conf
        else:
            evidence_score = 0.0

        # trajectory_score — neutral default for now
        trajectory_score = 0.5

        # actionability_score
        actionability_score = ACTIONABILITY.get(dk, 0.5)

        # overall_score
        overall = (
            W_IMPACT * impact_score
            + W_EVIDENCE * evidence_score
            + W_TRAJECTORY * trajectory_score
            + W_ACTIONABILITY * actionability_score
        )

        rows.append({
            'dimension_key': dk,
            'impact_priority_score': impact_score,
            'evidence_strength_score': evidence_score,
            'trajectory_score': trajectory_score,
            'actionability_score': actionability_score,
            'overall_score': overall,
            'n_negative_moments': n_neg,
        })

    # Sort by overall_score descending, then alphabetically for ties
    rows.sort(key=lambda r: (-r['overall_score'], r['dimension_key']))

    # Assign ranks and compute confidence_in_ranking
    for i, row in enumerate(rows):
        row['overall_rank'] = i + 1

    if len(rows) >= 2:
        gap = rows[0]['overall_score'] - rows[1]['overall_score']
    else:
        gap = 0.0

    for row in rows:
        row['confidence_in_ranking'] = gap

    return rows
