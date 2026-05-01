# Session Handoff — WS0c OCR-Prep Complete + 3 Waves Drafted

**Date**: 2026-05-01
**Status**: K-5 committed and pushed. Pause point — picking up next week
in a new PM session.
**Replaces**: `docs/SESSION-HANDOFF-WS0c-WAVE6-COMPLETE.md` (the
2026-04-30 handoff — superseded but kept on disk).

---

## One-Minute Context

The visual-theology Daniel 7 pilot's research corpus is now at **40
scholars / 1242 / 1242 verified citations** on origin/main at
`85d2f49`. Since the prior handoff:

- **Wave 3** (5 in-library scholars: Driver, Montgomery, Charles ICC
  Rev, Beale NIGTC, Sib Or via Charlesworth OTP1) committed in K-5
  with H-4 cleanup pass applied (35 codex-flagged relabels + Beale
  tradition-tag harmonization + Sib Or filename rename + 8
  passageCoverage trims).
- **OCR-prep × 5** sessions all complete: text files for 13 voices
  across `external-resources/{latin,german,greek,hebrew,judeo-arabic}/`
  ready to feed Wave 6.3 (Jewish reception) + Wave 7 (patristic +
  Reformation) surveys via the `external-ocr` backend.
- **Tooling**: `tools/extract_ocr.sh` archive-text endpoint bug fixed
  (OCR-1.5: `/stream/` → `/download/` + HTML-sniff regression tests,
  test count 31 → 36).
- **Persistence layer**: `docs/PROJECT-DECISIONS.md` +
  `docs/FOLLOW-UPS-TRACKER.md` populated through 2026-05-01;
  `docs/PM-CHARTER.md` §5 carries the subagent staging-file
  protection rule (added after Wave 3's Sib Or incident).
- **Documented gaps**: Pellican (no working PDF download from BSB /
  Google Books / e-rara / archive.org); Mede Latin original (no
  open-access scan; Cooper 1833 ET is the witness); Origen primary
  Daniel surface redirected from PG 13 to CCEL *Contra Celsum*
  (PG 13 has no contiguous Daniel commentary; only Ezek 14:14
  Noah-Daniel-Job typology cluster substantive).

**Pending dispatches** (drafted but not yet fired): Wave 4, Wave 6.3,
Wave 7-pt-1 — full prompts at
`docs/PENDING-DISPATCHES.md`.

---

## Current Corpus State

| Item | State |
|---|---|
| Scholars | 40 (post-K-5) |
| Verified citations | 1242 / 1242 |
| Strict-validate | 40 / 40 OK |
| Backends | `logos`, `external-epub`, `external-pdf`, `external-greek-ocr` (deprecated alias for `external-ocr`), `external-ocr`, `external-sefaria` |
| Schema | `quote.language` + `translations[]` enforced; ≥1 `language: "en"` required for non-en quotes (D-2.6) |
| Tests | 192 / 192 (validate + citations) + 36 / 36 (extract_ocr) |
| Origin | https://github.com/tendflock/visual-theology @ `85d2f49` |
| Last commits | K-5 = 60c9b43 / c199811 / b3a5ce6 / 85d2f49 |

---

## WS0.6 Sufficiency Map — Per-Mini-Dossier Status (post-K-5)

Anchor: `docs/research/2026-04-26-ws06-peer-review-sufficiency-map.md`.

| # | Dossier | Status post-K-5 | Note |
|---|---|---|---|
| M1 | Dan 7:1-8 four beasts + 4th kingdom | PASS | Driver + Montgomery (Wave 3) added pre-Collins critical baseline |
| M2 | Dan 7:9-12 Ancient of Days + court scene | PASS | (Wave 1 baseline; no change in this round) |
| M3 | Dan 7:13-14 Son of Man | PARTIAL | Wave 5 voices will deepen at scholar tier |
| M4 | Dan 7:15-18 saints + kingdom | PARTIAL | Wave 5 voices will deepen |
| M5 | Dan 7:19-27 little horn + persecution | PARTIAL | Wave 5 voices will deepen |
| M6 | Daniel 7 in Second Temple reception | PASS-borderline | Sib Or (Wave 3.5) closes the four-kingdoms reception axis; M6 likely PASS pending Phase D rescore |
| M7 | Daniel 7 in Jewish interpretation | PARTIAL | Wave 6.3 (Abrabanel + Saadia + Yefet) closes toward PASS |
| M8 | Daniel 7 in patristic + Reformation reception | PARTIAL | Wave 7-pt-1 (7 voices) + Wave 7-pt-2 (Origen + Mede) closes toward PASS |
| M9 | Daniel 7 in modern critical scholarship | PASS-borderline → PASS-on-Wave-4 | Wave 4 (Pace / Seow / Davies / Anderson + opt. Collins Apoc Imag) lands the in-library breadth |
| M10 | Daniel 7 in evangelical / Reformed / dispensational | PARTIAL | Wave 5 closes |
| M11 | Daniel 7 in Revelation + NT reuse | PASS-borderline | Charles + Beale NIGTC (Wave 3) deepen; Wave 5 Patterson/Koester finish |

---

## Next Dispatches (per `docs/PENDING-DISPATCHES.md`)

**Three parallel-safe wave coordinators** ready to dispatch:

1. **Wave 4** — 5 in-library Logos surveys (Pace, Seow, Davies, Anderson,
   optional Collins Apoc Imag). Strengthens M9. ~6-8h subagent + 1-2h
   verification. Standard wave-of-N coordinator pattern.
2. **Wave 6.3** — 3 Jewish reception OCR-fed surveys (Abrabanel, Saadia,
   Yefet). Closes M7 toward PASS. Visual-PDF-anchored quote discipline +
   Klein/Hurvitz attribution correction + Yefet line-9742 boundary
   (all documented in `docs/FOLLOW-UPS-TRACKER.md`).
3. **Wave 7-pt-1** — 7 patristic + Reformation OCR-fed surveys (Cyril,
   Gregory, Bullinger, Œcolampadius, Melanchthon, Lambert, Luther).
   Closes M8 toward PASS. Two sub-waves (4 + 3) to manage subagent
   concurrency.

After these return + their codex relabel cleanup passes (H-5 / H-7 /
H-8) land, K-6 consolidates and pushes. Then Wave 7-prep + Wave 7-pt-2
+ Wave 5 + Phase D + WS1 — see `docs/PENDING-DISPATCHES.md` §2 for the
trajectory.

---

## Active Decisions Awaiting Ratification (when Wave 7-prep dispatches)

- **`extend external-ocr to accept "en"` vs `implement external-html backend`**
  for English-source HTML-extracted text (CCEL Contra Celsum is the
  immediate use case; Mede Cooper 1833 ET secondary). Audit logged
  "external-html backend" but extending external-ocr is simpler. PM
  recommendation: extend external-ocr. Ratify with Bryan before Wave
  7-prep dispatches.

---

## Standing Project Conventions

See `docs/PM-CHARTER.md` for the canonical conventions. Highlights for
the new PM session:

- **Codex review required** (not optional) for all dispatch sessions;
  runs in `-s read-only` sandbox (per PM-CHARTER §5).
- **Parallel-coordinator coordination rule**: subagents and coordinators
  MUST NOT delete files outside their assigned scope. Subagent staging-
  file protection rule: `_*.json`, `*_citations.json`, `*.tmp.*`,
  `_*_shas.tmp` patterns are sibling-subagent staging files; do not
  delete (PM-CHARTER §5; added after Wave 3 Sib Or incident).
- **Translation architecture**: `quote.language` per citation;
  `translations[]` array enforced for non-English quotes; ≥1 entry with
  `language: "en"`; translator identifier from
  `docs/research/scholars/_TRANSLATION_CONFIG.md` (currently
  `anthropic:claude-opus-4-7`).
- **PM2**: never `pm2 kill` / `stop all` / `delete all` — other apps
  share. Stop/start `study-companion` only for pytest runs.
- **Codex CLI sandbox**: read-only is standard; never use
  `--dangerously-bypass-approvals-and-sandbox`.

---

## Out-of-Scope Active Work

- **Romans 3 TEAM page workstream** — Bryan's separate track
  (`Romans3/`, `docs/research/2026-04-23-romans-3-psalm-14-53-textual-history.md`,
  + commits `e845168` and `8c3a760` already on origin). PM does NOT
  cover this.
- **Manual-download source PDFs at `/Volumes/External/Logos4/daniel/`** —
  4 PDFs (Lambert, Melanchthon, Œcolampadius, Abrabanel) totaling
  ~80 MB. Now gitignored (K-5 commit `85d2f49`). Source-of-truth is the
  OCR text files derived from them; PDFs are local-only working copies.
  Re-fetchable from URLs documented in the audits + per-language
  `_OCR-PREP-NOTES.md` files.
- **Workbench dictation/whisper feature** — landed via G in K's commit
  range. Not visual-theology scope but lives in the same repo.

---

## Permanent Gaps (per `docs/research/method-and-limits.md` §3a)

- **Pellican on Daniel** — research-library-accessible only; BSB +
  Google Books + e-rara + archive.org all failed download. Reformation
  cluster (Bullinger + Œcolampadius + Melanchthon + Lambert) carries
  the load without him.
- **Mede Latin original** (*Clavis Apocalyptica*) — no open-access
  scan; Cooper 1833 ET on archive.org is the witness.
- **Origen primary Daniel surface — PG 13 yields only 1 substantive
  cluster.** Audit redirect: Wave 7 dispatches Origen via CCEL
  *Contra Celsum* (after Wave 7-prep). PG 13 OCR file is
  supplementary corroborating fragment.
- **Hippolytus full Comm Dan in Greek** (Lefèvre SC 14, 1947) —
  subscription/library only; ANF 5 fragments serve as witness.
- **Theodoret full Greek for Dan 1-4 + Dan 8-10** — partial coverage
  via PG 81 OCR in `external-resources/greek/`; Hill 2006 SBL English
  unobtainable online.
- **German continental commentaries** (Klaus Koch, Otto Plöger) —
  copyright + no open-access.
- **Roman Catholic post-V2 magisterial** + **Eastern Orthodox
  modern academic** + **Pentecostal-charismatic distinctively-
  eschatological** — all genuinely non-existent in academic-monograph
  form per the audits.

See also `docs/FOLLOW-UPS-TRACKER.md` for active follow-ups by source
session (deferred items + audit corrections + dispatch-prep notes).

---

## File-Path Cheat Sheet

| Path | Purpose |
|---|---|
| `docs/PM-CHARTER.md` | PM standing values + conventions |
| `docs/SESSION-HANDOFF-WS0c-OCR-PREP-COMPLETE.md` | This file (current handoff) |
| `docs/SESSION-HANDOFF-WS0c-WAVE6-COMPLETE.md` | Prior handoff (superseded) |
| `docs/PROJECT-DECISIONS.md` | Architectural decision log |
| `docs/FOLLOW-UPS-TRACKER.md` | Codex-surfaced items by source session |
| `docs/PENDING-DISPATCHES.md` | Three ready-to-dispatch prompts (Wave 4 / 6.3 / 7-pt-1) + trajectory outline |
| `docs/research/2026-04-26-ws06-peer-review-sufficiency-map.md` | WS0.6 rubric + 7-wave dispatch plan |
| `docs/research/2026-04-28-{patristic-reformation,jewish-reception}-...-audit.md` | Final D-1.6 multilingual audits |
| `docs/research/method-and-limits.md` | Scope + permanent gaps + PD ET availability |
| `docs/research/scholars/*.json` | 40 scholar JSONs (1242 verified citations) |
| `docs/research/scholars/_SURVEY_BRIEFING.md` | Briefing template (Multilingual surveys section relevant for Wave 6.3 / 7) |
| `docs/research/scholars/_TRANSLATION_CONFIG.md` | Translator identifier SSoT |
| `tools/citations.py` | Verifier + backend dispatch |
| `tools/validate_scholar.py` | Schema validator |
| `tools/sweep_citations.py` | Corpus-wide verifier |
| `tools/extract_ocr.sh` | Generalized OCR-prep tool |
| `tools/apply_wave{1,2,3,6}_*.py` | Per-wave codex-relabel apply scripts |
| `external-resources/{latin,german,greek,hebrew,judeo-arabic}/*.txt` | OCR text files for Wave 6.3 + Wave 7 dispatch |
| `external-resources/{latin,german,greek,hebrew,judeo-arabic}/_OCR-PREP-NOTES.md` | Per-language OCR provenance + quality notes |

---

## Next-Session Recommended Order

1. Run the 7-step bootstrap in `docs/PENDING-DISPATCHES.md` §3.
2. Confirm git state matches the handoff (`git log --oneline -10`).
3. Spin up Wave 4 / Wave 6.3 / Wave 7-pt-1 in parallel from the prompts
   in `docs/PENDING-DISPATCHES.md` §1.
4. As each returns, dispatch its codex relabel pass (H-5 / H-7 / H-8)
   and apply per the established H-* pattern (mirror H-2 / H-3 / H-4).
5. K-6 consolidates. PM ratifies the `extend external-ocr` vs
   `external-html` decision before Wave 7-prep dispatches.
6. Wave 7-prep → Wave 7-pt-2 → Wave 5 → Phase D → WS1.

---

## Bryan's Standing Values (PM internalizes)

From the original PM-CHARTER, still load-bearing:

- **Verified > confident.** Empirical check passes; no fabrication.
- **No fabrication, ever.** Quotes that aren't in the article aren't.
- **Specific over generic.** Named voices, named URLs, named LLS-ids.
- **Adversarial review wins.** Codex required; do NOT apply codex's
  suggestions during the originating session.
- **Test before claiming success.** Run validate + sweep + tests
  before reporting done.
- **Honest about scope and limits.** Document gaps, not paper over.
- **Methodical, not flashy.** Long careful work.
