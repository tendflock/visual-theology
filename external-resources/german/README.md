# German primary-text OCR (non-Logos resources)

German-language primary Reformation texts not held in the Logos library. Mirrors
`external-resources/greek/`; the same backend (`external-ocr`) handles all
languages via the citation's `quote.language` field.

## Citation backend

```json
{
  "backend": {
    "kind": "external-ocr",
    "filename": "german/<file>.txt",
    "passageRef": "<author> on <reference>"
  },
  "quote": {
    "text": "...verbatim German...",
    "language": "de",
    "sha256": "..."
  }
}
```

`backend.filename` MUST begin with `german/`.

## Expected sources (from D-1.5 audit)

- **Luther** — *Vorrede auff den Propheten Daniel* (WA-DB 11.II), *Auslegung
  des siebenden Capitels Daniels* (WA 25), *Tischreden* on Daniel
  (WA-TR). Wittenberg 1545 Bible: BSB or VD16.

## Extraction pattern

1. Acquire scan from BSB / VD16 / archive.org.
2. Tesseract with `-l deu` for modern Fraktur, `-l deu_frak` if available
   (the `deu_frak` traineddata reads 16th-century Fraktur appreciably
   better than `deu` alone, but is not in the homebrew tesseract-lang
   default install).
3. Normalize eszett (ß) and umlauts. Pre-1800 sources frequently use
   `aͤ`, `oͤ`, `uͤ` (combining-e diacritic) for ä, ö, ü; NFC normalization
   does not collapse these — store as-is and quote what the OCR emits.
4. Save plain-text to `external-resources/german/<work-tag>.txt`.

## OCR-quality notes

- Fraktur s vs. round-s vs. long-ſ confusion is the canonical pitfall.
- Capital initials at chapter starts are decorative letterforms; they
  often OCR as garbage and should be excluded from quote anchors.
- WA (Weimarer Ausgabe) editions are typeset in Antiqua post-1900 and
  OCR cleanly under `-l deu`.

## Provenance

- Weimarer Ausgabe (WA) volumes pre-1923 are public domain (US) /
  public domain in Germany after 70 years post-mortem (Luther d. 1546,
  so source text fully PD; the WA editorial apparatus is post-1883
  scholarship and may have edition-specific copyright).
- BSB / VD16 serve 16th-century Wittenberg editions directly.
