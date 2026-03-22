# EncryptedVolume API — Unlocking Logos Study Tool Datasets

> **Status**: Research complete, implementation not yet started.
> Created: 2026-03-10

## Discovery

All specialized Logos study tools (figurative language, biblical places, cross-references, grammatical constructions, thematic outlines, etc.) are backed by **encrypted SQLite databases** inside binary resource files (`.lbssd`, `.lbsxrf`, `.lbsplc`, `.lbsthg`, etc.).

These do NOT use the CTitle/Article API that LogosReader currently uses for `.logos4` text files. Instead, they use a separate `EncryptedVolume` API that:
1. Opens the encrypted container
2. Exposes embedded SQLite databases for direct SQL querying

## Architecture

```
.logos4 files (books)              .lbssd/.lbsxrf/.lbsplc/etc (datasets)
     │                                        │
     ▼                                        ▼
SinaiInterop_LoadTitle()           EncryptedVolume_New()
     │                            EncryptedVolume_Open(handle, licMgr, path)
     ▼                                        │
CTitle → Articles → Text          EncryptedVolume_OpenDatabase(handle, "db.db")
(what LogosReader does now)                   │
                                              ▼
                                     Raw sqlite3* pointer
                                              │
                                              ▼
                                     SQL queries on decrypted tables
```

## Native API Exports (all in libSinaiInterop.dylib)

Already confirmed present via `nm -gU`:

```
_EncryptedVolume_New
_EncryptedVolume_Open
_EncryptedVolume_OpenFile
_EncryptedVolume_OpenDatabase
_EncryptedVolume_CreateConnectionStringDataSource
_EncryptedVolume_GetResourceId
_EncryptedVolume_GetResourceVersion
_EncryptedVolume_GetResourceDriverName
_EncryptedVolume_GetResourceDriverVersion
_EncryptedVolume_GetDataTypesRequiredVersion
_EncryptedVolume_CopyCtor
_EncryptedVolume_Delete
```

## P/Invoke Declarations Needed (from decompiled .NET sources)

From `/tmp/logos-decompile/ResourceDrivers/Libronix.DigitalLibrary.ResourceDrivers.decompiled.cs` lines 45506-45547:

```csharp
// EncryptedVolume — opens encrypted dataset files (.lbssd, .lbsxrf, .lbsplc, etc.)
[DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
static extern IntPtr EncryptedVolume_New();

[DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
[return: MarshalAs(UnmanagedType.U1)]
static extern bool EncryptedVolume_Open(
    IntPtr ptr,
    IntPtr pLicenseManager,  // same licMgr we already have
    [MarshalAs(UnmanagedType.LPWStr)] string filePath);

[DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
static extern IntPtr EncryptedVolume_OpenFile(
    IntPtr ptr,
    [MarshalAs(UnmanagedType.LPWStr)] string strFileName);

[DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
static extern IntPtr EncryptedVolume_OpenDatabase(
    IntPtr ptr,
    [MarshalAs(UnmanagedType.LPWStr)] string strFileName);
// Returns raw sqlite3* handle

[DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
[return: MarshalAs(UnmanagedType.LPWStr)]
static extern string EncryptedVolume_CreateConnectionStringDataSource(
    IntPtr ptr,
    [MarshalAs(UnmanagedType.LPWStr)] string strFileName,
    [MarshalAs(UnmanagedType.U1)] bool bUseCerod);

[DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
[return: MarshalAs(UnmanagedType.LPWStr)]
static extern string EncryptedVolume_GetResourceId(IntPtr ptr);

[DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
[return: MarshalAs(UnmanagedType.LPWStr)]
static extern string EncryptedVolume_GetResourceVersion(IntPtr ptr);

[DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
[return: MarshalAs(UnmanagedType.LPWStr)]
static extern string EncryptedVolume_GetResourceDriverName(IntPtr ptr);

[DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
[return: MarshalAs(UnmanagedType.LPWStr)]
static extern string EncryptedVolume_GetResourceDriverVersion(IntPtr ptr);

[DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
[return: MarshalAs(UnmanagedType.LPWStr)]
static extern string EncryptedVolume_GetDataTypesRequiredVersion(IntPtr ptr);

[DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
static extern void EncryptedVolume_Delete(IntPtr ptr);
```

## How .NET Code Uses It

From decompiled `EncryptedVolume.TryOpen()` (lines 422-443):

```csharp
// 1. Create handle
SafeEncryptedVolumeHandle handle = NativeMethods.EncryptedVolume_New();
// 2. Open with license manager (same one LogosReader already creates)
if (NativeMethods.EncryptedVolume_Open(handle, licenseManager.GetCore(), filePath))
{
    // Success — can now open streams and databases
}

// 3a. Open embedded SQLite database (returns raw sqlite3*)
nint sqlitePtr = NativeMethods.EncryptedVolume_OpenDatabase(handle, "SupplementalData.db");
IDbConnection conn = SQLiteUtility.CreateConnection(sqlitePtr);

// 3b. OR open a file stream (for XML metadata, etc.)
SafeIStreamProxyHandle streamHandle = NativeMethods.EncryptedVolume_OpenFile(handle, "this.metadata.xml");
// wrap in ComStream → BufferedStream

// 3c. OR get connection string for cerod-encrypted database access
string connStr = NativeMethods.EncryptedVolume_CreateConnectionStringDataSource(handle, "SupplementalData.db", true);
```

## File Extension → Embedded Database Name Mapping

| Extension | Driver | Database Name | Key Tables |
|-----------|--------|---------------|------------|
| `.lbssd` | SupplementalData (#30) | `SupplementalData.db` | `ReferenceAttachments`, `DataTypeReferences`, `TextRangeAttachments`, `WordNumberSetAttachments`, `WordNumbers`, `Resources`, `LabelStrings`, `LocalizedStringKeys`, `Extras` |
| `.lbsxrf` | CrossReferences (#36) | `CrossReferences.db` | `CrossReferences`, `DataTypeReferences`, `Groups`, `GroupExpressions`, `Types`, `TypeExpressions` |
| `.lbslcr` | BibleCrossReferences (#39) | `bxrefs.db` | `CrossReferences`, `BibleReferences`, `CrossReferenceReasons`, `Reasons` |
| `.lbsbpd` | BibleKnowledgebase (#1) | `biblicalpeople.db` | `Entities`, `EntityTitles`, `EntityReferences`, `EntityLemmas`, `EntityRelationships` |
| `.lbsplc` | BibleKnowledgebase (#1) | `biblicalplaces.db` | Same entity schema |
| `.lbsthg` | BibleKnowledgebase (#1) | `biblicalthings.db` | Same entity schema |
| `.lbstod` | ThematicOutlines (#23) | `thematicoutlines.db` | `Outlines`, `OutlineTitles`, `Points`, `PointTitles`, `PointReferences`, `PointReferenceLabels`, `Words` |
| `.lbslco` | LexhamCulturalOntology (#33) | `lco.db` | `Concepts`, `Labels`, `SenseReferences`, `ConceptFrames`, `ConceptAncestry` |
| `.lbsgrm` | GrammaticalRelationships (#7) | `grammar.db` | `Lemma`, `Row`, `Cell`, `Hit`, `HitReference`, `Reference`, `Label` |
| `.lbsanc` | AncientLiterature (#26) | `ancientliterature.db` | `CrossReferences`, `DataTypeReferences`, `Relations`, `DataSets` |
| `.lbslms` | Lemmas | `lemmas.db` | `Lemma`, `Gloss`, `AnalysisGroup`, `Root` |
| `.lbswsd` | WordSenses | `wordsenses.db` | Word sense data |
| `.lbsut` | UniversalTimeline | `UniversalTimeline.db` | Timeline events |
| `.lbsptd` | PreachingThemes | `preachingthemes.db` | Preaching theme data |
| `.lbspsd` | PericopeSets | `pericopesets.db` | Pericope divisions |
| `.lbsbrd` | BiblicalReferents | `biblicalreferents.db` | Referent data |
| `.lbsevt` | Events (#17) | `biblicalevents.db` | Event data |
| `.lbsbio` | Biographies (#32) | `Biographies.db` | Biography data |
| `.lbsmps` | Maps (#15) | `mapsresource.db` | Map data |
| `.lbsrvi` | ReverseInterlinear | `align.db` + `word.db` | Translation alignment |
| `.lbspcd` | PhraseConcordance | `phraseconcordance.db` | Phrase concordance |
| `.lbsnt` | NamedTexts | `NamedTexts.db` | Named text data |
| `.lbsuav` | UnifiedAnnotationVocabulary | `uav.db` | Annotation vocabulary |
| `.lbssyn` | SyntaxDatabase | `monadranges.db` | Syntax trees |
| `.lbscls` | BiblicalClauses | `biblicalclauses.db` | Clause data |
| `.lbsch` | ChurchHistory | `churchhistory.db` | Church history data |
| `.lbslsto` | LexhamSTOntology (#37) | LSTO data | Systematic theology ontology |
| `.lbsfbm` | FactbookMedia | `FactbookMedia.db` | Media index |
| `.lbsiw` | ImportantWords (#38) | Important words data | Per-passage key terms |
| `.lbsrsd` | ReportedSpeech | `reportedspeech.db` | Reported speech data |

## Implementation Plan

### Phase 1: EncryptedVolume in LogosReader (C#)

Add to `Program.cs`:

1. **P/Invoke declarations** (listed above)
2. **`query-db` batch command**: `query-db <file> <db-name> <sql>`
   - Opens file via `EncryptedVolume_New()` + `EncryptedVolume_Open()`
   - Gets sqlite3* via `EncryptedVolume_OpenDatabase(handle, dbName)`
   - Runs SQL query using raw sqlite3 C API (sqlite3_prepare_v2, sqlite3_step, etc.)
   - Returns TSV results
   - Cache the EncryptedVolume handle like we cache CTitle handles
3. **`volume-info` batch command**: `volume-info <file>`
   - Opens volume, returns ResourceId, ResourceVersion, DriverName, DriverVersion, DataTypesVersion
4. **`volume-stream` batch command**: `volume-stream <file> <stream-name>`
   - Opens a stream from the volume (e.g., `this.metadata.xml`, `driver-specific.xml`)
   - Returns the stream contents

**Challenge**: `EncryptedVolume_OpenDatabase` returns a raw `sqlite3*`. We need to either:
- Use SQLite C API directly (sqlite3_prepare_v2, sqlite3_step, etc.) via P/Invoke to `libsqlite3.dylib` or the cerod-enabled sqlite bundled with Logos
- Or use `Microsoft.Data.Sqlite` with a custom connection that wraps the raw handle
- Or extract the data via `EncryptedVolume_OpenFile` if the DB is stored as a named baggage file

**Recommended approach**: Use raw SQLite C API via P/Invoke. The sqlite3 library is likely bundled inside libSinaiInterop.dylib or linked alongside it. We need:
```csharp
// Standard SQLite C API — may be in libsqlite3.dylib or in libSinaiInterop.dylib itself
[DllImport("libsqlite3.dylib")]
static extern int sqlite3_prepare_v2(IntPtr db, string sql, int nByte, out IntPtr stmt, out IntPtr tail);

[DllImport("libsqlite3.dylib")]
static extern int sqlite3_step(IntPtr stmt);

[DllImport("libsqlite3.dylib")]
static extern int sqlite3_column_count(IntPtr stmt);

[DllImport("libsqlite3.dylib")]
static extern IntPtr sqlite3_column_name(IntPtr stmt, int col);

[DllImport("libsqlite3.dylib")]
static extern IntPtr sqlite3_column_text(IntPtr stmt, int col);

[DllImport("libsqlite3.dylib")]
static extern int sqlite3_column_type(IntPtr stmt, int col);

[DllImport("libsqlite3.dylib")]
static extern int sqlite3_finalize(IntPtr stmt);
```

**Alternative**: Check if `libSinaiInterop.dylib` exports sqlite3 symbols (it might bundle them for cerod VFS support).

### Phase 2: Python Wrappers

Add to `logos_batch.py`:
- `query_dataset(resource_file, db_name, sql)` — sends `query-db` command
- `get_volume_info(resource_file)` — sends `volume-info` command

Add to `study.py`:
- Dataset query functions for each study tool type
- `get_cross_references(book, chapter, verse)` — queries `BIBLEXREFS.lbslcr`
- `get_figurative_language(book, chapter, verse)` — queries `FIGURATIVE-LANGUAGE.lbssd`
- `get_biblical_places(book, chapter, verse)` — queries `BiblicalPlaces.lbsplc`
- etc.

### Phase 3: Agent Tools

Add to `sermon_agent.py` TOOL_DEFINITIONS:
- `study_figurative_language` — matches workflow intent `studyFigurativeLanguage`
- `study_biblical_places` — matches `studyBiblicalPlaces`
- `study_biblical_things` — matches `studyBiblicalThings`
- `study_cross_references_curated` — matches `studyCrossReferencesCurated`
- `study_grammatical_constructions` — matches `studyGrammaticalConstructions`
- `study_cultural_concepts` — matches `studyCulturalConcepts`
- `study_thematic_outlines` — matches `studyOutlines`
- `study_systematic_theologies_xrefs` — matches `studySystematicTheologies` (xref lookup)
- `study_biblical_theologies_xrefs` — matches `studyBiblicalTheologies` (xref lookup)
- `study_confessional_xrefs` — matches `studyConfessionalDocuments` (xref lookup)
- `study_ancient_literature` — matches `studyAncientLiterature`

### Phase 4: Workflow Integration

Update `workbench_agent.py`:
- Replace generic 6-phase system with the user's 16-step ADHD workflow
- Map each `study*` intent to the corresponding agent tool
- Map each `respond` prompt to conversation prompts the agent asks the user
- Include timer targets from the workflow

## User's Custom Workflow

Found in: `/Volumes/External/Logos4/Documents/e3txalek.5iq/Workflows/Workflows.db`
- Template ID: `5d4a6471396e4168a663d88a5de1972a`
- Full JSON extracted to: `/tmp/workflow_template.json`
- 47 uses, 12 completed

### Workflow Steps with Logos Tool Intents

#### Step 1: Pray (15 min)
- [READ] "Extremely Important! Pray and ask God for help. Especially with your easily distracted mind."

#### Step 2: Translate the Text (2 hrs)
- [RESPOND] "What would your own translation be?"
- [RESPOND] "Were there any really odd words?"
- [RESPOND] "Was there repetition?"
- [STUDY] `studyCrossReferencesCurated` → `BIBLEXREFS.lbslcr` → `bxrefs.db`
- [RESPOND] "Were there any references to other texts?"

#### Step 3: Digest (1 hr)
- [RESPOND] "Write out a prayer for each phrase, sentence, or paragraph."

#### Step 4: Exegesis (1 hr)
- [STUDY] `studyTextualVariants` → critical apparatus books (.logos4)
- [RESPOND] "Are there any significant textual variants?"
- [STUDY] `studyFigurativeLanguage` → `FIGURATIVE-LANGUAGE.lbssd` → `SupplementalData.db`
- [RESPOND] "Is there any figurative language?"
- [STUDY] `studyLiteraryTyping` → `LITERARYTYPING.lbssd` → `SupplementalData.db`
- [RESPOND] "What literary typing is there?"
- [READ] "Follow the sentence diagram..."
- [STUDY] `studyOutlines` → `ThematicOutlines.lbstod` → `thematicoutlines.db`
- [RESPOND] "What is the subject grammatically?"
- [RESPOND] "What's going on in this section? Who is ___? ..."
- [STUDY] `studyGrammaticalConstructions` → `GREEK-CONSTRUCTIONS.lbssd` + `.lbsgrm`
- [RESPOND] "What grammatical constructions are being used?"

#### Step 5: Get Quick Answers (30 min)
- [READ] "Study Bibles can get you on the right track quickly..."
- [RESPOND] "Open 'Study Bible Collection' — anything significant you were missing?"

#### Step 6: Context Questions (15 min)
- [RESPOND] "What is the temporal setting?"
- [RESPOND] "What is the geographic setting?"
- [STUDY] `studyAtlas` → `BiblicalPlacesMaps.lbsmps` → `mapsresource.db`
- [RESPOND] "Are there cultural things that color this?"
- [STUDY] `studyCulturalConcepts` → `LCO.lbslco` → `lco.db`
- [STUDY] `studyBiblicalPlaces` → `BiblicalPlaces.lbsplc` → `biblicalplaces.db`
- [STUDY] `studyBiblicalThings` → `BiblicalThings.lbsthg` → `biblicalthings.db`
- [STUDY] `studyMediaResources` → media resources
- [STUDY] `studyMediaCollections` → media collections

#### Step 7: Big Picture (30 min)
- [RESPOND] "What is the point of this passage in larger picture of this book?"
- [RESPOND] "Are there surrounding units of thought?"
- [RESPOND] "Where does this fit in canonical and historical redemptive context?"

#### Step 8: Identify Christ (30 min)
- [READ] "Especially important in OT passages..."
- [RESPOND] Historical-redemptive progress (personal/national/redemptive history)
- [RESPOND] Promise-fulfillment / messianic hope
- [RESPOND] Typology (person/action/event → escalation to Christ)
- [RESPOND] Analogy (parallel situations)
- [RESPOND] Longitudinal themes (KOG, covenant, presence, grace, redemption, law, mediator, Day of the Lord...)
- [RESPOND] Contrast (OT → new in Christ)
- [RESPOND] NT references to this passage
- [STUDY] `studyCrossReferencesCurated` → `BIBLEXREFS.lbslcr`

#### Step 9: Systematic & Biblical Studies (30 min)
- [RESPOND] "Any systematic issues?"
- [STUDY] `studySystematicTheologies` → `THEOLOGY-XREFS.lbsxrf` → `CrossReferences.db` + 67 sys. theology books
- [RESPOND] "Any biblical theology issues?"
- [STUDY] `studyBiblicalTheologies` → `BIBLICAL-THEOLOGY-XREFS.lbsxrf` + 15 biblical theology books

#### Step 10: Historical Context (30 min)
- [RESPOND] "Any significant church fathers writings?"
- [STUDY] `studyAncientLiterature` → `AncientLiterature.lbsanc` → `ancientliterature.db` + 596 manuscripts

#### Step 11: Confessions (15 min)
- [RESPOND] "Any confessional documents?"
- [STUDY] `studyConfessionalDocuments` → `CREEDS-COUNCILS-XREFS.lbsxrf` + 10 confessional books

#### Step 12: Commentaries (30 min)
- [RESPOND] "Now you can turn to commentaries. Don't get bogged down."
- [STUDY] `studyCommentaries` → 1,038 commentaries (already working via navindex)

#### Step 13: Big Picture - Sermon Work
- [READ] "This is where the sermon writing process actually begins."

#### Step 14: Formal Sermon Writing
- [READ] "Use the sermon editor to help here..."

#### Step 15: Finishing Questions (30 min)
- [RESPOND] Faithfulness to text? Head vs heart? Lecture or sermon? Tangible application?

#### Step 16: Ruthlessly Edit (45 min)
- [READ] "Pray over the sermon..."
- [READ] "Ruthlessly edit it down..."

## Dataset File Inventory

All under `/Volumes/External/Logos4/Data/e3txalek.5iq/ResourceManager/Resources/`:

### SupplementalData (.lbssd) — 64 files
Key files for workflow:
- `FIGURATIVE-LANGUAGE.lbssd` (5.6 MB) — figurative language tagged to passages
- `BULLINGER-FIGURES.lbssd` (504 KB) — Bullinger's figures of speech
- `WORDPLAY.lbssd` (522 KB) — wordplay tagged to passages
- `LITERARYTYPING.lbssd` (219 KB) — literary genre classifications
- `LONGACRE-GENRE.lbssd` (258 KB) — Longacre genre analysis
- `GREEK-CONSTRUCTIONS.lbssd` (9.9 MB) — Greek grammatical constructions
- `HEBREW-CONSTRUCTIONS.lbssd` (16 MB) — Hebrew grammatical constructions
- `PROPOSITIONAL-OUTLINES.lbssd` (10 MB) — NT propositional outlines
- `PROPOSITIONAL-OUTLINES-OT.lbssd` (36 MB) — OT propositional outlines
- Plus: battles, marriages, prayers, miracles, covenants, parables, songs, fasts, burials, commandments, messianic prophecy, NT use of OT, discourse analysis, and more

### CrossReferences (.lbsxrf) — 4 files
- `THEOLOGY-XREFS.lbsxrf` (150 MB) — Bible passage → systematic theology sections
- `BIBLICAL-THEOLOGY-XREFS.lbsxrf` (137 MB) — Bible passage → biblical theology sections
- `GRAMMAR-XREFS.lbsxrf` (44 MB) — Bible passage → grammar book sections
- `CREEDS-COUNCILS-XREFS.lbsxrf` (22 MB) — Bible passage → confessional document sections

### BibleKnowledgebase — 3 files
- `BiblicalPeople.lbsbpd` (17 MB)
- `BiblicalPlaces.lbsplc` (3.9 MB)
- `BiblicalThings.lbsthg` (4.4 MB)

### Other Key Files
- `BIBLEXREFS.lbslcr` (148 MB) — Curated Bible cross-references
- `ThematicOutlines.lbstod` (19 MB) — Passage outlines
- `LCO.lbslco` (1.2 MB) — Cultural ontology
- `AncientLiterature.lbsanc` (13 MB) — Ancient literature cross-refs
- `Lemmas.lbslms` (63 MB) — Lemma glosses and morphology
- `BiblicalEvents.lbsevt` (5.1 MB) — Biblical events
- `Biographies.lbsbio` (229 MB) — Notable people bios
- `UniversalTimeline.lbsut` (26 MB) — Historical timeline
- `PreachingThemes.lbsptd` (7.1 MB) — Preaching themes per passage
- `IMPORTANTWORDS.lbsiw` (9 MB) — Important words per passage
- `PericopeSets.lbspsd` (19 MB) — Pericope divisions
- `WordSenses.lbswsd` (31 MB) — Word sense disambiguation

## Decompiled Source References

- `/tmp/logos-decompile/ResourceDrivers/Libronix.DigitalLibrary.ResourceDrivers.decompiled.cs` (86,206 lines)
  - EncryptedVolume class: lines 390-546
  - EncryptedVolumeResourceCore base: lines 66051-66170+
  - SupplementalDataResourceCore: lines 15709-15770+
  - P/Invoke declarations: lines 45506-45547
- `/tmp/logos-decompile/DigitalLibrary/Libronix.DigitalLibrary.decompiled.cs` (102,572 lines)
- `/tmp/logos-decompile/Factbook/Libronix.DigitalLibrary.Factbook.decompiled.cs` (10,334 lines)

## Technical Notes

### sqlite3* Handle
`EncryptedVolume_OpenDatabase` returns a raw `sqlite3*` pointer. To query it from C#:

**Option A**: P/Invoke directly to SQLite C API (`sqlite3_prepare_v2`, `sqlite3_step`, etc.). The sqlite3 library may be:
- System `/usr/lib/libsqlite3.dylib`
- Bundled in libSinaiInterop.dylib (check with `nm -gU | grep sqlite3`)
- A cerod-enabled custom build somewhere in the Logos app bundle

**Option B**: Use `Microsoft.Data.Sqlite` NuGet package which supports creating connections from raw handles via `new SqliteConnection()` with a custom `SQLitePCLRaw` provider.

**Option C**: Use `EncryptedVolume_CreateConnectionStringDataSource` to get a connection string, then connect via ADO.NET. This requires the cerod VFS to be registered (which happens when libSinaiInterop is loaded).

### Reference Format in Databases
Bible references in dataset tables use "sort keys" for range intersection queries. The exact format needs investigation but appears to be a binary or string-encoded canonical reference that supports range matching (e.g., "find all entries that overlap with Romans 8:28-30").

### EncryptedVolumeResourceCore.SetDatabaseName Pattern
Each driver calls `SetDatabaseName("dbname.db")` in its constructor, which:
1. Creates a connection pool via `CreateConnectorPool(name)`
2. Uses `EncryptedVolume_OpenDatabase` under the hood
3. Pool provides `IConnector` instances for thread-safe SQL access
