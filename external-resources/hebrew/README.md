# Hebrew primary-text OCR (non-Logos, non-Sefaria resources)

Hebrew-language primary medieval and post-medieval Jewish-reception texts not
held in the Logos library and not directly fetched from the Sefaria API.
Sefaria-borne texts use the `external-sefaria` backend; this directory is for
PDFs and scans (HebrewBooks, archive.org, MG facsimiles) that need a local
OCR pass.

## Citation backend

```json
{
  "backend": {
    "kind": "external-ocr",
    "filename": "hebrew/<file>.txt",
    "passageRef": "<author> on <reference>"
  },
  "quote": {
    "text": "...verbatim Hebrew (NFC)...",
    "language": "he",
    "sha256": "..."
  }
}
```

`backend.filename` MUST begin with `hebrew/`. Hebrew quotes must be NFC-normalized
at storage time (the verifier also re-normalizes; storing NFC keeps the corpus
self-consistent and avoids false hash mismatches across editing tools).

## Expected sources (from D-1J audit, Wave 6.3 candidates)

- **Abrabanel, *Ma'yanei ha-Yeshuah*** — HebrewBooks #23900 (Amsterdam 1647).
  Manual download or Cloudflare-aware fetcher; OCR with `heb`.
- **Ralbag (Gersonides) on Daniel** — Mikraot Gedolot 1525 vol. 4, or Qehillot
  Mosheh 1724 facsimile if HebrewBooks-borne.
- **Sefer ha-Geulah (Ramban)** — speculative HebrewBooks candidate; not yet
  located (D-1J §6).
- Future MG / HB scans for any Jewish commentator whose Daniel material
  isn't on Sefaria.

## Extraction pattern

1. Acquire PDF (HebrewBooks / archive.org / NLI direct download — note
   HebrewBooks uses Cloudflare; Bryan often downloads in browser and stages
   the file rather than scripting).
2. Tesseract with `-l heb` (modern Hebrew). Rashi-script fonts (used in
   classical commentaries' inner margins) are read better with
   `-l heb_old` if available; otherwise plan a manual cleanup pass.
3. Strip page headers; preserve page numbers as anchors.
4. NFC-normalize before saving.
5. Save plain-text to `external-resources/hebrew/<work-tag>.txt`.

## OCR-quality notes

- Vocalization (niqqud) and cantillation marks: Sefaria stores them; HB
  scans often don't. Quote anchors should be the consonantal text alone
  unless the source carries niqqud.
- Final-form letters (ך ם ן ף ץ) vs. medial forms: OCR reliable.
- Rashi script is a real obstacle. If a commentary appears in MG inner
  columns, prefer a Sefaria-side fetch when possible.
- Hebrew right-to-left + embedded numerals / Latin transliteration mix
  reliably under `heb` traineddata, but column-break artifacts can splice
  unrelated text — verify quote anchors against the printed page.

## Provenance

- All medieval/early-modern Hebrew commentaries cited under this backend
  are PD by age. Modern editorial apparatus (footnotes, vocalization,
  pagination) may be in copyright per the publisher; quote the source
  text itself, not the apparatus.
