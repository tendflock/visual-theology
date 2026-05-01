#!/bin/bash
# Generalized OCR-prep tool for external (non-Logos) resources.
#
# Generalizes external-resources/greek/extract_pg81_range.sh to handle the
# input-format population the D-1.5 / D-1J audits surfaced for Wave 6.3 and
# Wave 7 surveys. The Theodoret-specific wrapper is preserved unchanged at
# external-resources/greek/extract_pg81_range.sh; this tool is its successor
# for new voices.
#
# Format coverage (audited 2026-04-28; see docs/research/2026-04-28-*-audit.md):
#
#   * PDF, full or paged range — archive.org single-volume scans, e-rara,
#     MDZ/BSB digitale-sammlungen.de, Google Books legacy ?output=pdf form,
#     HebrewBooks (manual download recommended; Cloudflare blocks scripted
#     access). Uses pdftoppm + tesseract with the requested language pack.
#   * PDF, Migne-shaped column range — same pipeline + parameterised
#     col->page formula. Default formula (col + 55) / 2 matches PG 81;
#     pass --col-formula to override for other PG / PL volumes.
#   * archive.org _djvu.txt plain-text — skips OCR; archive.org already
#     publishes a full-volume plain-text extraction at
#     archive.org/download/<id>/<id>_djvu.txt (audit D-1J §B3 notes Yefet
#     ben Eli's commentary is best ingested this way). The /stream/ form
#     of the same path serves an HTML viewer wrapping the text — do NOT
#     use it; see Tool-bug follow-up in external-resources/latin/_OCR-PREP-NOTES.md.
#   * HTML — CCEL work-slug pages; strips tags via Python's html.parser.
#
# Subcommands:
#
#   extract_ocr.sh pdf <url> <language> <output-path> [--pages N-M] \
#                      [--dpi 200|300] [--psm N]
#   extract_ocr.sh pdf-columns <url> <first-col> <last-col> <language> \
#                      <output-path> [--col-formula "(col + 55) / 2"] \
#                      [--dpi 200|300] [--psm N]
#   extract_ocr.sh archive-text <archive-id> <output-path>
#   extract_ocr.sh html <url> <output-path>
#   extract_ocr.sh --help
#
# Language codes follow tesseract conventions (grc, lat, deu, heb, ara,
# fra, eng, frk for Fraktur, deu+frk for mixed). For Migne-shaped two-
# column layouts pass `<lang>+lat` to capture the parallel Latin column.
#
# URL hygiene: only https:// URLs are accepted. Shell metacharacters in
# URLs and `..` segments in output paths are rejected. Beyond that, URL
# trustworthiness is the caller's responsibility — this tool fetches what
# it is told to fetch.
#
# macOS Leptonica quirk: tesseract on absolute paths under /Volumes/External
# fails ("Error in fopenReadStream"). The OCR loop `cd`s to the per-run
# cache dir before invoking tesseract; relative basenames work around the
# Leptonica path bug. Don't refactor that without testing on macOS.
#
# Quality heuristic: a final OCR text smaller than 500 bytes per 100 PDF
# pages is flagged as a warning — usually a missing language pack, an
# encrypted PDF, or a scan where pdftoppm produced empty pages.

set -e

usage() {
  cat <<'EOF'
Usage: extract_ocr.sh <subcommand> [args...]

Subcommands:
  pdf <url> <language> <output-path> [--pages N-M] [--dpi DPI] [--psm N]
      Download a PDF and OCR its pages. --pages defaults to all pages;
      --dpi defaults to 200; --psm defaults to 6 (single uniform block).

  pdf-columns <url> <first-col> <last-col> <language> <output-path> \
              [--col-formula "(col + 55) / 2"] [--dpi DPI] [--psm N]
      Migne-shaped column range. Formula maps a column number to a PDF
      page number. Default matches PG 81; override for other volumes.
      --psm defaults to 4 (single column of variable text), which reads
      Migne's two-column Greek+Latin layout best.

  archive-text <archive-id> <output-path>
      Fetch archive.org's pre-extracted _djvu.txt plain-text for the
      given identifier. No OCR; preserves whatever archive.org's pass
      produced (mixed languages, page markers, etc.).

  html <url> <output-path>
      Fetch an HTML page and strip tags. CCEL work-slug pages are the
      canonical use case; other hosts work but are not specifically
      tuned. Output is plain text with paragraph spacing preserved.

  --help, -h
      Print this message.

Examples:
  # Migne PG 81 (Theodoret on Daniel 7) — equivalent to
  # external-resources/greek/extract_pg81_range.sh 1411 1437 dan7 :
  extract_ocr.sh pdf-columns \
    https://archive.org/download/patrologiaecursusxx81mign/patrologiae_cursus_completus_gr_vol_081.pdf \
    1411 1437 grc+lat \
    /Volumes/External/Logos4/external-resources/greek/theodoret-pg81-dan7.txt

  # archive.org full-volume PDF (Cooper-Mede 1833 ET):
  extract_ocr.sh pdf \
    https://archive.org/download/atranslationmed00medegoog/atranslationmed00medegoog.pdf \
    eng \
    /Volumes/External/Logos4/external-resources/english/mede-clavis-cooper.txt \
    --pages 50-80

  # archive.org plain-text (Yefet ben Eli 1889 Margoliouth):
  extract_ocr.sh archive-text commentaryonbook00japhuoft \
    /Volumes/External/Logos4/external-resources/judeo-arabic/yefet-daniel-margoliouth.txt

  # CCEL HTML (Origen Against Celsus, work-slug pattern):
  extract_ocr.sh html \
    https://ccel.org/ccel/origen/against_celsus/anf04.vi.ix.vi.lv.html \
    /Volumes/External/Logos4/external-resources/english/origen-celsus-vi-lv.txt
EOF
}

die() {
  echo "extract_ocr.sh: error: $*" >&2
  exit 2
}

require_command() {
  local cmd=$1
  command -v "$cmd" >/dev/null 2>&1 || die "required tool not on PATH: $cmd"
}

# https-only, no shell metachars, no file:// or javascript:.
validate_url() {
  local url=$1
  case "$url" in
    https://*) ;;
    *) die "URL must start with https://: $url" ;;
  esac
  case "$url" in
    *' '*|*$'\t'*|*$'\n'*|*\`*|*\$*|*\;*|*\&*|*\|*|*\<*|*\>*)
      die "URL contains shell metacharacters: $url"
      ;;
  esac
}

# Disallow path traversal in output paths.
validate_output_path() {
  local p=$1
  case "$p" in
    *../*|../*|*/..|..) die "output path contains '..': $p" ;;
  esac
}

# archive.org identifier must be ASCII alphanumeric with ._- only.
validate_archive_id() {
  local id=$1
  if ! printf '%s' "$id" | LC_ALL=C grep -Eq '^[A-Za-z0-9._-]+$'; then
    die "archive identifier contains unsafe characters: $id"
  fi
}

# Confirm tesseract has the requested language pack(s). Accepts "grc",
# "grc+lat", etc.
require_tesseract_langs() {
  local lang_spec=$1
  require_command tesseract
  local available
  available=$(tesseract --list-langs 2>&1 | tail -n +2)
  local IFS='+'
  for lang in $lang_spec; do
    if ! printf '%s\n' "$available" | grep -qx "$lang"; then
      die "tesseract language pack '$lang' not installed; have:
$available

Install via: brew install tesseract-lang  (or for Fraktur: download
deu_frak.traineddata into \$(brew --prefix)/share/tessdata/)"
    fi
  done
}

# Download with curl. Resumable (-C -). Sets a UA so archive.org and
# CCEL don't 403 the bare libcurl default. Skips re-download if the
# cached file is non-empty.
fetch_url() {
  local url=$1
  local dest=$2
  if [ -s "$dest" ]; then
    echo "  cached: $dest"
    return 0
  fi
  require_command curl
  echo "  fetching: $url"
  echo "    -> $dest"
  mkdir -p "$(dirname "$dest")"
  curl --location \
       --fail \
       --silent --show-error \
       --user-agent "extract_ocr.sh/1.0 (+https://github.com/anthropics/claude-code)" \
       --connect-timeout 30 \
       --max-time 1800 \
       -C - \
       -o "$dest" \
       "$url"
}

# OCR every PNG in CACHE matching p<page>.png; produce p<page>.txt next
# to it. Skips already-OCR'd pages. Uses macOS Leptonica path workaround
# (cd into CACHE so tesseract sees relative paths).
ocr_cache_pages() {
  local cache=$1
  local lang=$2
  local psm=$3
  require_command tesseract
  local pwd_save
  pwd_save=$(pwd)
  cd "$cache"
  local n=0
  for img in p*.png; do
    [ -e "$img" ] || continue
    local txt="${img%.png}.txt"
    if [ ! -s "$txt" ]; then
      tesseract "$img" "${img%.png}" -l "$lang" --psm "$psm" >/dev/null 2>&1 || true
      n=$((n+1))
    fi
  done
  cd "$pwd_save"
  echo "  OCR'd pages: $n new"
}

# Extract a contiguous page range from a PDF as PNGs into CACHE/p####.png.
# pdftoppm names files like prefix-NNNN.png; we rename to canonical.
pdf_to_pngs() {
  local pdf=$1
  local cache=$2
  local first=$3
  local last=$4
  local dpi=$5
  require_command pdftoppm
  mkdir -p "$cache"
  local n=0
  local p
  for p in $(seq -f "%04g" "$first" "$last"); do
    local img="${cache}/p${p}.png"
    if [ ! -s "$img" ]; then
      pdftoppm -f "$((10#$p))" -l "$((10#$p))" -r "$dpi" -png \
               "$pdf" "${cache}/p${p}_tmp" >/dev/null 2>&1
      mv "${cache}/p${p}_tmp-${p}.png" "$img" 2>/dev/null \
        || mv "${cache}/p${p}_tmp"-*.png "$img" 2>/dev/null \
        || true
      n=$((n+1))
    fi
  done
  echo "  Extracted images: $n new"
}

# Concatenate per-page txt files in CACHE into OUT, with the supplied
# header lines and page markers.
concat_with_markers() {
  local cache=$1
  local out=$2
  local first=$3
  local last=$4
  local marker_template=$5
  shift 5
  mkdir -p "$(dirname "$out")"
  {
    for line in "$@"; do
      printf '%s\n' "$line"
    done
    echo
    local p
    for p in $(seq -f "%04g" "$first" "$last"); do
      local txt="${cache}/p${p}.txt"
      if [ -s "$txt" ]; then
        local marker
        marker=$(printf "$marker_template" "$p")
        printf '%s\n' "$marker"
        cat "$txt"
        echo
      fi
    done
  } > "$out"
}

# Warn if OCR output is suspiciously small.
quality_check() {
  local out=$1
  local pages=$2
  local size
  size=$(wc -c <"$out" | tr -d ' ')
  local expected=$(( pages * 5 ))  # ~5 bytes/page is the absolute floor
  echo "  Output size: ${size} bytes across ${pages} page(s)"
  if [ "$pages" -ge 100 ] && [ "$size" -lt 500 ]; then
    echo "  WARNING: ${size} bytes for ${pages} pages is suspiciously small."
    echo "           Likely missing language pack, encrypted PDF, or empty scan."
  elif [ "$size" -lt "$expected" ]; then
    echo "  WARNING: output smaller than ${expected} bytes; check OCR quality."
  fi
}

# Get the basename of an output path, stripping .txt suffix, for cache
# directory naming.
output_tag() {
  local out=$1
  local base
  base=$(basename "$out")
  printf '%s' "${base%.txt}"
}

# ---------- subcommand: pdf ----------

cmd_pdf() {
  local url=""
  local language=""
  local output=""
  local pages=""
  local dpi=200
  local psm=6

  local positional=()
  while [ $# -gt 0 ]; do
    case "$1" in
      --pages) pages=$2; shift 2 ;;
      --dpi) dpi=$2; shift 2 ;;
      --psm) psm=$2; shift 2 ;;
      --help|-h) usage; exit 0 ;;
      --*) die "unknown flag: $1" ;;
      *) positional+=("$1"); shift ;;
    esac
  done
  [ ${#positional[@]} -eq 3 ] || die "pdf: need <url> <language> <output-path>; got ${#positional[@]} positional"
  url=${positional[0]}
  language=${positional[1]}
  output=${positional[2]}

  validate_url "$url"
  validate_output_path "$output"
  # Parse --pages format up-front so a misformatted value fails before
  # the network fetch. last is filled in post-fetch when --pages is absent.
  local first="" last=""
  if [ -n "$pages" ]; then
    case "$pages" in
      *-*) first=${pages%-*}; last=${pages#*-} ;;
      *) die "--pages must be N-M, got: $pages" ;;
    esac
    case "$first" in ''|*[!0-9]*) die "--pages must be N-M, got: $pages" ;; esac
    case "$last" in ''|*[!0-9]*) die "--pages must be N-M, got: $pages" ;; esac
  fi
  require_tesseract_langs "$language"
  require_command pdftoppm

  local tag
  tag=$(output_tag "$output")
  local cache="/tmp/extract-ocr-${tag}"
  mkdir -p "$cache"

  local pdf="${cache}/source.pdf"
  fetch_url "$url" "$pdf"

  # If --pages was absent, fall back to pdfinfo or a conservative cap.
  if [ -z "$first" ]; then
    first=1
    if command -v pdfinfo >/dev/null 2>&1; then
      last=$(pdfinfo "$pdf" 2>/dev/null | awk '/^Pages:/ {print $2}')
      [ -n "$last" ] || last=2000
    else
      last=2000
    fi
  fi

  echo "Extracting PDF pages ${first}-${last} from ${url}"
  echo "  Cache: ${cache}"
  pdf_to_pngs "$pdf" "$cache" "$first" "$last" "$dpi"
  ocr_cache_pages "$cache" "$language" "$psm"

  local marker='==== PDF page %s ===='
  concat_with_markers "$cache" "$output" "$first" "$last" "$marker" \
    "# Extracted from PDF" \
    "# Source: ${url}" \
    "# Pages: ${first}-${last}, DPI: ${dpi}, PSM: ${psm}, language: ${language}" \
    "# Generated $(date '+%Y-%m-%d %H:%M:%S')" \
    "# WARNING: OCR-quality. Verify against the printed page for any citation."

  echo
  echo "Output: $output"
  quality_check "$output" "$((last - first + 1))"
}

# ---------- subcommand: pdf-columns ----------

cmd_pdf_columns() {
  local url=""
  local first_col=""
  local last_col=""
  local language=""
  local output=""
  local formula="(col + 55) / 2"
  local dpi=200
  local psm=4

  local positional=()
  while [ $# -gt 0 ]; do
    case "$1" in
      --col-formula) formula=$2; shift 2 ;;
      --dpi) dpi=$2; shift 2 ;;
      --psm) psm=$2; shift 2 ;;
      --help|-h) usage; exit 0 ;;
      --*) die "unknown flag: $1" ;;
      *) positional+=("$1"); shift ;;
    esac
  done
  [ ${#positional[@]} -eq 5 ] || die "pdf-columns: need <url> <first-col> <last-col> <language> <output-path>; got ${#positional[@]}"
  url=${positional[0]}
  first_col=${positional[1]}
  last_col=${positional[2]}
  language=${positional[3]}
  output=${positional[4]}

  validate_url "$url"
  validate_output_path "$output"
  case "$first_col" in ''|*[!0-9]*) die "first-col must be integer: $first_col" ;; esac
  case "$last_col" in ''|*[!0-9]*) die "last-col must be integer: $last_col" ;; esac
  [ "$last_col" -ge "$first_col" ] || die "last-col < first-col"
  require_tesseract_langs "$language"
  require_command pdftoppm

  # Evaluate formula via a constrained python expression. Reject anything
  # that is not pure integer arithmetic against the 'col' name.
  if ! printf '%s' "$formula" | LC_ALL=C grep -Eq '^[ ()0-9+*/col-]+$'; then
    die "col-formula must be pure integer arithmetic on 'col': $formula"
  fi

  local first_page last_page
  first_page=$(python3 -c "col=$first_col; print(int(($formula)))")
  last_page=$(python3 -c "col=$last_col; print(int(($formula)) + 1)")

  local tag
  tag=$(output_tag "$output")
  local cache="/tmp/extract-ocr-${tag}"
  mkdir -p "$cache"

  local pdf="${cache}/source.pdf"
  fetch_url "$url" "$pdf"

  echo "Extracting PDF columns ${first_col}-${last_col} (pages ${first_page}-${last_page})"
  echo "  Source: ${url}"
  echo "  Formula: ${formula}"
  echo "  Cache: ${cache}"
  pdf_to_pngs "$pdf" "$cache" "$first_page" "$last_page" "$dpi"
  ocr_cache_pages "$cache" "$language" "$psm"

  local marker='==== PDF page %s ===='
  concat_with_markers "$cache" "$output" "$first_page" "$last_page" "$marker" \
    "# Extracted from PDF column range" \
    "# Source: ${url}" \
    "# Columns: ${first_col}-${last_col}; PDF pages: ${first_page}-${last_page}" \
    "# Formula: ${formula}; DPI: ${dpi}, PSM: ${psm}, language: ${language}" \
    "# Generated $(date '+%Y-%m-%d %H:%M:%S')" \
    "# WARNING: OCR-quality. Greek/Latin parallel text may interleave."

  echo
  echo "Output: $output"
  quality_check "$output" "$((last_page - first_page + 1))"
}

# ---------- subcommand: archive-text ----------

cmd_archive_text() {
  local positional=()
  while [ $# -gt 0 ]; do
    case "$1" in
      --help|-h) usage; exit 0 ;;
      --*) die "unknown flag: $1" ;;
      *) positional+=("$1"); shift ;;
    esac
  done
  [ ${#positional[@]} -eq 2 ] || die "archive-text: need <archive-id> <output-path>; got ${#positional[@]}"
  local archive_id=${positional[0]}
  local output=${positional[1]}

  validate_archive_id "$archive_id"
  validate_output_path "$output"

  # /download/ serves the raw _djvu.txt; /stream/ serves an HTML viewer
  # wrapping it. The HTML wrapper is large enough to clear the < 1000-byte
  # quality floor below, so the wrong endpoint will silently produce a
  # citation-unsafe file. See external-resources/latin/_OCR-PREP-NOTES.md
  # ("Tool-bug follow-up").
  local url="https://archive.org/download/${archive_id}/${archive_id}_djvu.txt"
  echo "Fetching archive.org plain-text for ${archive_id}"
  fetch_url "$url" "$output"
  echo
  echo "Output: $output"
  local size
  size=$(wc -c <"$output" | tr -d ' ')
  echo "  Size: ${size} bytes"
  if [ "$size" -lt 1000 ]; then
    echo "  WARNING: < 1000 bytes — archive.org may not have a _djvu.txt for this id."
    echo "           Try the IA item page directly: https://archive.org/details/${archive_id}"
  fi
  # Defensive sniff: if archive.org ever returns an HTML page (redirect to
  # a viewer, item-not-found stub, etc.) on the /download/ path, fail the
  # subcommand rather than letting downstream survey runs treat it as
  # text. The HTML wrapper is large enough to clear the < 1000-byte floor
  # above, so a non-fatal warning would silently degrade — see codex
  # follow-up in OCR-1.5 session notes.
  if head -c 256 "$output" 2>/dev/null | LC_ALL=C grep -qE '<!DOCTYPE|<html|<body'; then
    echo "  ERROR: output begins with HTML markup — archive.org returned a" >&2
    echo "         viewer page rather than plain text. The output file" >&2
    echo "         was written but is NOT citation-ready. Inspect:" >&2
    echo "           $output" >&2
    echo "         and re-fetch from a corrected URL before retrying." >&2
    exit 3
  fi
}

# ---------- subcommand: html ----------

cmd_html() {
  local positional=()
  while [ $# -gt 0 ]; do
    case "$1" in
      --help|-h) usage; exit 0 ;;
      --*) die "unknown flag: $1" ;;
      *) positional+=("$1"); shift ;;
    esac
  done
  [ ${#positional[@]} -eq 2 ] || die "html: need <url> <output-path>; got ${#positional[@]}"
  local url=${positional[0]}
  local output=${positional[1]}

  validate_url "$url"
  validate_output_path "$output"
  require_command python3

  local tag
  tag=$(output_tag "$output")
  local cache="/tmp/extract-ocr-${tag}"
  mkdir -p "$cache"
  local html="${cache}/source.html"
  fetch_url "$url" "$html"

  mkdir -p "$(dirname "$output")"
  echo "Stripping HTML -> plain text"
  python3 - "$html" "$output" "$url" <<'PY'
import html.parser
import sys

src, dest, source_url = sys.argv[1], sys.argv[2], sys.argv[3]

class Stripper(html.parser.HTMLParser):
    BLOCK_TAGS = {
        "p", "div", "br", "h1", "h2", "h3", "h4", "h5", "h6",
        "li", "tr", "section", "article", "blockquote",
    }
    SKIP_TAGS = {"script", "style", "head", "noscript"}

    def __init__(self):
        super().__init__()
        self._chunks = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP_TAGS:
            self._skip += 1
            return
        if tag in self.BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP_TAGS and self._skip > 0:
            self._skip -= 1
            return
        if tag in self.BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_data(self, data):
        if self._skip == 0:
            self._chunks.append(data)

    def text(self):
        return "".join(self._chunks)

with open(src, "r", encoding="utf-8", errors="replace") as fh:
    raw = fh.read()

parser = Stripper()
parser.feed(raw)
text = parser.text()

# Collapse 3+ blank lines to 2; trim trailing whitespace per line.
lines = [ln.rstrip() for ln in text.splitlines()]
out_lines = []
blank = 0
for ln in lines:
    if ln.strip() == "":
        blank += 1
        if blank <= 2:
            out_lines.append("")
    else:
        blank = 0
        out_lines.append(ln)
body = "\n".join(out_lines).strip() + "\n"

# CCEL "loading..." placeholder check (D-1.5 audit §4b notes some
# work-slug sub-pages render with hydration placeholders).
if body.lower().count("loading") > 5 and len(body) < 2000:
    sys.stderr.write(
        "  WARNING: page body is small and contains many 'loading' tokens.\n"
        "           CCEL sometimes hydrates content via JS; consider fetching\n"
        "           the work-level XML / TML / plain-text export instead.\n"
    )

header = (
    f"# Extracted from HTML\n"
    f"# Source: {source_url}\n"
    f"# WARNING: HTML-stripped. Verify against the canonical edition for citations.\n\n"
)
with open(dest, "w", encoding="utf-8") as fh:
    fh.write(header + body)
PY
  echo
  echo "Output: $output"
  local size
  size=$(wc -c <"$output" | tr -d ' ')
  echo "  Size: ${size} bytes"
  if [ "$size" -lt 500 ]; then
    echo "  WARNING: < 500 bytes — page may be a JS-hydrated stub."
  fi
}

# ---------- dispatcher ----------

main() {
  if [ $# -eq 0 ]; then
    usage
    exit 2
  fi

  local sub=$1
  shift
  case "$sub" in
    pdf) cmd_pdf "$@" ;;
    pdf-columns) cmd_pdf_columns "$@" ;;
    archive-text) cmd_archive_text "$@" ;;
    html) cmd_html "$@" ;;
    --help|-h|help) usage; exit 0 ;;
    *) die "unknown subcommand: $sub (try --help)" ;;
  esac
}

main "$@"
