# Latin primary-text OCR (non-Logos resources)

Latin-language primary patristic, medieval, and Reformation texts that are not held
in the Logos library. Mirrors `external-resources/greek/`; the same backend
(`external-ocr`) handles both via the citation's `quote.language` field
(`la` for Latin, `grc` for Greek).

## Citation backend

D-2 (`external-ocr` backend) shape:

```json
{
  "backend": {
    "kind": "external-ocr",
    "filename": "latin/<file>.txt",
    "passageRef": "<author> on <reference>"
  },
  "quote": {
    "text": "...verbatim Latin...",
    "language": "la",
    "sha256": "..."
  }
}
```

`backend.filename` MUST begin with `latin/`; the verifier (`tools/citations.py:_load_ocr_text`)
cross-checks that the path's first segment matches the citation's `quote.language`.

## Expected sources (from D-1.5 audit)

The `2026-04-28-patristic-reformation-fulltext-audit.md` audit identifies these
voices needing Latin OCR ingestion:

- **Gregory the Great** — Migne PL 75/76 (Moralia in Job; Hom. on Ezekiel)
- **Bullinger** — *In Apocalypsim conciones centum* (1557, e-rara/Zürich)
- **Œcolampadius** — *In Danielem libri duo* (Basel 1530, e-rara)
- **Lambert of Avignon** — *Exegeseos in Apocalypsim libri VII* (1539)
- **Pellican** — *Commentaria Bibliorum* vol. on prophets (Basel 1532+)
- **Melanchthon** — *In Danielem prophetam commentarius* (Wittenberg 1543, BSB)
- **Mede** — *Clavis Apocalyptica* if/when a clean Latin scan surfaces

## Extraction pattern

Mirror the Greek pipeline (`external-resources/greek/extract_pg81_range.sh`):

1. Acquire scan as PDF (Migne PL via archive.org/Gallica/MDZ; Reformation
   editions via e-rara/BSB).
2. Tesseract with `-l lat` (or `-l lat+eng` if facing translation).
3. Strip running headers + page footers; preserve column / page anchors.
4. Save plain-text to `external-resources/latin/<work-tag>.txt`.

## OCR-quality notes

- Latin OCR via `lat` traineddata is generally cleaner than Greek `grc`,
  but long-s (ſ) → `f` substitution is the canonical pitfall in pre-1800
  scans. Quote-anchors should prefer post-long-s passages or normalize
  before storage.
- Ligatures (æ, œ, ct, st) and abbreviations (ꝯ for `con`, q̃ for `que`)
  vary by edition; document per-source quirks here as they're discovered.

## Provenance

- Migne *Patrologia Latina* (1844-1855) is public domain.
- 16th-century editions (Bullinger, Œcolampadius, Pellican, Melanchthon)
  are public domain; e-rara/BSB serve them as direct-download PDFs.
