> **SUPERSEDED 2026-04-28** by `docs/SESSION-HANDOFF-WS0c-WAVE1-COMPLETE.md`.
> Kept on disk as historical record. Do not start a session from this doc.

# Session Handoff — WS0c Daniel-7 Pilot Corpus Expansion

**Date:** 2026-04-26
**Status:** WS0c surveys complete (12 dispatched, 13 corpus deltas), tooling complete.
Codex final audit landed; ~26 relabels + a few coverage repairs pending. Working tree
unstaged; nothing committed. **Replaces** `SESSION-HANDOFF-VISUAL-THEOLOGY-WS0.md` for
directing visual-theology research work.

## One-Minute Context

WS0 closed last session with 4 surveyed scholars, 89 verified citations, and the
"verified quote ≠ warranted claim" critique acknowledged. WS0.5 added supportStatus
tagging, schema validation, and post-audit relabels.

This session expanded dramatically:

- Logos Daniel Expository Preaching Kit landed → 60+ Daniel resources, mostly
  scholars I had previously listed as out-of-corpus
- Bryan acquired 2 EPUBs (Lacocque, Menn), 1 PDF (Hippolytus partial), and the full
  archive.org Migne PG 81 PDF (canonical Theodoret source)
- Built three new citation backends: `external-epub`, `external-greek-ocr`,
  `external-pdf` (the PDF backend untested in production)
- Dispatched 12 surveys in three waves; all back, all 100% verified
- Final corpus: **17 surveyed scholars, 426 / 426 citations verified, 53.1% with page
  numbers, 17/17 strict-validate**
- Codex audit: pass-with-conditions

The Daniel 7 pilot now has all the patristic anchors (Jerome Latin + Theodoret Greek),
the previously-missing critical voices (Hartman/DiLella, Goldingay, Lacocque), the
conservative-critical Reformed counter-voice (Young), the second classical-disp voice
(Pentecost), the contemporary Reformed exegete (Duguid), the Beale-school cross-book
authority (Beale + Hamilton), and the Second Temple reception anchor (1 Enoch Parables).

## What's Done (Working Tree, Unstaged)

### Tools (5 changes)

| File | Change |
|---|---|
| `tools/citations.py` | Added `backend.kind` dispatch — Logos (default), `external-epub`, `external-greek-ocr`, `external-pdf`. Each kind has its own loader; whitespace+typography normalization shared. EPUB extractor strips social-DRM watermark. PDF backend uses `pdftotext`. Added `EXTERNAL_RESOURCES_DIR` constant + path-traversal protection. |
| `tools/validate_scholar.py` | Added `PASSAGE_COVERAGE_VOCAB` controlled vocabulary (21 entries: Dan 7 verse-blocks + adjacent + NT cross-refs + 1 En 37-71). Backend-kind dispatch with conditional `LLS:` prefix rule (only required when ≥1 logos-kind citation). Forbid Logos-only fields on external backends. |
| `tools/sweep_citations.py` | Unchanged (works against the new backends transparently via `verify_citation`). |
| `external-resources/greek/extract_pg81_range.sh` | New. `pdftoppm + tesseract grc+lat`. Maps Migne col → PDF page = `(col + 55) / 2`. macOS Leptonica path-quirk worked around by `cd`-ing into cache. |
| `external-resources/greek/ingest_theodoret.sh` | Now legacy. Kept for any future TLG-screenshot workflow on a different patristic resource. |

### Tests (current state)

```
tools/workbench/tests/test_validate_scholar.py        44 tests, all pass
tools/workbench/tests/test_citations.py                16 tests, all pass
tools/workbench/tests/test_article_meta.py              5 tests, all pass
tools/workbench/tests/test_lbxlls_reader.py            20 tests, all pass
```

Run: `pm2 stop study-companion && cd tools/workbench && python3 -m pytest tests/test_validate_scholar.py tests/test_citations.py tests/test_article_meta.py tests/test_lbxlls_reader.py -q && pm2 start study-companion`

### Schema docs

- `docs/schema/citation-schema.md` — added §"backend kind: external-epub", §"external-greek-ocr", §"external-pdf"; §"Scholar-file passage coverage (WS0c-8)" with vocabulary table.
- `docs/research/method-and-limits.md` — §3 rewritten as "Acquired in WS0c expansion" (lists 13 new entries); new §3a "Out of corpus — what remains genuinely missing" (Koch/Plöger German, Hill 2006 Theodoret ET, Wright JVG, Eastern Orthodox, etc.).
- `docs/research/bibliography.md` — added 11 new entries (Calvin, Goldingay, Hartman & DiLella, Young, Beale Use of Daniel, Hamilton, Duguid, Pentecost, Jerome, Lacocque, Menn, Theodoret) plus Anderson ITC noted but unsurveyed.

### External resources (staged, not committed)

```
external-resources/
├── pdfs/
│   ├── Hippolytus-EndTimes.pdf            (37 pp, ANF 5 Salmond — On Christ&Antichrist
│   │                                       + On End of World; NOT the Daniel commentary)
│   ├── Jeromes-Commentary-on-Daniel-BN.pdf (now redundant — Jerome is in Logos as
│   │                                        LLS:JRMSCMMDNL Archer 1958 ET; PDF kept as
│   │                                        backup against Archer translation drift)
│   └── README.md
├── epubs/
│   ├── 9781498221689.epub  (Lacocque, Cascade 2018; ISBN watermark stripped at
│   │                        verifier-time)
│   ├── 9781532643194.epub  (Menn, Resource 2018)
│   └── README.md
└── greek/
    ├── README.md
    ├── extract_pg81_range.sh        (active)
    ├── ingest_theodoret.sh          (legacy)
    ├── theodoret-pg81-dan5_6.txt    (PG 81 cols 1362-1410)
    ├── theodoret-pg81-dan7.txt      (PG 81 cols 1411-1437 — Daniel 7 complete)
    ├── theodoret-pg81-dan11_12.txt  (PG 81 cols 1493-1546)
    ├── theodoret-daniel-pg81-ocr.txt (legacy 100-screenshot OCR; superseded)
    └── migne-pg81-archiveorg/       (123 MB — PG 81 PDF + page index + fts.txt)
```

### Scholar JSONs (17 files)

```
docs/research/scholars/
├── _SURVEY_BRIEFING.md                         (template; passageCoverage[] required)
├── 1-enoch-parables-nickelsburg-vanderkam.json (25 cit, 5 passages, second-temple)
├── beale-use-of-daniel-in-revelation.json      (34 cit w/pp, 17 passages, cross-book)
├── blaising-bock-progressive-dispensationalism.json (22 cit, 6 passages, prog-disp)
├── calvin-daniel.json                          (25 cit, 10 passages, reformed-historic)
├── collins-hermeneia-daniel.json               (15 cit, 10 passages, critical-modern)
├── duguid-rec-daniel.json                      (23 cit w/pp, 14 passages, reformed-cont)
├── durham-revelation.json                      (14 cit, 8 passages, historicist-reform)
├── goldingay-wbc-daniel.json                   (25 cit w/pp, 14 passages, critical-mediating)
├── hamilton-clouds-of-heaven.json              (29 cit w/pp, 15 passages, BT)
├── hartman-dilella-anchor-daniel.json          (23 cit w/pp, 11 passages, critical-Catholic)
├── jerome-commentary-on-daniel.json            (23 cit w/pp, 13 passages, patristic-Latin)
├── lacocque-book-of-daniel.json                (16 cit, 11 passages, continental-Catholic)
├── menn-biblical-eschatology.json              (19 cit, 13 passages, amillennial-eclectic)
├── pentecost-things-to-come.json               (31 cit w/pp, 12 passages, classical-disp)
├── theodoret-pg81-daniel.json                  (22 cit, 10 passages, patristic-Greek)
├── walvoord-daniel.json                        (38 cit, 13 passages, classical-disp)
└── young-prophecy-of-daniel.json               (34 cit w/pp, 12 passages, reformed-cons)

Total: 418 citations across positions[] + crossBookReadings[]
       222 (53.1%) page-bearing
       17 / 17 strict-validate
```

### Reports

- `docs/research/2026-04-24-codex-logos-metadata-design.md` — codex's earlier dylib investigation (already on `main`)
- `docs/research/2026-04-24-citation-verification-report.md` — pre-WS0c sweep
- `docs/research/2026-04-24-ws0-audit-report.md` — earlier audit
- `docs/research/2026-04-24-ws05-6-claim-warrant-audit.md` — WS0.5-6 codex audit
- `docs/research/2026-04-26-citation-verification-report.md` — **current sweep: 426/426 verified**
- `docs/research/2026-04-26-ws0c-corpus-audit.md` — **current codex audit: pass-with-conditions**

### Tasks already on `main` (unaffected)

WS0a-A1, WS0a-A2, WS0a-A3, WS0b (4 surveys), WS0c (8 verifier+sweep), WS0e codex audit
were committed in three commits on `main` (`a426760`, `ee4a77d`, `6e65f12`) at the end
of WS0.5. Everything from WS0.5 forward (including all of WS0c) is uncommitted.

## What Codex Just Flagged (pass-with-conditions)

Full audit at `docs/research/2026-04-26-ws0c-corpus-audit.md`. Headlines:

### Must-fix-before-WS1

1. **~26 supportStatus relabels from `directly-quoted` to `paraphrase-anchored` or
   `summary-inference`.** Pattern: cross-book rows where the quote anchors part of the
   claim but the rationale's full architecture (e.g., a complete Rev 20 sequence, a
   detailed Matt 24 mapping) outruns it. Specific table is in §2 of the audit. Apply
   the same way as WS0.5-6's relabel script (revert any over-application by inspecting
   the audit's per-citation reasons; codex was specific about which citations to relabel
   vs. which whole axes — don't blanket-apply).

2. **Cross-book / passageCoverage mismatches to repair**:
   - **Goldingay Mark 13** — listed in `passageCoverage[]` and as a `crossBookReadings[]`
     entry, but the cross-book entry has zero citations. Either add a citation or remove
     the entry.
   - **LaCocque Rev 13** — the cross-book row is labeled Rev 13 but the quote is
     actually Rev 12:10. Retarget the row to Rev 12 (extending vocabulary) or recite
     against Rev 13 directly.
   - **Walvoord Rev 1** — listed in `passageCoverage[]` but no specific Rev 1
     cross-book row exists. Either add the cross-book entry or remove from coverage.
   - **Theodoret Matt 24** — cross-book row anchored on a too-short Greek phrase.
     Strengthen with a longer OCR quote.

3. **Theodoret OCR quote-quality**: several stored fragments are too short to carry
   the English rationale (codex's tightest critique). Longer Greek quotes — even if
   imperfect OCR — would carry more weight. Optionally add a `frontend.section`-level
   transliteration or translation hint for reader-facing auditability.

4. **Manifest mismatch corrections**:
   - 1 Enoch Parables uses the Logos backend (`LLS:HRMNEIAENCH1B`), not external as I
     told the audit — clarify in the survey briefing template and the audit prompt
     for any future work.
   - Tradition-cluster list in §4 mentions legacy voices (Newsom, Hoekema, Riddlebarger,
     Sproul, Longman, Lucas, Bauckham, Wright) that aren't JSON-backed — they're
     bibliography/narrative-only in the current corpus. Either backfill JSONs for them
     or mark clusters as bibliography-only in `bibliography.md`.

### Nice-to-have

5. Build a small report that cross-checks `passageCoverage[]` against
   `crossBookReadings[].targetPassage` + citations and flags any orphan coverage values
   (no supporting row). Could be a `--coverage-audit` flag on `sweep_citations.py`.
6. Add `notes` field to `summary-inference` citations naming the adjacent articles
   the inference draws on.
7. Fill `Dan 10:1-21` (the one zero-coverage passage) only if WS1 visualizations need
   it; otherwise prune it from the vocabulary.
8. Add one more progressive-dispensational voice (Saucy?) and one more historicist
   or partial-preterist voice (Mauro? Kik? Gentry?) if the pilot will compare
   traditions, not just display poles.
9. Treat 1 Enoch Parables entry explicitly as a *reception-event survey*, not a
   single-author scholar, in downstream labels and UI copy.

## Tasks Remaining in WS0c Queue (Lower Priority)

| # | task | status | est. effort |
|---|------|--------|---|
| 26 | WS0c-9 Aramaic anchor field + Lexham Aramaic Lexicon integration | pending | 3h |
| 23 | WS0c-4 1 Enoch Parables Hermeneia reception entry | done (#23 mismarked? check) | – |
| – | ACCS Daniel anthology (`LLS:ACCSREVOT13`) reception entry | not started | 4h (anthology-shape schema needed) |
| – | RCS Daniel anthology (`LLS:REFORMCOMMOT12`) reception entry | not started | 4h (same) |

## Decision Points for Next Session

1. **Apply the 26 relabels?** Same script approach as WS0.5-6 — read codex's per-citation
   table, apply via Python script, re-sweep, confirm. ~30 min total.
2. **Repair the 4 mismatches?** Each is a small targeted edit. ~30 min total.
3. **Theodoret OCR-quote tightening?** Could be done by re-extracting longer quotes from
   `theodoret-pg81-dan7.txt` for the flagged citations. ~30 min if done by hand; could
   dispatch a focused subagent.
4. **Backfill legacy-voice JSONs (Hoekema, Riddlebarger, Newsom, Sproul, Longman,
   Lucas, Bauckham, Wright)?** They're already extensively cited in the legacy
   2026-04-23 narrative survey. If WS1 needs them as JSON, dispatch 8 more parallel
   surveys. ~45 min wall time.
5. **Anthology reception entries (ACCS, RCS)?** Requires a schema variant for
   per-extract anthologies (one file = many patristic/Reformation voices). Not blocking
   pilot; defer if pilot is moving forward.
6. **Commit?** WS0c expansion is much larger than WS0/WS0.5 was. A clean commit plan
   is probably 4–5 commits:
   - `feat(citations): backend.kind dispatch + external-epub/greek-ocr/pdf backends + tests`
   - `feat(validator): passageCoverage[] + backend-kind dispatch + new tests`
   - `feat(extract): external-resources/greek/extract_pg81_range.sh + Theodoret PG 81 source`
   - `docs(research): WS0c scholar surveys (12 new files + bibliography + method updates)`
   - `docs(research): WS0c codex audit + verification report`
   First commit (citations backend) is the prerequisite for everything else.

## Standing Project Conventions

- **PM2**: never `pm2 kill`/`stop all`/`delete all` — other apps share. Stop/start
  `study-companion` only if running pytest (port 5111 conflict).
- **Logos reader**: `tools/LogosReader` builds with `dotnet 8` (export `PATH` +
  `DOTNET_ROOT` first). Test files use `LogosBatchReader` for speed.
- **macOS Leptonica path bug**: tesseract on absolute paths under `/Volumes/External`
  fails with "Error in fopenReadStream". `cd` into the cache dir before invocation.
- **Codex CLI**: `codex exec --dangerously-bypass-approvals-and-sandbox
  --skip-git-repo-check -c model_reasoning_effort=high < prompt.txt > log.txt 2>&1`.
  **Do NOT use `--output-last-message`** — it clobbers any file codex writes during the
  run. Codex writes its outputs directly via the Write tool to the path you specify in
  the prompt.

## Standing Subagent Conventions

- Briefing at `docs/research/scholars/_SURVEY_BRIEFING.md` is the source of truth for
  scholar surveys; subagents read it first.
- `general-purpose` agent type for surveys.
- Wave-of-5 parallel dispatch worked well; wave-of-9 was OK but pushed Logos reader
  contention. Don't exceed ~5 concurrent surveys per dispatch unless surveys are tiny.
- Background-mode dispatch (Agent with `run_in_background: true`) frees the controller
  to do other work; notifications land when each agent finishes. Don't poll.

## Resources Available But Not Yet Surveyed

These are in the library or staged in `external-resources/`, not yet surveyed:

| Resource | LLS / path | Why not yet |
|---|---|---|
| Anderson ITC Daniel | `LLS:ITC21DAN` | low priority — older critical, similar to Hartman/DiLella |
| Pace Smyth & Helwys Daniel | `LLS:SHC27DA` | moderate critical, Baptist — could fill out critical-mediating cluster |
| Seow Westminster Bible Companion Daniel | `LLS:WBCS27DA` | moderate critical |
| Davies Sheffield Daniel | `LLS:SHEFFCL27DA` | critical-introductory |
| Harman EP Study Commentary Daniel | `LLS:EVPRESS27DA` | Reformed-evangelical |
| Schwab Gospel of OT: Daniel | `LLS:GSPLOTDANIEL` | Reformed-pastoral |
| Greidanus Preaching Christ from Daniel | `LLS:PRCHNGCHRSTDNL` | Reformed-typological-homiletic |
| Akin Christ-Centered Daniel | `LLS:9780805496895` | homiletical |
| Helm God's Word for You Daniel | `LLS:GWFY27DA` | popular-expository |
| Fyall Focus on the Bible Daniel | `LLS:FOBC27DA` | Reformed-expository |
| Davis BST Daniel | `LLS:BST27DA` | Reformed-pastoral (legacy first-pass — already cited narratively) |
| Mangano College Press Daniel | `LLS:CPC_ESTHDAN` | moderate evangelical |
| ACCS OT XIII (Ezekiel/Daniel) | `LLS:ACCSREVOT13` | patristic anthology — needs anthology-shape schema |
| RCS OT XII (Ezekiel/Daniel) | `LLS:REFORMCOMMOT12` | Reformation anthology — same |
| Hippolytus *Commentary on Daniel* (CCEL ANF 5) | not yet fetched | requires CCEL fetch path; not blocking |
| Theodoret Hill 2006 ET (WGRW 7) | not obtainable online | interlibrary loan needed |
| Wright *Jesus and the Victory of God* | not in library | acquisition needed if Wright depth wanted |
| Klaus Koch / Otto Plöger | German-only, not in library | acquisition + translation needed |
| Lexham Aramaic Lexicon | `LLS:FBARCLEX` | tooling integration pending (WS0c-9) |

## Where the Pilot Now Stands

Daniel 7 pilot's primary topics (Four Beasts, Little Horn, Son of Man) are covered by
multiple primary voices in every tradition cluster. Adjacent topics (Saints, Ancient of
Days) and adjacent passages (Dan 2, Dan 8, Dan 9, Dan 11/12, Rev 13/17/20, Matt 24,
1 En 37–71) all have ≥3 surveyed scholars except Dan 9:1–19 (3 — borderline thin),
1 En 37–71 (3 — borderline), and Dan 10:1–21 (0 — genuine gap).

Per-axis coverage (each pilot axis A/B/C/D/E/F/G/H/I/J/K/L/N/O has ≥4 voices except G —
rapture timing — which is cleanly Walvoord+Pentecost only because no other tradition
engages it substantively).

WS1 ingestion is not blocked by data; it's blocked by the 26 cross-book relabels +
4 mismatches above, which take ~1 hour of focused work to clean.

## Next-Session Recommended Order

1. Read `docs/research/2026-04-26-ws0c-corpus-audit.md` (200 lines).
2. Apply codex relabels (script approach — same as WS0.5-6).
3. Repair the 4 coverage/cross-book mismatches.
4. Re-run sweep + validator.
5. Commit the WS0c expansion as 4–5 logical commits.
6. Decide: backfill 8 legacy-voice JSONs, or mark clusters as bibliography-only.
7. Decide: ACCS + RCS anthology integration now or defer.
8. Decide: Aramaic-anchors schema work, or skip until WS1 needs it.
9. WS1 only after the relabels land.

## File-Path Cheat Sheet

```
spec:                     docs/superpowers/specs/2026-04-23-visual-theology-architecture-design.md
schema:                   docs/schema/citation-schema.md
method/limits:            docs/research/method-and-limits.md
bibliography:             docs/research/bibliography.md
sweep report:             docs/research/2026-04-26-citation-verification-report.md
codex audit:              docs/research/2026-04-26-ws0c-corpus-audit.md
this handoff:             docs/SESSION-HANDOFF-WS0c-EXPANSION.md (you are here)

scholars dir:             docs/research/scholars/
survey briefing:          docs/research/scholars/_SURVEY_BRIEFING.md
external resources:       external-resources/{pdfs,epubs,greek}/
PG 81 PDF source:         external-resources/greek/migne-pg81-archiveorg/
PG 81 extract tool:       external-resources/greek/extract_pg81_range.sh

reader:                   tools/LogosReader/Program.cs (article-meta cmd)
study orchestrator:       tools/study.py (get_article_meta, read_article_text)
citations:                tools/citations.py (build_citation, verify_citation, sha256_of)
validator:                tools/validate_scholar.py
sweep:                    tools/sweep_citations.py

tests:                    tools/workbench/tests/test_{validate_scholar,citations,article_meta,lbxlls_reader}.py
```

## Memory Pointers

- Auto-memory system at `~/.claude/projects/-Volumes-External-Logos4/memory/`. Active
  priority memo is `project_visual_theology_build.md`; it should be updated after the
  next session's commits to point at this handoff and note the WS0c relabel work as
  the active task.
- This handoff doc supersedes `docs/SESSION-HANDOFF-VISUAL-THEOLOGY-WS0.md` for
  visual-theology research. The WS0 handoff can stay on disk as historical record.
