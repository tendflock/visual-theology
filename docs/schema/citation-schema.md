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

The backend dispatches on a `kind` field (defaults to `"logos"` for back-compat).
Required fields and shape vary per kind.

#### `kind: "logos"` (default)

| field | type | source | notes |
|---|---|---|---|
| `kind` | string \| absent | implicit | Optional; absent means logos. |
| `resourceId` | string | `study.get_article_meta(...).resourceId` | Logos LLS identifier. Stable across Logos library rebuilds. |
| `logosArticleNum` | integer | `study.get_article_meta(...).logosArticleNum` | Sequential article ordinal within the resource. Not scholarly. |
| `nativeSectionId` | string | `study.get_article_meta(...).nativeSectionId` | `ArticleNumberToArticleId`. Stable human-readable anchor (e.g., `R48.2`, `DA.7.13`, `GDANIEL0416`). Required. |

#### `kind: "external-epub"` (WS0c-7)

For citations against EPUBs in `external-resources/epubs/` (currently Lacocque, Menn).

| field | type | required | notes |
|---|---|---|---|
| `kind` | string | required | Literal `"external-epub"`. |
| `filename` | string | required | Path relative to `external-resources/` root, e.g. `"epubs/9781498221689.epub"`. Absolute paths and path traversal are rejected. |
| `spineSection` | string | optional | Human-readable spine-section hint (e.g. `"ch. 7"`). |
| `passageRef` | string | optional | Free-form descriptor (e.g. `"Lacocque on Dan 7:13"`). |

The verifier extracts text from every XHTML chapter, strips HTML tags + the social-DRM
watermark documented in `external-resources/epubs/README.md`, and runs the same
normalize-and-match logic as the Logos path.

#### `kind: "external-ocr"` (WS0c-7 → D-2)

For citations against OCR'd plain-text files in any language under
`external-resources/{language-dir}/`. Generalized from the prior
`external-greek-ocr` kind (D-2, 2026-04-29) so Wave 6 / Wave 7 multilingual
surveys (patristic Latin, Reformation Latin/German, Jewish-reception Hebrew /
Aramaic / Judeo-Arabic) can share a single backend with per-language
pre-processing concentrated in the OCR pipeline rather than at the backend
level.

The citation's `quote.language` field selects the per-language subdirectory:

| `quote.language` | dir | typical sources |
|---|---|---|
| `grc` | `greek/` | Theodoret PG 81 (Migne); future Greek patristic OCR |
| `la` | `latin/` | Migne PL; e-rara/BSB Reformation editions |
| `he` | `hebrew/` | HebrewBooks scans, archive.org, MG facsimiles |
| `arc` | `aramaic/` | Targumic / Talmudic Aramaic from local scans |
| `jrb` | `judeo-arabic/` | Karaite + Geonic Arabic-in-Hebrew-script scans |
| `de` | `german/` | Wittenberg-1545, BSB; future Fraktur scans |
| `fr` | `french/` | reserved; not yet populated |

The verifier (`tools/citations.py:_load_ocr_text`) requires the citation's
`backend.filename` to begin with the language-dir prefix matching
`quote.language`, e.g. a `quote.language == "grc"` citation must have
`filename` starting with `greek/`. Mismatches return `resource-unreadable`.

| field | type | required | notes |
|---|---|---|---|
| `kind` | string | required | Literal `"external-ocr"`. |
| `filename` | string | required | Path relative to `external-resources/`, e.g. `"greek/theodoret-pg81-dan7.txt"`. First path segment must match the language-dir for `quote.language`. |
| `tlgCanon` | string | optional | TLG canon work id (e.g. `"4089.028"` for Theodoret on Daniel). |
| `mignePgVolume` | integer | optional | Migne PG/PL volume number. |
| `migneColumn` | integer | optional | Migne column anchor. |
| `passageRef` | string | optional | Free-form (e.g. `"Theodoret on Dan 7:9"`). |

`external-ocr` citations MUST carry a non-null `quote` whose `quote.language`
is in the table above; the validator rejects the citation otherwise.

#### `kind: "external-pdf"` (WS0c-7)

For citations against PDFs in `external-resources/pdfs/` (currently the Hippolytus
*On Christ and Antichrist* + *On the End of the World* anthology). Verifier shells out
to `pdftotext -layout` (Poppler) for text extraction.

| field | type | required | notes |
|---|---|---|---|
| `kind` | string | required | Literal `"external-pdf"`. |
| `filename` | string | required | Path rel to `external-resources/`, e.g. `"pdfs/Hippolytus-EndTimes.pdf"`. |
| `page` | integer | optional | Print-page anchor when known. |
| `passageRef` | string | optional | Free-form. |

#### `kind: "external-sefaria"` (WS0c-expansion)

For citations against verse text fetched from the [Sefaria](https://www.sefaria.org)
REST API. Used by Wave 6 medieval-Jewish reception surveys (Rashi, Ibn Ezra,
Joseph ibn Yahya, Malbim, Steinsaltz) and any future free-online Hebrew/English
text whose canonical edition lives on Sefaria.

| field | type | required | notes |
|---|---|---|---|
| `kind` | string | required | Literal `"external-sefaria"`. |
| `resourceUrl` | string | required | Full Sefaria text-API URL, e.g. `"https://www.sefaria.org/api/texts/Rashi_on_Daniel.7.13"`. The trailing `Work.chapter.verse` form is what the verifier fetches and caches. |
| `language` | string | required | One of `"he"` or `"en"`. Selects which field of the Sefaria response (`he` or `text`) is the canonical text for the citation. Sefaria entries may have one or both. |
| `verseRef` | string | required | Human-readable reference, e.g. `"Daniel 7:13"`. Frontend-only; the verifier does not parse it. |
| `commentator` | string | optional | Display name (e.g. `"Rashi"`, `"Ibn Ezra"`). |

The verifier (`tools/citations.py:_load_sefaria_text`) fetches the API URL
(disk-cached under `external-resources/sefaria-cache/`), pulls the array named
by `language`, joins segments with newlines, strips inline HTML tags (Sefaria
wraps lemmata in `<b>` and similar), and NFC-normalizes — Hebrew niqqud and
cantillation marks differ between NFC and NFD forms, so quote and source must
be normalized to the same form before matching.

Forbidden on `external-sefaria` backends: `resourceId`, `logosArticleNum`,
`nativeSectionId`, and `filename`.

For all non-`logos` kinds, the validator forbids the Logos-only fields
(`resourceId`, `logosArticleNum`, `nativeSectionId`) on the same backend.

### `frontend` (human anchor — required except as noted)

| field | type | source | notes |
|---|---|---|---|
| `author` | string | resource metadata / research notes | Display name. E.g., `Beeke & Smalley`, `Collins`, `Walvoord`. |
| `title` | string | resource metadata / research notes | Short title plus volume/ed. if applicable. |
| `section` | string \| null | derived | `§{nativeSectionId} — {heading}` when heading is known. Fall back to `§{nativeSectionId}` alone. |
| `page` | integer \| null | `get_article_meta(...).pageStart` | Primary printed page. Null when the resource has no embedded milestone index, or the article's offsets don't overlap a page milestone. **Do not fabricate a page number.** |
| `pageEnd` | integer \| null | `get_article_meta(...).pageEnd` | Only present when the article spans multiple printed pages and `pageEnd > page`. Omit (or null) otherwise. |
| `citationString` | string | derived | Pre-rendered scholarly citation. Pattern below. |

### `quote` (the verifiable substance)

| field | type | source | notes |
|---|---|---|---|
| `text` | string | verbatim article text | The exact quoted fragment, UTF-8. Prefer 40+ chars for robust matching. Verification normalizes whitespace to single spaces and matches case-insensitively (so sentence-initial capitalization drift still verifies). Preserve punctuation and diacritics exactly. |
| `sha256` | string (64-hex lowercase) | derived | `sha256(text.encode("utf-8")).hexdigest()`. Tamper-evidence: future verifier runs confirm the stored `text` hasn't drifted. |
| `language` | string | author / `build_citation` default | ISO 639-1/-2/-3 code of the quote's original language. Defaults to `"en"` when `build_citation` is given an English source and no explicit `language=` kwarg. **Required** when `backend.kind == "external-ocr"`. Accepted: `en`, `la`, `grc`, `he`, `arc`, `jrb`, `de`, `fr`. |

`quote` may be `null`, but only when paired with a `supportStatus` other than `directly-quoted`.

### `translations` (optional, D-2)

When the source's `quote.text` is in a non-English language, an optional
`translations[]` array sibling to `quote` carries derivative
modern-English (or other-target-language) renderings with provenance.
Translations are **not** verified against the source by `verify_citation` —
only `quote.text` is the verifier's anchor; translations are
human/LLM-produced editorial artifacts.

```json
{
  "quote": {
    "text": "θηρίον τὴν Ῥωμαϊχὴν χαλεῖ βασιλείαν",
    "sha256": "3940...",
    "language": "grc"
  },
  "translations": [
    {
      "language": "en",
      "text": "[the prophet] calls the Roman empire a beast",
      "translator": "anthropic:claude-opus-4-7",
      "translatedAt": "2026-04-29",
      "method": "llm",
      "register": "modern-faithful"
    }
  ]
}
```

| field | type | required | notes |
|---|---|---|---|
| `language` | string | required | ISO code of the translation's target language. Same accepted set as `quote.language`. |
| `text` | string | required | The translation. |
| `translator` | string | required | When `method == "llm"`, must be `"<provider>:<model>"` format (e.g., `"anthropic:claude-opus-4-7"`). When `method == "human-published"`, the translator's name + short-cite (e.g., `"Salmond, ANF 5"`). When `method == "human-volunteer"`, the volunteer's name. |
| `translatedAt` | string | required | ISO date `YYYY-MM-DD`. |
| `method` | string | required | One of `"llm"`, `"human-published"`, `"human-volunteer"`. |
| `register` | string | required | One of `"modern-faithful"` (neither wooden-literal nor paraphrastic; preferred for LLM survey-time translations), `"wooden-literal"` (preserves source-language word-order at the cost of fluency), `"paraphrastic"` (sense-for-sense, looser). |

Translations are **derivative** and explicitly not subject to verification
against the source — `quote.text` remains the verifier anchor. The site
renders the translation alongside the original and discloses the
translator/method/register so readers can judge fidelity.

### `supportStatus` (required) — the evidential posture

Every citation carries one of four labels. The label tells consumers (and the WS0.5-6 audit) what
kind of scrutiny each citation deserves; "verified quote exists" is *not* the same as "claim is
warranted."

| value | meaning | requires |
|---|---|---|
| `directly-quoted` | The quote is verbatim and the rationale's relevant sub-claim is pinned to that quote. | non-null `quote.text`; quote must verify against the article. |
| `paraphrase-anchored` | The cited article supports the claim, but the cited fragment is a representative paraphrase rather than a verbatim quote of the exact wording. | `quote` may be null. The article must still address the claim. |
| `summary-inference` | The claim summarizes a position spanning multiple articles, sections, or implicit logic; this single citation is one anchor, not a proof. | `quote` may be null. The author should add a `notes` paragraph in the rationale explaining what the inference draws on. |
| `uncited-gap` | The position is acknowledged (often `commitment: tentative`) but no supporting quote or article was found in the surveyed material. Honest "I tried, nothing was there." | `quote: null`. Use sparingly — these are landmines that need follow-up reading. |

The default produced by `tools/citations.build_citation` is `directly-quoted` when a `quote_text`
is supplied, `uncited-gap` otherwise. Override with the `support_status=` keyword argument when
the cite is a paraphrase or summary inference.

The validator (`tools/validate_scholar.py`) enforces:

- `supportStatus ∈ {directly-quoted, paraphrase-anchored, summary-inference, uncited-gap}`.
- `directly-quoted` requires a non-null `quote.text`.
- Otherwise `quote` may be null; structural fields (backend/frontend) still required.

## Scholar-file passage coverage (WS0c-8)

Each scholar JSON now carries a top-level `passageCoverage[]` array — the list of biblical
verse-blocks the surveyed material engages substantively. This makes per-passage coverage a
first-class diagnostic: the validator + a small reporting tool can answer "who covers
Dan 7:9–12?" without re-reading every rationale.

```json
{
  "scholarId": "...",
  "passageCoverage": [
    "Dan 7:1-6",
    "Dan 7:7-8",
    "Dan 7:9-12",
    "Dan 7:13-14",
    "Dan 7:23-27",
    "Dan 9:24-27",
    "Rev 13"
  ]
}
```

### Vocabulary

The validator enforces a controlled vocabulary. For the Daniel 7 pilot, the locked
verse-blocks are:

| value | passage |
|---|---|
| `Dan 7:1-6` | first three beasts (lion / bear / leopard) |
| `Dan 7:7-8` | fourth beast + little horn |
| `Dan 7:9-12` | Ancient of Days, court scene, judgment |
| `Dan 7:13-14` | Son of Man, kingdom transfer |
| `Dan 7:15-18` | Daniel's distress + interpreter, saints receive kingdom |
| `Dan 7:19-22` | fourth-beast detail, little horn waging war on saints |
| `Dan 7:23-27` | full angelic interpretation |

Adjacent passages a Daniel 7 site reasonably cross-references (also accepted):

| value | passage |
|---|---|
| `Dan 2:31-45` | Nebuchadnezzar's statue / Four Kingdoms parallel |
| `Dan 8:1-27` | ram and goat |
| `Dan 9:1-19` | Daniel's prayer of confession |
| `Dan 9:20-27` | seventy weeks |
| `Dan 10:1-21` | mourning + angelic vision on the Tigris |
| `Dan 11:1-45` | the king of the north |
| `Dan 12:1-13` | resurrection + final visions |
| `Rev 1` | Christ as one like a son of man |
| `Rev 13` | beast from the sea + beast from the land |
| `Rev 17` | seven heads, seven hills |
| `Rev 20` | thousand years |
| `Matt 24` | Olivet Discourse (Dan 9:27 reference) |
| `Mark 13` | Olivet Discourse (Markan parallel) |
| `1 En 37-71` | Book of Parables (Second Temple Son of Man) |

Future topic sites can extend the vocabulary by appending entries; the validator reads it from
`tools/validate_scholar.py:PASSAGE_COVERAGE_VOCAB`.

`passageCoverage` is optional today (legacy files predate it); strict-mode validation will warn
but not fail when the field is absent. After WS0c-8 back-population the field is required for new
scholars.

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
