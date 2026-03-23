# Session Handoff: Interlinear Fix + BDAG Integration

**Date:** 2026-03-23
**Status:** Segfault fixed, BDAG integrated, conversation phase verified. 118 tests passing.

## What Was Done This Session

### Critical Fix: NativeLogosResourceIndexer Segfault (RESOLVED)
Root cause found via disassembly: `NativeLogosResourceIndexer_New` takes **7 parameters** (title, languageStr, callback, bool×4), not 2. The C# P/Invoke only declared 2 params, so the callback pointer was read as the language string → garbage callback → SIGSEGV.

Also fixed: `AddResourceJump` delegate was 11 params but should be 13 params (same as AddReference), verified via demangled C++ constructor symbols.

**Result**: Indexer now works. 1179 English words extracted from Romans 1. However, the ProcessReverseInterlinearIndexData callback (morphology/Strong's/Louw-Nida) is never called — requires the full `Logos4Indexer` pipeline from `libSinaiBookBuilderAndIndexer.dylib`, which is too complex to invoke directly.

### BDAG Integration (COMPLETE)
- Added BDAG.logos4 to NT_LEXICONS (first position — gold standard)
- Fixed resource_index.py to filter BDAG to only R.xxx entries (skipping 2300+ abbreviation articles)
- Fixed Unicode NFC normalization mismatch: BDAG text uses decomposed Greek (ο+combining accent) but queries use precomposed (ό) — SQLite byte comparison was failing
- 8110 entries indexed, all major Greek words lookup correctly (ἀγάπη, πίστις, λόγος, θεός, χάρις, δικαιοσύνη, σταυρός)
- Updated system prompt references in both `build_system_prompt` and `build_study_prompt`

### Conversation Phase Verification
- Verified all 25 key elements of the 16-step workflow in the study system prompt
- Steps 9-10-12: Volume triaging present ("TRIAGE THE VOLUME", "PREVENT RABBIT HOLES")
- Step 11: Confessional docs surfacing present ("PROACTIVELY SURFACE", Westminster references)
- Steps 13-14: Sermon construction push present ("PUSH HARDEST HERE", "SHORT-CIRCUITS", all 8 substeps of step 13 encoded)
- Card→conversation transition tested end-to-end via curl
- Server restarted with all changes

## Test Status
118 tests passing across 14 test files:
```bash
cd /Volumes/External/Logos4/tools/workbench
python3 -m pytest tests/ -v
```

## Key Files Changed

| File | What Changed |
|------|-------------|
| `tools/LogosReader/Program.cs` | Fixed NativeLogosResourceIndexer_New (7 params), AddResourceJump delegate (13 params), word extraction with charLen, cleaned up debug logging |
| `tools/resource_index.py` | BDAG R.xxx filter, Unicode NFC normalization for headwords and queries |
| `tools/workbench/companion_tools.py` | Added BDAG to NT_LEXICONS, updated tool description |
| `tools/workbench/companion_agent.py` | Updated BDAG references in both system prompts |

## What the Next Session Should Do

### Priority 1: Live Conversation Phase Testing
The system prompt is verified structurally, but needs live testing with Claude to confirm:
- Does the AI actually triage volume at steps 9-10-12?
- Does it proactively surface confessional docs at step 11?
- Does it push through sermon construction at steps 13-14?
- Does illustration discipline coaching work?
Test by creating a study session for a real sermon passage and walking through the conversation.

### Priority 2: MorphGNT Integration (Optional Enhancement)
The Haiku fallback for word-level morphology works well enough. For authoritative data:
- Load MorphGNT data into a SQLite cache
- Provide lemma, morphology code (V-AAI-3S style), Strong's number for every GNT word
- Much cheaper than per-word Haiku calls and fully authoritative

### Priority 3: Encrypted Dataset Exploration
The `Lemmas.lbslms` + `WordSenses.lbswsd` datasets together might provide lemma + part-of-speech + Louw-Nida data that supplements MorphGNT.

## Server
```bash
pm2 restart sermon-study
pm2 logs sermon-study
```

## Environment
```bash
export PATH="/opt/homebrew/opt/dotnet@8/bin:/opt/homebrew/bin:$PATH"
export DOTNET_ROOT="/opt/homebrew/opt/dotnet@8/libexec"
```
