# Logos Reader Hardening Plan

## Purpose
Improve the Logos library bridge without destabilizing the sermon companion or study tooling. Each fix below is intentionally small, independently testable, and safe to revert. Treat Logos private APIs as inherently brittle; make our code resilient around them.

## Current Baseline
- Catalog reports 4,493 locally available resources with file locations.
- Normal `.logos4` resources are readable after switching native library paths to Logos `Current`.
- Encrypted datasets (`.lbssd`, etc.) require `volume-info` / `query-db`, not the normal article reader path.
- Known-good smoke resources: `ESV.logos4`, `COMNTUSEOT.logos4`, `HAL.logos4`, `LOGOSLXX.logos4`, `LXXCAPP.logos4`.

## Guardrails
- Change one access path at a time.
- Add or update tests before broad refactors.
- Keep old fallback behavior until the replacement is proven.
- Prefer catalog/resource-id resolution over hardcoded filenames.
- After every step, run the narrow test plus a smoke read of the five known-good resources.

## Smoke Test Command
```bash
cd tools && python3 - <<'PY'
import study
for res in ["ESV.logos4", "COMNTUSEOT.logos4", "HAL.logos4", "LOGOSLXX.logos4", "LXXCAPP.logos4"]:
    out, err = study.run_reader("--info", res, timeout=60)
    print(res, "OK" if out else "FAIL", (out or err).splitlines()[0] if (out or err) else "")
study.shutdown_batch_reader()
PY
```

## Fix 1: Stabilize Native Library Resolution
Problem: `Program.cs` previously hardcoded a Logos versioned framework path.

Task:
- Keep `Versions/Current/.../Versions/Current/Resources/lib` paths.
- Add a startup check that prints the resolved native library path when initialization fails.

Test:
```bash
dotnet build tools/LogosReader/LogosReader.csproj --no-restore
cd tools && python3 -c "import study; print(study.run_reader('--info','ESV.logos4')[0].splitlines()[0]); study.shutdown_batch_reader()"
```

## Fix 2: Catalog-First Resource Resolution
Problem: Calls fail when using guessed filenames such as `HALOT.logos4` instead of actual files like `HAL.logos4`.

Task:
- Add `resolve_resource(query)` using `LibraryCatalog/catalog.db` + `ResourceManager.db`.
- Match by exact filename, resource id, abbreviated title, then title.
- Return filename, title, type, and a confidence reason.

Test:
```bash
cd tools/workbench && python3 -m pytest tests/test_resource_resolution.py -v
```

Cases: `HALOT -> HAL.logos4`, `BDAG -> BDAG.logos4`, `COMNTUSEOT -> COMNTUSEOT.logos4`.

## Fix 3: Better Failure Diagnostics
Problem: Many failures collapse to “Load result: Failed.”

Task:
- Distinguish wrong filename, missing file, locked resource, version incompatible, dataset passed to article reader, and native init failure.
- Surface these reasons in `study.run_reader()` callers.

Test:
```bash
cd tools/workbench && python3 -m pytest tests/test_reader_diagnostics.py -v
```

## Fix 4: Resource Ranking For Research
Problem: Commentary lookup often returns older/default resources before stronger scholarly sources.

Task:
- Add ranking profiles: `technical`, `pastoral`, `textual`, `background`.
- For `technical`, prioritize NIGTC, NICNT, BECNT, WBC, ICC, PNTC, EGGNT, COMNTUSEOT.
- Keep alphabetical fallback.

Test:
```bash
cd tools/workbench && python3 -m pytest tests/test_priority_ranker.py tests/test_resource_ranking.py -v
```

## Fix 5: LXX And Psalm Numbering Support
Problem: `find_chapter_article()` misses LXX resources because Psalm numbering/article IDs differ (`Psalm 14` may be `BK.19.13`).

Task:
- Add canonical-to-LXX Psalm mapping for Greek OT resources.
- Teach article lookup patterns like `BK.19.{chapter}` and Swete `PS.1.13`.
- Preserve Hebrew/English numbering for LHB and English Bibles.

Test:
```bash
cd tools/workbench && python3 -m pytest tests/test_lxx_reference_resolution.py -v
```

Cases: Psalm 14 resolves in `LOGOSLXX.logos4`; Psalm 53 resolves to LXX Psalm 52.

## Fix 6: Expose Existing Study Note Helpers
Problem: `find_study_bible_notes()` exists, but the CLI does not expose it.

Task:
- Add `--study-notes` CLI flag to `tools/study.py`.
- Include notes in normal and JSON output.

Test:
```bash
cd tools/workbench && python3 -m pytest tests/test_study_cli.py -v
python3 ../study.py "Romans 3:10-18" --study-notes --commentaries 0
```

## Fix 7: Dataset Access Wrappers
Problem: encrypted datasets open through `query-db`, but useful schema-aware access is incomplete.

Task:
- Add table introspection helper.
- Add tested wrappers for `NT-USE-OF-OT.lbssd` and `PSALMS-BROWSER.lbssd` first.
- Do not generalize until schemas are verified.

Test:
```bash
cd tools/workbench && python3 -m pytest tests/test_dataset_query.py tests/test_nt_use_of_ot_dataset.py -v
```

## Fix 8: Safer Text Cleanup
Problem: extracted text includes footnote markers, cross-reference symbols, language tags, and stray Unicode.

Task:
- Centralize cleanup in one function.
- Add fixtures from ESV, LHB, Logos LXX, and one commentary.
- Keep raw read available for debugging.

Test:
```bash
cd tools/workbench && python3 -m pytest tests/test_clean_text.py -v
```

## Fix 9: Full-Text Search Strategy
Problem: `--find-article` searches article IDs only, not article content.

Task:
- Add a bounded `find-text` command or Python-side article scan with limits.
- Cache hits by resource/query.
- Use only for selected resources to avoid slow whole-library scans.

Test:
```bash
cd tools/workbench && python3 -m pytest tests/test_resource_text_search.py -v
```

## Fix 10: Interlinear Isolation
Problem: interlinear extraction is fragile and avoided in batch mode.

Task:
- Keep interlinear calls isolated in subprocess mode.
- Add timeout and crash recovery tests.
- Document which resources support forward/reverse interlinears.

Test:
```bash
cd tools/workbench && python3 -m pytest tests/test_interlinear_reader.py -v
```

## Fix 11: Detect Cataloged-But-Not-Installed Resources
Problem: The catalog lists ~4,683 owned resources but ResourceManager records only ~4,493 local files. About 190 owned resources are not downloaded to disk. Calls to `get_resource_articles()` on those resources return an empty article list silently, indistinguishable from a resource that genuinely has no articles. Surfaced by the Daniel interpretive survey: Riddlebarger's *A Case for Amillennialism* (LLS:CSAMLLNLSM) is in the catalog but has no ResourceManager entry and no file on disk.

Task:
- Before opening a resource, verify that `Resources.Location` in `ResourceManager.db` exists as a readable file on disk.
- If the catalog has the entry but ResourceManager does not, return a diagnostic: "not locally installed — open Logos.app to download."
- At reader startup, log the count and a sample of cataloged-but-not-installed resources so the gap is visible.

Test:
```bash
cd tools/workbench && python3 -m pytest tests/test_resource_install_check.py -v
```

Cases: `LLS:CSAMLLNLSM` returns `not-locally-installed`; `LLS:EEC27DA` returns `ok`.

## Completion Criteria
- All existing workbench tests pass.
- Smoke test passes.
- A Romans 3:10-18 research run can retrieve BECNT, NICNT, NIGTC, WBC, ICC, COMNTUSEOT, LHB, Logos LXX, and Swete apparatus without manual filename lookup.
- Dataset queries for NT Use of OT and Psalms Explorer return structured rows or clear “no data” results.
- Cataloged-but-not-installed resources return a clear diagnostic rather than silent empty results.
