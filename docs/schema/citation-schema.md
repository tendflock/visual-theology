# Dual-Citation Schema (WS0a-A3)

Status: **locked 2026-04-24.** Supersedes the older `{resourceId, logosArticleNum, quote}`
shape used in `docs/research/2026-04-23-daniel-interpretive-taxonomy-survey.md` (pre-WS0).

## Why this shape

A citation has to serve two masters:

1. **The verifier** (tools/`citations.py`, WS0c) — needs a stable backend anchor to re-open the
   resource and confirm the quote is still there.
2. **The reader with a book in hand** — needs a human-readable anchor (author, title, section
   heading, page) to find the same material in the print or ebook edition.

So we carry both. `backend` is the machine handle. `frontend` is the scholarly one. `quote` binds
them with the verbatim text and a tamper-evidence hash.

## Canonical shape

```json
{
  "backend": {
    "resourceId": "LLS:RFRMDSYSTH04",
    "logosArticleNum": 4718,
    "nativeSectionId": "R48.2"
  },
  "frontend": {
    "author": "Beeke & Smalley",
    "title": "Reformed Systematic Theology, Vol. 4: Church and Last Things",
    "section": "§R48.2 — A Failed Expectation",
    "page": 1497,
    "pageEnd": 1498,
    "citationString": "Beeke & Smalley, RST 4, §R48.2 (pp. 1497–1498)"
  },
  "quote": {
    "text": "Inaugurated eschatology implies that eschatology has indeed begun, but is by no means finished.",
    "sha256": "c4f0a8…"
  }
}
```

## Field reference

### `backend` (machine handle — required)

| field | type | source | notes |
|---|---|---|---|
| `resourceId` | string | `study.get_article_meta(...).resourceId` | Logos LLS identifier. Stable across Logos library rebuilds. |
| `logosArticleNum` | integer | `study.get_article_meta(...).logosArticleNum` | Sequential article ordinal within the resource. Not scholarly. |
| `nativeSectionId` | string | `study.get_article_meta(...).nativeSectionId` | `ArticleNumberToArticleId`. Stable human-readable anchor (e.g., `R48.2`, `DA.7.13`, `GDANIEL0416`). Required. |

### `frontend` (human anchor — required except as noted)

| field | type | source | notes |
|---|---|---|---|
| `author` | string | resource metadata / research notes | Display name. E.g., `Beeke & Smalley`, `Collins`, `Walvoord`. |
| `title` | string | resource metadata / research notes | Short title plus volume/ed. if applicable. |
| `section` | string \| null | derived | `§{nativeSectionId} — {heading}` when heading is known. Fall back to `§{nativeSectionId}` alone. |
| `page` | integer \| null | `get_article_meta(...).pageStart` | Primary printed page. Null when the resource has no embedded milestone index, or the article's offsets don't overlap a page milestone. **Do not fabricate a page number.** |
| `pageEnd` | integer \| null | `get_article_meta(...).pageEnd` | Only present when the article spans multiple printed pages and `pageEnd > page`. Omit (or null) otherwise. |
| `citationString` | string | derived | Pre-rendered scholarly citation. Pattern below. |

### `quote` (the verifiable substance — required for every cited claim)

| field | type | source | notes |
|---|---|---|---|
| `text` | string | verbatim article text | The exact quoted fragment, UTF-8. Prefer 40+ chars for robust matching. Verification normalizes whitespace to single spaces and matches case-insensitively (so sentence-initial capitalization drift still verifies). Preserve punctuation and diacritics exactly. |
| `sha256` | string (64-hex lowercase) | derived | `sha256(text.encode("utf-8")).hexdigest()`. Tamper-evidence: future verifier runs confirm the stored `text` hasn't drifted. |

If a claim is paraphrased rather than quoted, `quote` may be `null` — but in that case, the
`backend` must still pin a specific article (not a vague range), and the research doc's narrative
must make the paraphrase explicit.

## Null rules, explicit

These fields are genuinely nullable on some resources in the library. Do not hallucinate them
when the reader returns `null`.

- `frontend.section` — null if both `nativeSectionId` and `heading` are missing (rare).
- `frontend.page`, `frontend.pageEnd` — null when `hasMilestoneIndex == false`, or when no
  `SegmentReferences_page` row overlaps the article's character range. Empirically, the three
  `.lbxlls` Daniel primary-voice resources (Collins Hermeneia, Walvoord, Blaising & Bock) lack
  milestone indexes and will have `page: null`. Durham Revelation (COMMREVDURHAM.logos4) also
  lacks milestone index — confirmed 2026-04-24.
- `quote.text` and `quote.sha256` — null together if the citation is a paraphrase anchor only.

## `citationString` pattern

Pre-rendered citation strings let each agent produce the same display form. Use:

| case | pattern |
|---|---|
| page known, single page | `{author}, {shortTitle}, §{nativeSectionId} (p. {page})` |
| page known, range | `{author}, {shortTitle}, §{nativeSectionId} (pp. {page}–{pageEnd})` |
| no page, native section only | `{author}, {shortTitle}, §{nativeSectionId}` |
| no section or page (degenerate) | `{author}, {shortTitle}, Logos art. {logosArticleNum}` — use sparingly |

`shortTitle` is author's discretion — e.g., `RST 4`, `Hermeneia Daniel`, `Progressive Dispensationalism`.

Examples:
- `Beeke & Smalley, RST 4, §R48.2 (pp. 1497–1498)`
- `Collins, Hermeneia Daniel, §DA.7.13`
- `Walvoord, Daniel, §GDANIEL0416`
- `Newsom, OTL Daniel, §7.13 (p. 240)` — hypothetical if OTL has milestone index

## sha256 computation

```python
import hashlib
sha = hashlib.sha256(quote_text.encode("utf-8")).hexdigest()
```

Lowercase hex. UTF-8 encoding. No trimming, no normalization — the hash binds the exact string
you chose to store in `quote.text`.

## Python helper (authoritative)

`tools/citations.py` (WS0c) is the reference implementation. Agents must import from it rather
than re-rolling the derivation logic:

```python
from citations import build_citation, verify_citation, sha256_of

c = build_citation(
    resource_file="RFRMDSYSTH04.logos4",
    article_num=4718,
    quote_text="Inaugurated eschatology implies …",
    author="Beeke & Smalley",
    short_title="RST 4",
    full_title="Reformed Systematic Theology, Vol. 4: Church and Last Things",
)
# c matches the canonical shape above.

v = verify_citation(c)
# {"status": "verified" | "partial" | "quote-not-found" | "resource-unreadable",
#  "articleText_hash": "...", "match_span": (start, end) | None,
#  "notes": "..."}
```

Agents without access to `build_citation` must replicate the derivation rules above exactly,
including the null-field rules.

## Migration from pre-WS0 format

Existing research at `docs/research/2026-04-23-daniel-interpretive-taxonomy-survey.md` uses the
older `(art. N)` inline-citation shorthand. That format is grandfathered — the citation-sweep
(WS0c, task #9) will attempt to upgrade each one by running `get_article_meta` on the named
article and producing a canonical citation. Citations that fail upgrade are flagged.

New research (WS0b scholars) must emit the canonical shape directly.

## Test fixtures (for WS0c verifier tests)

Use these known-good citations:

- Article `4718` of `RFRMDSYSTH04.logos4` → `nativeSectionId = "R48.2"`, heading `A Failed
  Expectation`, pages `1497–1498`.
- Article `1323` of `PCLYPTCMGNTNPLT.logos4` (Collins, Apocalyptic Imagination) → contains the
  exact text `"the second-century date for the visions of Daniel (chaps. 7–12) is accepted as
  beyond reasonable doubt by critical scholarship."`
- Article `488` of `OTL27DA.logos4` (Newsom) → contains `"reinterpret this figure with
  increasing specificity, as prince of the host (8:11) and as Michael"` — caveat: article is
  46 k chars, verifier must read full article (default 20 k truncation loses this quote).
