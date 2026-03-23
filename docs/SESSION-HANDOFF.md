# Session Handoff: MorphGNT Integration

**Date:** 2026-03-23
**Status:** Ready for MorphGNT integration. Segfault fixed, BDAG wired in, 118 tests passing.

## What Needs To Be Done

### Load MorphGNT for Authoritative Word-Level Morphology

The `/word-info` endpoint currently calls Claude Haiku per click to parse Greek words. This works but:
- Costs an API call per word click
- ~90% accurate (Haiku sometimes hallucinates rare forms)
- No Strong's numbers or Louw-Nida codes

**MorphGNT** (https://github.com/morphgnt/sblgnt) provides authoritative, free morphological data for every word in the Greek NT:
- Lemma
- Morphology code (e.g., `V-AAI-3S` = Verb, Aorist, Active, Indicative, 3rd person Singular)
- Part of speech
- Normalized form

**What to build:**

1. **Download MorphGNT data** — CSV files, one per NT book (Matthew through Revelation). ~5MB total. Format per line:
   ```
   BBCCCVVVWWWP  word  normalized  lemma  part-of-speech  parsing-code  text
   ```
   Where BBCCCVVVWWWP = book/chapter/verse/word/part encoding.

2. **Create `tools/morphgnt_cache.py`** — Load MorphGNT into a SQLite database:
   ```sql
   CREATE TABLE morphgnt (
       book INTEGER,      -- 1-27 (Matthew=1, Revelation=27)
       chapter INTEGER,
       verse INTEGER,
       word_num INTEGER,   -- word position in verse
       text TEXT,          -- surface form (with accents)
       normalized TEXT,    -- normalized form
       lemma TEXT,         -- dictionary form
       pos TEXT,           -- part of speech (N, V, A, etc.)
       parsing TEXT,       -- full parsing code
       PRIMARY KEY (book, chapter, verse, word_num)
   );
   CREATE INDEX idx_lemma ON morphgnt(lemma);
   CREATE INDEX idx_text ON morphgnt(text);
   ```

3. **Wire into `/word-info` endpoint** — In `app.py`, check MorphGNT cache FIRST. Fall back to Haiku only if not found (OT words, or if MorphGNT doesn't cover it).

4. **Wire into `word_study_lookup` tool** — In `companion_tools.py`, the `_word_study_lookup` function can use MorphGNT instead of the (non-functional) ESV interlinear.

5. **Optional: Add Strong's numbers** — MorphGNT doesn't include Strong's, but the `IMPORTANTWORDS.lbsiw` encrypted dataset maps passages to lemmas with word numbers. Cross-referencing MorphGNT lemma + position with this dataset could add Strong's numbers.

**Book number mapping (MorphGNT → Logos):**
- MorphGNT: Matthew=1, Mark=2, ..., Revelation=27
- Logos: Matthew=40 (OSIS), Mark=41, ..., Revelation=66
- Offset: logos_book = morphgnt_book + 39

**Testing:**
- Add tests for morphgnt_cache.py (load, query by reference, query by word)
- Verify `/word-info` returns MorphGNT data for NT words
- Verify Haiku fallback still works for OT words
- All 118 existing tests must keep passing

## Previous Session's Work (2026-03-23)

### Fixed: NativeLogosResourceIndexer Segfault
`NativeLogosResourceIndexer_New` takes 7 params (title, langStr, callback, bool×4), not 2. Callback was read as language string → garbage callback → SIGSEGV. Also fixed AddResourceJump delegate (13→correct params). Forward word indexing now works (1179 words from Romans 1). Reverse interlinear (ProcessRVI) requires full Logos4Indexer pipeline — too complex.

### Completed: BDAG Integration
BDAG.logos4 added as first NT lexicon. 8110 entries indexed. Fixed Unicode NFC normalization for decomposed Greek headwords. All lookups working at score=100.

### Verified: 16-Step Conversation Phase
System prompt verified with 25/25 checks: triaging (steps 9-10-12), confessional docs (step 11), sermon construction push (steps 13-14), all substeps encoded.

## Test Status
118 tests passing:
```bash
cd /Volumes/External/Logos4/tools/workbench
python3 -m pytest tests/ -v
```

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
