"""Read-only corpus-scoped query tools for the meta-coach agent.

Every function takes a CompanionDB instance as its first arg and returns
structured dicts.  No mutations — the meta-coach reads the sermon_moments,
sermons, sermon_reviews, analysis_runs, and coaching_commitments tables but
never writes to them.

Common filter kwargs accepted by most functions:
    window_days     (int, default 90)   — date range from today
    min_confidence  (float, default 0.65) — confidence floor on moments
    per_sermon_cap  (int, default 2)    — max moments per sermon in results
    series          (str, optional)     — filter by sermon series name
    dimension_key   (str, optional)     — filter by specific dimension
"""

from __future__ import annotations

import statistics
from typing import Optional

from sermon_tagger import DIMENSION_KEYS


# ── Shared helpers ────────────────────────────────────────────────

def _apply_filters(base_query: str, params: list, filters: dict,
                   moment_alias: str = 'sm', sermon_alias: str = 's',
                   run_alias: str = 'ar') -> tuple[str, list]:
    """Append WHERE clauses for the common filter parameters.

    Returns the extended query string and updated params list.
    The caller must have already included the base JOINs for
    sermon_moments (moment_alias), sermons (sermon_alias), and
    analysis_runs (run_alias).
    """
    clauses: list[str] = []

    # Only active analysis runs
    clauses.append(f'{run_alias}.is_active = 1')

    # Only real sermons, not deleted
    clauses.append(f"{sermon_alias}.classified_as = 'sermon'")
    clauses.append(f'{sermon_alias}.is_remote_deleted = 0')

    # Date window
    window_days = filters.get('window_days', 90)
    clauses.append(
        f"{sermon_alias}.preach_date >= date('now', '-' || ? || ' days')"
    )
    params.append(int(window_days))

    # Confidence floor
    min_confidence = filters.get('min_confidence', 0.65)
    clauses.append(f'{moment_alias}.confidence >= ?')
    params.append(float(min_confidence))

    # Optional series filter
    series = filters.get('series')
    if series:
        clauses.append(f'{sermon_alias}.series = ?')
        params.append(series)

    # Optional dimension filter
    dimension_key = filters.get('dimension_key')
    if dimension_key:
        clauses.append(f'{moment_alias}.dimension_key = ?')
        params.append(dimension_key)

    where = ' AND '.join(clauses)
    if ' WHERE ' in base_query:
        base_query += ' AND ' + where
    else:
        base_query += ' WHERE ' + where

    return base_query, params


def _row_to_dict(row, cursor_description) -> dict:
    """Convert a sqlite3.Row or tuple to a plain dict using cursor.description."""
    if row is None:
        return {}
    return {cursor_description[i][0]: row[i] for i in range(len(cursor_description))}


def _apply_per_sermon_cap(rows: list[dict], cap: int,
                          sermon_key: str = 'sermon_id') -> list[dict]:
    """Keep at most *cap* rows per sermon, preserving input order."""
    counts: dict[int, int] = {}
    result = []
    for r in rows:
        sid = r.get(sermon_key)
        counts.setdefault(sid, 0)
        if counts[sid] < cap:
            result.append(r)
            counts[sid] += 1
    return result


# ── 1. get_corpus_dimension_summary ──────────────────────────────

def get_corpus_dimension_summary(db, **filters) -> list[dict]:
    """Per-dimension aggregate stats across the corpus.

    Returns one dict per dimension with counts of positive/negative moments,
    rates, and median confidence.
    """
    conn = db._conn()
    try:
        query = """
            SELECT sm.dimension_key, sm.valence, sm.confidence, sm.sermon_id
            FROM sermon_moments sm
            JOIN analysis_runs ar ON ar.id = sm.analysis_run_id
            JOIN sermons s ON s.id = sm.sermon_id
        """
        params: list = []
        query, params = _apply_filters(query, params, filters)

        cur = conn.execute(query, params)
        rows = cur.fetchall()

        # Bucket by dimension
        buckets: dict[str, dict] = {}
        for dk in DIMENSION_KEYS:
            buckets[dk] = {
                'positive': [], 'negative': [],
                'sermons': set(), 'confidences': [],
            }

        for r in rows:
            dk = r[0]
            if dk not in buckets:
                continue
            valence = r[1]
            conf = r[2]
            sid = r[3]
            buckets[dk][valence].append(sid)
            buckets[dk]['sermons'].add(sid)
            buckets[dk]['confidences'].append(conf)

        result = []
        for dk in sorted(DIMENSION_KEYS):
            b = buckets[dk]
            n_pos = len(b['positive'])
            n_neg = len(b['negative'])
            n_sermons = len(b['sermons'])
            confs = b['confidences']
            result.append({
                'dimension_key': dk,
                'n_positive': n_pos,
                'n_negative': n_neg,
                'positive_rate': round(n_pos / n_sermons, 2) if n_sermons else 0.0,
                'negative_rate': round(n_neg / n_sermons, 2) if n_sermons else 0.0,
                'n_sermons_with_moments': n_sermons,
                'median_confidence': round(statistics.median(confs), 2) if confs else 0.0,
            })
        return result
    finally:
        conn.close()


# ── 2. get_dimension_trend ───────────────────────────────────────

def get_dimension_trend(db, dimension: str, **filters) -> list[dict]:
    """Dimension scores over time — one row per sermon ordered by preach_date."""
    filters['dimension_key'] = dimension
    conn = db._conn()
    try:
        query = """
            SELECT sm.sermon_id, s.preach_date, s.title, sm.valence
            FROM sermon_moments sm
            JOIN analysis_runs ar ON ar.id = sm.analysis_run_id
            JOIN sermons s ON s.id = sm.sermon_id
        """
        params: list = []
        query, params = _apply_filters(query, params, filters)
        query += ' ORDER BY s.preach_date ASC'

        cur = conn.execute(query, params)
        rows = cur.fetchall()

        # Aggregate per sermon
        sermon_data: dict[int, dict] = {}
        for r in rows:
            sid = r[0]
            if sid not in sermon_data:
                sermon_data[sid] = {
                    'sermon_id': sid,
                    'preach_date': r[1],
                    'title': r[2],
                    'n_positive': 0,
                    'n_negative': 0,
                }
            if r[3] == 'positive':
                sermon_data[sid]['n_positive'] += 1
            else:
                sermon_data[sid]['n_negative'] += 1

        # Sort by preach_date
        result = sorted(sermon_data.values(), key=lambda d: d['preach_date'] or '')
        return result
    finally:
        conn.close()


# ── 3. get_dimension_distribution ────────────────────────────────

def get_dimension_distribution(db, dimension: str, **filters) -> dict:
    """Variance/spread for one dimension — net score per sermon."""
    filters['dimension_key'] = dimension
    conn = db._conn()
    try:
        query = """
            SELECT sm.sermon_id, sm.valence
            FROM sermon_moments sm
            JOIN analysis_runs ar ON ar.id = sm.analysis_run_id
            JOIN sermons s ON s.id = sm.sermon_id
        """
        params: list = []
        query, params = _apply_filters(query, params, filters)

        cur = conn.execute(query, params)
        rows = cur.fetchall()

        sermon_counts: dict[int, dict] = {}
        for r in rows:
            sid = r[0]
            if sid not in sermon_counts:
                sermon_counts[sid] = {'positive': 0, 'negative': 0}
            if r[1] == 'positive':
                sermon_counts[sid]['positive'] += 1
            else:
                sermon_counts[sid]['negative'] += 1

        scores = []
        for sid, c in sorted(sermon_counts.items()):
            scores.append({
                'sermon_id': sid,
                'net': c['positive'] - c['negative'],
                'positive': c['positive'],
                'negative': c['negative'],
            })

        return {
            'dimension_key': dimension,
            'scores': scores,
        }
    finally:
        conn.close()


# ── 4. get_representative_moments ────────────────────────────────

_SORT_MAP = {
    'confidence_desc': 'sm.confidence DESC',
    'recency_desc': 's.preach_date DESC',
    'impact_desc': """CASE sm.impact
        WHEN 'major' THEN 3 WHEN 'moderate' THEN 2 ELSE 1 END DESC""",
    'position_asc': 'sm.sermon_position_pct ASC',
}


def get_representative_moments(db, dimension: str, valence: str,
                               sort: str = 'confidence_desc',
                               **filters) -> list[dict]:
    """Top moments for a dimension + valence, with sermon context."""
    per_sermon_cap = filters.pop('per_sermon_cap', 2)
    filters['dimension_key'] = dimension
    conn = db._conn()
    try:
        order_clause = _SORT_MAP.get(sort, 'sm.confidence DESC')
        query = f"""
            SELECT sm.sermon_id, s.title, s.preach_date,
                   sm.dimension_key, sm.valence, sm.confidence, sm.impact,
                   sm.excerpt_text, sm.rationale,
                   sm.start_ms, sm.end_ms,
                   sm.sermon_position_pct, sm.section_role
            FROM sermon_moments sm
            JOIN analysis_runs ar ON ar.id = sm.analysis_run_id
            JOIN sermons s ON s.id = sm.sermon_id
        """
        params: list = []
        query, params = _apply_filters(query, params, filters)
        query += f' AND sm.valence = ?'
        params.append(valence)
        query += f' ORDER BY {order_clause}'

        cur = conn.execute(query, params)
        desc = cur.description
        rows = [_row_to_dict(r, desc) for r in cur.fetchall()]

        return _apply_per_sermon_cap(rows, per_sermon_cap)
    finally:
        conn.close()


# ── 5. get_counterexamples ───────────────────────────────────────

def get_counterexamples(db, dimension: str,
                        target_pattern: str = 'recurring_weakness',
                        **filters) -> list[dict]:
    """Sermons where a typically weak dimension was unusually strong.

    Finds sermons with positive moments in the given dimension — these are
    counterexamples to a recurring weakness pattern.
    """
    per_sermon_cap = filters.pop('per_sermon_cap', 2)
    filters['dimension_key'] = dimension
    conn = db._conn()
    try:
        query = """
            SELECT sm.sermon_id, s.title, s.preach_date,
                   sm.dimension_key, sm.valence, sm.confidence, sm.impact,
                   sm.excerpt_text, sm.rationale,
                   sm.start_ms, sm.end_ms,
                   sm.sermon_position_pct, sm.section_role
            FROM sermon_moments sm
            JOIN analysis_runs ar ON ar.id = sm.analysis_run_id
            JOIN sermons s ON s.id = sm.sermon_id
        """
        params: list = []
        query, params = _apply_filters(query, params, filters)
        query += " AND sm.valence = 'positive'"
        query += ' ORDER BY sm.confidence DESC'

        cur = conn.execute(query, params)
        desc = cur.description
        rows = [_row_to_dict(r, desc) for r in cur.fetchall()]

        return _apply_per_sermon_cap(rows, per_sermon_cap)
    finally:
        conn.close()


# ── 6. get_sermon_context ────────────────────────────────────────

def get_sermon_context(db, sermon_id: int) -> dict:
    """Single sermon metadata + review scores.  No moment data."""
    conn = db._conn()
    try:
        cur = conn.execute("""
            SELECT s.id, s.title, s.bible_text_raw, s.preach_date,
                   s.duration_seconds, s.series,
                   sr.burden_clarity, sr.movement_clarity,
                   sr.application_specificity, sr.ethos_rating,
                   sr.concreteness_score, sr.christ_thread_score,
                   sr.exegetical_grounding,
                   sr.actual_duration_seconds, sr.duration_delta_seconds,
                   sr.one_change_for_next_sunday
            FROM sermons s
            LEFT JOIN sermon_reviews sr ON sr.sermon_id = s.id
            WHERE s.id = ?
        """, (sermon_id,))
        row = cur.fetchone()
        if not row:
            return {}
        return _row_to_dict(row, cur.description)
    finally:
        conn.close()


# ── 7. get_sermon_moment_sequence ────────────────────────────────

def get_sermon_moment_sequence(db, sermon_id: int,
                               dimension: Optional[str] = None) -> list[dict]:
    """Moments ordered through the sermon arc (by start_ms).

    If *dimension* is given, only moments for that dimension are returned.
    """
    conn = db._conn()
    try:
        query = """
            SELECT sm.id, sm.dimension_key, sm.valence, sm.confidence,
                   sm.impact, sm.start_ms, sm.end_ms,
                   sm.sermon_position_pct, sm.section_role,
                   sm.homiletic_move, sm.excerpt_text, sm.rationale
            FROM sermon_moments sm
            JOIN analysis_runs ar ON ar.id = sm.analysis_run_id
            WHERE sm.sermon_id = ? AND ar.is_active = 1
        """
        params: list = [sermon_id]
        if dimension:
            query += ' AND sm.dimension_key = ?'
            params.append(dimension)
        query += ' ORDER BY sm.start_ms ASC'

        cur = conn.execute(query, params)
        desc = cur.description
        return [_row_to_dict(r, desc) for r in cur.fetchall()]
    finally:
        conn.close()


# ── 8. compare_periods ───────────────────────────────────────────

def compare_periods(db, period_a: dict, period_b: dict,
                    dimensions: Optional[list[str]] = None) -> dict:
    """Compare dimension stats between two date ranges.

    Each period dict must have 'start_date' and 'end_date' (YYYY-MM-DD).
    Returns per-dimension stats for each period.
    """
    conn = db._conn()
    try:
        dims = dimensions or sorted(DIMENSION_KEYS)
        result: dict[str, dict] = {}

        for label, period in [('period_a', period_a), ('period_b', period_b)]:
            start = period['start_date']
            end = period['end_date']

            query = """
                SELECT sm.dimension_key, sm.valence, sm.sermon_id
                FROM sermon_moments sm
                JOIN analysis_runs ar ON ar.id = sm.analysis_run_id
                JOIN sermons s ON s.id = sm.sermon_id
                WHERE ar.is_active = 1
                  AND s.classified_as = 'sermon'
                  AND s.is_remote_deleted = 0
                  AND s.preach_date >= ? AND s.preach_date <= ?
            """
            params = [start, end]

            cur = conn.execute(query, params)
            rows = cur.fetchall()

            # Bucket by dimension
            buckets: dict[str, dict] = {}
            for dk in dims:
                buckets[dk] = {'positive': 0, 'negative': 0, 'sermons': set()}
            for r in rows:
                dk = r[0]
                if dk not in buckets:
                    continue
                buckets[dk][r[1]] += 1
                buckets[dk]['sermons'].add(r[2])

            period_stats = {}
            for dk in dims:
                b = buckets[dk]
                n_sermons = len(b['sermons'])
                period_stats[dk] = {
                    'n_positive': b['positive'],
                    'n_negative': b['negative'],
                    'n_sermons': n_sermons,
                    'positive_rate': round(b['positive'] / n_sermons, 2) if n_sermons else 0.0,
                    'negative_rate': round(b['negative'] / n_sermons, 2) if n_sermons else 0.0,
                }

            result[label] = {
                'start_date': start,
                'end_date': end,
                'dimensions': period_stats,
            }

        return result
    finally:
        conn.close()


# ── 9. get_evidence_quality ──────────────────────────────────────

def get_evidence_quality(db, **filters) -> dict:
    """Uncertainty report — how much to trust the moment data."""
    conn = db._conn()
    try:
        window_days = filters.get('window_days', 90)

        # Total sermons analyzed (have an active tagging run)
        cur = conn.execute("""
            SELECT COUNT(DISTINCT ar.sermon_id)
            FROM analysis_runs ar
            JOIN sermons s ON s.id = ar.sermon_id
            WHERE ar.is_active = 1 AND ar.run_type = 'tagging'
              AND s.classified_as = 'sermon' AND s.is_remote_deleted = 0
              AND s.preach_date >= date('now', '-' || ? || ' days')
        """, (int(window_days),))
        total_sermons_analyzed = cur.fetchone()[0] or 0

        # Total moments in window
        query = """
            SELECT sm.confidence, sm.dimension_key
            FROM sermon_moments sm
            JOIN analysis_runs ar ON ar.id = sm.analysis_run_id
            JOIN sermons s ON s.id = sm.sermon_id
            WHERE ar.is_active = 1
              AND s.classified_as = 'sermon' AND s.is_remote_deleted = 0
              AND s.preach_date >= date('now', '-' || ? || ' days')
        """
        cur = conn.execute(query, (int(window_days),))
        rows = cur.fetchall()
        total_moments = len(rows)

        # Low-confidence percentage (below 0.75)
        low_conf = sum(1 for r in rows if r[0] < 0.75)
        low_confidence_pct = round(low_conf / total_moments, 2) if total_moments else 0.0

        # Dimensions with few moments (< 3)
        dim_counts: dict[str, int] = {dk: 0 for dk in DIMENSION_KEYS}
        for r in rows:
            dk = r[1]
            if dk in dim_counts:
                dim_counts[dk] += 1
        dimensions_with_few_moments = [
            dk for dk, count in sorted(dim_counts.items()) if count < 3
        ]

        # Sermons missing tagging (sermon exists in window but has no active tagging run)
        cur = conn.execute("""
            SELECT COUNT(*)
            FROM sermons s
            WHERE s.classified_as = 'sermon' AND s.is_remote_deleted = 0
              AND s.preach_date >= date('now', '-' || ? || ' days')
              AND s.id NOT IN (
                  SELECT DISTINCT ar.sermon_id
                  FROM analysis_runs ar
                  WHERE ar.is_active = 1 AND ar.run_type = 'tagging'
              )
        """, (int(window_days),))
        sermons_missing_tagging = cur.fetchone()[0] or 0

        return {
            'total_sermons_analyzed': total_sermons_analyzed,
            'total_moments': total_moments,
            'low_confidence_pct': low_confidence_pct,
            'dimensions_with_few_moments': dimensions_with_few_moments,
            'sermons_missing_tagging': sermons_missing_tagging,
        }
    finally:
        conn.close()


# ── 10. get_data_freshness ───────────────────────────────────────

def get_data_freshness(db) -> dict:
    """Pipeline completeness — how much of the sermon corpus has been processed."""
    conn = db._conn()
    try:
        # Total sermons (real, not deleted)
        cur = conn.execute("""
            SELECT COUNT(*) FROM sermons
            WHERE classified_as = 'sermon' AND is_remote_deleted = 0
        """)
        total_sermons = cur.fetchone()[0] or 0

        # Sermons with transcript segments
        cur = conn.execute("""
            SELECT COUNT(*) FROM sermons
            WHERE classified_as = 'sermon' AND is_remote_deleted = 0
              AND transcript_segments IS NOT NULL
        """)
        sermons_with_segments = cur.fetchone()[0] or 0

        # Sermons with reviews
        cur = conn.execute("""
            SELECT COUNT(*) FROM sermon_reviews sr
            JOIN sermons s ON s.id = sr.sermon_id
            WHERE s.classified_as = 'sermon' AND s.is_remote_deleted = 0
        """)
        sermons_with_reviews = cur.fetchone()[0] or 0

        # Sermons with active tagging
        cur = conn.execute("""
            SELECT COUNT(DISTINCT ar.sermon_id)
            FROM analysis_runs ar
            JOIN sermons s ON s.id = ar.sermon_id
            WHERE ar.is_active = 1 AND ar.run_type = 'tagging'
              AND s.classified_as = 'sermon' AND s.is_remote_deleted = 0
        """)
        sermons_with_tagging = cur.fetchone()[0] or 0

        # Most recent sermon date
        cur = conn.execute("""
            SELECT MAX(preach_date) FROM sermons
            WHERE classified_as = 'sermon' AND is_remote_deleted = 0
        """)
        row = cur.fetchone()
        most_recent_sermon_date = row[0] if row else None

        # Most recent tagging date
        cur = conn.execute("""
            SELECT MAX(ar.created_at) FROM analysis_runs ar
            JOIN sermons s ON s.id = ar.sermon_id
            WHERE ar.is_active = 1 AND ar.run_type = 'tagging'
              AND s.classified_as = 'sermon' AND s.is_remote_deleted = 0
        """)
        row = cur.fetchone()
        most_recent_tagging_date = row[0] if row else None

        return {
            'total_sermons': total_sermons,
            'sermons_with_segments': sermons_with_segments,
            'sermons_with_reviews': sermons_with_reviews,
            'sermons_with_tagging': sermons_with_tagging,
            'most_recent_sermon_date': most_recent_sermon_date,
            'most_recent_tagging_date': most_recent_tagging_date,
        }
    finally:
        conn.close()


# ── 11. get_active_commitment ────────────────────────────────────

def get_active_commitment(db) -> Optional[dict]:
    """Current coaching commitment and progress toward it.

    Returns None if no active commitment exists.
    """
    conn = db._conn()
    try:
        cur = conn.execute("""
            SELECT id, dimension_key, practice_experiment, target_sermons,
                   baseline_sermon_id, status, created_at, reviewed_at
            FROM coaching_commitments
            WHERE status = 'active'
            LIMIT 1
        """)
        row = cur.fetchone()
        if not row:
            return None

        commitment = _row_to_dict(row, cur.description)
        created_at = commitment['created_at']
        dimension_key = commitment['dimension_key']

        # Count sermons preached since the commitment was created
        cur = conn.execute("""
            SELECT COUNT(*) FROM sermons
            WHERE classified_as = 'sermon' AND is_remote_deleted = 0
              AND preach_date >= date(?)
        """, (created_at,))
        sermons_since = cur.fetchone()[0] or 0

        # Count positive and negative moments in that dimension since commitment
        cur = conn.execute("""
            SELECT sm.valence, COUNT(*)
            FROM sermon_moments sm
            JOIN analysis_runs ar ON ar.id = sm.analysis_run_id
            JOIN sermons s ON s.id = sm.sermon_id
            WHERE ar.is_active = 1
              AND s.classified_as = 'sermon' AND s.is_remote_deleted = 0
              AND s.preach_date >= date(?)
              AND sm.dimension_key = ?
            GROUP BY sm.valence
        """, (created_at, dimension_key))
        valence_counts = {r[0]: r[1] for r in cur.fetchall()}

        commitment['progress'] = {
            'sermons_since': sermons_since,
            'positive_moments_found': valence_counts.get('positive', 0),
            'negative_moments_found': valence_counts.get('negative', 0),
        }
        return commitment
    finally:
        conn.close()
