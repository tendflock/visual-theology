# Session Handoff — WS0c Wave 6.1 + 6.2 Complete

**Date:** 2026-04-30
**Status:** Wave 1, Sefaria backend (C-series), workbench cleanup (M/N), three multilingual
audits (D-1 / D-1J / D-1.6 — all final), `external-ocr` generalization + `translations[]`
schema enforcement (D-2 series), and Wave 6.1 + 6.2 (8 new Jewish-reception scholars + relabel
script) all committed. HEAD = `f06d4de`. Working tree clean for visual-theology research.
Romans 3 TEAM-page workstream remains unstaged and out of scope.
**Replaces** `docs/SESSION-HANDOFF-WS0c-WAVE1-COMPLETE.md`.

## One-Minute Context

The 2026-04-28 Wave 1 handoff closed with 22 scholars / 641 verified citations and Waves 2–7
queued. Since then:

1. **C-series — Sefaria backend.** Sessions C / C-2 / C-3 / C-4 shipped the
   `external-sefaria` backend kind, URL canonicalization, Hebrew NFC handling, and the
   verse-anchored matcher. Wave 6 is now backend-unblocked.
2. **M / N — handoff supersede + workbench cleanup.** `69ae687` pinned the Wave 1 handoff
   as canonical; `e861fe7` scoped the workbench E2E tests to `conftest.base_url` and removed
   a flake.
3. **D-series multilingual audits (final at D-1.6).**
   `docs/research/2026-04-28-patristic-reformation-fulltext-audit.md` and
   `docs/research/2026-04-28-jewish-reception-multilingual-audit.md` reframe Wave 7 + Wave 6
   under a multilingual rubric: original-language full-text counts as a verified path even
   when no English translation exists. Patristic+Reformation tally: **8 / 13 voices (62 %)**
   work-level VERIFIED, 2 INFERRED, 3 structural GAPs (Vermigli, Brenz tentative, Bucer).
   Jewish-reception tally: ≥11 candidate voices recoverable across Sefaria + HebrewBooks +
   archive.org + YU (Saadia thesis).
4. **D-2 / D-2.5 / D-2.6 — schema + backend.** `9773226` shipped the `external-sefaria`
   backend kind and generalized `external-greek-ocr` → `external-ocr` (per-citation `language`
   field, language-agnostic storage). `77e9681` added strict `translations[]` enforcement and
   the en-target rule (every non-English quote must carry a verified English target).
   Theodoret backfilled to the new schema. The anthology-shape design doc was archived
   (`f4e88af`) as superseded by per-voice JSONs.
5. **Wave 6.1 + 6.2 — 8 Jewish-reception scholars.** `f06d4de` committed Rashi, Ibn Ezra,
   Joseph ibn Yahya, Malbim, Steinsaltz (Wave 6.1, Sefaria-borne) plus Bavli Sanhedrin,
   Vayikra Rabbah 13:5, and Yalkut Shimoni Nach §1066 (Wave 6.2, Talmud + midrash
   reception-event surveys). Codex H-2 relabel + factual fixes folded into the same commit
   via `tools/apply_wave6_fixes.py`. M7 moves **FAIL → PARTIAL** (not yet PASS — Wave 6.3 +
   the next codex audit are still ahead).

The corpus now passes verbal verification at **795 / 795** with 30 / 30 strict-validate.
WS1 visual implementation remains gated on Phase D end-to-end audit clearance after Waves
2–7 land.

## Current Corpus State

| metric | value | delta from 2026-04-28 |
|---|---|---|
| JSON-backed scholars | **30** | +8 |
| Total citations | **795** | +154 |
| Verified citations (sweep) | **795 / 795** (100 %) | +154 |
| `supportStatus` distribution | 680 `directly-quoted` / 44 `paraphrase-anchored` / 71 `summary-inference` | +136 / +12 / +6 |
| Strict-validate pass | **30 / 30** | +8 |
| Mini-dossier verdicts (last published, sufficiency map §6) | 2 PASS / 7 PARTIAL / 2 FAIL — pre-Wave-6 baseline; **M7 has since moved FAIL → PARTIAL** | (Phase D will re-score) |

**Anchor docs (read these to load state):**

- Sufficiency map: `docs/research/2026-04-26-ws06-peer-review-sufficiency-map.md`
  (§6 matrix; §8 dispatch waves — read with the revised trajectory below; §9 permanent gaps)
- Patristic+Reformation multilingual audit (D-1.6 final):
  `docs/research/2026-04-28-patristic-reformation-fulltext-audit.md`
- Jewish-reception multilingual audit (D-1.6 final):
  `docs/research/2026-04-28-jewish-reception-multilingual-audit.md`
- Wave 1 codex audit: `docs/research/2026-04-27-wave1-codex-audit.md`
- Method/limits: `docs/research/method-and-limits.md`
- Bibliography: `docs/research/bibliography.md`
- Schema: `docs/schema/citation-schema.md` (current); `docs/schema/anthology-schema-variant.md` (archived/superseded)
- Translation enforcement config: `docs/research/scholars/_TRANSLATION_CONFIG.md`

## Revised Trajectory — Waves 2–5 In-Library First, OCR-Prep Concurrent, Then 6.3 + 7 + Phase D

PM and Bryan ratified this ordering on 2026-04-30. The two changes from sufficiency-map §8:
(a) Waves 2–5 dispatch **in order before any OCR-dependent wave**, so the in-library voices
land first and reach Phase D unblocked; (b) OCR-1 + the per-language OCR-prep sessions run
**concurrently alongside** the in-library waves (no file conflicts; the prep work is ready
when Wave 6.3 and Wave 7 dispatch). A future session reading this handoff cold should pick
up from here without further PM input.

### Wave 2 — patristic / DSS / Bauckham (in-library, ~1 session day)

| # | Voice | Resource | Mini-dossier(s) |
|---|---|---|---|
| 2.1 | Cyril of Jerusalem *Cat. Lec.* XV | `LLS:6.60.21` | M8 |
| 2.2 | Chrysostom *Hom. Matt* 75–78 | `LLS:6.60.10` | M8, M11 |
| 2.3 | Victorinus *Comm. on the Apocalypse* | `LLS:6.50.7` | M8, M11 |
| 2.4 | Lexham DSS — Qumran Dan-7 reception (1QM, 4Q174, 11Q13, 4Q246, 4QDan a/b/c, 4Q243-245) | `LLS:LDSSHEIB` | M6 |
| 2.5 | Bauckham *Theology of Revelation* | `LLS:NTTHEO87REV` | M10, M11 |

**Strengthens:** M2 / M6 / M8 / M10 / M11. Reception-event briefing for #2.4.

### Wave 3 — pre-Collins critical + Beale NIGTC + Sib Or (in-library, ~1 session day)

| # | Voice | Resource | Mini-dossier(s) |
|---|---|---|---|
| 3.1 | Driver *Cambridge Bible Daniel* | `LLS:CAMBC27DA` | M1, M9 |
| 3.2 | Montgomery *ICC Daniel* | `LLS:ICC_DA` | M1, M9 |
| 3.3 | Charles *ICC Revelation* | `LLS:ICC_REV` | M11 |
| 3.4 | Beale *NIGTC Revelation* | `LLS:29.71.18` | M11 |
| 3.5 | Charlesworth *OTP Vol 2* — Sib Or III + IV reception-event survey | `LLS:OTPSEUD02` | M6, M9 |

**Strengthens:** M1 / M6 / M9 / M11.

### Wave 4 — modern critical breadth (in-library, ~1 session day)

Pace *Smyth & Helwys* (`LLS:SHC27DA`); Seow *WBC* (`LLS:WBCS27DA`); Davies *Sheffield*
(`LLS:SHEFFCL27DA`); Anderson *ITC* (`LLS:ITC21DAN`); optional Collins *Apocalyptic
Imagination* 3rd ed. (`LLS:PCLYPTCMGNTNPLT`).

**Strengthens:** M9 (deep PASS).

### Wave 5 — Reformed-pastoral cluster (in-library, ~1–2 session days)

Hoekema *Bible and the Future* (`LLS:BBLANDTHEFUTURE`); Riddlebarger *Case for Amill*
(`LLS:CSAMLLNLSM`); Sproul *Last Days according to Jesus* (`LLS:LSTDYSCCRDNGJSS`); Gentry
*Beast of Revelation* (`LLS:BEASTREVELATION`); Davis BST *Daniel* (`LLS:BST27DA`); optional
follow-on: Longman NIVAC (`LLS:NIVAC27DA`); Lucas AOT (`LLS:AOT27DA`); Ladd *Theology of
the NT* (`LLS:THEONTLADD`); Patterson NAC (`LLS:NAC39`); Koester *Revelation and the End*
(`LLS:RVLTNNDLLTHNGS2ED`).

**Strengthens:** M3 / M4 / M5 / M10 / M11.

Dispatched LAST among in-library waves so Bryan's own posture does not anchor the
foundation.

### OCR-1 — generalize the OCR pipeline (~3–4 h, parallel-safe alongside Waves 2–5)

Build `tools/extract_ocr.sh` by generalizing
`external-resources/greek/extract_pg81_range.sh`. Take **URL + language + output path**;
handle `pdftoppm` + `tesseract`; bake in the macOS Leptonica path workaround (`cd` into the
cache directory before invoking tesseract; ASCII-only filenames). Output cached plain text
under `external-resources/{language}/`.

### OCR-prep × 5 — per-language sessions (parallel-safe, after OCR-1)

One session per language, each running `extract_ocr.sh` per voice and committing the cached
text files. Languages and target voices:

- **Hebrew** — Abrabanel (HebrewBooks 23900); the live Cloudflare-aware fetch path.
- **Judeo-Arabic** — Saadia *Tafsir on Daniel* (YU/Hurvitz 1977 thesis,
  `repository.yu.edu/items/f04a17f7-cc80-422c-8f75-cd5132521785`); chs 2:4b–7:28 only.
- **Latin** — Origen (PG 13 fragments, archive.org); Cyril of Alexandria (Mai vol. 2 +
  PG 70); Gregory the Great (PL 75 / 76); Bullinger; Œcolampadius (e-rara); Pellican (BSB
  10142935); Melanchthon (BSB 10176881 / Google Books `DPU7AAAAcAAJ`); Lambert; Mede (when
  Latin scan surfaces).
- **German** — Luther *Vorrede auf den Propheten Daniel* (WA DB 11/II at archive.org
  `diedeutschebibel1121unse`; 1545 Wittenberg Bibel as printing witness).
- **Greek** — any new patristic adds beyond the Theodoret precedent (Origen Greek + Cyril of
  Alexandria Greek if separated from the Latin OCR-prep).

### Wave 6.3 — Hebrew + Judeo-Arabic Jewish-reception fills (after Hebrew + Judeo-Arabic OCR-prep)

| # | Voice | Source | Note |
|---|---|---|---|
| 6.3.1 | Abrabanel *Ma'yanei ha-Yeshuah* | hebrewbooks.org/23900 (Amsterdam 1647) | single largest Jewish Daniel commentary |
| 6.3.2 | Saadia Gaon *Tafsir on Daniel* | YU/Hurvitz 1977 thesis | scope: chs 2:4b–7:28 only per codex IMPORTANT-3 |
| 6.3.3 | Yefet ben Eli *Commentary on Daniel* 1–6 | archive.org/details/commentaryonbook00japhuoft (Margoliouth 1889) | full Dan 7 coverage in PD English ET + Judeo-Arabic facing |

**Pushes M7 from PARTIAL toward PASS** (geographic / chronological span:
Geonic → Karaite → Rashi → Ibn Ezra → ibn Yahya → Abrabanel → Acharonim → Malbim →
Steinsaltz → classical rabbinic).

### Wave 7 — patristic + Reformation multilingual surveys (after Latin + German + Greek OCR-prep)

~10 surveys: **Origen** (PG 13 fragments + *Contra Cels.* + *Comm. Matt.*); **Cyril of
Alexandria** (Mai vol. 2 + PG 70); **Gregory the Great** (PL 75 / 76); **Bullinger** *Daniel
sapientissimus*; **Œcolampadius** *In Danielem*; **Pellican** *Comm. Bibl.* tom. 3;
**Melanchthon** *In Danielem*; **Lambert** *In Apocalypsim* (engagement-density survey);
**Luther** *Vorrede*; **Mede** *Clavis* (ET via Cooper 1833 verified; Latin INFERRED).
Vermigli, Brenz, Bucer remain structural GAPs.

**Strengthens:** M8 (Reformation cluster moves from Calvin alone to multi-voice; patristic
deepens with Cyril of Alexandria + Gregory + Origen).

### Phase D — codex adversarial end-to-end audit of full corpus (after all waves above land)

Single read-only codex pass against the entire corpus + audits + sufficiency map. If PASS:
declare peer-review-grade. If FAIL: address findings before WS1.

### WS1 — visual implementation per spec

Only after Phase D PASS.

**Bryan ratified Waves 2–5 dispatching IN ORDER** with OCR-1 + OCR-prep running
**CONCURRENTLY ALONGSIDE** them — no file conflicts; helpful to have OCR text files staged
when later waves dispatch.

## Pending Decisions

These items are open and PM should ratify (or kick to Bryan) before the relevant wave fires.

1. **Sefaria license adjudication for the midrashim.** "Midrash Rabbah -- TE" and "Yalkut
   Shimoni on Nach" both report `license: unknown` on Sefaria. Wave 6.2 stored quote-text
   defensibly under fair-use treatment for verbatim Jewish-reception inclusion; if Bryan
   wants stricter handling, add a `licenseRestricted: true` flag and gate downstream display.
2. **Steinsaltz license.** Steinsaltz Center copyright applies to both Hebrew and English;
   stored under attribution. Confirm display posture for the rendered site.
3. **Acquisition-needed mitigations** (gap-mapping §5c; $0 budget; deferred indefinitely):
   Stuckenbruck *1 Enoch 91-108*, Yarbro Collins *Cosmology and Eschatology*, Wright
   *Resurrection of the Son of God*, Henze *Jewish Apocalypticism*, Mounce *Revelation*,
   Aune *Revelation 1-22*. Each has a partial mitigation via in-library secondary engagement.
4. **Pre-Tannaitic Jewish-reception consolidated survey** (Bavli / Yerushalmi / midrash
   beyond what Wave 6.2 already captured). Sufficiency map §9 #7. Permanent gap absent a
   dedicated workstream.
5. **Eastern Orthodox modern academic Daniel commentary.** §9 #4 — permanent gap unless an
   external acquisition surfaces.
6. **Pentecostal-charismatic distinctive academic eschatology.** §9 #5 — permanent gap.
7. **Post-Vatican-II Roman Catholic magisterial commentary.** §9 #6 — permanent gap.
8. **Additional progressive-dispensational voice.** Saucy is the natural candidate; corpus
   currently has Blaising/Bock alone.
9. **Theodoret OCR-quote tightening.** WS0c codex audit §6.5 deferred; PG 81 OCR text is
   in-corpus at `external-resources/greek/theodoret-pg81-dan*.txt`. Not permanent.
10. **Comprehensive Aramaic textual-criticism (OG vs Theodotion at Dan 7:13).** Wave J
    (Lexham Aramaic Lexicon, `LLS:FBARCLEX`, ~3 h tooling integration) anchors linguistic;
    full text-critical adjudication is a future workstream.

## Standing Project Conventions

- **PM-Charter** (`docs/PM-CHARTER.md`) is the source of truth for role / authority /
  verification discipline / decision escalation. Read it once at session start.
- **PM2:** never `pm2 kill` / `stop all` / `delete all` — other apps share the daemon.
  Stop/start `study-companion` only if running pytest (port 5111 conflict).
- **Logos reader:** `tools/LogosReader` builds with `dotnet 8` (export `PATH` +
  `DOTNET_ROOT` first). Test files use `LogosBatchReader` for speed.
- **Codex CLI — read-only sandbox is now standard.** Use
  `codex exec -s read-only --skip-git-repo-check -c model_reasoning_effort=high
  < prompt.txt > log.txt 2>&1`. The previous
  `--dangerously-bypass-approvals-and-sandbox` form is reserved for cases where codex must
  write a deliverable file via the Write tool. Default to read-only for advisory review.
  **Never `--output-last-message`** — it clobbers files codex writes.
- **Subagent dispatch:** 4–5 concurrent surveys is the sweet spot. Background-mode dispatch
  (`run_in_background: true`) frees the controller; notifications land when each agent
  finishes — don't poll.
- **Parallel-coordinator briefings must enumerate "expected sibling files from parallel
  coordinators."** Wave 6.1 vs 6.2 hit a cross-coordinator file-vanishing conflict
  (each coordinator did not know the other was writing into the same `apply_*` script
  namespace, and one overwrote the other). Going forward, every parallel-coordinator
  briefing must list, by exact path, every file the *other* coordinator is expected to
  produce or modify, so each coordinator merges rather than overwrites.
- **Survey briefing:** every survey subagent reads
  `docs/research/scholars/_SURVEY_BRIEFING.md` first; per-scholar prompts customize.
- **Verification on completion:** never trust a subagent's "100 % verified" report without
  independently re-running `verify_citation` on the file they produced.
- **`supportStatus` honesty:** never label `directly-quoted` unless the quote alone proves
  the rationale's sub-claim. Codex audits have caught over-applications in every wave so far.
- **Multilingual `translations[]` enforcement:** any non-English quote must carry a verified
  English target via the `translations[]` array; the validator enforces this strictly.

## Permanent Gaps (summary)

Catalogued in full in `docs/research/method-and-limits.md §3a`, sufficiency map §9, and the
two D-1.6 audits. Highlights:

- **Hippolytus full *Comm. on Daniel* in Greek-French** (Lefèvre SC 14, 1947) — subscription
  Sources Chrétiennes; only ANF 5 fragments + tracts in-library.
- **Theodoret Hill 2006 SBL English (WGRW 7)** — out of stock at SBL; behind Brill paywall.
  Mitigation: PG 81 Greek OCR is in-corpus via `external-ocr` (lang=greek).
- **Continental German commentaries** (Koch BKAT XXII; Plöger KAT; Berger; Stegemann; Ego)
  — German-only, no English translation; not actionable at $0.
- **Ramban / Ralbag** — Ramban wrote no complete Daniel commentary (Sefer ha-Geulah's
  Hebrew availability INFERRED only); Ralbag's Daniel commentary location not yet pinned.
- **Vermigli, Bucer, Brenz (tentative)** — wrote no Daniel work in any language; structural
  gaps. ACCS / RCS extracts are the only available primary engagement.
- **Eastern Orthodox modern academic Daniel commentary.**
- **Pentecostal-charismatic distinctive academic eschatology.**
- **Post-Vatican-II Roman Catholic magisterial Daniel commentary.**
- **Babylonian / Persian apocalyptic parallels** (Akkadian prophecy, Bahman Yasht) — out of
  pilot scope.

## Out-of-Scope Active Work — Romans 3 TEAM Page

Bryan has a separate workstream in flight that this handoff does not cover:

- `Romans3/` directory — unstaged.
- `docs/research/2026-04-23-romans-3-psalm-14-53-textual-history.md` — unstaged.
- Spec: `docs/superpowers/specs/2026-04-27-romans3-team-page-design.md` (committed in
  `8c3a760`).
- Implementation plan: `docs/superpowers/plans/2026-04-23-...` (committed in `3e26fab`).
- Site shipped at `tendflock.github.io/romans-3-9-20/` (`2a879c7`); handbook at
  `docs/passage-pages.md` (`24ddcd7`).

Do **not** pull Romans 3 work into the visual-theology dispatch sequence above.

## Next-Session Recommended Order

1. **Run the session-start checklist** (PM-Charter §8): `git status` + `git log --oneline -5`;
   `python3 tools/validate_scholar.py docs/research/scholars/` (expect 30/30 valid);
   `python3 tools/sweep_citations.py --scholars docs/research/scholars --out
   /tmp/sweep-status.md` (expect 795/795 verified).
2. **Dispatch Wave 2 immediately** (5 in-library patristic / DSS / Bauckham surveys; ~6–8 h
   subagent + 1–2 h verification). Briefing template in `_SURVEY_BRIEFING.md` plus the
   reception-event variant for the Qumran survey (#2.4).
3. **In parallel with Wave 2: dispatch OCR-1** (~3–4 h). Build `tools/extract_ocr.sh`. No
   file conflict with Wave 2 surveys (different paths).
4. After Wave 2 returns and verifications land: **dispatch Wave 3** (in-library, ~1 day).
5. After Wave 3 returns: **dispatch Wave 4** (in-library, ~1 day).
6. After Wave 4 returns: **dispatch Wave 5** (in-library, ~1–2 days). Held until the prior
   waves are committed so Bryan's Reformed-pastoral posture does not anchor the foundation.
7. **OCR-prep × 5** runs concurrent with Waves 3 / 4 / 5 once OCR-1 returns. One session per
   language; output goes to `external-resources/{language}/`.
8. After Hebrew + Judeo-Arabic OCR-prep returns: **dispatch Wave 6.3** (Abrabanel + Saadia +
   Yefet).
9. After Latin + German + Greek OCR-prep returns: **dispatch Wave 7** (~10 patristic +
   Reformation surveys).
10. After all waves committed: **dispatch Phase D** (codex adversarial end-to-end audit of
    the full corpus, sufficiency map, audits). Read-only sandbox.
11. If Phase D passes: **WS1** visual implementation per spec. If Phase D fails: address
    findings before WS1.

The visual-theology pilot remains gated on Phase D PASS before WS1 begins.

## File-Path Cheat Sheet

```
this handoff:                docs/SESSION-HANDOFF-WS0c-WAVE6-COMPLETE.md (you are here)
prior handoff (super.):      docs/SESSION-HANDOFF-WS0c-WAVE1-COMPLETE.md
PM charter:                  docs/PM-CHARTER.md
spec:                        docs/superpowers/specs/2026-04-23-visual-theology-architecture-design.md
schema (current):            docs/schema/citation-schema.md
schema (archived):           docs/schema/anthology-schema-variant.md
method/limits:               docs/research/method-and-limits.md
bibliography:                docs/research/bibliography.md
translation config:          docs/research/scholars/_TRANSLATION_CONFIG.md

sufficiency map:             docs/research/2026-04-26-ws06-peer-review-sufficiency-map.md
gap-mapping:                 docs/research/2026-04-26-ws0c-gap-mapping.md
WS0c codex audit:            docs/research/2026-04-26-ws0c-corpus-audit.md
Wave 1 codex audit:          docs/research/2026-04-27-wave1-codex-audit.md
patristic+Reformation audit: docs/research/2026-04-28-patristic-reformation-fulltext-audit.md
Jewish-reception audit:      docs/research/2026-04-28-jewish-reception-multilingual-audit.md

scholars dir (30 files):     docs/research/scholars/
survey briefing:             docs/research/scholars/_SURVEY_BRIEFING.md

external-resources tree:     external-resources/{aramaic,epubs,french,german,greek,hebrew,
                                                 judeo-arabic,latin,pdfs,sefaria-cache}/
PG 81 PDF source:            external-resources/greek/migne-pg81-archiveorg/
PG 81 extract tool:          external-resources/greek/extract_pg81_range.sh
Theodoret ingest tool:       external-resources/greek/ingest_theodoret.sh
(planned) generalized OCR:   tools/extract_ocr.sh  (build in OCR-1)

reader:                      tools/LogosReader/Program.cs
study orchestrator:          tools/study.py
citations:                   tools/citations.py    (build_citation, verify_citation, sha256_of)
validator:                   tools/validate_scholar.py
sweep:                       tools/sweep_citations.py
WS0c relabel script:         tools/apply_ws0c_relabels.py
Wave 1 relabel script:       tools/apply_wave1_relabels.py
Wave 6 fixes script:         tools/apply_wave6_fixes.py

tests:                       tools/workbench/tests/test_{validate_scholar,citations,
                                                          article_meta,lbxlls_reader}.py
```

## Memory Pointers

- Auto-memory at `~/.claude/projects/-Volumes-External-Logos4/memory/`. Active priority
  memo is `project_visual_theology_build.md`; it should be updated after the next session's
  commits to point at this handoff and reflect Wave 2 + OCR-1 as the active dispatch pair.
- This handoff supersedes `docs/SESSION-HANDOFF-WS0c-WAVE1-COMPLETE.md`; both remain on
  disk. Earlier handoffs (`WS0c-EXPANSION.md`, `VISUAL-THEOLOGY-WS0.md`) were already
  superseded and remain as historical record.
