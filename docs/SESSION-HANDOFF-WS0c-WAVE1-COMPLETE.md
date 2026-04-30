# Session Handoff — WS0c Expansion, Wave 1 Complete

> **SUPERSEDED 2026-04-30** by `docs/SESSION-HANDOFF-WS0c-WAVE6-COMPLETE.md`.
> Kept on disk as historical record. Do not start a session from this doc.

**Date:** 2026-04-28
**Status:** WS0.6 sufficiency map + WS0c gap-mapping committed; verifier patch committed;
Wright JVG errata applied; Wave 1 dispatched, audited, relabeled, and committed (5 new
scholar JSONs + codex audit + relabel script). Working tree clean for visual-theology
research. Romans 3 TEAM-page workstream is unstaged and out of scope for this handoff.
**Replaces** `docs/SESSION-HANDOFF-WS0c-EXPANSION.md`.

## One-Minute Context

The 2026-04-26 handoff closed with WS0c surveys done (17 scholars, 426 verified
citations, codex pass-with-conditions) and an open queue of ~26 supportStatus relabels
plus 4 cross-book mismatches.

Since then:

1. **WS0c-cleanup landed.** Relabels and mismatch repairs were applied to the WS0c
   corpus and pushed in commits `4bac02a` (scholar corpus + bibliography +
   method-and-limits) and `e75673d` (audit + post-audit relabel + verification report
   + handoff).
2. **Verifier patch.** `tools/citations.py` gained dotted-stem ResourceId fallback for
   catalog-only `LLS:` ids that lack a Resources/ directory file (`7e4e19c`); the
   validator's `PASSAGE_COVERAGE_VOCAB` was expanded to add `Acts 7`, `2 Thess 2`,
   `John 5`, `Heb 1`, `Heb 2` for M11 NT cross-book scoring (`554be55`).
3. **WS0.6 sufficiency map produced** (`f5e24dc`): per-mini-dossier rubric across 11
   dossiers (M1–M11), three-tier verdict (layman / pastor / scholar), 7-wave dispatch
   plan, permanent-gap acknowledgments. Headline: **2 / 11 PASS, 7 / 11 PARTIAL,
   2 / 11 FAIL** at scholar tier. Wright JVG errata corrected: `LLS:JESUSVICTYGOD` was
   in-library all along; the prior `method-and-limits.md §3a` "not in library" note
   was wrong and has been amended.
4. **Wave 1 dispatched and committed** (`3593a89`): 5 new scholar surveys (Newsom &
   Breed OTL, Hippolytus ANF 5, Augustine *City of God* Bk XX, Stone Hermeneia 4
   Ezra, Wright JVG); codex Wave 1 audit returned 17 supportStatus over-applications;
   `tools/apply_wave1_relabels.py` applied them (3 → `paraphrase-anchored`,
   14 → `summary-inference`); corpus rebuilt to 22 scholars / 641 verified citations.
5. **Workbench dictation/whisper landed** (separate workstream): `acedb66`, `600a4fb`,
   `737c5e6`. Not part of visual-theology; mentioned only because it appears in `git
   log` for orientation.

The corpus now passes the verbal-verification gate at the new scale (641 / 641
verified) and Wave 1 has flipped M2 / M3 / M6 / M9 toward PASS at scholar tier.
WS1 visual implementation is *still* gated on Waves 2–7 work per the sufficiency map.

## Current Corpus State

| metric | value |
|---|---|
| JSON-backed scholars | **22** (was 17) |
| Verified citations (positions[] + crossBookReadings[]) | **641 / 641** (was 426) |
| `supportStatus` distribution | 544 `directly-quoted` / 32 `paraphrase-anchored` / 65 `summary-inference` |
| Strict-validate pass | 22 / 22 |
| Mini-dossier verdicts (sufficiency map §6) | 2 PASS · 7 PARTIAL · 2 FAIL |
| Tier rollup | Layman 9 / 1 / 1 · Pastor 8 / 1 / 2 · Scholar 2 / 7 / 2 |

**Anchor docs (read these to load state):**

- Sufficiency map: `docs/research/2026-04-26-ws06-peer-review-sufficiency-map.md` (995 lines; §6 is the planning matrix, §8 is dispatch waves, §9 is permanent gaps)
- Gap-mapping: `docs/research/2026-04-26-ws0c-gap-mapping.md` (acquisition map; in-library / freely-online / acquisition-needed / unobtainable)
- Wave 1 codex audit: `docs/research/2026-04-27-wave1-codex-audit.md` (the 17 relabels just applied; per-citation table in §2)
- Method/limits: `docs/research/method-and-limits.md` (current as of 2026-04-28; §3a names permanent gaps; §3 lists the WS0c expansion acquisitions)
- Bibliography: `docs/research/bibliography.md`

## WS0.6 Trajectory — 7-Wave Dispatch Plan

Sequencing is per sufficiency map §8 (4–5-concurrent-survey ceiling). Order: Wave 1
done; Waves 2–3 next (in-library, no schema work); Wave 4 (modern critical breadth);
Wave 5 (Reformed-pastoral, dispatched LAST per priority discipline); Waves 6–7 require
backend / schema work.

| Wave | Voices | Status | Prerequisite | Outcome |
|---|---|---|---|---|
| **1** | Newsom OTL, Hippolytus ANF 5, Augustine *CoG* Bk XX, Stone Hermeneia 4 Ezra, Wright JVG | **✓ done (`3593a89`)** | none | M2 / M3 / M6 / M9 advanced; 17-citation relabel applied via `tools/apply_wave1_relabels.py` |
| **2** | Cyril of Jerusalem *Cat. Lec.* XV, Chrysostom *Hom. Matt* 75–78, Victorinus *Apoc.*, Lexham DSS Qumran reception, Bauckham *Theology of Revelation* | **pending** | none (in-library) | patristic Greek + Latin each ≥3 voices; M6 → PASS; M11 deepens; M10 gains post-critical anchor |
| **3** | Driver *Cambridge Bible Daniel*, Montgomery *ICC Daniel*, Charles *ICC Revelation*, Beale *NIGTC Revelation*, Charlesworth *OTP Vol 2* (Sib Or) | **pending** | none (in-library) | pre-Collins critical baseline (M1, M9); M6 → PASS at 5 voices |
| **4** | Pace *Smyth & Helwys*, Seow *WBC*, Davies *Sheffield*, Anderson *ITC*, optional Collins *Apocalyptic Imagination* | **pending** | none (in-library) | M9 deep-PASS |
| **5** | Hoekema, Riddlebarger, Sproul, Gentry, Davis BST, optional Longman / Lucas / Ladd / Patterson NAC / Koester | **pending — dispatch LAST** | Waves 1–4 first | M10 → PASS; Bryan's Reformed-pastoral cluster anchored as one tradition among many, not foundation |
| **6** | Rashi, Ibn Ezra, Joseph ibn Yahya, Malbim, Steinsaltz (all Sefaria) | **pending — backend-blocked** | new `external-sefaria` (or `external-html`) backend; Hebrew NFC normalization; ~1–2 days backend work | M7 FAIL → PASS (largest single deficiency closes) |
| **7** | ACCS Daniel, RCS Daniel/Ezekiel | **pending — schema-blocked** | anthology-shape schema variant (one file = many extracts); ~2–3 days schema design | M8 → PASS at scholar tier (Reformation cluster expands beyond Calvin alone) |
| **J** (parallel) | Lexham Aramaic Lexicon integration | **pending** | none (tooling integration, not a survey; ~3h) | Dan 7:13 OG vs Th text-critical anchor; supports M2, M3 |

## Pending Decisions

These items are open from the sufficiency map and gap-mapping; PM should ratify before
the relevant wave fires.

1. **Anthology-shape schema variant** (one file = many primary-voice extracts, each
   with its own backend anchor + scholar attribution). Required for Wave 7 (ACCS, RCS).
   Estimated 2–3 days schema design.
2. **`external-sefaria` (or `external-html`) backend.** Required for Wave 6. Hebrew
   NFC normalization, HTML stripping, verse-anchored matching. Estimated 1–2 days.
3. **Reception-event survey schema-clarification** for non-single-author entries. The
   current corpus already has two such entries (1 Enoch Parables Hermeneia, Stone
   Hermeneia 4 Ezra); Wave 2 (Qumran reception via Lexham DSS) and Wave 3 (Sibylline
   Oracles via OTP V2) reuse the pattern. The `_SURVEY_BRIEFING.md` should explicitly
   describe the reception-event variant.
4. **Reformed-pastoral wave timing.** Sufficiency map §7 P7 dispatches Wave 5 LAST so
   Bryan's own posture does not anchor the foundation. PM may choose to dispatch a
   subset of Wave 5 earlier if M10 PARTIAL becomes a bottleneck for visual-theology
   PRD work — but the priority order is intentional and should be defended.
5. **Additional progressive-dispensational voice** (Saucy is the natural candidate;
   Blaising/Bock co-author elsewhere). Sufficiency map §2.1 lists prog-disp at floor 2
   but the corpus has only Blaising/Bock; second voice would close the cluster.
6. **Additional partial-preterist voice** beyond what Wave 5 brings (Sproul + Gentry).
   Mathison or Kik or Mauro could deepen.
7. **Additional historicist-Reformation voice** beyond Durham. Optional; cluster floor
   is 1, currently met.
8. **Pre-Tannaitic Jewish reception** (Bavli / Yerushalmi / midrash). No consolidated
   commentary exists; would require manual extraction. Sufficiency map §9 #7 names
   this as a permanent gap; out-of-scope absent a dedicated workstream.
9. **Eastern Orthodox modern academic Daniel commentary.** §9 #4: no English-language
   academic monograph located. Theodoret is patristic-Antiochene and predates the
   East-West split. Permanent gap unless an external acquisition surfaces.
10. **Pentecostal-charismatic distinctive eschatology.** §9 #5: field is
    popular-devotional (Hagee, Lindsey, LaHaye), no academic primary-voice work.
    Permanent gap.
11. **Post-Vatican-II Roman Catholic magisterial commentary.** §9 #6: LaCocque +
    Hartman/Di Lella are the closest proxies, both pre-Vatican-II in sensibility.
    Permanent gap unless an external acquisition surfaces.
12. **Theodoret OCR-quote tightening.** Codex audit §6.5 (in the WS0c corpus audit)
    flagged several Greek fragments as too short for the rationale; the PG 81 OCR
    text is in `external-resources/greek/theodoret-pg81-dan7.txt`. Deferred, not
    permanent.
13. **Comprehensive Aramaic textual-criticism (Old Greek vs Theodotion at Dan 7:13).**
    No scholar JSON adjudicates. Wave J (Lexham Aramaic Lexicon integration) anchors
    linguistic; full text-critical adjudication is a future workstream.
14. **Acquisition-needed mitigations** (gap-mapping §5c, $0 budget, deferred
    indefinitely): Stuckenbruck *1 Enoch 91-108*, Yarbro Collins *Cosmology and
    Eschatology*, Wright *Resurrection of the Son of God*, Henze *Jewish Apocalypticism*,
    Mounce *Revelation*, Aune *Revelation 1-22*. Each has a partial mitigation via an
    in-library secondary engagement.

## Standing Project Conventions

- **PM2:** never `pm2 kill` / `stop all` / `delete all` — other apps share. Stop/start
  `study-companion` only if running pytest (port 5111 conflict).
- **Logos reader:** `tools/LogosReader` builds with `dotnet 8` (export `PATH` +
  `DOTNET_ROOT` first). Test files use `LogosBatchReader` for speed.
- **macOS Leptonica path bug:** tesseract on absolute paths under `/Volumes/External`
  fails with "Error in fopenReadStream". `cd` into the cache dir before invocation.
- **Codex CLI:** `codex exec --dangerously-bypass-approvals-and-sandbox
  --skip-git-repo-check -c model_reasoning_effort=high < prompt.txt > log.txt 2>&1`.
  **Never `--output-last-message`** — it clobbers files codex writes via Write tool.
- **Subagent dispatch:** 4–5 concurrent surveys is the sweet spot. Wave-of-9 pushed
  Logos reader contention. Background-mode dispatch (`run_in_background: true`) frees
  the controller; notifications land when each agent finishes — don't poll.
- **Survey briefing:** every survey subagent reads
  `docs/research/scholars/_SURVEY_BRIEFING.md` first; per-scholar prompts customize.
- **Verification on completion:** never trust a subagent's "100% verified" report
  without independently re-running `verify_citation` on the file they produced.
  Subagents have been wrong about tradition tags, schema-required fields, and quote
  presence.
- **PM-Charter** (`docs/PM-CHARTER.md`) is the source of truth for role / authority /
  verification discipline / decision escalation. Read it once at session start.
- **`supportStatus` honesty:** never label `directly-quoted` unless the quote alone
  proves the rationale's sub-claim. When the rationale outruns the quote, downgrade.

## Permanent Gaps (Summary)

Catalogued in full in `docs/research/method-and-limits.md §3a` and sufficiency map §9.
Highlights:

- **Hippolytus full *Commentary on Daniel* in Greek-French (Lefèvre SC 14, 1947)** —
  subscription Sources Chrétiennes; only ANF 5 fragments + tracts are in-library.
- **Theodoret Hill 2006 SBL English (WGRW 7)** — out of stock at SBL; behind Brill
  paywall; dokumen.pub intermittent. Mitigation: PG 81 Greek OCR is in-corpus via
  `external-greek-ocr` backend.
- **Continental German commentaries** (Koch *Das Buch Daniel* + BKAT XXII; Plöger
  *KAT* + *Theokratie und Eschatologie*; Berger; Stegemann; Ego). Not actionable at
  $0 budget.
- **Medieval Jewish voices beyond Wave 6** — Saadia Gaon (Judeo-Arabic fragments only),
  Yefet ben Eli (rare 1889 OUP), Ramban (no complete Daniel commentary), Ralbag
  (Sefaria 404), Abrabanel (Sefaria 404).
- **Eastern Orthodox modern academic Daniel commentary.**
- **Pentecostal-charismatic distinctive academic eschatology.**
- **Post-Vatican-II Roman Catholic magisterial Daniel commentary.**
- **Pre-Tannaitic Jewish reception (Bavli / Yerushalmi / midrash) consolidated.**
- **Babylonian / Persian apocalyptic parallels** (cuneiform Akkadian prophecy,
  Bahman Yasht). Specialist primary-source field; out of pilot scope.

## Out-of-Scope Active Work — Romans 3 TEAM Page

Bryan has a separate workstream in flight:

- `Romans3/` directory — unstaged.
- `docs/research/2026-04-23-romans-3-psalm-14-53-textual-history.md` — unstaged.
- `docs/superpowers/specs/2026-04-27-romans3-team-page-design.md` — committed in
  `8c3a760` (`docs(specs): Romans 3:9-20 TEAM page design — replaces codex
  chalk_and_talk`).
- Implementation plan: `docs/superpowers/plans/2026-04-23-...` (per `3e26fab`).

This is **not** the visual-theology Daniel 7 pilot. Do not pull Romans 3 work into
visual-theology dispatch. The Romans 3 spec / page design replaces the earlier "chalk
and talk" approach and is its own initiative.

## Next-Session Recommended Order

1. Read this handoff + sufficiency map §6, §8 (highest-density information).
2. Run the standard session-start checklist (PM-Charter §8): `git status`, `git log
   --oneline -5`, `python3 tools/validate_scholar.py docs/research/scholars/`,
   `python3 tools/sweep_citations.py --scholars docs/research/scholars --out
   /tmp/sweep-status.md` (expect 22/22 valid; 641/641 verified).
3. **Dispatch Wave 2** (5 in-library patristic / DSS / Bauckham surveys; ~6–8h
   subagent + 1–2h verification). All five resources are in-library; no backend or
   schema work required. Briefing template in `_SURVEY_BRIEFING.md` plus the
   reception-event variant for the Qumran survey (#2.4).
4. **In parallel** (independent of Wave 2): begin scoping the `external-sefaria`
   backend if Wave 6 is ratified, and/or scope the anthology-shape schema variant if
   Wave 7 is ratified. Either unblocks a non-trivial portion of the dossier matrix
   (M7 FAIL → PASS via Wave 6; M8 PARTIAL → PASS via Wave 7).
5. After Wave 2 returns and verifications land: dispatch Wave 3 (pre-Collins critical
   + Beale NIGTC + Sib Or).
6. Wave 4 → Wave 5 in order. Hold Wave 5 until Waves 1–4 are committed; this is the
   discipline that keeps Bryan's Reformed-pastoral posture from anchoring the
   foundation.
7. Workbench test cleanup (dictation / whisper coverage gaps) is non-blocking and
   parallelizable; not on the visual-theology critical path.

The visual-theology pilot remains gated on the dossier matrix reaching ≥9 / 11 PASS
at scholar tier before WS1 visual implementation begins. Wave 1 moved the dial; Waves
2–5 close most of the remaining PARTIALs; Waves 6–7 close the two FAILs.

## File-Path Cheat Sheet

```
this handoff:             docs/SESSION-HANDOFF-WS0c-WAVE1-COMPLETE.md (you are here)
prior handoff (super.):   docs/SESSION-HANDOFF-WS0c-EXPANSION.md
PM charter:               docs/PM-CHARTER.md
spec:                     docs/superpowers/specs/2026-04-23-visual-theology-architecture-design.md
schema:                   docs/schema/citation-schema.md
method/limits:            docs/research/method-and-limits.md
bibliography:             docs/research/bibliography.md

sufficiency map:          docs/research/2026-04-26-ws06-peer-review-sufficiency-map.md
gap-mapping:              docs/research/2026-04-26-ws0c-gap-mapping.md
WS0c codex audit:         docs/research/2026-04-26-ws0c-corpus-audit.md
Wave 1 codex audit:       docs/research/2026-04-27-wave1-codex-audit.md
sweep report (latest):    docs/research/2026-04-26-citation-verification-report.md

scholars dir (22 files):  docs/research/scholars/
survey briefing:          docs/research/scholars/_SURVEY_BRIEFING.md
external resources:       external-resources/{pdfs,epubs,greek}/
PG 81 PDF source:         external-resources/greek/migne-pg81-archiveorg/
PG 81 extract tool:       external-resources/greek/extract_pg81_range.sh

reader:                   tools/LogosReader/Program.cs
study orchestrator:       tools/study.py
citations:                tools/citations.py        (build_citation, verify_citation, sha256_of)
validator:                tools/validate_scholar.py (PASSAGE_COVERAGE_VOCAB; backend.kind dispatch)
sweep:                    tools/sweep_citations.py
WS0c relabel script:      tools/apply_ws0c_relabels.py
Wave 1 relabel script:    tools/apply_wave1_relabels.py

tests:                    tools/workbench/tests/test_{validate_scholar,citations,article_meta,lbxlls_reader}.py
```

## Memory Pointers

- Auto-memory at `~/.claude/projects/-Volumes-External-Logos4/memory/`. Active priority
  memo is `project_visual_theology_build.md`; it should be updated after the next
  session's commits to point at this handoff and reflect Wave 2 as the active task.
- This handoff supersedes `docs/SESSION-HANDOFF-WS0c-EXPANSION.md`; both remain on
  disk. Earlier `docs/SESSION-HANDOFF-VISUAL-THEOLOGY-WS0.md` was superseded by the
  WS0c-EXPANSION handoff and is also kept as historical record.
