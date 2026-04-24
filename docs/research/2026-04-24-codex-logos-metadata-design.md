# libSinaiInterop.dylib Metadata Exports: Design Notes

Investigation date: 2026-04-24  
Workspace: `/Volumes/External/Logos4`  
Throwaway probes used: `/tmp/probe_logos_metadata/Program.cs`, existing `tools/LogosReader`

## 1. Exports map

### ResourceVolume / milestone-related exports

| C export | Mangled / demangled | What it actually does |
|---|---|---|
| `_SinaiInterop_ResourceVolume_HasEmbeddedMilestoneIndex` | `__ZN12SinaiInterop40ResourceVolume_HasEmbeddedMilestoneIndexEPN5Sinai18ResourceVolumeBaseE` = `SinaiInterop::ResourceVolume_HasEmbeddedMilestoneIndex(Sinai::ResourceVolumeBase*)` | Direct vtable dispatch. This is the reliable boolean gate. `True` for `RFRMDSYSTH04.logos4`; `False` for the two tested `.lbxlls` files. |
| `_SinaiInterop_ResourceVolume_GetMilestoneIndexDatabaseDataSource` | `__ZN12SinaiInterop50ResourceVolume_GetMilestoneIndexDatabaseDataSourceEPN5Sinai18ResourceVolumeBaseE` = `SinaiInterop::ResourceVolume_GetMilestoneIndexDatabaseDataSource(Sinai::ResourceVolumeBase*)` | Returns a UTF-16 string, not a pointer/handle. Example: `*cerod*:cerod::/Volumes/.../RFRMDSYSTH04.logos4;MilestoneIndexCerodDb.mstidx`. |
| `_SinaiInterop_ResourceVolume_GetFullPath` | `__ZN12SinaiInterop26ResourceVolume_GetFullPathEPN5Sinai18ResourceVolumeBaseE` | Returns canonical volume path. Useful because the working open path was `EncryptedVolume_Open(fullPath)` + `OpenDatabase("MilestoneIndexCerodDb.mstidx")`. |
| `_SinaiInterop_ResourceVolume_GetLogos4MetadataStream` | `__ZN12SinaiInterop38ResourceVolume_GetLogos4MetadataStreamEPN5Sinai18ResourceVolumeBaseE` | Returns `IStream*`. Not used here; no evidence this is a better source than the milestone DB. |
| `_SinaiInterop_ResourceVolume_GetUniqueMetadataStream` | `__ZN12SinaiInterop38ResourceVolume_GetUniqueMetadataStreamEPN5Sinai18ResourceVolumeBaseEPP7IStream` | Returns `IStream**` via vtable. Not probed further. |
| `_SinaiInterop_ResourceVolume_HasArticleImageRectanglesData` | `__ZN12SinaiInterop44ResourceVolume_HasArticleImageRectanglesDataEPN5Sinai18ResourceVolumeBaseE` | Unrelated to page/section metadata. |
| `_SinaiInterop_ResourceVolume_HasLiteEdition` / `_IsLDLS3` / `_IsLSFLIX` | matching `SinaiInterop::ResourceVolume_*` demangles | Format/edition flags; no direct metadata payoff in this pass. |

### EncryptedVolume / SQLite bridge exports

| C export | Demangled note | What it actually does |
|---|---|---|
| `_EncryptedVolume_OpenDatabase` | wraps `LbxUtil::EncryptedVolume::OpenDatabase(std::u16string const&) const` | Returns the working `sqlite3*` handle for `MilestoneIndexCerodDb.mstidx` inside `RFRMDSYSTH04.logos4`. |
| `_EncryptedVolume_CreateConnectionStringDataSource` | unresolved refs show both static and instance `CreateConnectionStringDataSource(...)` overloads | Produces the same kind of `cerod` connection-string datasource string. Not needed for the successful open path. |
| `ResUtil::c_pszDefaultMilestoneIndexDatabase` | unresolved const symbol | Best inference: default DB name is `MilestoneIndexCerodDb.mstidx`, matching the returned datasource string and the working `OpenDatabase` call. |

### Already-wired exports that turned out to be the real metadata source

| C export | Demangled note | What it actually does |
|---|---|---|
| `_SinaiInterop_CTitle_ArticleNumberToArticleId` | `SinaiInterop::CTitle_ArticleNumberToArticleId(...)` | This already returns the UI-visible native section/article ID. Example: article `4718` in `RFRMDSYSTH04` -> `R48.2`. |
| `_SinaiInterop_GetArticleTitle` | `SinaiInterop::GetArticleTitle(CTitle*, Sinai::ResourceVolumeBase*, unsigned int, std::u16string&)` | Best heading source found. Example: article `4716` -> `Chapter 27: The Structure of Inaugurated Eschatology`; article `4718` -> `A Failed Expectation`. |
| `NativeLogosResourceIndexerCallbackImpl::AddNamedSectionStart/End` | `...AddNamedSectionStart(char16_t const*, unsigned long)` | Empirically not the source of `R48.2`-style IDs. On tested resources it either emitted nothing relevant or only Bible data-type markers like `bible-verse`. |

### Negative finding

Public symbol search did **not** surface any richer `Page` / `Citation` / `Publication` / `Edition` export family beyond the `ResourceVolume_*` milestone path above. No separate “printed citation” API showed up.

## 2. Milestone index structure

## Access path verdict

The leading hypothesis was only half right.

- `ResourceVolume_GetMilestoneIndexDatabaseDataSource(...)` does identify the milestone DB, but it returns a **string connection descriptor**, not an open DB handle.
- Raw `sqlite3_open_v2()` on that string failed with `rc=14` / `unable to open database file`.
- The **working** path was:
  1. `ResourceVolume_GetFullPath(volume)` -> `/Volumes/.../RFRMDSYSTH04.logos4`
  2. `EncryptedVolume_Open(...)` on that file
  3. `EncryptedVolume_OpenDatabase(vol, "MilestoneIndexCerodDb.mstidx")`

So for reader work, the practical path is: use `HasEmbeddedMilestoneIndex` as the gate, then reopen the volume through `EncryptedVolume_*`.

## Per-resource results

### A. `RFRMDSYSTH04.logos4`

- `HasEmbeddedMilestoneIndex = True`
- `MilestoneDataSource = *cerod*:cerod::/Volumes/.../RFRMDSYSTH04.logos4;MilestoneIndexCerodDb.mstidx`
- `EncryptedVolume_OpenDatabase("MilestoneIndexCerodDb.mstidx")` works

Schema:

```text
Info(
  Version INTEGER NOT NULL,
  DriverMetadataVersion TEXT NOT NULL
)

DataTypes(
  DataTypeName TEXT PRIMARY KEY,
  IndexType TEXT NOT NULL,
  TableName TEXT NOT NULL
)

Headwords(
  Language TEXT PRIMARY KEY,
  TableName TEXT NOT NULL
)

SegmentReferences_page(
  TextSegmentOffset INT NOT NULL,
  TextSegmentPastEnd INT NOT NULL,
  Reference BLOB NOT NULL,
  ReferenceStartSortKey BLOB NOT NULL,
  ReferencePastEndSortKey BLOB NOT NULL
)

SegmentReferences_vp(
  same columns as SegmentReferences_page
)
```

Table counts:

- `Info`: `1`
- `DataTypes`: `2`
- `Headwords`: `0`
- `SegmentReferences_page`: `1232`
- `SegmentReferences_vp`: `1232`

Sample rows:

```text
Info
Version=5 | DriverMetadataVersion=2009-10-08T00:00:00Z

DataTypes
DataTypeName=page | IndexType=Binary | TableName=SegmentReferences_page
DataTypeName=vp   | IndexType=Binary | TableName=SegmentReferences_vp
```

Early `page` rows:

```text
TextSegmentOffset=644275 | TextSegmentPastEnd=644391 | ReferenceHex=0003020500 | StartHex=02010501000000 | EndHex=02010501010000
TextSegmentOffset=644391 | TextSegmentPastEnd=646494 | ReferenceHex=0003020600 | StartHex=02010601000000 | EndHex=02010601010000
TextSegmentOffset=646494 | TextSegmentPastEnd=646909 | ReferenceHex=0003020700 | StartHex=02010701000000 | EndHex=02010701010000
```

Article `4718` (`R48.2`) spans offsets `2007383..2011146`. Overlapping milestone rows:

```text
SegmentReferences_page
2007383..2009452 | ReferenceHex=000302D90500
2009452..2011685 | ReferenceHex=000302DA0500

SegmentReferences_vp
2007383..2009452 | ReferenceHex=0005040002D90500
2009452..2011685 | ReferenceHex=0005040002DA0500
```

Best hypothesis for column semantics:

- `TextSegmentOffset` / `TextSegmentPastEnd`: absolute character-range coverage in the title text.
- `Reference`: encoded Logos reference datum.
  - For `page`, the trailing little-endian integer appears to be the printed page number.
  - For `vp`, the trailing little-endian integer matches the same ordinal but wrapped in a different data type.
- `ReferenceStartSortKey` / `ReferencePastEndSortKey`: sortable binary keys for the same reference, likely inclusive/exclusive bounds.

For the `page` table, the evidence is strong:

- `0003020500` corresponds to page `5`
- `000302D90500` corresponds to page `1497`
- `000302DA0500` corresponds to page `1498`

I would treat that as confirmed enough to implement, but still as a resource-format decode rather than a documented contract.

### B. `HRMNEIA27DA.lbxlls`

- `HasEmbeddedMilestoneIndex = False`
- `MilestoneDataSource` still returns a cerod-looking string
- Raw `sqlite3_open_v2()` on that string fails
- `EncryptedVolume_Open(...)` on the `.lbxlls` file fails
- No accessible milestone DB discovered

Sample rows: none; no schema available.

### C. `GS_WALV_DANIEL.lbxlls`

- `HasEmbeddedMilestoneIndex = False`
- `MilestoneDataSource` still returns a cerod-looking string
- Raw `sqlite3_open_v2()` on that string fails
- `EncryptedVolume_Open(...)` on the `.lbxlls` file fails
- No accessible milestone DB discovered

Sample rows: none; no schema available.

## 3. Section-ID source of truth

Recommendation:

- **Native section ID:** use `CTitle_ArticleNumberToArticleId`
- **Section heading:** use `SinaiInterop_GetArticleTitle`
- **Page number:** use milestone DB `SegmentReferences_page` when `HasEmbeddedMilestoneIndex`

Specific answer for `R48.2`-style UI anchors:

- `RFRMDSYSTH04`, article `4718` -> `CTitle_ArticleNumberToArticleId(...) = "R48.2"`
- This is already the exact human-readable anchor Bryan wants
- The milestone DB does **not** expose `R48.2`; it exposes page/vp milestones only

Why not use `AddNamedSectionStart(...)`?

- I scanned all articles in all three test resources.
- `RFRMDSYSTH04`: `NamedSectionEventsObserved = 0`
- `HRMNEIA27DA`: named events were only `bible-verse`, `content-verse`, `bible-chapter`, `bible-book`
- `GS_WALV_DANIEL`: same pattern

So the callback is useful for Bible-data milestones, not for book-native section IDs.

## 4. Page-number verdict

**Yes, printed page numbers are exposed at all.**

But the precise answer is:

- They are exposed **for some resources** via the embedded milestone DB, specifically the `SegmentReferences_page` table.
- They are **not universal** across the tested library surface.
- In this test set, only `RFRMDSYSTH04.logos4` exposed them.
- `HRMNEIA27DA.lbxlls` and `GS_WALV_DANIEL.lbxlls` did **not** expose an accessible embedded milestone DB through the investigated exports.

So the schema should treat page as:

- required when the resource has a `page` milestone table and the quote/article overlaps a page milestone
- nullable otherwise

Do **not** derive authoritative print pages from `vp` unless product explicitly accepts virtual/Logos page ordinals as a fallback.

## 5. Proposed reader extension

Add a non-breaking command:

```bash
dotnet run -- article-meta RESOURCE ARTICLE
```

Proposed JSON:

```json
{
  "backend": {
    "resourceId": "LLS:RFRMDSYSTH04",
    "logosArticleNum": 4718,
    "nativeSectionId": "R48.2",
    "pageStart": 1497,
    "pageEnd": 1498
  },
  "frontend": {
    "author": "Beeke & Smalley",
    "title": "Reformed Systematic Theology, Vol. 4: Church and Last Things",
    "section": "§R48.2 — A Failed Expectation",
    "page": null,
    "citationString": "Beeke & Smalley, RST 4, §R48.2, pp. 1497-1498"
  },
  "article": {
    "articleId": "R48.2",
    "heading": "A Failed Expectation",
    "absoluteStart": 2007383,
    "absoluteEnd": 2011146
  }
}
```

Why `page: null` above?

- At **article** granularity, one article can span multiple printed pages.
- For `4718`, it spans pages `1497` and `1498`.
- So the article command should emit `pageStart/pageEnd`.
- Downstream quote extraction or verification can collapse that to a single `frontend.page` when the quote falls on one page.

Implementation shape:

1. Open title as today.
2. `resourceId = SinaiInterop_CTitle_GetResourceId(title)`
3. `nativeSectionId = SinaiInterop_CTitle_ArticleNumberToArticleId(title, articleNum)`
4. `articleStart = SinaiInterop_CTitle_GetAbsoluteCharacterOffsetForArticle(title, articleNum, true)`
5. `articleLen = CTitle_GetArticleLength(title, articleNum)`
6. `articleEnd = articleStart + articleLen`
7. `heading = SinaiInterop_GetArticleTitle(title, resourceVolume, articleNum)`; if blank, leave null
8. If `HasEmbeddedMilestoneIndex(resourceVolume)`:
   - `fullPath = ResourceVolume_GetFullPath(resourceVolume)`
   - `EncryptedVolume_Open(fullPath)`
   - `EncryptedVolume_OpenDatabase("MilestoneIndexCerodDb.mstidx")`
   - query `SegmentReferences_page` for overlapping rows:

```sql
select TextSegmentOffset, TextSegmentPastEnd, Reference
from SegmentReferences_page
where TextSegmentOffset < @articleEnd
  and TextSegmentPastEnd > @articleStart
order by TextSegmentOffset;
```

9. Decode `Reference` blobs for the page rows and compute `pageStart/pageEnd`
10. Build `frontend.section` as:

```text
§{nativeSectionId} — {heading}
```

Optional follow-on command, if Bryan wants exact quote-page resolution later:

```bash
dotnet run -- quote-meta RESOURCE ARTICLE QUOTE_START QUOTE_END
```

That command should map the quote’s sub-article char range onto the same milestone table and set a single `frontend.page` when possible.

## 6. Risks and non-obvious gotchas

- `GetMilestoneIndexDatabaseDataSource()` is **not** an open DB handle. It returns a string descriptor. Raw `sqlite3_open_v2()` on that string failed in this environment.
- `HasEmbeddedMilestoneIndex()` is the real guard. The datasource string is returned even for resources where no accessible milestone DB exists.
- `.lbxlls` is not enough to imply a usable milestone DB. Both tested `.lbxlls` targets failed here.
- `query-db` currently treats BLOBs as text; real implementation must use `sqlite3_column_blob()` / `sqlite3_column_bytes()` or equivalent byte extraction. Without that, page decode is invisible.
- `page` is not always a scalar at article level. Many articles span multiple milestone rows.
- Page coverage is not total. In `RFRMDSYSTH04`, the first `page` milestone begins at offset `644275`, so early/front-matter articles may have no page.
- `GetArticleTitle()` is useful but not universal; some articles return blank. The command should allow `heading = null`.
- `AddNamedSectionStart()` is not the source of book-native section IDs in these tests. Do not build around it for `R48.2`.
- `ResourceVolume*` should be treated as dependent on the live `CTitle*`. Do metadata extraction before releasing the title.
- Callback names are UTF-16 `char16_t*`; explicit UTF-16 marshalling is required.
- TOC is not a reliable fallback here. On `RFRMDSYSTH04`, `--toc` returned root `-1`.

## Bottom line

- **Native section ID**: already available via `ArticleNumberToArticleId`
- **Section heading**: use `GetArticleTitle`
- **Printed page**: use embedded milestone DB `SegmentReferences_page` when `HasEmbeddedMilestoneIndex == true`
- **Do not** use `AddNamedSectionStart` for `R48.2`-style IDs
- **Do not** assume page exists for every resource; the two tested `.lbxlls` commentaries did not expose it through this path
