# Session Handoff: Visual Theology — WS0 Research Hardening

**Date:** 2026-04-24
**Status:** Plan approved, ready to execute. WS0 (research-hardening) must complete before any visual-theology implementation (WS1+) begins.
**Preceded by:** Fix 12 implementation (committed, 20 tests green)
**Replaces:** the coaching-bridge handoff for directing visual-theology work

## One-Minute Context

Bryan is a Reformed Presbyterian pastor building a repeatable visual-theology site generator. First site (Romans 3, already live at tendflock.github.io/Romans3) was a single-thesis study. Second target is Daniel 7 pilot — contentious multi-tradition material where the "factually accurate, verifiable, non-strawman" standard matters.

Earlier in this session we discovered the research backbone had four structural gaps. User directive: **do WS0 before building visuals.** Also bought Durham's Revelation commentary. Also approved dual-citation format (backend article numbers + frontend scholarly refs with page numbers) and sha256 quote hashes for tamper evidence.

## What's Done (Committed)

**Architecture spec v2:** `docs/superpowers/specs/2026-04-23-visual-theology-architecture-design.md`
- 5-layer data model (axes, readingRules, scholars-primary, traditions, topics)
- 16 axes (14 content + 2 meta); Daniel 7 pilot invokes 11
- Compositional positions (basePosition + fulfillmentMode + extendsTo + scope)
- Commitment field (strong/moderate/tentative) separate from confidence tiers
- Editorial charter adds 3 voice habits: name-the-kind-of-disagreement, pastoral-de-escalation, text/inference/system distinction
- Pilot scope: 3 topics (Four Beasts, Little Horn, Son of Man); Saints + Ancient of Days fold in
- Signature motion: branch-and-lock (user toggles fourth-kingdom decision, downstream readings re-route)
- Durham added to historicist-Reformation tradition primary sources

**Research doc v2:** `docs/research/2026-04-23-daniel-interpretive-taxonomy-survey.md` — covers 29 library resources across 4 streams (Daniel commentaries, Revelation commentaries, biblical theology, systematic eschatology).

**Codex creative review:** `docs/research/2026-04-24-codex-review-visual-theology-spec.md` — integrated via 12 spec revisions.

**Fix 12 (.lbxlls reader):** 9 commits `84a6466..4e13bed`. Collins Hermeneia Daniel (9,431 articles), Walvoord Daniel (988), Blaising & Bock *Progressive Dispensationalism* (290) now readable. 20 tests pass. Commentary discovery broadened to surface Collins for Daniel 7. Codex `.lbxlls` design at `docs/research/2026-04-24-codex-lbxlls-design.md`.

**Hardening plan:** `docs/plans/2026-04-23-logos-reader-hardening.md` — Fix 11 (cataloged-but-not-installed), Fix 12 (implemented), Fix 13-16 (PR-review fallout for pre-existing silent-failure risks).

**Durham installed:** `LLS:COMMREVDURHAM` at `.../Resources/COMMREVDURHAM.logos4`, 169 articles, verified readable.

## Why WS0 Is Required

Four foundation gaps that disqualify the current state from "factually accurate / verifiable / non-strawman":

1. **Three primary voices unsurveyed.** Collins Hermeneia (critical-modern Daniel anchor), Walvoord (classical dispensational anchor), Blaising & Bock (progressive dispensational) — all just became readable with Fix 12, none incorporated into research doc. Classical dispensationalism for Daniel is currently a strawman (we only have Patterson on Revelation).
2. **Zero cross-verification performed.** Every citation came from subagents; none independently spot-checked. Citations are claims, not proofs.
3. **Citation format insufficient for scholarly credibility.** Current format = `{resource, logosArticleNum, quote}`. Logos article numbers are internal ordinals, not page numbers. A scholar with the physical book can't find "article 4716."
4. **Durham/Mede/Newton historicist content referenced but not ingested.** Durham just got bought (solves the tradition gap) but needs surveying.

## WS0 Plan — 10 Tracked Tasks

See `TaskList` tool for current state. Task IDs 18-27.

```
WS0a-A1 (#18)  →  WS0a-A2 (#19)  →  WS0a-A3 (#20) schema locked
                                          ↓
                          ┌────────┬──────┴──────┬────────┐
                      Collins   Walvoord      B&B     Durham
                       (#21)     (#22)       (#23)    (#24)
                          └────────┴──────┬──────┴────────┘
                                          ↓
                                   WS0c tool (#25, parallel build)
                                          ↓
                                   Run verifier (#26)
                                          ↓
                                   WS0e codex audit (#27)
```

### WS0a — Dual-citation infrastructure (gates everything)

**#18 — Codex investigation.** Dispatch codex to map `libSinaiInterop.dylib` exports: page numbers, native section IDs (R48.2-style stable IDs), section headings. Prompt template in spec's "Research Workflow" section. Output to `/tmp/logos_metadata_design.md`.

**#19 — Reader extension.** Based on #18 findings, extend `tools/LogosReader/Program.cs` + `tools/study.py` to return articles with full metadata. Via subagent-driven-development (spec + quality review per task).

**#20 — Canonical citation schema.**
```json
{
  "backend": {
    "resourceId": "LLS:RFRMDSYSTH04",
    "logosArticleNum": 4716,
    "nativeSectionId": "R48.2"
  },
  "frontend": {
    "author": "Beeke & Smalley",
    "title": "Reformed Systematic Theology, Vol. 4: Church and Last Things",
    "section": "§R48.2 — The Structure of Inaugurated Eschatology",
    "page": 492,
    "citationString": "Beeke & Smalley, RST 4.27.R48.2 (p. 492)"
  },
  "quote": {
    "text": "Inaugurated eschatology implies that eschatology has indeed begun, but is by no means finished.",
    "sha256": "..."
  }
}
```
User approved: **capture both articleNum and sectionId** (#1 decision), **include sha256 quote hash** (#2 decision).

### WS0b — Four parallel research subagents (after WS0a)

Each produces `docs/research/scholars/{id}.json` in the new schema:

- **#21 Collins Hermeneia Daniel** — critical-modern anchor
- **#22 Walvoord Daniel** — classical dispensational anchor (most urgent — biggest strawman risk without him)
- **#23 Blaising & Bock Progressive Dispensationalism** — progressive dispensational anchor, distinct from classical
- **#24 Durham Revelation** — historicist-Reformation anchor, Scottish Covenanter primary voice

Subagents dispatch in a single message for true parallelism. Each needs: resource path, 16-axis taxonomy reference, dual-citation schema.

### WS0c — Verifier + sweep

- **#25** Build `citation_verifier` Python tool. Takes a dual-citation JSON, opens the resource, confirms quote appears in article with normalized-whitespace matching. Returns `verified / partial / quote-not-found / resource-unreadable`.
- **#26** Run the tool across every citation (existing research doc + new WS0b scholars). Output: `docs/research/2026-04-24-citation-verification-report.md`. Any non-verifying citation gets flagged for re-extraction.

### WS0e — Final gate

- **#27** Codex audits hardened research + verification report. Checks: every tradition has ≥1 primary-voice citation; no strawman wording; all citations verifiable; intra-tradition divergences documented.

## Running Services (Don't Kill)

PM2 processes under `family` user share a single pm2 instance:
- `study-companion` (Logos4 Flask app, no port bound in normal state) — **stop before running pytest** (conftest port-5111 conflict), restart after
- `couple-companion` (8000), `mighty-oaks` (3000), `adhd-align` (5003) — leave alone

Commands: `pm2 stop study-companion`, `pm2 start study-companion`, `pm2 save`.

## Environment Setup

```bash
export PATH="/opt/homebrew/opt/dotnet@8/bin:$PATH"
export DOTNET_ROOT="/opt/homebrew/opt/dotnet@8/libexec"
```

## Key File Paths

- **Spec:** `docs/superpowers/specs/2026-04-23-visual-theology-architecture-design.md`
- **Research:** `docs/research/2026-04-23-daniel-interpretive-taxonomy-survey.md`
- **Romans 3 template:** `/Users/family/Downloads/_push 2/` (STYLE.md + CLAUDE.md + data.js pattern)
- **Hardening plan:** `docs/plans/2026-04-23-logos-reader-hardening.md`
- **Logos reader:** `tools/LogosReader/Program.cs` (C#) + `tools/study.py` (Python orchestrator)
- **Resources dir:** `/Users/family/Library/Application Support/Logos4/Data/e3txalek.5iq/ResourceManager/Resources/`
- **Catalog DBs:** `Data/e3txalek.5iq/LibraryCatalog/catalog.db` + `ResourceManager/ResourceManager.db`

## Collaborators

- **Bryan** — owner, theological compass, final edit, pew-reader representative.
- **Codex** (CLI at `/opt/homebrew/bin/codex`) — adversarial reviewer + design/UX collaborator + `.lbxlls`-style investigations. Use `codex exec --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check -c model_reasoning_effort=high --output-last-message FILE < prompt.txt`. Pass prompts via stdin from a file; stdin-less invocations hang.
- **Subagents** — bounded research + implementation tasks. Use `general-purpose` type; provide environment setup and PM2 quirk in every prompt.

## Starting the Next Session

1. Load `TaskList` — all 10 WS0 tasks are there with dependencies.
2. Read this handoff.
3. Read `docs/research/2026-04-23-daniel-interpretive-taxonomy-survey.md` §"Second-Pass Survey (2026-04-24)" for the 16-axis taxonomy reference.
4. Start with task #18 (codex metadata investigation). Dispatch codex with the investigation prompt; background task; move on to #19 planning while it runs.

## Decisions Already Made (Don't Re-litigate)

- Pilot: Daniel 7 with 3 topics (Four Beasts, Little Horn, Son of Man).
- Data model: scholars-primary with traditions as cluster tags.
- Citation format: dual (backend articleNum + sectionId, frontend page + citationString, sha256 hash).
- Durham: acquired in Logos; primary historicist-Reformation source.
- No per-tradition color; color reserved for argument role or chapter identity.
- Signature motion: branch-and-lock (not back-absorption).
- `.lbxlls` reader issue: resolved (Fix 12 complete).
