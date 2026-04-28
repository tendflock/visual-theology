"""Dual-citation builder and verifier (WS0c).

Schema: docs/schema/citation-schema.md.

Three public functions:

- ``sha256_of(text)`` — hex digest of UTF-8 bytes.
- ``build_citation(...)`` — compose a canonical citation dict from a resource
  file, an article number, and optional scholarly metadata.
- ``verify_citation(citation)`` — confirm the cited quote still appears in the
  named article.

CLI::

    python tools/citations.py verify <path-to-citation.json>

Exits 0 when the citation verifies, 1 otherwise.
"""

from __future__ import annotations

import hashlib
import html.parser
import json
import os
import re
import sys
import zipfile
from pathlib import Path
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from study import _resolve_bare_stem, get_article_meta, get_resource_file, read_article_text  # noqa: E402


_MAX_ARTICLE_CHARS = 500_000  # Covers the longest articles in the library.

# Root for external (non-Logos) resources. Citations against PDFs, EPUBs, or
# OCR'd Greek text use paths relative to this directory.
EXTERNAL_RESOURCES_DIR = Path(__file__).resolve().parent.parent / "external-resources"

# Backend kinds (WS0c-7). Default is "logos" for back-compat with all existing
# citations; new external-resource citations declare their kind explicitly.
BACKEND_KINDS = ("logos", "external-epub", "external-pdf", "external-greek-ocr")

# Social-DRM watermark stripped from EPUB-extracted text (see
# external-resources/epubs/README.md).
_EPUB_WATERMARK_RE = re.compile(r"ThiseBookislicensedtoBryanSchneider\d*bryans?")


def sha256_of(text: str) -> str:
    """Return the lowercase-hex SHA-256 of ``text`` encoded as UTF-8."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


SUPPORT_STATUS_VALUES = (
    "directly-quoted",
    "paraphrase-anchored",
    "summary-inference",
    "uncited-gap",
)


def build_citation(
    resource_file: str,
    article_num: int,
    quote_text: str | None = None,
    author: str | None = None,
    short_title: str | None = None,
    full_title: str | None = None,
    support_status: str | None = None,
) -> dict[str, Any]:
    """Compose a canonical dual-citation dict.

    See ``docs/schema/citation-schema.md`` for field semantics.
    """
    meta = get_article_meta(resource_file, article_num)
    if meta is None:
        raise RuntimeError(
            f"Cannot build citation: get_article_meta returned None "
            f"for {resource_file!r} article {article_num}"
        )

    native_section_id = meta["nativeSectionId"]
    heading = meta.get("heading")
    page_start = meta.get("pageStart")
    page_end_raw = meta.get("pageEnd")
    page_end = page_end_raw if page_end_raw not in (None, page_start) else None

    if heading:
        section = f"§{native_section_id} — {heading}"
    else:
        section = f"§{native_section_id}" if native_section_id else None

    citation_string = _render_citation_string(
        author=author,
        short_title=short_title or full_title,
        native_section_id=native_section_id,
        page=page_start,
        page_end=page_end,
        logos_article_num=article_num,
    )

    quote: dict[str, str] | None
    if quote_text is None:
        quote = None
    else:
        quote = {"text": quote_text, "sha256": sha256_of(quote_text)}

    if support_status is None:
        support_status = "directly-quoted" if quote is not None else "uncited-gap"
    if support_status not in SUPPORT_STATUS_VALUES:
        raise ValueError(
            f"support_status: {support_status!r} not in {SUPPORT_STATUS_VALUES}"
        )
    if support_status == "directly-quoted" and quote is None:
        raise ValueError(
            "support_status='directly-quoted' requires a non-null quote_text"
        )

    return {
        "backend": {
            "resourceId": meta["resourceId"],
            "logosArticleNum": article_num,
            "nativeSectionId": native_section_id,
        },
        "frontend": {
            "author": author,
            "title": full_title,
            "section": section,
            "page": page_start,
            "pageEnd": page_end,
            "citationString": citation_string,
        },
        "quote": quote,
        "supportStatus": support_status,
    }


def verify_citation(citation: dict[str, Any]) -> dict[str, Any]:
    """Confirm that the cited quote appears in the referenced source.

    Dispatches by ``backend.kind``: ``logos`` (default; uses the LogosReader),
    ``external-epub`` (extracts plain text from a watermarked EPUB),
    ``external-greek-ocr`` (reads an OCR'd Greek .txt file), or
    ``external-pdf`` (extracts plain text via ``pdftotext``).

    Returns a dict with ``status`` ∈ {``verified``, ``partial``,
    ``quote-not-found``, ``resource-unreadable``} plus diagnostic fields.
    """
    backend = citation.get("backend") or {}
    kind = backend.get("kind", "logos")

    if kind == "logos":
        article_text, source_label, error = _load_logos_text(backend)
    elif kind == "external-epub":
        article_text, source_label, error = _load_epub_text(backend)
    elif kind == "external-greek-ocr":
        article_text, source_label, error = _load_text_file(backend)
    elif kind == "external-pdf":
        article_text, source_label, error = _load_pdf_text(backend)
    else:
        return {
            "status": "resource-unreadable",
            "notes": f"unknown backend.kind: {kind!r} (expected one of {BACKEND_KINDS})",
        }

    if error:
        return {"status": "resource-unreadable", "notes": error}
    if not article_text:
        return {
            "status": "resource-unreadable",
            "notes": f"empty source text from {source_label}",
        }

    quote = citation.get("quote")
    if quote is None or not quote.get("text"):
        # Paraphrase-only citation: verified means "the article still opens".
        return {
            "status": "verified",
            "paraphrase": True,
            "notes": "paraphrase citation; article readable but no quote to match",
            "articleLength": len(article_text),
        }

    needle = quote["text"]
    stored_hash = quote.get("sha256")
    if stored_hash and stored_hash != sha256_of(needle):
        return {
            "status": "partial",
            "notes": "quote.sha256 does not match sha256(quote.text) — tampered citation",
        }

    norm_article = _normalize(article_text)
    norm_needle = _normalize(needle)
    # Case-insensitive: case drift at sentence boundaries ("the X" vs "The X")
    # is normal citation practice, not tampering.
    idx = norm_article.lower().find(norm_needle.lower())
    if idx >= 0:
        return {
            "status": "verified",
            "matchSpan": [idx, idx + len(norm_needle)],
            "articleLength": len(article_text),
        }

    return {
        "status": "quote-not-found",
        "notes": (
            f"quote text (len={len(needle)}) not found in {source_label} "
            f"(text len={len(article_text)})"
        ),
    }


# ── source-text loaders (one per backend.kind) ──────────────────────────────


def _load_logos_text(
    backend: dict[str, Any],
) -> tuple[str | None, str, str | None]:
    resource_id = backend.get("resourceId")
    article_num = backend.get("logosArticleNum")
    if not resource_id or article_num is None:
        return None, "<logos>", "citation missing backend.resourceId or logosArticleNum"
    resource_file = _resource_id_to_file(resource_id)
    text = read_article_text(
        resource_file, int(article_num), max_chars=_MAX_ARTICLE_CHARS
    )
    return text, f"{resource_id} #{article_num}", None


def _resolve_external_path(filename: str) -> Path:
    """Resolve a relative external-resources/ path; reject path traversal."""
    p = (EXTERNAL_RESOURCES_DIR / filename).resolve()
    root = EXTERNAL_RESOURCES_DIR.resolve()
    if not str(p).startswith(str(root)):
        raise ValueError(f"path traversal blocked: {filename!r}")
    return p


_EPUB_TEXT_CACHE: dict[str, str] = {}


def _load_epub_text(
    backend: dict[str, Any],
) -> tuple[str | None, str, str | None]:
    filename = backend.get("filename")
    if not filename:
        return None, "<external-epub>", "citation missing backend.filename"
    try:
        path = _resolve_external_path(filename)
    except ValueError as e:
        return None, f"<external-epub:{filename}>", str(e)
    if not path.exists():
        return None, f"<external-epub:{filename}>", f"file not found: {path}"

    cache_key = str(path)
    if cache_key not in _EPUB_TEXT_CACHE:
        try:
            _EPUB_TEXT_CACHE[cache_key] = _extract_epub_text(path)
        except (zipfile.BadZipFile, OSError) as e:
            return None, f"<external-epub:{filename}>", f"epub extract failed: {e}"
    return _EPUB_TEXT_CACHE[cache_key], f"epub:{filename}", None


def _extract_epub_text(path: Path) -> str:
    """Extract concatenated plain text from every XHTML chapter in an EPUB.

    Strips HTML tags, the social-DRM watermark embedded in chapter filenames
    (and sometimes inline), and collapses whitespace. Order is the EPUB's
    spine order (alphabetical-by-filename approximates this for the EPUBs
    we currently hold)."""
    parts: list[str] = []
    with zipfile.ZipFile(path) as z:
        # Skip the social-DRM single-page xhtml that just shows the licence
        # banner — its content isn't part of the text.
        names = sorted(
            n for n in z.namelist()
            if n.lower().endswith(".xhtml") and "exlibris" not in n.lower()
        )
        for name in names:
            try:
                raw = z.read(name).decode("utf-8", errors="replace")
            except KeyError:
                continue
            stripper = _HtmlStripper()
            stripper.feed(raw)
            parts.append(stripper.text())
    text = "\n".join(parts)
    text = _EPUB_WATERMARK_RE.sub("", text)
    return text


class _HtmlStripper(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._chunks: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in ("script", "style"):
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style") and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            self._chunks.append(data)

    def text(self) -> str:
        return "".join(self._chunks)


def _load_text_file(
    backend: dict[str, Any],
) -> tuple[str | None, str, str | None]:
    """For external-greek-ocr: just read the .txt file (already plain text)."""
    filename = backend.get("filename")
    if not filename:
        return None, "<external-greek-ocr>", "citation missing backend.filename"
    try:
        path = _resolve_external_path(filename)
    except ValueError as e:
        return None, f"<external-greek-ocr:{filename}>", str(e)
    if not path.exists():
        return None, f"<external-greek-ocr:{filename}>", f"file not found: {path}"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        return None, f"<external-greek-ocr:{filename}>", f"read failed: {e}"
    return text, f"greek-ocr:{filename}", None


_PDF_TEXT_CACHE: dict[str, str] = {}


def _load_pdf_text(
    backend: dict[str, Any],
) -> tuple[str | None, str, str | None]:
    """Extract plain text from a PDF via ``pdftotext`` subprocess (poppler)."""
    import subprocess

    filename = backend.get("filename")
    if not filename:
        return None, "<external-pdf>", "citation missing backend.filename"
    try:
        path = _resolve_external_path(filename)
    except ValueError as e:
        return None, f"<external-pdf:{filename}>", str(e)
    if not path.exists():
        return None, f"<external-pdf:{filename}>", f"file not found: {path}"

    cache_key = str(path)
    if cache_key not in _PDF_TEXT_CACHE:
        try:
            r = subprocess.run(
                ["pdftotext", "-layout", str(path), "-"],
                capture_output=True,
                text=True,
                timeout=60,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            return None, f"<external-pdf:{filename}>", f"pdftotext failed: {e}"
        if r.returncode != 0:
            return (
                None,
                f"<external-pdf:{filename}>",
                f"pdftotext exit {r.returncode}: {r.stderr[:200]}",
            )
        _PDF_TEXT_CACHE[cache_key] = r.stdout
    return _PDF_TEXT_CACHE[cache_key], f"pdf:{filename}", None


# ── helpers ─────────────────────────────────────────────────────────────────


_WHITESPACE_RE = re.compile(r"\s+")

# Typographic normalization: curly↔ASCII quotes, em/en-dashes,
# ellipsis. SBL and Chicago treat these as cosmetically equivalent
# in citation practice; differences here should not trigger
# fabrication flags.
_TYPO_MAP = str.maketrans({
    "‘": "'",  # left single
    "’": "'",  # right single / apostrophe
    "“": '"',  # left double
    "”": '"',  # right double
    "–": "-",  # en dash
    "—": "-",  # em dash
    "…": "...",  # horizontal ellipsis (unrolls to 3 dots)
})


def _normalize(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text.translate(_TYPO_MAP)).strip()


def _normalize_whitespace(text: str) -> str:
    """Backward-compatible alias; same as ``_normalize``."""
    return _normalize(text)


def _resource_id_to_file(resource_id: str) -> str:
    """``LLS:GS_WALV_DANIEL`` → ``GS_WALV_DANIEL.lbxlls`` (actual filename).

    The reader's ``--article-meta`` path resolves bare stems via the
    ResourceManager catalog, but ``read_article_text`` goes through the
    positional-arg path which requires a filename with extension.

    Resolution order:
      1. Direct catalog lookup by full ``ResourceId`` (handles dotted-stem IDs
         like ``LLS:6.60.2`` whose filename does not match the stem; e.g.
         ``LLS:6.60.2`` → ``NPNF02.logos4``).
      2. Bare-stem basename match via ``_resolve_bare_stem`` (handles
         alphabetic-stem IDs whose filename equals the stem case-insensitively;
         e.g. ``LLS:GS_WALV_DANIEL`` → ``GS_WALV_DANIEL.lbxlls``).

    Raises ``FileNotFoundError`` if neither path resolves.
    """
    full_path = get_resource_file(resource_id)
    if full_path:
        return os.path.basename(full_path)
    stem = resource_id[4:] if resource_id.startswith("LLS:") else resource_id
    return _resolve_bare_stem(stem)


def _render_citation_string(
    *,
    author: str | None,
    short_title: str | None,
    native_section_id: str | None,
    page: int | None,
    page_end: int | None,
    logos_article_num: int,
) -> str:
    parts: list[str] = []
    if author:
        parts.append(author)
    if short_title:
        parts.append(short_title)

    if native_section_id:
        section_bit = f"§{native_section_id}"
        if page is not None and page_end is not None:
            section_bit += f" (pp. {page}–{page_end})"
        elif page is not None:
            section_bit += f" (p. {page})"
        parts.append(section_bit)
    else:
        parts.append(f"Logos art. {logos_article_num}")

    return ", ".join(parts) if parts else f"Logos art. {logos_article_num}"


# ── CLI ─────────────────────────────────────────────────────────────────────


def _cli_verify(path: str) -> int:
    with open(path, encoding="utf-8") as fh:
        citation = json.load(fh)
    result = verify_citation(citation)
    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0 if result["status"] == "verified" else 1


def _main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[1] != "verify":
        sys.stderr.write("Usage: python tools/citations.py verify <citation.json>\n")
        return 2
    return _cli_verify(argv[2])


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
