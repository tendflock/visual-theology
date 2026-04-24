# `.lbxlls` Investigation and Implementation Plan

## Executive Summary

The important finding is that the current native load path already opens the three sample `.lbxlls` files. On April 24, 2026 I ran the existing compiled reader (`LogosReader.dll`) with the current `SinaiInterop_LoadTitleWithoutDataTypeOptions` call, and all three loaded successfully, listed articles, and returned article text.

That means this is not primarily a “reverse-engineer and implement a new native `.lbxlls` decoder” problem. The likely fix is to treat `.lbxlls` as a supported resource extension everywhere above the native loader, and to audit catalog/discovery logic that may still assume `.logos4` or specific commentary metadata patterns.

## 1. File Format Findings

### Sample `.logos4`
- File: `EEC27DA.logos4`
- `file`: `data`
- First bytes:
  - `4c 52 45 53 30 31 0d 0a` = `LRES01\r\n`
  - Followed by readable metadata:
    - `LLS:EEC27DA`
    - `2020-03-25T22:20:30Z`
    - `logos`
    - `2019-06-28T00:00:00Z`
- `strings -n 8` shows the resource id/version header immediately.

### Sample `.lbxlls`
- File: `HRMNEIA27DA.lbxlls`
- `file`: `data`
- First bytes:
  - `4c 54 45 53` = `LTES`
  - Then `00 00 01 01`
  - Then a 32-bit little-endian value that varies per file
  - Then mostly high-entropy binary data
- `strings -n 8` shows almost no useful metadata near the start; output looks like encrypted/compressed noise.
- No `SQLite format 3` signature found anywhere in the sampled `.lbxlls`.
- No ZIP `PK\x03\x04` / `PK\x05\x06` / `PK\x07\x08` signatures found.
- One sample contained a lone `lbxm` string late in the file, but not enough to identify a container structure.

### Likely structural difference

`.logos4` has a clear text header with resource id/version/driver metadata in the file itself. `.lbxlls` uses a compact binary header (`LTES`) and keeps metadata opaque until opened through Logos’ native libraries.

Based on the on-disk shape and runtime metadata dates, `.lbxlls` looks like a legacy pre-`.logos4` encrypted title container, not a newer SQLite- or ZIP-based format. The three sampled `.lbxlls` resources reported these native metadata values after open:

- `HRMNEIA27DA.lbxlls` -> `LLS:HRMNEIA27DA`, version `2006-11-01T18:45:06Z`, driver `2006-04-20T16:21:19Z`
- `GS_WALV_DANIEL.lbxlls` -> `LLS:gs_walv_daniel`, version `2008-12-17T21:10:46Z`, driver `2006-04-20T16:21:19Z`
- `PROGDISPNM.lbxlls` -> `LLS:PROGDISPNM`, version `2009-06-26T20:21:15Z`, driver `2008-05-14T19:22:40Z`

By contrast, the sampled `.logos4` file reported version `2020-03-25T22:20:30Z`, driver `2019-06-28T00:00:00Z`.

## 2. Native Export Inventory

### `libSinaiInterop.dylib`

Relevant exported symbols include:

- `SinaiInterop_LoadTitle`
- `SinaiInterop_LoadTitleWithoutDataTypeOptions`
- `SinaiInterop_TryGetResourceIdAndVersion`
- `SinaiInterop_CTitle_*`
- `EncryptedVolume_Open`
- `EncryptedVolume_OpenDatabase`
- `EncryptedVolume_OpenFile`
- `EfsVolumeProxy_TryOpenFromFile`
- `EfsVolumeProxy_TryOpenStream`

I did **not** find exported symbols named `Ltes*`, `LTES*`, `lbxlls`, `ResourceReader`, or similar format-specific entry points.

### `libsqlite3-logos.dylib`

Exports looked like standard SQLite API surface (`sqlite3_open`, `sqlite3_open_v2`, `sqlite3_blob_open`, etc.). I did **not** find `.lbxlls`-specific or `Ltes*` exports there either.

### Interpretation

The fast path is already present: the generic title loader in `libSinaiInterop.dylib` can open `.lbxlls`. No separate public native entry point appears necessary.

One caveat: `SinaiInterop_TryGetResourceIdAndVersion` appears to succeed for `.logos4` but not for the sampled `.lbxlls` files. `OpenResource()` still succeeds because it ignores failure from that preflight call and proceeds to `LoadTitleWithoutDataTypeOptions`.

## 3. Existing `Program.cs` Call Pattern

`/Volumes/External/Logos4/tools/LogosReader/Program.cs` does this:

1. Initializes `libSinaiInterop.dylib`
2. Creates and loads `LicenseManagerCore`
3. Calls `SinaiInterop_TryGetResourceIdAndVersion(...)`
4. Calls `SinaiInterop_LoadTitleWithoutDataTypeOptions(...)`
5. Uses `SinaiInterop_CTitle_*` accessors for article ids, text, TOC, nav index, etc.

There is no format branch for `.logos4` vs `.lbxlls`. The loader is already generic.

## 4. Runtime Validation

All of these succeeded with the existing compiled reader and the existing Python wrapper:

- `--info` on all 3 `.lbxlls` files
- `--list` on `HRMNEIA27DA.lbxlls`
- reading article `0` from `HRMNEIA27DA.lbxlls` and `PROGDISPNM.lbxlls`
- `study.run_reader('--info', full_lbxlls_path)`
- `study.get_resource_articles(full_lbxlls_path)`
- `study.read_article_text(full_lbxlls_path, 0)`
- `study.find_commentary_section(full_lbxlls_path, parse_reference('Daniel 1:1'))` for:
  - `GS_WALV_DANIEL.lbxlls`
  - `HRMNEIA27DA.lbxlls`

So the reader stack can already read `.lbxlls` when given the real file path.

## 5. Recommended Implementation Approach

### Recommendation

Choose **(a) do not add a new native reader; wire existing support through the current stack**.

Concretely:

1. Treat `.lbxlls` as a first-class resource extension anywhere filenames are resolved or defaulted.
2. Do not use `SinaiInterop_TryGetResourceIdAndVersion` failure as proof that a resource cannot open.
3. Prefer the exact path from `ResourceManager.db.Resources.Location` over synthesized filenames.
4. Add integration tests that prove `.lbxlls` works through the current `LogosReader` and Python helpers.

### Likely code areas to audit

- `study.py`
  - `resolve_bible_files()` currently falls back to appending `.logos4`
  - any bare-name or curated-list paths that assume `.logos4`
- any higher-level selection code that stores only filename stems and reconstructs paths
- any capability/probe logic that treats pre-open metadata lookup failure as an open failure

### Adjacent discovery issue

There is at least one non-extension issue in commentary discovery:

- `GS_WALV_DANIEL.lbxlls` is returned by `find_commentaries_for_ref('Daniel 1:1')`
- `HRMNEIA27DA.lbxlls` is not, because `ReferenceSupersets` is `bible+bhs.27`
- `PROGDISPNM.lbxlls` is `text.monograph`, not `text.monograph.commentary.bible`

So if those titles are “blocked” in app UX, extension handling may not be the only cause.

## 6. Ordered Task List

1. Add a reader smoke test for one `.logos4` and the three `.lbxlls` files using the existing loader.
2. Audit filename resolution code for `.logos4` defaults and make extension handling symmetric (`.logos4` + `.lbxlls`).
3. Audit any preflight logic that uses `TryGetResourceIdAndVersion`; remove it as a gate.
4. Add Python integration tests for `get_resource_articles`, `read_article_text`, and `find_commentary_section` on at least one `.lbxlls`.
5. Decide whether commentary discovery should include OT supersets like `bible+bhs.*`.
6. Decide whether monographs like `PROGDISPNM` should remain outside commentary search or be surfaced elsewhere.
7. Update docs/help text to say the reader supports both `.logos4` and `.lbxlls`.

## 7. Risks and Unknowns

- Support depends on Logos’ shipped native libraries; this is not a standalone decoder.
- `TryGetResourceIdAndVersion` may remain incomplete for `.lbxlls`.
- Commentary discovery semantics are partly separate from file-format support.
- I did not reverse the full `LTES` block layout because the current fix does not require it.

## 8. Test Plan

### Must keep working
- `EEC27DA.logos4`
  - `--info`
  - `--list`
  - read article `0`

### Must work after fix
- `HRMNEIA27DA.lbxlls`
  - `--info`
  - `--list`
  - read article `0`
  - `find_commentary_section(Daniel 1:1)`
- `GS_WALV_DANIEL.lbxlls`
  - `--info`
  - `find_commentary_section(Daniel 1:1)`
  - `find_commentaries_for_ref(Daniel 1:1)` should continue to surface it
- `PROGDISPNM.lbxlls`
  - `--info`
  - `--list`
  - read article `0`
  - not expected in commentary search unless product requirements expand monograph handling

