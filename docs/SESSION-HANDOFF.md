# Session Handoff: Hybrid Card→Conversation Study UI

**Date:** 2026-03-23
**Status:** Hybrid UI built and deployed. Word-level morphology from Logos blocked by native API crash — Haiku fallback in place.

## What Was Done This Session

### Major Breakthrough: Driver Version Update
Updated LogosReader driver version from `2019-05-26` to `2025-05-27`, unlocking:
- **All 7 study bibles** (ESV SB, Ancient Faith, Reformation, FSB, Geneva Notes, NIV Cultural BG, NIVBT SB)
- **BDAG** (the gold-standard NT Greek lexicon)
- Fixed navindex matching for `bible+version` prefix format

### Hybrid Study UI (BUILT AND DEPLOYED)
Built the complete hybrid `/study/` UI:

1. **4 card phases** (Bryan drives, AI quiet):
   - Prayer — textarea for Bryan's prayer
   - Read & Translate — side-by-side: THGNT/BHS on left, translation textarea on right
   - Digestion — pray through text phrase by phrase
   - Study Bible Consultation — tabbed view of 7 study bibles with star annotations + notepad

2. **Conversation phase** (AI as interlocutor, phases 6-16):
   - System prompt encodes Bryan's full 16-step Christ-Centered Sermon Prep workflow
   - Phase-aware coaching: triages volume at steps 9-10-12, proactively surfaces confessional docs at step 11, pushes hardest at steps 13-14 (sermon construction)
   - Card work (prayer, translation, digestion, starred study bible passages, notepad) feeds into conversation context

3. **Features**:
   - Click-to-parse Greek/Hebrew words (Haiku fallback — see below)
   - Pause/resume session clock
   - Auto-save textarea content (resumes on refresh)
   - Star annotations on study bible text with notepad
   - Outline sidebar throughout
   - Session resume from front page

### Word-Level Morphology (PARTIALLY DONE)
- **Working**: Click any Greek word → popup shows lemma, gloss, parsing via Claude Haiku call (cached per word)
- **Blocked**: Getting authoritative Logos morphology data. The ESV.logos4 file HAS the data (10 interlinear columns: Surface, Manuscript, Lemma, Root, Morphology, Strong's, Louw-Nida). But `NativeLogosResourceIndexer_IndexArticle` segfaults before any callback fires.
- **Investigation documented**: See `memory/reference_interlinear_investigation.md`
- **Next step**: Debug under lldb to catch exact crash location

## What the Next Session Should Do

### Priority 1: Debug Interlinear Segfault
The ESV interlinear data is the key to authoritative word-level morphology. Debug the `NativeLogosResourceIndexer` crash:
```
cd /Volumes/External/Logos4/tools/LogosReader
lldb -- dotnet run --no-build -- --interlinear ESV.logos4 0
# Set breakpoint at NativeLogosResourceIndexer_IndexArticle
# Run and catch the crash location
```

### Priority 2: Test & Refine the Conversation Phase
The conversation phase uses the 16-step system prompt but hasn't been tested end-to-end. Test with a real passage and verify:
- AI follows Bryan's lead in early conversation phases (6-8)
- AI triages volume at steps 9-10-12
- AI proactively surfaces confessional documents at step 11
- AI pushes through sermon construction at steps 13-14
- Illustration discipline coaching works

### Priority 3: BDAG Integration
BDAG is now readable but article IDs use a different format (A.xxx, R.xxx instead of transliterated Greek). Need to:
- Map BDAG article IDs to Greek lemmas
- Wire BDAG into the `lookup_lexicon` tool
- Test with actual word lookups

## Test Status
118 tests passing across 14 test files:
```bash
cd /Volumes/External/Logos4/tools/workbench
python3 -m pytest tests/ -v
```

## Key Files Changed This Session

| File | What Changed |
|------|-------------|
| `tools/LogosReader/Program.cs` | Driver version 2019→2025, callback type investigation |
| `tools/study.py` | `find_study_bible_notes()`, navindex `bible+version` fix, `--no-build` |
| `tools/logos_batch.py` | `--no-build` for PM2 compatibility |
| `tools/workbench/app.py` | Card routes, CARD_PHASES, auto-save, word-info endpoint |
| `tools/workbench/companion_db.py` | `card_annotations`, `card_notepads` tables |
| `tools/workbench/companion_agent.py` | 16-step system prompt, card work in conversation |
| `tools/workbench/templates/study_session.html` | Hybrid card/conversation template |
| `tools/workbench/templates/partials/study_card.html` | Card partial with side-by-side, tabs, stars |
| `tools/workbench/static/study.css` | Full dark theme, side-by-side, word popup |
| `tools/workbench/static/study.js` | Cards, tabs, stars, auto-save, word popup, SSE streaming |
| `tools/workbench/templates/study_start.html` | Session resume with phase labels |

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
