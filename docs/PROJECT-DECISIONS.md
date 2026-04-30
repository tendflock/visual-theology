# Project Decision Log — Visual Theology Pilot

Architectural decisions, with date + rationale + ratifier. Ordered chronologically.
A decision marked `superseded` retains historical value; do not delete it.

---

## 2026-04-23 — Visual-theology pilot scope: Daniel 7 + 3-tier distillation

**Decision:** The pilot scope is Daniel 7 with three primary topics (Four Beasts,
Little Horn, Son of Man) and two fold-in topics (Ancient of Days, Saints), with
each scholar's engagement distilled to three audience tiers (layman, pastor,
scholar).

**Rationale:** Daniel 7 sits at the intersection of OT apocalyptic, Second Temple
reception, and NT Christology, which gives the pilot enough surface area to
exercise every backend (in-library + external) and every cluster (patristic,
medieval Jewish, Reformation, modern critical, Reformed-pastoral) without scope
ballooning beyond a single chapter. The 3-tier distillation forces editorial
discipline: every voice must yield something useful to a layman *and* something
defensible to a scholar, or it gets cut.

**Alternatives considered:**
- Whole-book Daniel pilot — rejected; too much surface area for an MVP.
- Romans 3 as visual-theology pilot — deferred; became a parallel TEAM-page
  workstream (`Romans3/`) that proved out a different presentation pattern.
- Two-tier distillation (pastor + scholar) — rejected; layman tier is the
  audience that most needs the visual modality.

**Ratified by:** Bryan (PM dialogue, spec at
`docs/superpowers/specs/2026-04-23-visual-theology-architecture-design.md`).

**Affected:** entire WS0–WS7 trajectory; sufficiency map; all scholar JSONs.

**Status:** active.

---

## 2026-04-25 — PM standing values

**Decision:** Four standing values govern PM judgment for the duration of the
pilot: (1) verified > confident; (2) no fabrication, ever; (3) specific over
generic; (4) honest gaps beat false coverage.

**Rationale:** Subagent reports have been wrong in specific structural ways
(fabricated quotes, mislabeled traditions, synthetic resourceIds). A fixed set
of values makes correction quick: when the PM or a subagent drifts, Bryan can
point at a value and the trajectory snaps back without re-litigating. The
values are the *minimum* discipline that distinguishes peer-review-grade work
from confidently-wrong work.

**Alternatives considered:**
- Looser "trust subagent reports" stance — rejected by repeated empirical
  failures.
- Heavier formal-process stance (full review checklists per artifact) —
  rejected as too slow for the iteration cadence.

**Ratified by:** Bryan (PM dialogue), encoded in `docs/PM-CHARTER.md` §2.

**Affected:** every dispatch; every codex audit; every verification gate.

**Status:** active.

---

## 2026-04-25 — Single dual-citation schema (quote + sha256 + supportStatus + verifier-anchored matching)

**Decision:** All scholar citations follow a single dual-citation schema
combining: stored quote text (NFC-normalized), sha256 of the normalized quote,
a `supportStatus` enum (`directly-quoted` / `paraphrase-anchored` /
`summary-inference`), and a verifier (`tools/citations.py:verify_citation`)
that anchors the quote in the named article via `_normalize` whitespace and
typography handling.

**Rationale:** A single schema with a verifier replaces the prior practice of
freeform quote + page-number citations that could not be machine-checked.
sha256 lets us detect corpus drift. `supportStatus` makes the rationale-vs-quote
relationship explicit so a `directly-quoted` claim must hold up against the
quote alone. Verifier-anchored matching catches both fabrication and
quiet-paraphrase rot.

**Alternatives considered:**
- Anthology-shape schema (one record per voice with embedded extracts) —
  considered, designed at `docs/schema/anthology-schema-variant.md`, then
  superseded 2026-04-29 by the full-text per-voice approach.
- Looser "page number is enough" citation — rejected; not auditable.

**Ratified by:** Bryan (PM dialogue); Codex (initial audit `e75673d`).

**Affected:** `tools/citations.py`, `tools/validate_scholar.py`,
`tools/sweep_citations.py`, every scholar JSON.

**Status:** active.

---

## 2026-04-26 — supportStatus relabel discipline (apply\_\*\_relabels.py script artifact pattern)

**Decision:** Whenever a codex audit returns supportStatus relabel
recommendations, the relabels are applied via a generated
`tools/apply_*_relabels.py` (or equivalent fixes) script committed alongside
the corpus changes, rather than via ad-hoc edits.

**Rationale:** Codex audits regularly catch `directly-quoted` over-application
where the rationale outruns the quote. Captured as a script, the relabel set
is reviewable, reproducible, and forms a verifiable audit trail. Ad-hoc edits
hide which entries were touched and why.

**Alternatives considered:**
- Manual per-file Edit calls — rejected as opaque and unreviewable in
  aggregate.
- A standing relabel CLI — rejected as premature; a script per audit keeps
  history clear.

**Ratified by:** Bryan (PM dialogue); Codex (WS0c audit, `e75673d`).

**Affected:** `tools/apply_ws0c_relabels.py`, `tools/apply_wave1_relabels.py`
(commit `3593a89`), `tools/apply_wave6_fixes.py` (commit `f06d4de`).

**Status:** active.

---

## 2026-04-26 — WS0.6 sufficiency map: 11 mini-dossiers + per-tier pass/fail rubric

**Decision:** Peer-review readiness is judged against 11 mini-dossiers (M1–M11)
with an explicit per-tier pass/fail rubric. The Reformed-pastoral cluster
dispatches LAST among the in-library waves so Bryan's own posture does not
anchor the foundation.

**Rationale:** Bryan is Reformed-pastoral himself; if that cluster surveys
first, every subsequent voice gets weighed against a Reformed baseline that
the pilot is supposed to be testing, not assuming. Mini-dossiers force the
sufficiency question to be answered per topic, not in aggregate, so a strong
M1 cannot mask a thin M7.

**Alternatives considered:**
- Single corpus-wide sufficiency verdict — rejected as too coarse to act on.
- Reformed-pastoral first (chronological / pastoral-relevance order) —
  rejected for the anchoring reason above.

**Ratified by:** Bryan (PM dialogue, sufficiency map at
`docs/research/2026-04-26-ws06-peer-review-sufficiency-map.md`).

**Affected:** dispatch order for Waves 2–5; mini-dossier verdict tracking.

**Status:** active.

---

## 2026-04-26 — $0 acquisition budget

**Decision:** Resource acquisition for the pilot is restricted to
in-Logos-library resources plus freely-online sources. No subscription, no
purchase, no interlibrary-loan budget. Public-domain originals are preferred
over copyrighted modern translations when both exist.

**Rationale:** The pilot must be reproducible by a single pastor on a single
laptop without spending money. This forces honest disclosure of permanent
gaps (Sources Chrétiennes Hippolytus, Hill 2006 Theodoret SBL ET, German
KAT/BKAT, etc.) instead of papering over them. Public-domain originals also
free the eventual visual site from licensing constraints.

**Alternatives considered:**
- Bounded acquisition budget — rejected; hard to draw the line.
- Subscription-database access (Brill, SC) — rejected; not reproducible.

**Ratified by:** Bryan (PM dialogue).

**Affected:** `docs/research/method-and-limits.md §3a`; gap-mapping doc;
sufficiency map §9 permanent-gap list.

**Status:** active.

---

## 2026-04-27 — Verifier patch: catalog ResourceId-first lookup

**Decision:** `tools/citations.py:verify_citation` resolves resources by
catalog `ResourceId` first, falling back to bare-stem resolution only when
the catalog lookup misses. This handles dotted-stem catalog IDs (e.g.
`LLS:6.60.21` style with embedded dots) without requiring synthetic-stem
workarounds in scholar JSONs.

**Rationale:** Some Logos resources carry dotted-stem catalog IDs that the
prior bare-stem-first resolver could not match without per-scholar synthetic
IDs (Lacocque was the canary). A catalog-first lookup is the principled fix
and lets every scholar JSON store the real ResourceId.

**Alternatives considered:**
- Continue with synthetic resourceId per-file — rejected; opaque and
  unscalable.
- A registry of dotted-stem aliases — rejected; the catalog already is the
  registry.

**Ratified by:** Bryan (PM dialogue); Codex (review accepting the patch).

**Affected:** `tools/citations.py` (commit `7e4e19c`); all dotted-stem
scholar files.

**Status:** active.

---

## 2026-04-27 — `PASSAGE_COVERAGE_VOCAB` expansion for M11 NT cross-book

**Decision:** Extend `tools/validate_scholar.py:PASSAGE_COVERAGE_VOCAB`
with Acts 7, 2 Thess 2, John 5, Heb 1, Heb 2 to enable validator-level
scoring of NT cross-book breadth for M11.

**Rationale:** WS0.6 sufficiency map §9 item 14 noted that scholar
rationale text already engages these passages (Walvoord, Pentecost,
Theodoret, Jerome on 2 Thess 2; Beale on Acts 7) but they were not
flag-able by the validator without controlled-vocabulary entries.
Pre-expanding the vocabulary is cheaper than per-survey schema-extension
cycles and keeps M11 coverage scorable when later waves land.

**Alternatives considered:**
- Free-form passage entries — rejected: defeats the controlled-
  vocabulary discipline.
- Add entries only when a survey first lands them — rejected:
  preparatory expansion is cheaper than per-survey schema-extension
  cycles.

**Ratified by:** Bryan (PM dialogue 2026-04-27).

**Affected:** `tools/validate_scholar.py:PASSAGE_COVERAGE_VOCAB`
(commit `554be55`).

**Status:** active.

---

## 2026-04-28 — Multilingual scope: original language preferred over English translation

**Decision:** Where a voice's primary work exists in a non-English original
(Latin / Greek / Hebrew / Aramaic / Judeo-Arabic / German / French), the
original-language full text counts as the verified path. An English
translation is required as a `translations[]` target on every non-English
quote, but the English text is not the source of record.

**Rationale:** The pilot must be defensible to scholars who will check the
Latin / Greek / Hebrew. An English-only path forfeits that audience. It also
collapses voices like Theodoret, Abrabanel, and Saadia into "no available ET"
GAPs when the originals are freely online (Migne PG/PL, HebrewBooks, YU
thesis). Original-language-first opens those voices.

**Alternatives considered:**
- English-only sourcing — rejected; collapses pilot to mostly-modern voices.
- Originals optional — rejected; weakens the verifiability claim.

**Ratified by:** Bryan (PM dialogue); the two D-1.6 audits at
`docs/research/2026-04-28-patristic-reformation-fulltext-audit.md` and
`docs/research/2026-04-28-jewish-reception-multilingual-audit.md` operate
under this rule.

**Affected:** Wave 6 + Wave 7 dispatch; `external-ocr` backend; Theodoret
backfill; every multilingual scholar file.

**Status:** active.

---

## 2026-04-28 — Translation architecture: pre-computed at survey time, stored in JSON

**Decision:** Every non-English quote carries a `translations[]` array
populated at survey time using the latest Opus model, per the SSoT at
`docs/research/scholars/_TRANSLATION_CONFIG.md`. Register: modern-faithful.
The validator strictly enforces: every non-English quote MUST have at least
one entry with `language: "en"`. Translations are NOT verified against the
source by `verify_citation`; only `quote.text` is the verifier's anchor.
The validator's check on `translations[]` is structural (required fields,
allowed languages/methods/registers, ISO date, llm-translator format).

**Rationale:** Translations baked into the corpus at survey time are
reproducible, citable, and audit-stable. Computing translations at render time
would couple the visual site to a live LLM, complicate caching, and invite
drift. Modern-faithful register matches Bryan's pastoral audience without
sliding into paraphrase. The SSoT config keeps model + register choices
co-located so they can be revised in one place.

**Alternatives considered:**
- Render-time translation — rejected for caching + drift reasons.
- Use existing public ETs where available — rejected as inconsistent across
  voices and rights-encumbered for some.

**Ratified by:** Bryan (PM dialogue); D-2 / D-2.5 / D-2.6 sequence.

**Affected:** `tools/validate_scholar.py` (commit `77e9681`);
`docs/schema/citation-schema.md §"translations"`;
`docs/research/scholars/_TRANSLATION_CONFIG.md`; Theodoret backfill.

**Status:** active.

---

## 2026-04-28 — Full-text per-voice approach over anthology

**Decision:** Each scholarly voice is captured as its own per-voice JSON file
covering the voice's actual work in full, rather than as anthology extracts
(ACCS, RCS) keyed to a passage.

**Rationale:** Per-voice JSON keeps a voice's argument intact across topics
and lets us cite the voice directly rather than via an editor's curation.
Anthology shape would have created two indirection layers (voice → editor →
passage) that fight `supportStatus` honesty: an anthology extract isn't
necessarily what the voice said about *this* topic, only what the editor
selected. Full-text per-voice also lets a single voice contribute to multiple
mini-dossiers without duplicating extracts.

**Alternatives considered:** All three were enumerated in the archived
design doc (`docs/schema/anthology-schema-variant.md §5`) and considered
before the pivot to full-text per-voice:
- Option A — anthology JSON file with `extracts[]` array (each extract a
  primary-voice citation) — rejected: substantial validator + dossier-
  traversal changes; conflated "what the editor selected" with "what the
  voice said about Daniel 7".
- Option B — per-extract scholar JSONs sharing `backend.resourceId` —
  rejected: shape works without schema changes but still encodes "ACCS
  editor's selection of Theodoret" rather than Theodoret's own argument
  on Daniel 7; the per-voice full-text approach reaches the voice
  directly when the original is recoverable.
- Option C — Option B plus a thin per-anthology markdown index —
  rejected: same indirection problem as B; the index adds editorial
  provenance but does not change the supportStatus-honesty issue.
- Hybrid per-voice for primaries + anthology for fold-ins — rejected as
  unnecessary complexity once Wave 7 multilingual full-text became
  feasible.

**Ratified by:** Bryan (PM dialogue); D-2 series.

**Affected:** every scholar file; archived design at
`docs/schema/anthology-schema-variant.md` (commit `f4e88af`).

**Status:** active. Supersedes the earlier anthology-shape design.

---

## 2026-04-28 — `external-ocr` backend generalization

**Decision:** The `external-greek-ocr` backend kind was renamed and
generalized to `external-ocr`, with a per-citation `language` field carrying
the OCR'd language. One backend handles every OCR'd language path
(Greek / Latin / German / Hebrew / Judeo-Arabic).

**Rationale:** Greek-specific naming was an artifact of Theodoret being the
first OCR voice. Wave 7 + Wave 6.3 will OCR Latin, German, Hebrew, and
Judeo-Arabic; a per-language backend would multiply code paths for no
real-world difference. A `language` field on each citation captures the
distinction without code branching.

**Alternatives considered:**
- One backend per language (`external-latin-ocr`, etc.) — rejected as
  needless code duplication.
- Keep the Greek-specific name and detect language from path — rejected;
  language metadata belongs on the citation.

**Ratified by:** Bryan (PM dialogue); D-2 series.

**Affected:** `tools/citations.py` (commit `9773226`);
`docs/schema/citation-schema.md`; Theodoret backfill;
`external-resources/{greek,latin,german,hebrew,judeo-arabic}/`.

**Status:** active.

---

## 2026-04-28 — `external-sefaria` backend kind

**Decision:** Add a new citation backend kind for the Sefaria REST API
(`external-sefaria`), enabling Wave 6 medieval-Jewish reception surveys
(Rashi, Ibn Ezra, Joseph ibn Yahya, Malbim, Steinsaltz, Bavli Sanhedrin,
Vayikra Rabbah, Yalkut Shimoni). The backend ships with URL
canonicalization, Hebrew NFC normalization, and a verse-anchored matcher
hardened across sessions C-2 / C-3 / C-4.

**Rationale:** Sefaria provides free API access to medieval and modern
Jewish commentaries on Daniel, with stable refs and ET. An API-native
backend is more verifiable and stable than HTML scraping. Wave 6 was
backend-blocked without it.

**Alternatives considered:**
- HTML scraping of Sefaria pages — rejected: fragile; harder to
  verify quote anchoring; no clean URL canonicalization.
- Local-OCR pattern via `external-ocr` — rejected: Sefaria is
  API-native, no scanning needed; OCR would discard the structured ref
  metadata Sefaria already exposes.
- Skip Wave 6 until Hebrew OCR-prep lands — rejected: would push the
  Jewish-reception cluster past Phase D; Sefaria covers ≥11 candidate
  voices that would otherwise need separate OCR pipelines.

**Ratified by:** Bryan (PM dialogue 2026-04-28).

**Affected:** `tools/citations.py`; `tools/validate_scholar.py`;
`docs/schema/citation-schema.md`; Wave 6.1 + 6.2 scholar files (commit
`9773226` initial; hardened across C-2/C-3/C-4; landed in Wave 6.1/6.2
via `f06d4de`).

**Status:** active.

---

## 2026-04-29 — Codex review required for all dispatch sessions; read-only sandbox

**Decision:** Every dispatch session that produces an artifact (scholar JSON,
audit doc, schema change, code change) ends with a codex adversarial review.
The review runs in `-s read-only` sandbox, scoped to the session's own work.
Codex's suggestions are NOT applied during the same session — they are
captured as findings and folded into a follow-on session.

**Rationale:** Codex catches what the PM and the executing subagent miss,
but only if it actually runs. Marking it required (not optional) eliminates
the "we'll skip this one" drift. Read-only sandbox prevents codex from
mutating files mid-review. Deferring application of suggestions to a
follow-on prevents scope creep and keeps the session's commit boundary clean.

**Alternatives considered:**
- Codex review optional — rejected; drift was real.
- Apply codex suggestions in the same session — rejected; bloats commit
  scope and conflates "what the session shipped" with "what codex asked for".
- `--dangerously-bypass-approvals-and-sandbox` for review — rejected;
  read-only is sufficient and safer. The bypass form is reserved for cases
  where codex must write a deliverable file.

**Ratified by:** Bryan (PM dialogue).

**Affected:** every dispatch session from this date forward;
`docs/PM-CHARTER.md §5`.

**Status:** active.

---

## 2026-04-29 — Cross-coordinator coordination rule

**Decision:** When two or more coordinators run in parallel, each
coordinator's briefing must enumerate by exact path every file the *other*
coordinator is expected to produce or modify. Coordinators (and their
subagents) MUST NOT delete or overwrite files outside their assigned scope;
if a file appears that's outside the assignment, leave it alone.

**Rationale:** Wave 6.1 and Wave 6.2 dispatched in parallel and hit a
file-vanishing incident: each coordinator wrote into the same
`tools/apply_*` script namespace and one overwrote the other's. The fix is
explicit cross-coordinator awareness in the briefing plus a non-deletion
rule that survives even when the awareness fails.

**Alternatives considered:**
- Strict serialization of coordinators — rejected; sacrifices the
  parallelism benefit.
- Centralized lockfile — rejected as overkill; the briefing-level rule is
  sufficient and self-documenting.

**Ratified by:** Bryan (PM dialogue) after the Wave 6.1 / 6.2 incident.

**Affected:** every parallel-coordinator briefing from this date forward;
`docs/PM-CHARTER.md §5`.

**Status:** active.

---

## 2026-04-30 — Wave dispatch ordering revised: in-library Waves 2–5 BEFORE OCR-prep Waves 6.3 + 7

**Decision:** The dispatch order from sufficiency map §8 is revised so
in-library Waves 2–5 dispatch in order BEFORE the OCR-dependent waves
(6.3, 7). OCR-1 + per-language OCR-prep run concurrently alongside the
in-library waves, so the cached OCR text is staged when 6.3 and 7 fire.

**Rationale:** Wave 6 jumped ahead of Waves 2–5 because the Sefaria backend
was ready and the in-library work was queued. Going forward, in-library
voices need no new tooling and should land first to reach Phase D unblocked.
OCR-prep is parallel-safe (no file conflicts with in-library surveys) so
running it concurrently costs nothing and prepays the OCR-dependent waves.

**Alternatives considered:**
- Continue the original sufficiency-map §8 order — rejected; out of order
  with current readiness.
- Block OCR-prep until all in-library waves land — rejected; wastes parallel
  capacity.

**Ratified by:** Bryan (PM dialogue, 2026-04-30); recorded in the
`docs/SESSION-HANDOFF-WS0c-WAVE6-COMPLETE.md` "Revised Trajectory" section.

**Affected:** Wave 2–7 dispatch order; OCR-1 + OCR-prep × 5 scheduling.

**Status:** active.

---

## 2026-04-30 — Phase D end-to-end codex audit gates WS1

**Decision:** Once all dispatch waves (2–7) commit, an independent codex
adversarial audit of the entire corpus must PASS before WS1 (visual
implementation) begins. Phase D runs in read-only sandbox over the full
scholar corpus, the audits, and the sufficiency map.

**Rationale:** Verified-citation discipline at session level is necessary
but not sufficient: an end-to-end audit catches cross-corpus issues
(over-application patterns, dossier coverage gaps, schema drift) that
per-session reviews miss. WS1 freezes the taxonomy and visual mappings;
corrections after WS1 are expensive (reflows of layouts, copy, claim
extraction). A peer-review-grade audit before WS1 is the cheapest place
to catch them.

**Alternatives considered:**
- Skip Phase D — rejected: would commit "good enough" rather than
  peer-review-grade; the pilot's defensibility hinges on this gate.
- WS1 incremental with mid-stream audits — rejected: WS1 implementation
  effort warrants stable input data; mid-stream audits would force
  rework already shipped.

**Ratified by:** Bryan (PM dialogue, original phase plan 2026-04-26).

**Affected:** pilot trajectory; gates WS1 dispatch; recorded in
`docs/SESSION-HANDOFF-WS0c-WAVE6-COMPLETE.md` "Revised Trajectory".

**Status:** active.
