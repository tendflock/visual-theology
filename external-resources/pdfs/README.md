# External PDFs (non-Logos resources)

Acquired primary-source PDFs that fill gaps the Logos library does not cover.
Unlike `Data/e3txalek.5iq/ResourceManager/Resources/`, these are **not** readable by
`tools/LogosReader/Program.cs`; they require a separate text-extraction path before they
can be cited under the dual-citation schema.

A sibling directory `external-resources/epubs/` holds EPUB-only acquisitions; see its
own README for the EPUB inventory and the (different, easier) ingestion path EPUBs
need.

## Inventory

| filename | author | work | year (orig.) | fills gap |
|---|---|---|---:|---|
| `Hippolytus-EndTimes.pdf` | Hippolytus of Rome | *On Christ and Antichrist* (et al., end-times material) | c. 200 CE | patristic Daniel reception (Antichrist motif) |
| `Jeromes-Commentary-on-Daniel-BN.pdf` | Jerome | *Commentariorum in Danielem libri III* | c. 407 CE | patristic flagship Daniel commentary; verse-by-verse |

## Ingestion plan

These cannot be cited via `tools/citations.py` as currently built — the schema's `backend`
fields (`resourceId`, `logosArticleNum`, `nativeSectionId`) are Logos-library-specific.
Two options:

1. **Schema extension (preferred).** Add a sibling `backend` shape:
   ```json
   "backend": {
     "kind": "external-pdf",
     "filename": "Jeromes-Commentary-on-Daniel-BN.pdf",
     "page": 47,
     "passageRef": "Comm. Dan. on 7:7"
   }
   ```
   Then `verify_citation` learns to open the PDF (via `pdftotext` or `pdfplumber`),
   normalize, and check the quote text. Same SHA-256 binding as Logos citations.

2. **Manual citations only.** Cite Hippolytus and Jerome in narrative research docs
   without machine verification. Lower fidelity; would not appear in the sweep totals.

Option 1 is the right shape. The work is roughly: a `pdf_text` extraction helper
(probably `pdftotext -layout` or `pdfplumber`), a `verify_pdf_citation` variant on
`tools/citations.py:verify_citation`, and an `external` discriminator on `backend.kind`.
The same `backend.kind` field also covers the EPUB pathway (with `external-epub` as a
sibling value to `external-pdf`) so the schema extension is one shape covering both
formats.

## Status

Staged; not yet ingested. WS0c plan tracks ingestion as a separate item from the four
primary scholar JSON expansions (Calvin, Goldingay, Beale, 1 Enoch).

## Provenance

- `Hippolytus-EndTimes.pdf` — source unknown; user-acquired 2026-04-25. Likely from
  archive.org or a public-domain ANF/NPNF reprint. Should be re-checked for
  edition/translator.
- `Jeromes-Commentary-on-Daniel-BN.pdf` — `BN` suffix suggests a Bibliothèque-Nationale
  scan or a particular edition; user-acquired 2026-04-25. Should record the edition
  (Migne PL 25? Archer 1958 ET? Braverman 1978?) before any citation goes live.
