# Logos 4 Library + Sermon Study Companion

## Project Overview
Read books from a Logos 4 library (4,652 books, 33GB) programmatically. Built an ADHD-friendly sermon study companion that walks through a 12-phase prep workflow with an AI study partner.

## Allowed Commands
Run without asking permission:
- `export` (environment variables like PATH, DOTNET_ROOT)
- `sqlite3` (querying catalog.db, ResourceManager.db, logos_cache.db)
- `python3 -c` (one-liner Python scripts)
- `python3 tools/*.py` (running project Python scripts)
- `dotnet build` and `dotnet run` (building/running LogosReader)
- `ls`, `wc`, `file`, `xxd`, `hexdump` (file inspection)
- `python3 -m pytest` (running tests)
- `kill`, `lsof` (managing the Flask server process)

## Environment Setup
```bash
export PATH="/opt/homebrew/opt/dotnet@8/bin:$PATH"
export DOTNET_ROOT="/opt/homebrew/opt/dotnet@8/libexec"
```

## Running the App
```bash
cd tools/workbench && python3 app.py
# Old workbench: http://localhost:5111/
# Companion:     http://localhost:5111/companion/
```

## Key Paths
- **Catalog DB**: `Data/e3txalek.5iq/LibraryCatalog/catalog.db`
- **ResourceManager DB**: `Data/e3txalek.5iq/ResourceManager/ResourceManager.db`
- **Resources**: `Data/e3txalek.5iq/ResourceManager/Resources/`
- **Licenses**: `Data/e3txalek.5iq/LicenseManager/`
- **User ID**: `5621617`

## Architecture
```
Browser (HTMX + JS) ←SSE→ Flask app (port 5111)
  ↓                          ↓
Card UI + Discussion     companion_agent.py (streaming Claude)
[side-by-side layout]        ↓
                         companion_tools.py (7 tools)
                             ↓
                         study.py (orchestrator)
                             ↓
                         logos_batch.py → LogosReader (C# P/Invoke)
                             ↓
                         libSinaiInterop.dylib → .logos4 files
```

## Key Files — Companion
| File | Purpose |
|------|---------|
| `tools/workbench/app.py` | Flask routes (old workbench + `/companion/` routes) |
| `tools/workbench/companion_db.py` | SQLite: sessions, cards, messages, outline, questions |
| `tools/workbench/companion_agent.py` | Streaming Claude loop, 12-phase system prompt, homiletical guardrails |
| `tools/workbench/companion_tools.py` | 7 tools: Bible, lexicon, grammar, commentary, cross-refs, outline, interlinear |
| `tools/workbench/seed_questions.py` | 110 questions across 12 phases |
| `tools/workbench/genre_map.py` | Book → genre mapping (7 genres, 66 books) |
| `tools/workbench/static/companion.css` | ADHD-first dark theme |
| `tools/workbench/static/companion.js` | Timer, SSE streaming, mode toggle |

## Key Files — Logos Reader Layer
| File | Purpose |
|------|---------|
| `tools/LogosReader/Program.cs` | C# P/Invoke to libSinaiInterop.dylib |
| `tools/study.py` | Bible reading, commentary lookup, interlinear, article search |
| `tools/logos_batch.py` | Persistent reader subprocess for performance |
| `tools/logos_cache.py` | SQLite cache for article lookups |
| `tools/morphgnt_cache.py` | MorphGNT Greek NT morphology (137k words) + BDAG glosses |

## Available Library Resources (confirmed readable)
### Lexicons
- **NT**: BDAG, EDNT, TDNTA (abridged TDNT), Louw-Nida, TLNT, LSJ, ANLEX, Moulton-Milligan
- **OT**: BDB, HALOT, TDOT, TLOT, DCH, AnLexHeb
- **Not readable** (VersionIncompatible): full TDNT — updated to newer format by Logos

### Grammars
- **NT**: Wallace (Ex.Syn.), Robertson, Blass-Debrunner, Discourse Grammar, Morphology of Biblical Greek, Verbal Aspect, Idioms of GNT
- **OT**: GKC (Gesenius), Waltke-O'Connor

### Other
- 1,025 commentaries, 302 Bibles (including THGNT, BHS), 596 ancient manuscripts

## Testing
```bash
cd tools/workbench && python3 -m pytest tests/ -v
# 48 tests across 7 test files
```

## Design Principles
- **ADHD-first**: One question at a time, no step counts, calm dark theme
- **Study partner, not assistant**: Push back on weak exegesis, ask hard questions
- **Original languages first**: Translation cards show THGNT (NT) / BHS (OT), not ESV
- **Use the library**: Lexicon and grammar lookups pull from Bryan's actual resources
- **Homiletical coaching**: "So What?" gate, Christ thread, time estimator, congregation awareness
- **Timer auto-resumes**: Pause for interruptions, resumes on any interaction

## The User
Bryan is a Reformed Presbyterian pastor with ADHD who preaches weekly. His wife says sermons run too long (40 min vs 25-30 target) and are too exegetically dense. He's excellent at exegesis but struggles with the bridge to homiletics. The companion coaches that transition.
