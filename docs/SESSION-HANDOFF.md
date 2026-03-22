# Session Handoff: Library Tools Supercharge

**Date:** 2026-03-22
**Status:** Plan written and reviewed. Ready to implement.

## What We're Building

Three-phase upgrade to make the sermon companion's library access actually work:

1. **Fix broken lexicon/grammar search** — the current search returns garbage (abbreviation entries like `ABBR.MID` instead of Wallace's actual voice chapter) because article IDs are transliterated Latin, not Greek. Solution: build a one-time index that reads article headwords.

2. **Unlock encrypted volume datasets** — 150+ `.lbs*` files contain pre-indexed study tool data (figurative language, grammatical constructions, cross-references, biblical places/people/things, theology xrefs, preaching themes). These are encrypted SQLite databases accessed via the EncryptedVolume API in libSinaiInterop.dylib.

3. **Wire up 30+ tools** into the companion agent so it can be a real graduate assistant.

## Implementation Plan

**Path:** `docs/superpowers/plans/2026-03-22-library-tools-supercharge.md`

### 7 Tasks, 3 Phases

| Task | Phase | What | Status |
|------|-------|------|--------|
| 1 | Fix Search | Build `resource_index.py` — lemma→article index | Not started |
| 2 | Fix Search | Rewrite `_search_lexicon()` to use index | Not started |
| 3 | Encrypted Volume | Add EncryptedVolume + sqlite3 P/Invoke to LogosReader | Not started |
| 4 | Encrypted Volume | Add `query_dataset()` Python wrapper | Not started |
| 5 | Encrypted Volume | Discover actual database schemas | Not started |
| 6 | Wire Tools | Create `dataset_tools.py` with 16 query functions | Not started |
| 7 | Wire Tools | Wire tools into companion agent + system prompt | Not started |

**Tasks 1-2 and 3-4 can run in parallel** (different files, no dependencies).

### Key Technical Decisions Already Made

1. **libsqlite3-logos.dylib** (confirmed exists at 824KB) provides sqlite3 C API for raw handle queries
2. **`Marshal.PtrToStringUTF8`** (not `PtrToStringAnsi`) for Greek/Hebrew data from sqlite3
3. **SQL quoting**: Python double-quotes the SQL argument; `ParseCommandLine` treats it as one token
4. **Batch loop integration**: `query-db` and `volume-info` are early-exit cases in the switch that set `mode = "__skip__"` to bypass the CTitle path
5. **Shared batch reader**: `dataset_tools.py` reuses study.py's singleton (no duplicate process)
6. **Wallace chapter mapping**: approximate, with verification substep in Task 1

## What NOT to Touch

- `LogosReader/Program.cs` existing commands (read, list, toc, etc.) — they work
- `logos_batch.py` existing methods — they work
- `study.py` existing functions — they work
- Old workbench routes — they still serve the companion UI

## Environment

```bash
export PATH="/opt/homebrew/opt/dotnet@8/bin:$PATH"
export DOTNET_ROOT="/opt/homebrew/opt/dotnet@8/libexec"
cd /Volumes/External/Logos4
```

## Key Files

| Purpose | Path |
|---------|------|
| **Implementation Plan** | `docs/superpowers/plans/2026-03-22-library-tools-supercharge.md` |
| **Design Spec** | `docs/specs/2026-03-21-sermon-companion-design.md` |
| **EncryptedVolume Research** | `docs/plans/2026-03-10-encrypted-volume-api.md` |
| **Companion Tools** | `tools/workbench/companion_tools.py` |
| **LogosReader** | `tools/LogosReader/Program.cs` |
| **Batch Reader** | `tools/logos_batch.py` |
| **Study Orchestrator** | `tools/study.py` |

## What the Next Session Should Do

1. Read the plan at `docs/superpowers/plans/2026-03-22-library-tools-supercharge.md`
2. Execute tasks using `superpowers:subagent-driven-development` or `superpowers:executing-plans`
3. Tasks 1-2 and 3-4 can be parallelized
4. Task 5 (schema discovery) is research — run the SQL queries, document what you find
5. Tasks 6-7 depend on Task 5's schema findings — update SQL queries with real column names
