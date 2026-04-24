# Plan: `.lbxlls` Resource Support (Fix 12)

Date: 2026-04-24
Status: Ready for subagent-driven-development execution
Depends on: none (codex investigation complete — design at `docs/research/2026-04-24-codex-lbxlls-design.md`)

## Purpose

Unblock three currently-unreadable Logos resources that are critical for the visual theology project:

- Collins, *Daniel* (Hermeneia, 1993) — `HRMNEIA27DA.lbxlls` — modern critical Daniel standard
- Walvoord, *Daniel: The Key to Prophetic Revelation* — `GS_WALV_DANIEL.lbxlls` — classical dispensational Daniel
- Blaising & Bock, *Progressive Dispensationalism* — `PROGDISPNM.lbxlls` — progressive dispensational reference

## Context

Codex's investigation (archived at `docs/research/2026-04-24-codex-lbxlls-design.md`) established that the **existing native loader in `libSinaiInterop.dylib` already opens `.lbxlls` files** via `SinaiInterop_LoadTitleWithoutDataTypeOptions`. Direct verification on 2026-04-24:

```python
# Passing the full .lbxlls path to study.get_resource_articles() works:
HRMNEIA27DA.lbxlls → 9,431 articles
GS_WALV_DANIEL.lbxlls →   988 articles
PROGDISPNM.lbxlls  →     290 articles
```

The "fix" is caller-level. Two concrete issues:

1. **Bare-stem filename resolution defaults to `.logos4`.** `tools/study.py:1896` in `resolve_bible_files()` does `resolved.append(name if "." in name else name + ".logos4")`. When a lookup misses the Bibles-cache and the user passed a bare stem, `.logos4` is force-appended. `.lbxlls` resources are invisible to bare-stem lookups.
2. **Commentary discovery uses a narrow superset LIKE pattern.** `tools/study.py:356` produces `"bible.{book}%"`. Collins Hermeneia Daniel has `ReferenceSupersets = bible+bhs.27` (the `+bhs` infix). The current pattern won't match, so Hermeneia is silently filtered out of `find_commentaries_for_ref('Daniel ...')`.

A separate decision for `PROGDISPNM.lbxlls`: catalog type is `text.monograph` (not `text.monograph.commentary.bible`). Progressive Dispensationalism is not a commentary; it shouldn't surface in commentary-search. That's out of scope for this plan.

## Scope Boundaries

**In scope:**
- Caller-level audit of filename-defaulting code.
- Extension-agnostic bare-stem resolution.
- Broadened superset matching for commentary discovery (the `bible+bhs.*` case).
- Automated tests covering the three blocked resources.

**Out of scope:**
- Reverse-engineering the `.lbxlls` container format (not needed — native loader already handles it).
- Changes to `tools/LogosReader/Program.cs` (the C# side is fine; `TryGetResourceIdAndVersion` failure is already non-fatal in the current code path).
- Promoting monographs (e.g., `PROGDISPNM`) into commentary-search (separate policy decision).

## Tasks

Each task below is a self-contained unit for subagent-driven-development with TDD, spec-compliance review, and code-quality review. Execute in order; later tasks depend on earlier ones.

### Task 1: Baseline test suite

**Goal.** Before changing code, capture current behavior and prove the bug reproducibly.

**Files.** Create `tools/workbench/tests/test_lbxlls_reader.py`.

**Spec:**
1. One test that confirms bare-stem `.logos4` resolution still works (regression guard). Use `EEC27DA` as the canonical example.
2. One test per blocked resource that **fails in current code** (marked `xfail` with reason="Fix 12 not yet implemented"):
   - `HRMNEIA27DA` (Collins Hermeneia Daniel)
   - `GS_WALV_DANIEL` (Walvoord Daniel)
   - `PROGDISPNM` (Blaising & Bock)
   Each test should attempt to open the resource via a bare stem (no extension) using whichever study.py function is called by downstream code for resource lookup. If the function is `resolve_bible_files`, use that. If no existing function resolves by bare stem, write the test against `get_resource_file(resource_id)` and `get_resource_articles(path)`.
3. One test that confirms `get_resource_articles` with the **full `.lbxlls` path** succeeds (proves native loader already works). Use all three blocked resources.

**Acceptance:** Tests in category 1 and 3 pass; tests in category 2 xfail with a clear reason string. Committed with a commit message that says "baseline tests for Fix 12."

**Tests to run:**
```bash
cd tools/workbench && python3 -m pytest tests/test_lbxlls_reader.py -v
```

### Task 2: Extension-agnostic bare-stem resolution

**Goal.** Fix `resolve_bible_files` and any similar pattern so bare-stem lookups find `.lbxlls` resources.

**Files.**
- `tools/study.py` — `resolve_bible_files` (line 1877), specifically the fallback at line 1896.
- Any other callsite the investigation surfaces (grep: `name + "\.logos4"`, `stem + "\.logos4"`, `+ "\.logos4"`).

**Spec:**
1. When a bare stem doesn't match any cached Bible entry, **look it up via `ResourceManager.Resources.Location`** keyed off `ResourceId` or a filename-derived key. If found, append the actual extension. If not found, try both `.logos4` and `.lbxlls` and return whichever resolves.
2. Preserve current behavior for any input that already contains `.` (an extension is respected as-is).
3. Do NOT remove the existing `.logos4` / `.lbxlls` normalization patterns elsewhere (lines 736, 827, 1885, 1888, 1986). Those are correct and symmetric.

**Acceptance:**
- `xfail` tests from Task 1 now pass (remove the `xfail` marker).
- Existing tests continue to pass — run the full workbench test suite and confirm no regressions:
```bash
cd tools/workbench && python3 -m pytest tests/ -v
```

**Non-goals:** No new CLI flags. No help-text changes yet. No behavior change for already-working resources.

### Task 3: Broadened commentary superset matching

**Goal.** Surface Collins Hermeneia Daniel (and any other resource with a `+bhs`, `+lxx`, `+sblgnt`, or similar infix in `ReferenceSupersets`) in `find_commentaries_for_ref('Daniel ...')`.

**Files.**
- `tools/study.py:354` — `ref_to_logos_superset_pattern` and its caller at line 456.

**Spec:**
1. Inspect the distribution of `ReferenceSupersets` values in the catalog. Identify all non-`bible.` prefixes that actually occur (e.g., `bible+bhs.`, `bible+lxx.`, `bible+sblgnt.`). Query:
   ```sql
   SELECT DISTINCT substr(ReferenceSupersets, 1, 15), COUNT(*)
   FROM Records
   WHERE Type = 'text.monograph.commentary.bible' AND Availability = 2
   GROUP BY substr(ReferenceSupersets, 1, 15)
   ORDER BY COUNT(*) DESC;
   ```
   (Run in the task — the exact set of prefixes shapes the fix.)
2. Change `ref_to_logos_superset_pattern` (or the query) to match ANY `bible*.{book}%` variant. Either make the LIKE pattern `bible%.{book}%` OR run multiple queries and union results.
3. Verify `ref_covers_passage` still correctly handles the resulting superset strings — it already parses `superset_str` without assuming a specific prefix.

**Tests:**
- Extend `test_lbxlls_reader.py` with a test that `find_commentaries_for_ref` with `Daniel 7:1` surfaces Collins Hermeneia (`HRMNEIA27DA`).
- Regression: existing `find_commentaries_for_ref` behavior for `.logos4` commentaries (e.g., EEC, NAC, ICC, TOTC) unchanged for Daniel and also for at least one NT reference (Romans 3:10) as regression guard.

**Acceptance:**
- New test passes: Collins Hermeneia surfaces for Daniel 7.
- Existing commentary-discovery tests pass.

### Task 4: End-to-end verification and smoke scripts

**Goal.** Prove the full stack (Python → reader → article content) works for the three blocked resources via the natural entry points callers actually use.

**Files.**
- `tools/workbench/tests/test_lbxlls_reader.py` (extend).
- Optionally update the hardening-plan smoke script section.

**Spec:**
1. Extend the test file with an end-to-end test per blocked resource:
   - Resolve by bare stem (Task 2 behavior)
   - `get_resource_articles` returns a non-empty article list
   - `read_article_text(path, 0)` returns non-empty text content
   - For Daniel commentaries (Collins, Walvoord): `find_commentary_section(path, parse_reference('Daniel 7:7'))` returns a non-empty result
2. Update `docs/plans/2026-04-23-logos-reader-hardening.md` Fix 12 section: change "Detailed implementation plan" reference from placeholder to this file, and mark Fix 12 as implemented (leave the test-case list as acceptance criteria).

**Acceptance:**
- All tests in `test_lbxlls_reader.py` pass.
- Smoke script (from the hardening plan) passes for all known-good `.logos4` resources AND for the three `.lbxlls` resources.
- Hardening plan updated to reflect completion of Fix 12.

**Final verification:**
```bash
cd tools/workbench && python3 -m pytest tests/test_lbxlls_reader.py -v
cd tools/workbench && python3 -m pytest tests/ -v   # regression guard
```

## Completion Criteria

- `tests/test_lbxlls_reader.py` exists with at least 12 test cases (3 blocked-resources × 4 behaviors: bare-stem resolution, article list, article text, commentary-section lookup).
- All existing workbench tests pass.
- `find_commentaries_for_ref('Daniel 7:1')` surfaces Collins Hermeneia.
- Hardening plan Fix 12 marked complete.
- One or more commits with clear, scope-bounded messages; no drive-by refactors.

## Review Targets

Per subagent-driven-development, each task goes through:
- **Spec-compliance review** — every deliverable in the Spec section is implemented; nothing extra; nothing missing.
- **Code-quality review** — no magic constants in filenames (use `ResourceManager.Resources.Location` lookups wherever possible); clear commit messages; tests readable; no coupling bumps.
