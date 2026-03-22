# Library Tool Audit — Complete Findings

**Date:** 2026-03-22
**Purpose:** Map every tool the companion could have against all available resources, identify what's broken, and define the path to a comprehensive research assistant.

## The Problem

The companion has 7 tools but Bryan's 16-step workflow needs 30+. Of the 7 existing tools, 2 are critically broken (lexicon/grammar search return garbage). 150+ encrypted dataset files containing pre-indexed passage data are completely inaccessible.

## Resource Inventory

### Readable (.logos4 via CTitle API) — WORKS NOW
| Category | Count | Examples |
|----------|-------|---------|
| Bibles | 302 | ESV, NASB95, KJV1900, THGNT, BHS |
| Commentaries | 1,025 | Hodge, Cranfield, Murray, Calvin |
| Lexicons (NT) | 7 readable | EDNT (12K), TDNTA (890), Louw-Nida (19K), TLNT (8K), LSJ (192K), ANLEX (26K), M-M |
| Lexicons (OT) | 6 readable | BDB (12K), HALOT (11K), TDOT (59K), TLOT, DCH, AnLexHeb |
| Grammars (NT) | 8 readable | Wallace (3,625), Robertson (8,094), Blass-Debrunner, Discourse, Morphology, Verbal Aspect, Idioms, Intermediate |
| Grammars (OT) | 2 readable | GKC, Waltke-O'Connor |
| Systematic Theology | 60 | Turretin (IET), Calvin (ICR), Berkhof, Hodge, Bavinck |
| Biblical Theology | 13 | Vos, Goldingay (OTT 1-3), NDBT, EDBT |
| Confessional Docs | 10 | WCF, WLC, WSC, Book of Concord, Schaff's Creeds |
| Study Bibles | 16 | ESV Study Bible, Reformation Study Bible, FSB |
| Church Fathers | 596+ | ANF/NPNF series, Josephus, Philo |
| Sermon Collections | 59+ | Simeon (21 vols), Piper (3 vols), Edwards |
| Sermon Outlines | 40 | Various outline collections |

**Not readable (VersionIncompatible):** BDAG (updated 2024), full TDNT (updated 2025) — Logos auto-updated these to a format the v48 native library can't read.

### Encrypted (.lbs* via EncryptedVolume API) — LOCKED

#### Workflow-Critical Datasets
| File | Size | Database | What it contains |
|------|------|----------|-----------------|
| `FIGURATIVE-LANGUAGE.lbssd` | 5.6MB | SupplementalData.db | Figures of speech tagged per passage |
| `BULLINGER-FIGURES.lbssd` | 504KB | SupplementalData.db | Bullinger's figures classifications |
| `LITERARYTYPING.lbssd` | 220KB | SupplementalData.db | Literary genre per passage |
| `LONGACRE-GENRE.lbssd` | 260KB | SupplementalData.db | Longacre discourse genre |
| `GREEK-CONSTRUCTIONS.lbssd` | 9.9MB | SupplementalData.db | Greek grammatical constructions per passage |
| `HEBREW-CONSTRUCTIONS.lbssd` | 16MB | SupplementalData.db | Hebrew constructions per passage |
| `PROPOSITIONAL-OUTLINES.lbssd` | 10MB | SupplementalData.db | NT propositional outlines |
| `PROPOSITIONAL-OUTLINES-OT.lbssd` | 36MB | SupplementalData.db | OT propositional outlines |
| `WORDPLAY.lbssd` | 524KB | SupplementalData.db | Wordplay instances |
| `NT-USE-OF-OT.lbssd` | 436KB | SupplementalData.db | OT quotations/allusions in NT |
| `NT-SYNTACTIC-FORCE.lbssd` | 11MB | SupplementalData.db | Syntactic force analysis |
| `DISCOURSE-GNT-SBL.lbssd` | 8.1MB | SupplementalData.db | Discourse grammar (GNT) |
| `DISCOURSE-HOT.lbssd` | 32MB | SupplementalData.db | Discourse grammar (Hebrew OT) |
| `IMPORTANTWORDS.lbsiw` | 9MB | importantwords.db | Key terms per passage |
| `PreachingThemes.lbsptd` | 7.1MB | preachingthemes.db | Preaching themes per passage |

#### Cross-Reference Databases
| File | Size | Database | What it contains |
|------|------|----------|-----------------|
| `BIBLEXREFS.lbslcr` | 148MB | bxrefs.db | Curated Bible cross-references with reasons |
| `THEOLOGY-XREFS.lbsxrf` | 150MB | CrossReferences.db | Passage → systematic theology sections |
| `BIBLICAL-THEOLOGY-XREFS.lbsxrf` | 137MB | CrossReferences.db | Passage → biblical theology sections |
| `GRAMMAR-XREFS.lbsxrf` | 44MB | CrossReferences.db | Passage → grammar book sections |
| `CREEDS-COUNCILS-XREFS.lbsxrf` | 22MB | CrossReferences.db | Passage → confessional doc sections |

#### Knowledge Base Datasets
| File | Size | Database | What it contains |
|------|------|----------|-----------------|
| `BiblicalPeople.lbsbpd` | 17MB | biblicalpeople.db | People with relationships, lemma links |
| `BiblicalPlaces.lbsplc` | 3.9MB | biblicalplaces.db | Places with details |
| `BiblicalThings.lbsthg` | 4.4MB | biblicalthings.db | Objects/concepts |
| `BiblicalEvents.lbsevt` | 5.1MB | biblicalevents.db | Events |
| `ThematicOutlines.lbstod` | 19MB | thematicoutlines.db | Passage outlines with points |
| `LCO.lbslco` | 1.2MB | lco.db | Cultural ontology |
| `AncientLiterature.lbsanc` | 13MB | ancientliterature.db | Church father cross-refs |
| `Lemmas.lbslms` | 63MB | lemmas.db | Lemma glosses, morphology, roots |
| `WordSenses.lbswsd` | 31MB | wordsenses.db | Word sense disambiguation |
| `PericopeSets.lbspsd` | 19MB | pericopesets.db | Pericope boundaries |
| `Biographies.lbsbio` | 229MB | Biographies.db | Notable people bios |
| `UniversalTimeline.lbsut` | 26MB | UniversalTimeline.db | Historical timeline |

## What's Broken: Lexicon/Grammar Search

### Root Cause
Article IDs in lexicons are **transliterated Latin abbreviations**, not Greek/Hebrew text:
- EDNT article `#7428` has ID `MATIOVW` (should be ματαιόω / mataioō)
- The ID even has a typo — `MATIOVW` drops the `A` from `MATAIOVW`
- Louw-Nida IDs are semantic domain codes: `F1.1`, `F1.2`
- Wallace IDs are opaque chapter/paragraph codes: `G16W22`

### Current Search Algorithm
1. Search article IDs for Greek text → **always fails** (Greek ≠ Latin)
2. Fall back to content sampling: read 200 random articles out of 12,000+ → **1.6% hit rate**
3. When it does find something, often matches abbreviation entries like `ABBR.MID` or `ABBR.PASS`

### Fix: Build Resource Index
Read the first line of every article (which contains the Greek headword in lexicons). Build a SQLite index mapping:
- Greek lemma → article number
- Transliterated form → article number
- English gloss → article number
- Grammar topic keyword → chapter article range

This is a one-time operation per resource. Subsequent lookups are sub-millisecond.

### Verified Article Structure
```
EDNT #7428 (MATIOVW):
"ματιόω   mataioō   give over to futility; pass.: become subject to futility*
In the NT only in Rom 1:21 (pass.) of the people who..."

Wallace #1095-1102 (G16W22-G16W29):
Voice chapter — contains actual discussion of middle/passive distinction
"Some verbs have followed separate paths for active and middle..."
```

## Technical Findings: EncryptedVolume API

### Confirmed P/Invoke Exports (via `nm -gU`)
```
_EncryptedVolume_New          → IntPtr handle
_EncryptedVolume_Open         → bool (handle, licMgr, path)
_EncryptedVolume_OpenDatabase → IntPtr (raw sqlite3*)
_EncryptedVolume_OpenFile     → IntPtr (stream)
_EncryptedVolume_Delete       → void
_EncryptedVolume_GetResourceId, _GetResourceDriverName, etc.
```

### SQLite Library
`libsqlite3-logos.dylib` (824KB) confirmed in Logos app bundle at:
```
/Applications/Logos.app/Contents/Frameworks/FaithlifeDesktop.framework/
  Versions/48.0.0.0238/Frameworks/ApplicationBundle.framework/
  Resources/lib/libsqlite3-logos.dylib
```
Exports all standard sqlite3 C API functions: `sqlite3_prepare_v2`, `sqlite3_step`, `sqlite3_column_text`, `sqlite3_finalize`, etc.

### Integration Architecture
```
Python (companion_tools.py)
  → logos_batch.py.query_dataset("FIGURATIVE-LANGUAGE.lbssd", "SupplementalData.db", sql)
    → sends: query-db FIGURATIVE-LANGUAGE.lbssd SupplementalData.db "SELECT ..."
      → LogosReader batch mode
        → EncryptedVolume_New() + EncryptedVolume_Open(handle, licMgr, path)
          → EncryptedVolume_OpenDatabase(handle, "SupplementalData.db") → raw sqlite3*
            → sqlite3_prepare_v2(db, sql) → sqlite3_step() → sqlite3_column_text()
              → TSV output on stdout
```

### Critical Implementation Notes
1. **UTF-8**: Use `Marshal.PtrToStringUTF8` for all sqlite3 string results (Greek/Hebrew data)
2. **SQL quoting**: Python must double-quote the SQL argument for `ParseCommandLine` to treat as one token
3. **Batch loop integration**: `query-db` and `volume-info` must be early-exit switch cases that bypass the CTitle path (set `mode = "__skip__"`)
4. **Singleton**: `dataset_tools.py` must reuse `study.py`'s batch reader, not spawn a second process

## Full Tool Map: 50+ Possible Tools

### Tier 1: Working (5 tools)
read_bible_passage, find_commentary_paragraph, word_study_lookup, expand_cross_references, save_to_outline

### Tier 2: Built But Broken (2 tools) — Fix with index
lookup_lexicon, lookup_grammar

### Tier 3: EncryptedVolume Datasets (28+ tools)
get_figurative_language, get_greek_constructions, get_hebrew_constructions, get_literary_typing, get_wordplay, get_propositional_outline, get_sentence_types, get_speech_acts, get_discourse_analysis, get_syntactic_force, get_important_words, get_preaching_themes, get_nt_use_of_ot, get_curated_cross_refs, get_systematic_theology_refs, get_biblical_theology_refs, get_confessional_refs, get_grammar_refs, get_biblical_places, get_biblical_people, get_biblical_things, get_biblical_events, get_cultural_concepts, get_ancient_literature, get_thematic_outlines, get_messianic_prophecy, get_pericope_sets, get_word_senses

### Tier 4: .logos4 Navigation (8+ tools)
search_systematic_theologies, search_biblical_theologies, search_confessional_docs, search_study_bibles, search_church_fathers, search_sermon_collections, search_sermon_outlines, search_homiletics

### Tier 5: Computed/Derived (8+ tools)
compare_translations, trace_word_through_book, survey_commentators, find_parallel_passages, estimate_sermon_time, check_christ_connection, generate_application_questions, check_congregation_readability

## Workflow → Tool Mapping

| Workflow Step | Tools Needed | Status |
|---------------|-------------|--------|
| 1. Prayer | read_bible_passage | Working |
| 2. Translate | read_bible_passage, compare_translations, get_curated_cross_refs, get_nt_use_of_ot | Partial |
| 3. Digestion | read_bible_passage | Working |
| 4. Exegesis | get_figurative_language, get_literary_typing, get_greek/hebrew_constructions, get_propositional_outline, get_wordplay, lookup_grammar | Broken/Locked |
| 5. Study Bibles | search_study_bibles | Not built |
| 6. Context | get_biblical_places, get_biblical_people, get_biblical_things, get_cultural_concepts | Locked |
| 7. Big Picture | get_pericope_sets, get_thematic_outlines | Locked |
| 8. Identify Christ | get_messianic_prophecy, get_curated_cross_refs | Locked |
| 9. Sys/Bib Theology | get_systematic_theology_refs, get_biblical_theology_refs | Locked |
| 10. Church Fathers | get_ancient_literature, search_church_fathers | Locked |
| 11. Confessions | get_confessional_refs | Locked |
| 12. Commentaries | find_commentary_paragraph | Working |
| 13-14. Sermon Writing | save_to_outline, estimate_sermon_time, check_christ_connection | Partial |
| 15-16. Edit | check_congregation_readability | Not built |
