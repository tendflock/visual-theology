# Logos Non-.logos4 Format Test Results

**Date:** 2026-03-09
**Tool:** LogosReader + custom FormatTest programs using SinaiInterop native library
**Library version:** Logos 48.0.0.0238

## Executive Summary

**The LogosReader's `LoadTitleWithoutDataTypeOptions` API cannot open non-.logos4 format files.** These files (.lbslcr, .lbslms, .lbsrvi) use the same `LRES01` container format but require different driver code that the CTitle API does not support. However, several important findings emerged:

1. The `EncryptedVolume` API can open and read metadata from all three formats
2. Interlinear, reverse interlinear, and lemma data are **already accessible through the .logos4 Bible files themselves** via CTitle accessor functions
3. The .lbsrvi/.lbslms/.lbslcr files appear to be **standalone database resources** used by Logos internally, not directly readable through the CTitle article-based API

## Files Tested

| File | Size | Format | Resource ID | Driver Name | Driver Version |
|------|------|--------|-------------|-------------|----------------|
| BIBLEXREFS.lbslcr | 148 MB | Cross-reference DB | DB:BIBLE-XREFS | BibleCrossReferences | 2019-03-25 |
| Lemmas.lbslms | 63 MB | Lemma DB | DB:LEMMAS | Lemmas | 2019-09-26 |
| ESVNT.lbsrvi | 33 MB | Reverse interlinear | RVI:ESVNT | ReverseInterlinear | 2014-10-09 |

There are **115 .lbsrvi files** total, covering NT, OT, Apocrypha, and variant editions for many translations (ESV, NASB, NIV, KJV, NRSV, NET, NLT, CSB, etc.). The largest are ~120 MB (LXX variants).

## Detailed Test Results

### Test 1: SinaiInterop_TryGetResourceIdAndVersion

**Result: SUCCESS for all three files.**

This function can probe any LRES01 file and extract its resource ID and version without loading it.

```
BIBLEXREFS.lbslcr -> DB:BIBLE-XREFS v2023-11-29T16:45:15Z
Lemmas.lbslms     -> DB:LEMMAS v2025-09-12T11:49:29Z
ESVNT.lbsrvi      -> RVI:ESVNT v2026-02-17T13:49:16Z
```

### Test 2: LoadTitleWithoutDataTypeOptions (CTitle)

**Result: FAILED for all three files with all load hints (Normal, Lite, Indexing).**

The `SinaiInterop_LoadTitleWithoutDataTypeOptions` function returns `TitleLoadResult.Failed` for all non-.logos4 formats. This function is designed for the "logos" driver and cannot handle BibleCrossReferences, Lemmas, or ReverseInterlinear drivers.

The `SinaiInterop_LoadTitle` variant (with DataTypeOptionsCallback parameter) also fails.

### Test 3: EncryptedVolume API

**Result: PARTIAL SUCCESS - metadata readable, internal data not directly accessible.**

`EncryptedVolume_New()` + `EncryptedVolume_Open()` works for all three files, providing:
- Resource ID, version, driver name, driver version, data types required version

However:
- `EncryptedVolume_OpenFile()` returns null for ALL internal file names tested (data, content, index, main, metadata, crossreferences, xrefs, lemmas, interlinear, 0, 1, data.db, etc.)
- `EncryptedVolume_OpenDatabase()` returns null for all names tested
- `EncryptedVolume_CreateConnectionStringDataSource()` returns non-null for ANY name (it appears to construct a connection string object unconditionally, not validate the name)

The encrypted data within these files requires driver-specific code to decrypt and interpret.

### Test 4: EfsVolumeProxy

**Result: CRASH (segfault) on TryOpenFromFile.**

The `EfsVolumeProxy_TryOpenFromFile` function caused a segfault, likely due to the C-wrapper function signature not matching the expected calling convention.

### Test 5: CLibronixFile

**Result: FAILED - OpenFile returned null for all tested files.**

### Test 6: ReverseInterlinearData API

**Result: Object created successfully, but ResourceIdToVersion returns empty strings for all resource IDs tested.**

`ReverseInterlinearData_New(licMgr, path)` creates an object from .lbsrvi files. However, `ReverseInterlinearData_ResourceIdToVersion()` returns empty strings for every resource ID tried, including:
- The ESV's actual resource ID: LLS:1.0.710
- Greek source texts: LLS:SBLGNT, LLS:NA28
- Various LLS:1.0.N patterns (1-100)
- Plain names: ESV, SBLGNT, ESVNT

This API appears to be designed for internal use and may require additional context (like a loaded DataTypeManager) to function properly.

### Test 7: CInterlinearData API

**Result: Objects created but empty for non-.logos4 files.**

`CInterlinearData_New(licMgr, path)` succeeds for all three file types but returns `LineCount: 0`. This API expects the data to come from a loaded CTitle, not from standalone database files.

## Critical Finding: Interlinear Data in .logos4 Files

The most important discovery is that **interlinear and reverse interlinear data is embedded within and accessible from the .logos4 Bible files themselves**:

### ESV.logos4 (LLS:1.0.710)

```
IsBible: True
HasInterlinear: True
HasReverseInterlinear: True
ArticleCount: 49,606
```

The ESV's `CTitle_GetInterlinearData()` returns a CInterlinearData object with **10 interlinear lines**:

| Line | Label | Show by Default |
|------|-------|----------------|
| 0 | Surface | Yes |
| 1 | Manuscript | Yes |
| 2 | Manuscript (Transliterated) | No |
| 3 | Lemma | Yes |
| 4 | Lemma (Transliterated) | No |
| 5 | Root | No |
| 6 | Root (Transliterated) | No |
| 7 | Morphology | Yes |
| 8 | Strong's Numbers | Yes |
| 9 | Louw-Nida | Yes |

**`GetInterlinearData()` and `GetReverseInterlinearData()` return the SAME pointer**, meaning the CInterlinearData object serves both forward and reverse interlinear data.

### Other Bibles with Reverse Interlinear

Many loaded .logos4 Bible files have `HasReverseInterlinear: True`:

| File | Resource ID | Has RVI | Has Interlinear |
|------|-------------|---------|-----------------|
| ESV.logos4 | LLS:1.0.710 | Yes | Yes |
| NIV2011.logos4 | LLS:NIV2011 | Yes | Yes |
| LELXX2.logos4 | LLS:LELXX2 | Yes | Yes |
| AV1873.logos4 | LLS:AV1873 | Yes | Yes |
| VULGATACLEM.logos4 | LLS:VULGATACLEM | Yes | Yes |
| GS_NETBIBLE.logos4 | LLS:1.0.1026 | Yes | Yes |
| NCPBWITHAPOCR.logos4 | LLS:NCPBWITHAPOCR | Yes | Yes |

## Raw File Format

All three file types share the same LRES01 header format:

```
Offset 0x00: "LRES01\r\n"                    (8 bytes - magic)
Offset 0x08: Resource ID (40 bytes, padded)   + "\r\n"
Offset 0x32: Commerce ID (40 bytes, padded)   + "\r\n"
Offset 0x5C: Version timestamp                + "\r\n"
Offset 0x76: Driver name (30 bytes, padded)   + "\r\n"
Offset 0x96: Driver version timestamp         + "\r\n"
Offset 0xB0: DataTypes version (20 bytes)     + "\r\n"
Offset 0xC6: 0x1A (EOF marker)
```

After the header, data is encrypted (not SQLite, not plain text).

## Implications for the Memory Project

### Cross-References (BIBLEXREFS.lbslcr)
- **Not directly readable** through any available API
- Cross-reference data would need to be extracted by other means (Logos app UI, or finding the actual driver implementation)
- The `BibleCrossReferences` driver is part of the encrypted volume system

### Lemmas (Lemmas.lbslms)
- **Not directly readable** through the available APIs
- However, **lemma data IS accessible through the .logos4 Bible interlinear data** (Line 3: "Lemma", Line 4: "Lemma (Transliterated)")
- The standalone Lemmas.lbslms is likely a global lookup database used by the Logos search engine

### Reverse Interlinear (*.lbsrvi)
- The `ReverseInterlinearData_New` API can create objects from these files but doesn't expose useful query functions through the C API
- **Reverse interlinear data IS accessible through CTitle on loaded .logos4 Bible files** - the ESV.logos4 reports `HasReverseInterlinear: True` and returns interlinear line data including Surface text, Manuscript, Lemma, Root, Morphology, Strong's Numbers, and Louw-Nida
- The standalone .lbsrvi files likely contain the mapping tables used at indexing time

### Recommended Path Forward

1. **For interlinear/lemma data**: Access through the loaded .logos4 Bible CTitle objects, which already have `HasInterlinear: True` and expose 10 interlinear data lines. The key challenge is finding the API to extract actual per-word interlinear data (the NativeLogosResourceIndexer has a `ProcessReverseInterlinearIndexData` callback that processes this data during indexing).

2. **For cross-references**: The BIBLEXREFS.lbslcr cannot be read through available APIs. Possible approaches:
   - Use the Logos desktop app's export/copy features
   - Investigate the NativeLogosResourceIndexer which has an `AddReference` callback
   - Look for additional native libraries that handle the BibleCrossReferences driver

3. **For full interlinear extraction**: The `NativeLogosResourceIndexer_New` + `IndexArticle` + callback pattern may be the way to extract per-word interlinear data from loaded CTitle objects. The callback receives word-by-word data including references and reverse interlinear column data.

## Available SinaiInterop APIs Summary

| API | .logos4 | .lbslcr | .lbslms | .lbsrvi |
|-----|---------|---------|---------|---------|
| TryGetResourceIdAndVersion | Yes | Yes | Yes | Yes |
| LoadTitleWithoutDataTypeOptions | Yes | No | No | No |
| EncryptedVolume_Open (metadata) | Yes | Yes | Yes | Yes |
| EncryptedVolume_OpenFile | No* | No | No | No |
| EncryptedVolume_OpenDatabase | No* | No | No | No |
| CInterlinearData_New (w/ lines) | N/A | 0 lines | 0 lines | 0 lines |
| ReverseInterlinearData_New | N/A | N/A | N/A | Yes (empty results) |
| CTitle HasInterlinear | Yes | N/A | N/A | N/A |
| CTitle HasReverseInterlinear | Yes | N/A | N/A | N/A |
| CTitle GetInterlinearData | 10 lines | N/A | N/A | N/A |

*OpenFile/OpenDatabase return null for all tested internal names on .logos4 as well.

## Test Programs Created

- `/Volumes/External/Logos4/tools/FormatTest/` - Initial EncryptedVolume/EfsVolumeProxy/CLibronixFile tests
- `/Volumes/External/Logos4/tools/FormatTest2/` - Deeper EncryptedVolume OpenFile/OpenDatabase probing
- `/Volumes/External/Logos4/tools/FormatTest3/` - Control test (.logos4 capabilities) + GetSupportedDriverVersions
- `/Volumes/External/Logos4/tools/FormatTest4/` - ReverseInterlinearData with known IDs + Bible RVI survey
- `/Volumes/External/Logos4/tools/FormatTest5/` - CInterlinearData exploration + interlinear line labels

## .lbsrvi File Inventory (115 files)

NT reverse interlinears: ASVNT, CJBNT, CSBNT, DARBYNT, ESVCENT, ESVNT, HCSBNT, KJV1900NT, LEBNT, LSBNT, MEVNT, NABRENT, NASB2020NT, NASB77NT, NASB95PARANT, NASBNT, NCPBNT, NCVNT, NEBNT, NET2NT, NETNT, NIV1984ANGNT, NIV2011ANGNT, NIV2011NT, NIVNT, NKJVNT, NLTNT, NRSVCENT, NRSVNT, NRSVUENT, PASSIONNT, REBNT, RSV2CENT, RSVCENT, RSVNT, TLVNT, VULNT, YLTNT, and more.

OT reverse interlinears: ASVOT, CJBOT, CSBOT, DARBYOT, ESVCEOT, ESVOT, HCSBOT, KJV1900OT, LEBOT, LSBOT, MEVOT, NASB2020OT, NASB77OT, NASB95PARAOT, NASBOT, NCPBOT, NCVOT, NLTOT, NRSVCEOT, NRSVOT, NRSVUEHEBOT, RSV2CEOT, RSVCEOT, RSVOT, TLVOT, VULOT, YLTOT, and more.

LXX/Apocrypha: LELXX2, LELXX2AT, LELXXAT, LESLXX, LOGOSLXXVARRI, LXXHEB, SWETELXXLHB, SWETELXXLHBALT, various APOC/DC variants.

Special: APFTHRI, EOBNTRI, LAKEAF, NABREGRKOT, NABREGRKOTALT, NABREHEBOT.
