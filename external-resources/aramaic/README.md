# Aramaic primary-text OCR (non-Logos, non-Sefaria resources)

Aramaic-language primary texts (Talmudic Aramaic, Targumic Aramaic) not held in
the Logos library and not directly fetched from Sefaria. Most Talmudic Aramaic
the project cites is Sefaria-borne (William Davidson Vocalized Aramaic) and uses
the `external-sefaria` backend; this directory is for PDFs / scans that need a
local OCR pass.

## Citation backend

```json
{
  "backend": {
    "kind": "external-ocr",
    "filename": "aramaic/<file>.txt",
    "passageRef": "<author> on <reference>"
  },
  "quote": {
    "text": "...verbatim Aramaic (NFC)...",
    "language": "arc",
    "sha256": "..."
  }
}
```

`backend.filename` MUST begin with `aramaic/`. ISO 639-2 `arc` covers Imperial
and Biblical Aramaic; for Babylonian Talmud-Aramaic and Targumic Aramaic the
same code is used.

## Expected sources

D-1J audit (`2026-04-28-jewish-reception-multilingual-audit.md`) confirms the
classical-canonical Targumim do **not** cover Daniel (Daniel sits in Ketuvim;
Onkelos covers Pentateuch only; Jonathan covers the Prophets but not Daniel).
This directory is therefore likely sparse for the Daniel pilot. Possible
content:

- Non-canonical / fragmentary Aramaic Daniel-reception texts (Genizah
  fragments, Qumran-related materials) if/when Bryan stages them.
- The Aramaic portions of Daniel itself (Dan 2:4b–7:28) if a critical edition
  scan is staged separately from the Sefaria + Logos copies.

## Extraction pattern

Same as Hebrew (see `external-resources/hebrew/README.md`); both languages
share the `heb` Tesseract traineddata. Save under `aramaic/` when the
language is Aramaic, even though the OCR command is identical to Hebrew.

## NFC discipline

NFC-normalize at storage time. Cantillation and niqqud appear sporadically
in critical editions; preserve only what the source actually carries —
hallucinated vocalization is a verification trap.
