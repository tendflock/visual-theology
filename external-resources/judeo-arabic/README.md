# Judeo-Arabic primary-text OCR (non-Logos resources)

Judeo-Arabic primary texts (Arabic in Hebrew script) used by Geonic and Karaite
exegetes. Not on Sefaria as full texts; needs local OCR pass.

## Citation backend

```json
{
  "backend": {
    "kind": "external-ocr",
    "filename": "judeo-arabic/<file>.txt",
    "passageRef": "<author> on <reference>"
  },
  "quote": {
    "text": "...verbatim Judeo-Arabic (NFC)...",
    "language": "jrb",
    "sha256": "..."
  }
}
```

`backend.filename` MUST begin with `judeo-arabic/`. ISO 639-3 `jrb` is the
Judeo-Arabic macrolanguage code; per-region narrow codes (`yhd` Judeo-Yemeni,
`yud` Judeo-Tripolitanian, etc.) are not used in this corpus.

## Expected sources (from D-1J audit, Wave 6.3 candidates)

- **Yefet ben Eli on Daniel 1–12** — archive.org `commentaryonbook00japhuoft`
  (Margoliouth 1889 ed.). The `_djvu.txt` plain-text on archive.org provides
  both the Judeo-Arabic original (Hebrew-script Arabic) and Margoliouth's
  facing English translation. Stage the djvu-text directly under
  `external-resources/judeo-arabic/yefet-daniel-margoliouth.txt`; the
  English half can either be split out into its own English-language
  citation source or quoted alongside the Judeo-Arabic via a translation
  record on the citation.
- **Saadia Gaon on Daniel** (Aramaic-portion fragment, Dan 2:4b–7:28) —
  Hurvitz 1977 YU dissertation, manual download via repository.yu.edu.
  Saadia wrote Tafsir on biblical books in Judeo-Arabic; this is a partial
  edition of the Daniel Tafsir.

## Extraction pattern

Yefet's archive.org volume already ships a `_djvu.txt` plain-text file —
no fresh OCR needed; extract the Daniel-7 page-range and save. For other
sources:

1. Tesseract with `-l heb` (Hebrew script reads Judeo-Arabic correctly).
2. Strip page headers, preserve page numbers as anchors.
3. NFC-normalize.
4. Save under `external-resources/judeo-arabic/<work-tag>.txt`.

## Provenance

Margoliouth (1889) is public domain. Saadia, Yefet, and other Geonic /
early-Karaite authors are PD by age; modern critical editions' apparatus
may carry edition copyrights — cite the source text itself, not the
editor's notes.
