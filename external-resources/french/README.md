# French primary-text OCR (reserved)

Per-language subdirectory provisioned for `external-ocr` citations whose
`quote.language == "fr"`. **Currently empty.** No audited Wave 6 / Wave 7
voice in the current pilot scope produces French primary text, but the
backend, validator, and schema all support French OCR; this directory
exists so the contract is uniform across all 7 OCR languages
(`grc`, `la`, `he`, `arc`, `jrb`, `de`, `fr`). `en` is also accepted on
`quote.language` and on `translations[].language` as a non-OCR target,
but no `external-resources/english/` subdirectory exists — English
primary text comes from Logos / EPUB / PDF / Sefaria backends, not OCR.

## When this directory becomes load-bearing

Reserved for future surveys whose primary text is in French and is not
already in the Logos library. Likely candidates:

- **Calvin's French sermons** (the `Sermons sur le livre de Daniel`
  Genève editions, 1561 onward; some material is in Logos but not all
  edition variants).
- **French-Reformation Daniel commentary** outside the project's
  current scholar queue (e.g., Théodore de Bèze's marginalia,
  17th-century Huguenot exposition, Calvin's French OT prefaces in
  their original-language printing).
- **Modern French Catholic / academic editions** whose scholarly
  apparatus is not in English (Cazelles' *Sources chrétiennes* notes,
  the *Bible de Jérusalem* dossier-prefaces, etc.) — only if the
  surveyed scholar's argument hangs on French phrasing the schema must
  preserve.

## Citation contract

Same as the other OCR language subdirectories. Set
`backend.kind = "external-ocr"`, `backend.filename = "french/<file>.txt"`,
and `quote.language = "fr"`. The validator enforces that
`backend.filename` begins with `french/` for any French-language quote
(see `tools/validate_scholar.py`).

The OCR pipeline (tesseract `-l fra`) and the matching `_normalize`
step in `tools/citations.py` are language-agnostic; nothing
French-specific is required to begin ingestion when a real source
arrives.

## Provenance

This README provisions the directory; no source files yet. Add an
**Inventory** section (mirroring `external-resources/greek/README.md`)
the moment a French OCR file is checked in.
