# Anthology-Shape Schema Variant — Design Document

> **SUPERSEDED 2026-04-29.** This design was produced before the PM-Bryan
> dialogue that pivoted Wave 7 from anthology-extract surveys (ACCS / RCS) to
> full-text per-voice surveys sourced from public-domain online repositories
> in original language (Latin / Greek / German / Hebrew / Aramaic /
> Judeo-Arabic). See `docs/research/2026-04-28-patristic-reformation-fulltext-audit.md`
> for the alternative path that was adopted, and the existing `external-ocr`
> backend for the implementation it landed in. Kept on disk as documented
> reasoning of the considered-and-rejected design — DO NOT use as a planning
> input for current work.

**Status:** SUPERSEDED — historical record only. PM ratification was never
completed; the full-text-per-voice path was chosen instead. See §5 for the
codex adversarial review (PASS_WITH_CONDITIONS, 14 findings) that contributed
to the pivot decision.

**Scope.** This document designs how the scholar-JSON corpus accommodates two
in-library reception anthologies needed by Wave 7 of the WS0.6 sufficiency map:

- ACCS Daniel — `LLS:ACCSREVOT13` (Old Testament XIII: Ezekiel, Daniel) —
  4,096 articles in the Logos build.
- RCS Daniel — `LLS:REFORMCOMMOT12` (Reformation Commentary on Scripture,
  Ezekiel/Daniel volume) — 1,520 articles in the Logos build.

Both volumes are confirmed in-library as of 2026-04-28 (sqlite3 against
`Data/e3txalek.5iq/LibraryCatalog/catalog.db`).

---

## 1. Problem statement

The current scholar-JSON schema (`docs/schema/citation-schema.md`) and validator
(`tools/validate_scholar.py`) assume one JSON file = one author engaging the
biblical text in their own voice. The envelope encodes that assumption:

```
{
  "scholarId":      "<one author>",
  "authorDisplay":  "<one author>",
  "workDisplay":    "<one work>",
  "resourceId":     "LLS:<one resource>",
  "traditionTag":   "<one tradition cluster>",
  "commitmentProfile": { strong/moderate/tentative arrays — one author's posture },
  "positions":      [ axis assignments — one author's ]
}
```

A patristic anthology (ACCS) or a Reformation anthology (RCS) breaks every
clause of that assumption simultaneously. ACCS Daniel embeds extracts from
**at least eight distinct primary voices** in the Daniel-7 pericope alone
(Hippolytus, Theodoret of Cyr, Augustine, Origen, Chrysostom, Cyril of
Alexandria, Cyril of Jerusalem, Gregory the Great), and many more across the
volume. RCS Daniel embeds extracts from a different set of primary voices
(Bullinger, Vermigli, Œcolampadius, Lambert, Brenz, Pellican, Melanchthon,
Calvin, Gerhard, and others). The anthology has one resource and one editor;
its theological content is many voices.

### Concrete example — ACCS Daniel article `DAN.7.5.1`

Article `DAN.7.5.1` (`logosArticleNum = 3230` in the Logos build) is a single
ACCS sub-article. Its body is a Theodoret-of-Cyr extract titled "Daniel's Love
of God," sourced from Theodoret's *Commentary on Daniel* 2.49. If we treat
this citation under the current schema we have three bad options:

1. **One ACCS scholar JSON `accs-daniel.json` with `authorDisplay: "Various"`
   and `traditionTag: "patristic-anthology"`.** Misrepresents the corpus.
   Theodoret has his own theological commitments; flattening eight voices into
   "Various" destroys the per-tradition-cluster diagnostic that drives M2/M8
   sufficiency scoring. The site's editorial charter (WS2) cannot honestly
   render "the patristic-Latin tradition says X" if Latin and Greek voices are
   stacked under one editor's banner.

2. **Eight separate scholar JSONs (`accs-hippolytus-daniel.json`,
   `accs-theodoret-daniel.json`, …) each with the same
   `resourceId: LLS:ACCSREVOT13` and `resourceFile: ACCSREVOT13.logos4`.**
   The validator currently allows this — `resourceId` is per-scholar, not
   unique-per-file. But it is not currently designed-for; the schema doc never
   states that a resource may anchor multiple scholars. Without an explicit
   contract, downstream consumers (citation-density tooling, dossier-coverage
   diagnostics) may assume scholarId-resourceId is 1:1 and miscount.

3. **Add Theodoret's ACCS extracts as additional citations on the existing
   `theodoret-pg81-daniel.json` (or its eventual successor) under
   `backend.resourceId: LLS:ACCSREVOT13`.** Cross-corpus accumulation of one
   author's voice. Confuses provenance: the ACCS extract uses the editor's
   chosen translation (often *Library of the Fathers* or a fresh translation),
   not the PG 81 Greek that the Theodoret JSON anchors to. The two are not
   substitutable; combining them obscures translation-history.

### Why the current schema is *insufficient* (not merely awkward)

- **Tradition-cluster scoring (M2/M8).** Mini-dossier sufficiency assessment
  in §4 of the WS0.6 map counts JSON-backed voices per tradition cluster. An
  ACCS-monolith JSON contributes one count to "patristic-anthology" — a
  cluster the project does not currently track and that combines two
  separately-meaningful clusters (patristic-Greek and patristic-Latin).

- **Cross-corpus query patterns.** Visualizations (WS1) and dossier text
  (WS3) need queries like *"every Hippolytus citation across the corpus,
  whether from his ANF 5 fragments or from ACCS extracts"*. A monolith JSON
  buries Hippolytus in `Various`; a per-extract scholar JSON surfaces him.

- **Commitment-profile coherence.** `commitmentProfile.strong` documents one
  author's load-bearing positions. There is no honest way to state "ACCS
  strongly holds X" — ACCS is an editorial product, not a theologian.

- **Tradition tag.** A single `traditionTag` per JSON cannot represent a
  Greek-and-Latin patristic anthology accurately.

The schema does not break loudly — the validator will accept option 1, option
2, or option 3 today. But each option is a different lie. The variant must
make one of them officially supported and, ideally, make the others fail
loud.

### Logos backend per resource — observed shape

For accuracy, both anthologies use Logos's standard logos-kind backend, with
no need for a new backend `kind`. Article shapes differ:

- **ACCS:** sub-article-per-extract. `DAN.7.5.1` holds exactly one Theodoret
  extract; `DAN.7.5.2` (if present) would hold the next-author's extract on
  the same verse. `nativeSectionId` is unique-per-extract in the Daniel-7
  pericope sample we read. `logosArticleNum` is unique-per-extract by
  consequence.

- **RCS:** *multiple extracts per sub-article*. `BK2.3.1` (Daniel 3:26–27,
  `logosArticleNum = 1403`) holds a Gerhard extract titled "Cross and
  Tribulation," then a Calvin extract titled "The Guardian and Protector of
  Life," then a Bullinger extract titled "The Omnipotence of God" —
  sequentially, in one article body. The `nativeSectionId` is *not*
  extract-unique. The verifier's substring match against `quote.text` *is* the
  per-extract anchor; multiple citations from one RCS sub-article will share
  the same `backend.logosArticleNum` and `backend.nativeSectionId` and
  disambiguate only by `quote.text`.

This RCS shape — N extracts per Logos article, distinguished only by quote
substring — is a real constraint on the variant. Any design that assumes one
extract = one nativeSectionId will misfit RCS.

---

## 2. Design options

Three options follow. Each is evaluated against eight criteria: (a) schema
additions, (b) validator rule changes, (c) verifier (`citations.py`) changes,
(d) dossier-coverage tracking, (e) citation-density accounting, (f) the
"all citations of voice X" query pattern, (g) RCS multi-extract-per-article
fit, (h) migration path.

### Option A — anthology JSON with `extracts[]`

**Shape.** One JSON per anthology resource:
`docs/research/scholars/accs-ot13-daniel.json` and
`docs/research/scholars/rcs-ot12-daniel.json`. Top-level fields drop the
single-author assumption:

```jsonc
{
  "anthologyId":     "accs-ot13-daniel",       // replaces scholarId
  "anthologyTitle":  "Old Testament XIII: Ezekiel, Daniel (ACCS)",
  "anthologyEditor": "Kenneth Stevenson; Michael Glerup",
  "resourceId":      "LLS:ACCSREVOT13",
  "resourceFile":    "ACCSREVOT13.logos4",
  "passageCoverage": ["Dan 7:1-6", "Dan 7:7-8", "Dan 7:9-12", ...],
  "extracts": [
    {
      "extractId":      "accs-ot13-daniel--theodoret-cyr",
      "attributedAuthor": "Theodoret of Cyrus",
      "attributedWork":   "Commentary on Daniel",
      "traditionTag":   "patristic-greek-antiochene",
      "commitmentProfile": { "strong": [...], "moderate": [...], "tentative": [...] },
      "positions":      [ {axis,axisName,position,commitment,rationale,citations} ]
    },
    { "extractId": "accs-ot13-daniel--hippolytus", "attributedAuthor": "Hippolytus", ... },
    ...
  ]
}
```

| Criterion | Cost / behavior |
|---|---|
| Schema additions | New top-level shape `{anthologyId, anthologyTitle, anthologyEditor, extracts[]}`. `extracts[]` element schema mirrors a *trimmed* scholar envelope. Existing scholar envelope continues to apply for non-anthology files. |
| Validator changes | Substantial. Detect anthology shape (presence of `extracts[]` instead of `positions[]`); validate each `extracts[i]` recursively; enforce per-extract `traditionTag` from the existing tradition vocabulary; enforce `extractId` kebab pattern with anthology prefix. ~80–120 LOC added. |
| Verifier changes | None. Each citation inside an extract is still an ordinary citation with `backend.kind: "logos"`. `verify_citation` unchanged. |
| Dossier-coverage | New traversal: `for s in scholars: yield s` becomes `for s in scholars: if "extracts" in s: yield from s["extracts"]; else yield s`. Most reporting tools must be touched. |
| Citation-density | Counted per extract, summed for the file. New denominator: extract count, not scholar count. Cross-corpus density math changes. |
| Query "all Hippolytus" | Two surfaces: top-level `authorDisplay: Hippolytus` files OR `extracts[].attributedAuthor: Hippolytus` within anthology files. Aggregation tool must merge both. |
| RCS multi-extract-per-article | Fits — citations within one extract may share `nativeSectionId`; nothing in the shape forbids it. |
| Migration | New shape from day one for ACCS + RCS. No existing files migrate. |

### Option B — per-extract scholar JSONs sharing `resourceId`

**Shape.** Multiple ordinary scholar JSONs, one per (anthology, primary voice)
pair, all referencing the same anthology `resourceId`. Names use an
anthology-prefix convention to avoid collision with the primary voice's other
JSONs:

- `docs/research/scholars/accs-hippolytus-daniel.json`
- `docs/research/scholars/accs-theodoret-daniel.json`
- `docs/research/scholars/accs-augustine-daniel.json`
- `docs/research/scholars/rcs-bullinger-daniel.json`
- … (one per primary voice with a Daniel-7-relevant extract)

Each file uses the existing scholar envelope unchanged:

```jsonc
{
  "scholarId":     "accs-theodoret-daniel",
  "authorDisplay": "Theodoret of Cyrus (ACCS extract)",
  "workDisplay":   "Commentary on Daniel (extracted in ACCS Daniel)",
  "resourceId":    "LLS:ACCSREVOT13",
  "resourceFile":  "ACCSREVOT13.logos4",
  "traditionTag":  "patristic-greek-antiochene",
  "commitmentProfile": { ... },
  "positions": [
    { "axis": "K", ..., "citations": [
      {
        "backend": { "resourceId": "LLS:ACCSREVOT13",
                     "logosArticleNum": 3230,
                     "nativeSectionId": "DAN.7.5.1" },
        "frontend": { "author": "Theodoret of Cyrus", ... },
        "quote": { "text": "...", "sha256": "..." },
        "supportStatus": "directly-quoted"
      }
    ]}
  ]
}
```

| Criterion | Cost / behavior |
|---|---|
| Schema additions | None to the citation/scholar envelope itself. Possibly: a new optional top-level field `anthologySource` on each per-extract JSON (e.g., `"anthologySource": {"resourceId": "LLS:ACCSREVOT13", "extractTranslator": "ACCS editorial"}`) for provenance, used by reporting tools but not strictly required by the validator. |
| Validator changes | Minimal. Document that `resourceId` is per-scholar, not unique-per-file; loosen no rules; optionally add a soft check that warns when two scholar files share the same `resourceId` *and* the same `authorDisplay` (a likely collision bug). |
| Verifier changes | None. |
| Dossier-coverage | Existing tools work unchanged. The ACCS Theodoret extract counts as one JSON-backed voice for the Antiochene cluster (a contribution to M8). |
| Citation-density | Counted per file, summed across the corpus, exactly as today. Density on each anthology-extract file is necessarily low (extracts are short — often 1–3 paragraphs); reporting must distinguish "thin extract files" from "thin survey files" so density-floor rules don't fire. |
| Query "all Hippolytus" | Single surface: `grep -l '"authorDisplay": "Hippolytus' docs/research/scholars/*.json`, or programmatic equivalent. Trivial. |
| RCS multi-extract-per-article | Fits with no special handling — multiple citations on one extract's positions[] all share the same backend.logosArticleNum and disambiguate via quote.text. |
| Migration | None. New files conform to existing schema. |

### Option C — hybrid: per-extract scholar JSONs + thin anthology index

**Shape.** Option B's per-extract scholar JSONs *plus* a single, non-validated
markdown index per anthology at:

- `docs/research/anthologies/accs-ot13-daniel.md`
- `docs/research/anthologies/rcs-ot12-daniel.md`

Each index documents the editor, the table of extract scholar JSONs, the
translation policy of the anthology, and the relationship of each extract to
the corpus's other voices for the same primary author (e.g., "ACCS
Hippolytus extracts use the *Library of the Fathers* translation; the
in-corpus `hippolytus-anf5-daniel.json` uses the ANF 5 translation; the two
are distinct text-witnesses to the same source").

The index is informational, not consumed by validators or scoring tools.

| Criterion | Cost / behavior |
|---|---|
| Schema additions | Same as Option B (none to envelope; optional `anthologySource` provenance field). |
| Validator changes | Same as Option B (minimal). |
| Verifier changes | None. |
| Dossier-coverage | Same as Option B. |
| Citation-density | Same as Option B. |
| Query "all Hippolytus" | Same as Option B. |
| RCS multi-extract-per-article | Same as Option B. |
| Migration | None. Anthology index files are new but not validator-bearing. |

### Side-by-side summary

| | Option A | Option B | Option C |
|---|---|---|---|
| New top-level shape | yes (`extracts[]`) | no | no |
| Validator LOC delta | ~80–120 | ~10 (doc + soft warn) | ~10 (doc + soft warn) |
| Reporting tool churn | every traversal updated | none | none (index ignored) |
| Per-extract `traditionTag` | yes (per-extract) | yes (per-file) | yes (per-file) |
| One file = one resource | yes | no | no |
| One file = one author voice | no | yes | yes |
| Provenance metadata first-class | yes (anthology-level) | optional (`anthologySource`) | yes (in markdown index) |
| Files added per anthology | 1 | 7–10 | 7–10 + 1 markdown |
| Honest representation of multi-voice | yes | yes | yes |

---

## 3. Recommended option + rationale

**Recommended: Option C** (per-extract scholar JSONs sharing `resourceId`, plus
a thin non-validated markdown anthology index per anthology).

### Why C over A

The single-author scholar envelope is a *load-bearing* invariant of the
existing corpus — it carries `commitmentProfile`, per-axis `positions[]`,
single `traditionTag`, single `authorDisplay`. Every reporting tool, every
sufficiency-map calculation, and every codex audit run since WS0.5 has
assumed one file = one voice. Option A pushes that invariant down one level
into `extracts[]` and forces every consumer to learn a second traversal
shape. The cost is concentrated in `validate_scholar.py` (~100 LOC),
`sweep_citations.py`, dossier-coverage reporting, and any future tool. The
*benefit* is exactly one thing: each anthology becomes one file. That benefit
is editorial cosmetics — it does not improve any verification, scoring, or
query that the project actually performs.

Option C accepts that an anthology is a fact about the *resource* (the Logos
book) but not a fact the *scholar envelope* needs to model. The schema's job
is to anchor each *theological commitment* to *its actual primary voice*.
ACCS-extracted-Theodoret and PG-81-Theodoret are two different
text-witnesses to the same theological voice; they belong in two different
JSONs joined by the shared `authorDisplay`. The anthology's editorial unity —
who's in it, what translation policy was used — is real but informational,
and lives well in a markdown index.

### Why C over B

C = B + a markdown index. The marginal cost is one short markdown file per
anthology. The marginal benefit is real: anyone reading
`docs/research/scholars/accs-theodoret-daniel.json` cold needs to know it is
an ACCS-extract file, not a full Theodoret survey, and that there is a
companion `theodoret-pg81-daniel.json` with a different translation. The
markdown index makes that relationship discoverable without forcing it into
the validator-bearing schema. Without the index, the relationship is
implicit-by-naming-convention only, and naming conventions rot. The index is
the cheapest reliable way to keep the relationships explicit.

### Defending C against likely objections

- *"Option C duplicates the same `backend.resourceId` across many files —
  isn't that a smell?"* No. `resourceId` is a *machine handle*, not an
  identity claim. Multiple authors share LLS:6.50.5 (ANF 5) today across
  separate scholar JSONs (or will, once the Wave 2 patristic JSONs land);
  the existing schema already permits this and the validator does not
  reject it. The smell is no worse than the existing pattern.

- *"Per-extract scholar files will violate density floors."* True if a
  density floor is naively applied. Mitigation: extract scholar JSONs are
  identifiable by an opt-in flag or by anthology-prefix scholarId
  (`accs-*`, `rcs-*`). Reporting tools can branch. See §4.4.

- *"Naming is ad-hoc."* Mitigation: lock the convention in the schema doc —
  `<anthology-prefix>-<author-slug>-<book-or-pericope>.json`, where
  `anthology-prefix ∈ {accs, rcs, ...}`.

- *"What about future anthologies (Ancient Christian Texts, Reformation
  Heritage, etc.)?"* C extends naturally. Each new anthology adds a new
  prefix and a new index file; no schema changes.

### What C explicitly does *not* try to solve

- Reconciliation between an anthology's translation and the same author's
  primary-text JSON. The two coexist. The dossier author (WS3) decides
  whether to cite both, one, or neither for any given claim.

- Cross-anthology de-duplication. If ACCS and RCS both quote the same
  Theodoret passage, both JSONs cite it, and that is fine — they are
  distinct scholarly editorial events.

- Multiple-extract-per-RCS-article disambiguation beyond
  `quote.text`-based substring matching. The verifier's existing match logic
  already disambiguates correctly.

---

## 4. Required schema/code changes (sketch — NO implementation here)

### 4.1 `docs/schema/citation-schema.md` additions

Add a new top-level section, e.g. `## Anthology-extract scholar files`,
documenting:

1. The convention that scholar JSONs may share a `resourceId` when the
   resource is a reception anthology (ACCS, RCS, future).
2. The naming convention: `<anthology-prefix>-<author-slug>-<scope>.json`,
   where prefixes are reserved (`accs`, `rcs`; new prefixes added by PM
   ratification).
3. The optional `anthologySource` provenance object on the scholar envelope:
   ```jsonc
   {
     "anthologySource": {
       "resourceId":        "LLS:ACCSREVOT13",
       "anthologyEditor":   "Kenneth Stevenson; Michael Glerup",
       "translationPolicy": "Library of the Fathers, lightly revised",
       "extractScopeNote":  "two paragraphs on Dan 7:5; one paragraph on Dan 7:13"
     }
   }
   ```
   When present, validator checks the type of each subfield and that
   `anthologySource.resourceId` matches the top-level `resourceId`.
4. A pointer to the per-anthology markdown index at
   `docs/research/anthologies/<anthology-prefix>-<volume-tag>.md`.
5. An explicit note about RCS multi-extract-per-`nativeSectionId`: that
   multiple citations may legitimately share the same backend article number
   and section id, distinguished only by `quote.text`. The verifier already
   handles this; no validator change needed.

### 4.2 `tools/validate_scholar.py` rule changes

- **No structural relaxations.** The existing scholar envelope continues to
  apply unchanged.
- **New optional field check.** If `anthologySource` is present, validate
  it's a dict, validate each subfield's type, and require its `resourceId`
  (if present) to equal the top-level `resourceId`.
- **Soft warning (stretch goal, not blocking).** If two files in the input
  set share both `authorDisplay` *and* `resourceId`, emit a warning to
  stderr — this is almost always a copy-paste bug, except for the rare case
  of two genuinely-distinct extract sets within one anthology (which is
  better expressed as a single merged file).
- **Naming-convention check (stretch goal).** Optional `--strict-naming`
  flag warning when an `accs-*` or `rcs-*` filename's top-level
  `resourceId` does not match the anthology-prefix-implied resource. Off by
  default to avoid flagging legacy files.

Estimated diff: ~30 LOC for the optional check + docstring edits; a further
~30 LOC if both stretch goals are accepted. No rule that currently passes
will newly fail.

### 4.3 `tools/citations.py` changes

**None required.** The verifier's logos-kind path already handles every
citation an anthology JSON would emit. The substring match against
`quote.text` is the per-extract disambiguator for RCS.

A future convenience: a helper `build_citation_from_anthology(...)` that
takes anthology resource file + article num + extract-author-tag + verbatim
quote + axis. Out of scope for this design — would simplify subagent
ergonomics, not change the schema.

### 4.4 Survey briefing template variant — `_SURVEY_BRIEFING_ANTHOLOGY.md`

A second briefing alongside `_SURVEY_BRIEFING.md` for anthology subagents.
The briefing differs from the standard one in five places:

1. **Output deliverable.** The subagent produces *N* scholar JSONs per
   anthology (one per primary voice with Daniel-7-relevant extract content),
   not one. The subagent must enumerate primary voices first, then write a
   per-voice JSON for each. Empty primary voices (an extract too short to
   support any axis) are documented in the anthology index but produce no
   scholar JSON.

2. **Honest extract scope.** Anthologies are short. A typical ACCS extract is
   1–3 paragraphs; a typical RCS extract similar. Per-extract scholar JSONs
   should expect:
   - 1–3 axes covered (rarely more);
   - `commitmentProfile.strong` with one or two entries, `moderate` and
     `tentative` likely empty;
   - 2–6 citations total;
   - explicit `uncertainties` enumerating the axes the extract does *not*
     speak to (e.g., "Theodoret-via-ACCS extract is silent on Axis A
     because the editorial selection bypasses Theodoret's prologue").

3. **Cross-corpus consistency check.** When the same primary voice has
   another scholar JSON in the corpus (e.g., `theodoret-pg81-daniel.json`
   exists when surveying ACCS Theodoret), the subagent must:
   - load the existing JSON;
   - confirm the new extract's `commitmentProfile` does not *contradict*
     the existing JSON's commitments (it may be silent on them; it may not
     reverse them without a recorded `distinctiveMoves` note explaining
     why);
   - cross-reference via `distinctiveMoves` or `uncertainties` if the two
     translation choices yield meaningfully different exegetical emphases.

4. **Anthology index.** The subagent writes (or appends to) the markdown
   anthology index file at
   `docs/research/anthologies/<anthology-prefix>-<volume-tag>.md`,
   listing each extract scholar JSON it produced and any voices it skipped.
   The index is the human entry point to "what's in this anthology."

5. **Translation provenance.** The subagent records the anthology's
   translation policy (per-volume metadata, usually in the volume preface)
   in the `anthologySource.translationPolicy` field of every per-extract
   JSON it produces. This is the field that disambiguates ACCS-Theodoret
   from PG-81-Theodoret for downstream readers.

The standard briefing's verification checklist applies unchanged at the
per-citation level: every `quote.text` must verify against the named ACCS or
RCS article via `verify_citation`. The 95%-verified bar applies *per
per-extract scholar JSON*, not per anthology.

### 4.5 Implementation order (for the future implementation session)

This is sketch only — the implementing session decides the actual sequence.

1. Add the §"Anthology-extract scholar files" section to
   `docs/schema/citation-schema.md`. Get PM ratification on the naming
   convention and reserved prefixes.
2. Add the optional `anthologySource` validator check.
3. Write `_SURVEY_BRIEFING_ANTHOLOGY.md`.
4. Dispatch ACCS Daniel survey subagent (Wave 7.1). Land per-voice JSONs.
5. Dispatch RCS Daniel survey subagent (Wave 7.2). Land per-voice JSONs.
6. Update the dossier-coverage report and sweep tooling if any per-cluster
   counting needs anthology-aware filtering. Likely none — but verify.

---

## 5. Codex adversarial review

Codex CLI run completed 2026-04-28 against the §1–4 draft above plus the
current `citation-schema.md`, `validate_scholar.py`, `citations.py`,
`_SURVEY_BRIEFING.md`, two scholar JSONs (Jerome, 1 Enoch Parables), and the
WS0.6 sufficiency map §8/§9. Reasoning effort: high. Run log preserved at
`/tmp/anthology-codex/log.txt` (~450 KB; not committed). Verdict and findings
below are captured verbatim. Per the design-session brief, suggestions are
**not applied** during this session; the PM ratifies them in a follow-up.

<!-- CODEX_REVIEW_BEGIN -->
ANTHOLOGY-VARIANT CODEX REVIEW — 2026-04-28

## Verdict
PASS_WITH_CONDITIONS

## Findings

### Finding N1 — Option C is defensible, but §3 overstates the case
- Severity: major
- Locus: `docs/schema/anthology-schema-variant.md` §3, especially lines 279-312
- Concern: The recommendation is directionally defensible: preserving the existing scholar envelope avoids a second traversal shape, and current `tools/sweep_citations.py` already sweeps ordinary files via `positions[]` and `crossBookReadings[]` at lines 84-107. The weak point is the claim that Option A’s benefit is “exactly one thing” and “editorial cosmetics” at lines 287-291. That dismisses real operational benefits: atomic anthology completeness, enforced extract inventory, centralized provenance, and preventing orphan extract files. A hostile reader will say §3 counts Option A’s implementation costs but treats Option C’s coordination costs as invisible human discipline.
- Recommendation: Ratification should require §3 to defend Option C against orphaning, partial anthology completion, optional provenance, and scoring inflation, not only against validator churn.

### Finding N2 — The RCS concrete example appears metadata-inconsistent
- Severity: major
- Locus: `docs/schema/anthology-schema-variant.md` lines 115-123
- Concern: The draft claims RCS `BK2.3.1`, `logosArticleNum = 1403`, is Daniel 3:26-27 and contains Gerhard, Calvin, and Bullinger extracts. A local `get_article_meta("REFORMCOMMOT12.logos4", 1403)` run returns `nativeSectionId: "BK2.3.1"` but heading `1:8–13 Defilement by Food`; reading the article begins with Daniel’s refusal of royal food and Heinrich Bullinger. That does not match the stated Daniel 3 example.
- Recommendation: Design issue, not a code recommendation. The observed RCS shape may still be real, but this specific example should not carry schema-ratification weight until the article number/section/content claim is rechecked.

### Finding N3 — `quote.text` does not disambiguate RCS extracts safely
- Severity: major
- Locus: `docs/schema/anthology-schema-variant.md` lines 346-348; `tools/citations.py` lines 225-233 and 570-577
- Concern: The verifier normalizes whitespace, typography, and case, then calls `.find()` and returns the first match span. It does not check uniqueness, author boundaries, heading boundaries, or extract boundaries. If two RCS extracts in the same Logos article both quote “Daniel 7:13,” share boilerplate, or quote the same biblical phrase, verification succeeds against the first occurrence and cannot tell whether the intended author’s extract was cited. `_load_logos_text` also ignores `nativeSectionId` entirely and loads by `resourceId` + `logosArticleNum` only at lines 252-259.
- Recommendation: §3/§4 should not claim current verifier logic “already disambiguates correctly.” At most, it verifies that the substring exists somewhere in the article.

### Finding N4 — `anthologySource` being optional undermines the design
- Severity: major
- Locus: `docs/schema/anthology-schema-variant.md` lines 221, 364-376, 388-390, 533-540
- Concern: The draft relies on `anthologySource` for provenance, display disambiguation, density-floor branching, and `voiceWeight` derivation, but makes it optional. If an anthology extract ships without it, current validation still passes, the index may be the only provenance record, and any later scoring rule “derived from presence of `anthologySource`” will misclassify the file as full voice.
- Recommendation: Ratification should treat this as a design blocker for Option C as written. Optional provenance is inconsistent with the role the field plays elsewhere in the draft.

### Finding N5 — Several hidden envelope invariants are not named
- Severity: major
- Locus: `tools/validate_scholar.py` lines 121-220, 221-257
- Concern: The validator checks `scholarId` format but not cross-file uniqueness or filename equality; it checks top-level `resourceId` type but not equality with each citation’s backend `resourceId`; it requires `positions[]` nonempty but allows a position with an empty `citations[]`; it validates `passageCoverage[]` vocabulary but not whether coverage is substantively supported. Option C stresses all of these because many thin files will share one resource and may contain only one or two extract-level claims.
- Recommendation: The design should explicitly state which invariants remain human-audit-only. Otherwise Option C looks more validator-supported than it is.

### Finding N6 — `authorDisplay` is not a stable canonical author key
- Severity: major
- Locus: `docs/schema/anthology-schema-variant.md` lines 296-298, 510-518; current `theodoret-pg81-daniel.json` lines 2-4
- Concern: §3 says ACCS-Theodoret and PG81-Theodoret are joined by shared `authorDisplay`, but the existing Theodoret file uses `"Theodoret"`, while the draft examples use “Theodoret of Cyrus.” Current code does not aggregate by `authorDisplay`; `sweep_citations.py` keys reports by `scholarId` at lines 74-75 and 90-104. So current tools will not collapse them, while future “all Hippolytus” or sufficiency tools might over-collapse full surveys and extracts unless they distinguish author identity from file/source instance.
- Recommendation: Treat `authorDisplay` as display text, not identity, unless the design defines and audits canonical display strings.

### Finding N7 — Naming-convention checks are mostly cosmetic
- Severity: major
- Locus: `docs/schema/anthology-schema-variant.md` lines 324-330, 396-399
- Concern: The proposed `--strict-naming` warning only catches files that already begin with `accs-*` or `rcs-*` but point to the wrong resource. It does not catch the more likely failure: a future subagent names an extract `hippolytus-accs-daniel.json`, `theodoret-acss-daniel.json`, or `hippolytus-daniel-extract.json`, omits `anthologySource`, and thereby bypasses extract-aware density/scoring rules.
- Recommendation: As written, naming cannot be the primary discriminator for anthology behavior.

### Finding N8 — Cross-corpus “contradiction” is undefined
- Severity: major
- Locus: `docs/schema/anthology-schema-variant.md` lines 439-448
- Concern: The briefing requires subagents to confirm that a new extract’s `commitmentProfile` does not “contradict” an existing full-author JSON, but gives no operational definition. A real contradiction may be caused by anthology selection, translation, a different work, a different genre, or an earlier/later phase of the same author. The subagent is being asked to adjudicate historical-theological coherence without a protocol for legitimate divergence.
- Recommendation: Ratification should not depend on this check unless the design states what counts as contradiction and what status a legitimate divergence receives.

### Finding N9 — Sufficiency scoring can double-count one primary voice
- Severity: critical
- Locus: `docs/schema/anthology-schema-variant.md` lines 323-326, 533-540; sufficiency map lines 730-735 and 446-499
- Concern: The scholar-tier rule counts JSON-backed primary voices per cluster. Under Option C, Hippolytus ANF 5 plus ACCS-Hippolytus can become two JSON files and be counted as two voices, even though they are one primary author. §6 proposes “X full + Y extract voices” and `voiceWeight`, but this is only an open PM question, not implemented in §4.5; worse, it depends on optional `anthologySource`.
- Recommendation: This is a blocker for using Option C outputs to upgrade M2/M8 sufficiency claims.

### Finding N10 — Migration claim is mostly true, but author consistency is not
- Severity: minor
- Locus: `docs/schema/anthology-schema-variant.md` lines 256, 471-479; `1-enoch-parables-nickelsburg-vanderkam.json` lines 2-15
- Concern: No existing file needs to be remodeled into an anthology shape. The closest precedent, `1-enoch-parables-nickelsburg-vanderkam.json`, is a joint modern commentary, not many primary voices. Same for other joint-author files like Blaising & Bock, Hartman & Di Lella, and Newsom & Breed. The real migration-adjacent issue is normalization: once ACCS-Theodoret arrives, the existing `theodoret-pg81-daniel.json` may need display/alias consistency even if the filename need not change.
- Recommendation: No concern on structural migration; concern remains on canonical author naming.

### Finding N11 — Subagent ergonomics are under-specified for partial completion
- Severity: major
- Locus: `_SURVEY_BRIEFING.md` lines 8-10, 86-87, 191; anthology draft lines 421-426 and 462-465
- Concern: The existing briefing is built around one subagent producing one JSON. Option C asks one anthology subagent to enumerate voices and produce N JSONs plus an index. The draft correctly says the 95% bar applies per extract JSON, not per anthology, but it does not say what happens when 4 of 8 voices verify and 4 are incomplete. That matters because a partial dispatch can silently create a misleading anthology index or sufficiency upgrade.
- Recommendation: The design needs a partial-completion status protocol before Wave 7 dispatch.

### Finding N12 — PM open questions include real blockers
- Severity: major
- Locus: `docs/schema/anthology-schema-variant.md` lines 496-555
- Concern: Blockers: Q1 reserved prefixes, Q3 `authorDisplay` convention, Q6 density/dossier scoring, Q7 whether to survey duplicate voices. Non-blockers: Q2 translation-policy vocabulary can start as free text, Q4 duplicate warning is quality tooling, Q5 same voice in ACCS and RCS is future-facing for Daniel, Q8 schema lock date is process metadata. The draft presents them all as open questions, but implementation cannot safely proceed on the blocker set.
- Recommendation: Separate “must answer before implementation” from “can ratify later.”

### Finding N13 — no concern: current citation sweep does not collapse by `authorDisplay`
- Severity: minor
- Locus: `tools/sweep_citations.py` lines 74-107
- Concern: Current citation verification uses `scholarId` for report identifiers and walks each file independently. It will not currently merge two files just because both say `authorDisplay: "Hippolytus"`.
- Recommendation: No action for citation-sweep specifically; the risk is future coverage/scoring aggregation.

### Finding N14 — no concern: Option C does not require a new backend kind
- Severity: minor
- Locus: `tools/citations.py` lines 168-243; `docs/schema/anthology-schema-variant.md` lines 405-414
- Concern: Ordinary Logos citations from ACCS/RCS can verify with the existing Logos backend. The concern is not backend support; it is attribution and uniqueness inside multi-extract articles.
- Recommendation: No new backend kind is needed for the basic read/verify path.

## Summary table

| # | Title | Severity | Recommendation summary |
|---|-------|----------|------------------------|
| N1 | Option C overstated | major | Defend coordination/provenance costs, not only validator churn |
| N2 | RCS example inconsistent | major | Recheck article number and evidence |
| N3 | Quote match not disambiguating | major | Stop claiming verifier resolves extract identity |
| N4 | Optional `anthologySource` | major | Treat as blocker if used for scoring/provenance |
| N5 | Hidden invariants | major | State which invariants remain unaudited |
| N6 | `authorDisplay` key risk | major | Do not use display text as canonical identity |
| N7 | Naming rot | major | Prefix warning is insufficient discriminator |
| N8 | Undefined contradiction check | major | Define divergence protocol |
| N9 | Double-counting voices | critical | Resolve before sufficiency upgrades |
| N10 | Migration mostly okay | minor | No remodel, but normalize author identity |
| N11 | Partial subagent output | major | Define partial-completion handling |
| N12 | PM blockers mixed with nice-to-have | major | Split blocker/non-blocker questions |
| N13 | no concern: citation sweep | minor | Current sweep does not collapse by display name |
| N14 | no concern: backend kind | minor | Existing Logos backend is enough for verification |

## Strongest objections the doc does not pre-empt
- 1. Option C creates “file-count theology”: the unit counted by sufficiency tools becomes the JSON file, not the historical voice, so extract proliferation can make the corpus look broader than it is.
- 2. The non-validated markdown index is asked to preserve anthology unity, completeness, and provenance, but no tool enforces that every extract file is indexed or every indexed voice exists.
- 3. The verifier proves only that a string exists in an article; it does not prove the quote belongs to the attributed extract author. For RCS, that is exactly the contested schema boundary.
<!-- CODEX_REVIEW_END -->

### Brief response (not applied — flagged for PM ratification)

The codex critique is substantive. Findings deemed *fundamental to the
recommendation* and requiring PM resolution before any Wave 7 implementation
dispatch:

- **N9 (critical) — double-counting voices.** The recommendation as written
  cannot be used to upgrade M2/M8 sufficiency scoring without a
  voice-weighting rule. PM Q6 (§6) is the locus; the answer needs to land
  before, not after, an anthology survey.
- **N3 (major) — verifier does not prove extract attribution.** §3 paragraph
  on RCS overstated the verifier's role. The verifier proves a quote string
  exists in the article body; per-extract author attribution is a *content
  audit* responsibility (subagent + PM), not a verification responsibility.
  The doc's RCS handling needs a corresponding tightening before
  implementation.
- **N4 (major) — optional `anthologySource` is inconsistent with its role.**
  The field is asked to carry provenance, scoring, and display
  disambiguation. PM should ratify making it required for any file matching
  the anthology-prefix naming convention.
- **N2 (major) — the RCS concrete example is mis-cited.** The doc names
  `BK2.3.1` / `logosArticleNum=1403` for Daniel 3:26–27 with Gerhard +
  Calvin + Bullinger; codex's `get_article_meta` run says that article is
  Daniel 1:8–13. The structural claim (multiple extracts per RCS article)
  is still well-grounded by the live `read_article_text` evidence captured
  during this session, but the named example needs to be re-anchored to
  the article that actually held the three-author body. Recheck before any
  ratification quote of this paragraph.

Findings N1, N5, N6, N7, N8, N11, N12 surface real operational risks the
PM should address either by tightening the design or by accepting the risk
explicitly in `method-and-limits.md`. None of them invalidates the choice
of Option C *over* Options A/B; they sharpen what Option C must include
to actually work.

Findings N10, N13, N14 are confirmed as not blocking.

---

## 6. Open questions for PM

1. **Reserved anthology prefixes.** Lock `accs` and `rcs` as reserved
   filename prefixes for these two anthologies. Any other prefixes
   anticipated (e.g., `act` for Ancient Christian Texts, `rht` for
   Reformation Heritage)? If yes, reserve now; if not, add by PM
   ratification when needed.

2. **`anthologySource.translationPolicy` vocabulary.** Free text or
   controlled vocabulary? Free text is simpler; a controlled vocabulary
   (e.g., `library-of-the-fathers-revised`, `accs-fresh-translation`,
   `rcs-fresh-translation`, `nicene-fathers-revised`) buys grouping queries
   later. Recommend free text for now; revisit if M8 audit demands it.

3. **`authorDisplay` convention for extracts.** Three candidates:
   (a) `"Theodoret of Cyrus"` (clean, but collides with the PG-81
   Theodoret JSON);
   (b) `"Theodoret of Cyrus (ACCS extract)"` (disambiguates loudly, but
   pollutes display in dossier text);
   (c) `"Theodoret of Cyrus"` with a `displayContext` field carrying
   "(ACCS extract)" for tooling that wants the suffix.
   Recommend (a) — ordinary `authorDisplay`, with `anthologySource` as the
   formal disambiguator. The dossier-author chooses the display form.

4. **Soft-warn on duplicate `(authorDisplay, resourceId)`?** Recommend yes
   for the standard scholar envelope (catches copy-paste bugs) and explicit
   exemption for files declaring `anthologySource` (which legitimately
   share `resourceId` with their anthology peers but not their
   `authorDisplay`).

5. **What if the same primary voice appears in *both* ACCS and RCS?** None
   of the Wave-7 voices the sufficiency map names overlap (ACCS is
   patristic, RCS is Reformation), so the question is theoretical for
   Daniel. For future anthologies it is real. Recommend: separate
   `accs-author-*` and `rcs-author-*` files; the markdown anthology indexes
   for each carry pointers to the other.

6. **Citation-density / dossier-coverage scoring.** Should
   anthology-extract JSONs count as full voices for tradition-cluster
   sufficiency, or as half-voices? Recommend: full voices for *cluster
   presence* (M2/M8 voice-count), explicitly flagged as "extract" voices in
   the WS0.6-style sufficiency map so a cluster's sufficiency can be read
   as "X full + Y extract voices." Implementation: a single
   `voiceWeight: "full" | "extract"` derived from presence of
   `anthologySource`.

7. **Anthology survey vs. waiting for primary-voice JSONs.** Wave 1
   already plans `hippolytus-anf5-daniel.json` and `augustine-city-of-god-
   book-20.json`. Both these voices reappear in ACCS. Should Wave 7
   subagents *defer to* those primary-text JSONs and survey only the ACCS
   voices not already represented (Origen, Cyril of Alexandria, Gregory the
   Great)? Recommend: survey *all* voices in the anthology, even
   duplicates, because the editorial selection itself is data — what ACCS
   chose to extract from Hippolytus is a fact about Hippolytus's
   reception, distinct from his own prose.

8. **Schema doc lock date.** This variant changes wording in
   `citation-schema.md`. The schema is currently locked 2026-04-24. PM
   should set a new lock date (e.g., 2026-04-29-anthology-variant) and a
   migration note documenting that pre-variant scholar JSONs remain valid.
