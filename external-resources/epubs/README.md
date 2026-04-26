# External EPUBs (non-Logos resources)

Acquired primary-source EPUBs that fill gaps the Logos library does not cover.
Like the PDFs in `external-resources/pdfs/`, these are **not** readable by
`tools/LogosReader/Program.cs` and require a separate ingestion path before they can be
cited under the dual-citation schema.

## Inventory

| filename | author | work | year (orig.) | edition | fills gap |
|---|---|---|---:|---|---|
| `9781498221689.epub` | André LaCocque | *The Book of Daniel* | 1979 (Knox) | Cascade Books reissue, 2018 | continental-French Catholic critical voice on Daniel; distinct from Anglo-American critical (Collins, Newsom) |
| `9781532643194.epub` | Jonathan Menn | *Biblical Eschatology*, 2nd ed. | 2018 | Resource Publications | mediating historic-premillennial / covenantal-eclectic voice; bridges Reformed amillennial and historic premillennial on F (millennium) and H (eschatological structure) |

## Ingestion

EPUBs are easier than PDFs: each is a ZIP containing XHTML chapter files plus a
`content.opf` manifest. Standard tools can extract clean text without OCR risk:

```python
import zipfile
from bs4 import BeautifulSoup
with zipfile.ZipFile("9781498221689.epub") as z:
    for name in z.namelist():
        if name.endswith(".xhtml"):
            text = BeautifulSoup(z.read(name), "html.parser").get_text("\n")
```

For dual-citation under the `backend.kind: external-epub` discriminator:

```json
"backend": {
  "kind": "external-epub",
  "filename": "9781498221689.epub",
  "spineSection": "ch. 7",
  "passageRef": "Lacocque on Dan 7:13"
}
```

The `quote.text` + `sha256` binding works the same way as Logos citations.
Whitespace/typography normalization (already in `tools/citations.py`) handles the
typical EPUB-source quirks.

### Social-DRM fingerprint

Both files have visible social-DRM watermarks: chapter filenames contain
`"ThiseBookislicensedtoBryanSchneiderbryans"` patterns (with random infixed digits).
These are unique-per-purchaser identifiers from the publishers (Cascade Books / Resource
Publications). The EPUBs are unlocked (no encryption); the watermark is metadata-level
only. Implication: the project's ingested text inherits this fingerprint, so any
quote-text storage should strip the watermark substring during extraction to keep
citation `quote.text` clean. Add this as a normalization step in the EPUB extractor:

```python
WATERMARK_RE = re.compile(r"ThiseBookislicensedtoBryanSchneider\d*bryans?")
clean = WATERMARK_RE.sub("", raw_text)
```

The watermark does not affect quote authenticity (the text is real Lacocque / Menn
text); it just clutters the extraction.

## Status

Staged 2026-04-25; not yet ingested. WS0c-6 (Lacocque survey) and a sibling task for
Menn pick this up once the EPUB-citation backend is wired.

## Provenance

- `9781498221689.epub` — André LaCocque, *The Book of Daniel*, Cascade Books reissue
  2018-06-19. ISBN 9781498221689. The 1979 Knox original is the authoritative print
  edition; the 2018 reissue preserves it. Cite the print original where pagination
  matters.
- `9781532643194.epub` — Jonathan Menn, *Biblical Eschatology*, 2nd ed., Resource
  Publications, 2018-03-12. ISBN 9781532643194. First-class voice for historic-
  premillennial eschatology in English-speaking covenantal-leaning circles.
