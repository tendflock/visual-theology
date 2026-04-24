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
import json
import os
import re
import sys
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from study import _resolve_bare_stem, get_article_meta, read_article_text  # noqa: E402


_MAX_ARTICLE_CHARS = 500_000  # Covers the longest articles in the library.


def sha256_of(text: str) -> str:
    """Return the lowercase-hex SHA-256 of ``text`` encoded as UTF-8."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_citation(
    resource_file: str,
    article_num: int,
    quote_text: str | None = None,
    author: str | None = None,
    short_title: str | None = None,
    full_title: str | None = None,
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
    }


def verify_citation(citation: dict[str, Any]) -> dict[str, Any]:
    """Confirm that the cited quote appears in the referenced article.

    Returns a dict with ``status`` ∈ {``verified``, ``partial``,
    ``quote-not-found``, ``resource-unreadable``} plus diagnostic fields.
    """
    backend = citation.get("backend") or {}
    resource_id = backend.get("resourceId")
    article_num = backend.get("logosArticleNum")

    if not resource_id or article_num is None:
        return {
            "status": "resource-unreadable",
            "notes": "citation missing backend.resourceId or logosArticleNum",
        }

    resource_file = _resource_id_to_file(resource_id)
    article_text = read_article_text(
        resource_file, int(article_num), max_chars=_MAX_ARTICLE_CHARS
    )

    if not article_text:
        return {
            "status": "resource-unreadable",
            "notes": f"empty article text from {resource_file!r} #{article_num}",
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

    norm_article = _normalize_whitespace(article_text)
    norm_needle = _normalize_whitespace(needle)
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
            f"quote text (len={len(needle)}) not found in article "
            f"{resource_id} #{article_num} (article len={len(article_text)})"
        ),
    }


# ── helpers ─────────────────────────────────────────────────────────────────


_WHITESPACE_RE = re.compile(r"\s+")


def _normalize_whitespace(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text).strip()


def _resource_id_to_file(resource_id: str) -> str:
    """``LLS:GS_WALV_DANIEL`` → ``GS_WALV_DANIEL.lbxlls`` (actual filename).

    The reader's ``--article-meta`` path resolves bare stems via the
    ResourceManager catalog, but ``read_article_text`` goes through the
    positional-arg path which requires a filename with extension. Use
    ``_resolve_bare_stem`` to look it up.
    """
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
