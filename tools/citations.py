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
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from study import _resolve_bare_stem, get_article_meta, get_resource_file, read_article_text  # noqa: E402


_MAX_ARTICLE_CHARS = 500_000  # Covers the longest articles in the library.

# Root for external (non-Logos) resources. Citations against PDFs, EPUBs, or
# OCR'd Greek text use paths relative to this directory.
EXTERNAL_RESOURCES_DIR = Path(__file__).resolve().parent.parent / "external-resources"

# Disk cache for Sefaria API responses. Gitignored. Each cache file is the
# trailing component of the API URL (e.g. ``Rashi_on_Daniel.7.13.json``)
# storing the raw JSON Sefaria returned. We cache full responses so future
# changes to extraction (HTML stripping, language selection) replay over the
# original payload without re-hitting the network.
SEFARIA_CACHE_DIR = EXTERNAL_RESOURCES_DIR / "sefaria-cache"

# Backend kinds (WS0c-7 + WS0c-expansion + D-2). Default is "logos" for
# back-compat with all existing citations; new external-resource citations
# declare their kind explicitly. ``external-sefaria`` (WS0c-expansion)
# supports Wave 6 medieval-Jewish reception surveys via the free Sefaria.org
# REST API. ``external-ocr`` (D-2) generalizes the prior ``external-greek-ocr``
# kind to handle OCR'd plain-text in any language; the citation's quote.language
# field selects the per-language subdirectory under ``external-resources/``.
BACKEND_KINDS = (
    "logos",
    "external-epub",
    "external-pdf",
    "external-ocr",
    "external-sefaria",
)

# Languages accepted on quote.language and on backend filename prefix for the
# external-ocr backend. ISO 639-1/-2/-3 codes. Single source of truth;
# tools/validate_scholar.py imports OCR_LANGUAGE_DIRS from this module and
# layers "en" on top to form its _QUOTE_LANGUAGES tuple (D-2.5 centralized
# the relationship to a one-way import).
OCR_LANGUAGE_DIRS = {
    "grc": "greek",
    "la": "latin",
    "he": "hebrew",
    "arc": "aramaic",
    "jrb": "judeo-arabic",
    "de": "german",
    "fr": "french",
}

SEFARIA_LANGUAGES = ("he", "en")
SEFARIA_API_PREFIX = "https://www.sefaria.org/api/texts/"
_SEFARIA_HOSTS = ("www.sefaria.org", "sefaria.org")

# Positive allowlist for the ref segment after /api/texts/. Sefaria refs are
# uniformly ASCII alphanumeric with underscores, dots, and hyphens
# (e.g. ``Rashi_on_Daniel.7.13``, ``Joseph_ibn_Yahya_on_Daniel``). Anything
# outside this set — backslash, whitespace, zero-width joiners, RTL overrides,
# non-breaking spaces, or any non-ASCII letter — is suspect and rejected.
_REF_SEGMENT_RE = re.compile(r"^[A-Za-z0-9_.-]+$")

# Sefaria's text-API names the English field ``text`` (not ``en``) and the
# Hebrew field ``he``. Map our schema-level language code to the response key.
_SEFARIA_LANGUAGE_FIELD = {"en": "text", "he": "he"}

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
    language: str | None = None,
    translations: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Compose a canonical dual-citation dict.

    See ``docs/schema/citation-schema.md`` for field semantics.

    ``language`` (D-2) attaches an ISO 639 code to the quote. Defaults to
    ``"en"`` when a ``quote_text`` is supplied. Required for non-English
    quotes; for ``external-ocr``-backed citations the surveyor's caller
    constructs the citation directly (Logos-backend ``build_citation`` is
    not used for OCR text), but the field round-trips through here so a
    multilingual scholar JSON can still be assembled if needed.

    ``translations`` (D-2) is an optional list of derivative-translation
    records. Each record is preserved verbatim; the validator enforces
    structure. Translations are NOT verified by ``verify_citation`` — only
    ``quote.text`` is the verifier's anchor.
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

    quote: dict[str, Any] | None
    if quote_text is None:
        quote = None
    else:
        quote = {"text": quote_text, "sha256": sha256_of(quote_text)}
        quote["language"] = language if language is not None else "en"

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

    citation: dict[str, Any] = {
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
    if translations:
        citation["translations"] = list(translations)
    return citation


def verify_citation(citation: dict[str, Any]) -> dict[str, Any]:
    """Confirm that the cited quote appears in the referenced source.

    Dispatches by ``backend.kind``: ``logos`` (default; uses the LogosReader),
    ``external-epub`` (extracts plain text from a watermarked EPUB),
    ``external-ocr`` (reads an OCR'd plain-text file in any language —
    succeeds the WS0c-7 ``external-greek-ocr`` kind),
    ``external-pdf`` (extracts plain text via ``pdftotext``), or
    ``external-sefaria`` (fetches verse text from the Sefaria REST API).

    Returns a dict with ``status`` ∈ {``verified``, ``partial``,
    ``quote-not-found``, ``resource-unreadable``} plus diagnostic fields.
    """
    backend = citation.get("backend") or {}
    kind = backend.get("kind", "logos")

    if kind == "logos":
        article_text, source_label, error = _load_logos_text(backend)
    elif kind == "external-epub":
        article_text, source_label, error = _load_epub_text(backend)
    elif kind == "external-ocr":
        article_text, source_label, error = _load_ocr_text(backend, citation)
    elif kind == "external-pdf":
        article_text, source_label, error = _load_pdf_text(backend)
    elif kind == "external-sefaria":
        article_text, source_label, error = _load_sefaria_text(backend)
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


def _load_ocr_text(
    backend: dict[str, Any],
    citation: dict[str, Any],
) -> tuple[str | None, str, str | None]:
    """For external-ocr: read an OCR'd plain-text file in any language.

    The citation's ``quote.language`` ISO code names the per-language
    subdirectory under ``external-resources/`` (e.g. ``grc`` → ``greek/``,
    ``la`` → ``latin/``). The backend's ``filename`` is the path relative
    to ``external-resources/`` and must begin with the language subdirectory.
    Texts are pre-stripped (the OCR pipeline produces plain text); we apply
    NFC normalization at match time via ``_normalize``.
    """
    filename = backend.get("filename")
    if not filename:
        return None, "<external-ocr>", "citation missing backend.filename"

    quote = citation.get("quote") or {}
    language = quote.get("language")
    if language is None:
        return (
            None,
            f"<external-ocr:{filename}>",
            "external-ocr citation missing quote.language",
        )
    if not isinstance(language, str):
        return (
            None,
            f"<external-ocr:{filename}>",
            f"quote.language is not a string (got {type(language).__name__})",
        )
    expected_dir = OCR_LANGUAGE_DIRS.get(language)
    if expected_dir is None:
        return (
            None,
            f"<external-ocr:{filename}>",
            f"unsupported quote.language={language!r}; "
            f"accepted: {sorted(OCR_LANGUAGE_DIRS.keys())}",
        )
    if not filename.startswith(f"{expected_dir}/"):
        return (
            None,
            f"<external-ocr:{filename}>",
            f"backend.filename {filename!r} does not start with "
            f"'{expected_dir}/' (required for language={language!r})",
        )

    try:
        path = _resolve_external_path(filename)
    except ValueError as e:
        return None, f"<external-ocr:{filename}>", str(e)
    if not path.exists():
        return None, f"<external-ocr:{filename}>", f"file not found: {path}"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        return None, f"<external-ocr:{filename}>", f"read failed: {e}"
    return text, f"ocr:{filename}", None


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


# ── external-sefaria loader (WS0c-expansion) ────────────────────────────────


def _load_sefaria_text(
    backend: dict[str, Any],
) -> tuple[str | None, str, str | None]:
    """Fetch + extract verse text from the Sefaria API.

    The Sefaria response carries parallel ``text`` (English) and ``he`` (Hebrew)
    fields, each an array of strings (one per comment segment within the cited
    verse). We pick the array named by ``backend.language``, flatten it,
    strip HTML tags, and NFC-normalize.
    """
    resource_url = backend.get("resourceUrl")
    if not resource_url:
        return None, "<external-sefaria>", "citation missing backend.resourceUrl"
    language = backend.get("language")
    if language not in SEFARIA_LANGUAGES:
        return (
            None,
            f"<external-sefaria:{resource_url}>",
            f"backend.language must be one of {SEFARIA_LANGUAGES}, got {language!r}",
        )
    try:
        validate_sefaria_url(resource_url)
    except ValueError as e:
        return None, f"<external-sefaria:{resource_url}>", str(e)

    try:
        data = _fetch_sefaria(resource_url)
    except (urllib.error.URLError, OSError, ValueError, json.JSONDecodeError) as e:
        return None, f"<external-sefaria:{resource_url}>", f"fetch failed: {e}"

    field_name = _SEFARIA_LANGUAGE_FIELD[language]
    field = data.get(field_name)
    flat = _flatten_sefaria_text(field)
    if not flat.strip():
        # Sefaria returned no text for the requested language. Fall back to the
        # other language only if the citation didn't request it (defensive —
        # a Hebrew-only entry being cited as English shouldn't silently verify
        # against the Hebrew, so we surface the empty-text condition).
        return (
            None,
            f"sefaria:{resource_url}",
            f"sefaria response has no text for language={language!r}",
        )

    stripped = _strip_html_tags(flat)
    normalized = unicodedata.normalize("NFC", stripped)
    return normalized, f"sefaria:{resource_url}", None


def validate_sefaria_url(url: str) -> None:
    """Reject URLs that aren't a canonical Sefaria text-API endpoint.

    The on-disk cache is keyed by the URL's path component only (see
    ``_sefaria_cache_path``), so any URL that smuggles state in via the query
    string, fragment, RFC-3986 path-params, userinfo, or explicit port would
    fetch a different payload while colliding with the bare-path entry in the
    cache. Reject all of them up front. Reject path traversal (literal or
    percent-encoded) too — the cache path is built by string concatenation
    under ``SEFARIA_CACHE_DIR``.

    Rejection-bypass surface closed in C-3:
      - userinfo (``user:pass@host``) — rewrites authority while urlparse keeps
        the canonical hostname intact
      - explicit port (``host:443``, ``host:abc``, ``host:``) — same idea, plus
        ``parsed.port`` raises on non-integer values, so we inspect the netloc
        as a string instead of touching ``.port``
      - percent-encoded characters in the ref segment — ``%2F`` / ``%2E%2E``
        decode after our segment check otherwise; double-encoding (``%252F``)
        compounds the problem. Reject any ``%`` outright (simpler and stricter
        than decode-then-recheck).
      - leading/trailing whitespace and embedded control characters —
        ``\\nhttps://...`` parses as a valid URL with the newline stripped from
        the scheme by some downstream consumers, so refuse anything that isn't
        already canonical.

    This function is the single source of truth for what counts as an
    acceptable Sefaria URL. ``tools/validate_scholar.py`` imports it so the
    document validator and the runtime fetch path stay in lockstep — any URL
    a scholar JSON can carry must be one the runtime is willing to fetch.
    """
    if url != url.strip():
        raise ValueError(
            "resourceUrl must not have leading/trailing whitespace"
        )
    if any(ord(c) < 0x20 or ord(c) == 0x7F for c in url):
        raise ValueError("resourceUrl must not contain control characters")
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https":
        raise ValueError(f"resourceUrl must be https, got {parsed.scheme!r}")
    if parsed.hostname not in _SEFARIA_HOSTS:
        raise ValueError(
            f"resourceUrl host {parsed.hostname!r} not in {_SEFARIA_HOSTS}"
        )
    # Userinfo: ``user:pass@host`` or even bare ``@host``. parsed.username is
    # empty-string (falsy) for the bare case, so check the netloc directly.
    if "@" in parsed.netloc:
        raise ValueError("resourceUrl must not contain userinfo (user:pass@)")
    # Explicit port: any ``:`` in the host authority is a port specifier
    # (Sefaria has no IPv6 endpoint, so ``[::1]``-style literals are out of
    # scope). Inspect the netloc string rather than parsed.port, because
    # parsed.port raises ValueError for non-integer ports like ``:abc``.
    host_authority = parsed.netloc.rsplit("@", 1)[-1]
    if ":" in host_authority:
        raise ValueError(
            "resourceUrl must not contain an explicit port; canonical "
            "Sefaria URLs have no port"
        )
    if parsed.params:
        raise ValueError(
            f"resourceUrl must not contain RFC-3986 path params, got {parsed.params!r}"
        )
    if parsed.query:
        raise ValueError(
            f"resourceUrl must not contain a query string, got {parsed.query!r}"
        )
    if parsed.fragment:
        raise ValueError(
            f"resourceUrl must not contain a fragment, got {parsed.fragment!r}"
        )
    if not parsed.path.startswith("/api/texts/"):
        raise ValueError(
            f"resourceUrl path must start with /api/texts/, got {parsed.path!r}"
        )
    key = parsed.path[len("/api/texts/"):]
    if not key:
        raise ValueError(
            f"resourceUrl missing ref segment after /api/texts/: {parsed.path!r}"
        )
    if "%" in key:
        # Reject percent-encoding outright. ``%2F`` would smuggle a ``/`` past
        # the single-segment check; ``%2E%2E`` would smuggle ``..``;
        # double-encoded ``%252F`` defeats single-pass decoding. Sefaria refs
        # use plain ASCII (``Rashi_on_Daniel.7.13``), so any ``%`` is suspect.
        raise ValueError(
            f"resourceUrl ref segment must not contain percent-encoded "
            f"characters: {key!r}"
        )
    segments = key.split("/")
    if len(segments) > 1:
        # Catches both trailing extras (.../Rashi_on_Daniel.7.13/extra) and
        # empty segments produced by a doubled slash (.../api/texts//foo).
        raise ValueError(
            f"resourceUrl ref must be a single path segment, got {parsed.path!r}"
        )
    seg = segments[0]
    if seg in (".", ".."):
        raise ValueError(f"resourceUrl ref segment is reserved: {seg!r}")
    if seg.startswith("."):
        raise ValueError(
            f"resourceUrl ref segment must not start with '.': {seg!r}"
        )
    if not _REF_SEGMENT_RE.match(seg):
        # Final positive allowlist: ASCII letters/digits/underscore/dot/hyphen
        # only. Catches backslash, embedded whitespace, zero-width joiners
        # (U+200D), right-to-left overrides (U+202E), non-breaking spaces
        # (U+00A0), and any non-ASCII character.
        raise ValueError(
            f"resourceUrl ref segment contains disallowed characters; "
            f"only [A-Za-z0-9_.-] permitted, got {seg!r}"
        )


def _sefaria_cache_path(url: str) -> Path:
    """Map a Sefaria text-API URL to its on-disk cache file."""
    parsed = urllib.parse.urlparse(url)
    key = parsed.path[len("/api/texts/"):]
    return SEFARIA_CACHE_DIR / f"{key}.json"


# Tests monkeypatch this to avoid hitting the network. Keep the signature
# narrow (one URL → parsed JSON) so substitutions are trivial.
def _fetch_sefaria_uncached(url: str) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "logos4-research-citations/0.1 (+local)"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
    return json.loads(raw.decode("utf-8"))


def _fetch_sefaria(url: str) -> dict[str, Any]:
    """Disk-cached wrapper around the Sefaria text API.

    Cache invalidation: Sefaria texts are stable references — a cached
    Daniel 7:13 response stays valid as long as Sefaria's underlying edition
    doesn't change. To force a refresh, delete the cache file by hand. We
    intentionally do not auto-expire: research citations should be reproducible
    against the exact text we verified them against.
    """
    cache_path = _sefaria_cache_path(url)
    if cache_path.exists():
        try:
            return json.loads(cache_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            # Corrupt cache file — fall through and re-fetch.
            pass
    data = _fetch_sefaria_uncached(url)
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except OSError:
        # Cache write failure is non-fatal; verification can still proceed.
        pass
    return data


def _flatten_sefaria_text(field: Any) -> str:
    """Sefaria's text/he fields are arrays of strings (one per segment within
    the cited verse). For multi-verse spans they may be nested arrays. Flatten
    to a newline-joined string preserving order."""
    if field is None:
        return ""
    if isinstance(field, str):
        return field
    if isinstance(field, list):
        parts: list[str] = []
        for item in field:
            sub = _flatten_sefaria_text(item)
            if sub:
                parts.append(sub)
        return "\n".join(parts)
    return ""


def _strip_html_tags(text: str) -> str:
    """Strip HTML tags using the same parser used for EPUB extraction."""
    stripper = _HtmlStripper()
    stripper.feed(text)
    return stripper.text()


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
    # Hebrew + Greek + Latin diacritic combinations differ between NFC (composed)
    # and NFD (decomposed). Sefaria returns mixed forms; some Logos articles
    # store NFD. Normalize to NFC so quote+article are compared in the same
    # form. Idempotent on already-NFC text.
    return _WHITESPACE_RE.sub(
        " ", unicodedata.normalize("NFC", text).translate(_TYPO_MAP)
    ).strip()


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
