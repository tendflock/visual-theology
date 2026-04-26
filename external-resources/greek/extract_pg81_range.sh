#!/bin/bash
# Direct PDF extraction of a Migne PG 81 column range.
#
# Replaces the TLG-screenshot pipeline (ingest_theodoret.sh) with direct
# extraction from the archive.org Migne PG 81 PDF scan.
#
# Usage:
#   external-resources/greek/extract_pg81_range.sh <first-col> <last-col> <output-tag>
#
# Example (Daniel 7):
#   extract_pg81_range.sh 1411 1437 dan7
#   → produces external-resources/greek/theodoret-pg81-dan7.txt
#
# Empirical mapping (verified 2026-04-26 by inspecting page headers):
#   PDF page 730 = cols 1405-1406  Dan VI
#   PDF page 733 = cols 1411-1412  ← Dan VII opener (LIBER SEPTIMUS / CAPUT VII)
#   PDF page 740 = cols 1425-1426  Dan VII (mid)
#   PDF page 770 = cols 1485-1486  Dan IX (end) / X (start)
#   PDF page 772 = cols 1489-1490  Dan X
#   PDF page 773 = cols 1491-1492  Dan X
#   PDF page 780 = cols 1505-1508  Dan XI
#
# Mapping formula:
#   PDF page = (Migne col + 55) / 2
#   (i.e., 2 cols per PDF page, with a +27.5 page offset for front matter)
#
# Pipeline:
#   pdftoppm -r 200 -png  →  tesseract -l grc --psm 6  →  concatenate

set -e

if [ "$#" -ne 3 ]; then
  echo "Usage: $0 <first-col> <last-col> <output-tag>"
  echo "Example (Dan 7): $0 1411 1437 dan7"
  exit 2
fi

FIRST_COL=$1
LAST_COL=$2
TAG=$3

PDF=/Volumes/External/Logos4/external-resources/greek/migne-pg81-archiveorg/patrologiae_cursus_completus_gr_vol_081.pdf
OUT=/Volumes/External/Logos4/external-resources/greek/theodoret-pg81-${TAG}.txt
CACHE=/tmp/pg81-extract-${TAG}
mkdir -p "$CACHE"

# col → page formula: PDF page = (col + 55) / 2
FIRST_PAGE=$(( (FIRST_COL + 55) / 2 ))
LAST_PAGE=$(( (LAST_COL + 55) / 2 + 1 ))

echo "Extracting PG 81 cols ${FIRST_COL}–${LAST_COL}"
echo "  PDF page range: ${FIRST_PAGE}–${LAST_PAGE} (${PDF})"
echo "  Cache dir:      ${CACHE}"
echo

# Extract PNGs at 200dpi (good quality for grc OCR)
NEW=0
for p in $(seq -f "%04g" "$FIRST_PAGE" "$LAST_PAGE"); do
  img="${CACHE}/p${p}.png"
  if [ ! -s "$img" ]; then
    pdftoppm -f "$((10#$p))" -l "$((10#$p))" -r 200 -png "$PDF" "${CACHE}/p${p}_tmp" >/dev/null 2>&1
    # pdftoppm appends a -NNNN suffix; rename to canonical
    mv "${CACHE}/p${p}_tmp-${p}.png" "$img" 2>/dev/null \
      || mv "${CACHE}/p${p}_tmp"-*.png "$img" 2>/dev/null
    NEW=$((NEW+1))
  fi
done
echo "  Extracted images: ${NEW} new (cached: $((LAST_PAGE - FIRST_PAGE + 1 - NEW)))"

# OCR each page with grc (Ancient Greek), single uniform block.
# Migne is a 2-column page (Greek + Latin parallel). --psm 4 (assume single
# column of variable text) handles the parallel layout best by reading the
# whole page; the output mixes Greek and Latin lines but we can filter.
NEW=0
# Tesseract+Leptonica fail on absolute paths under /Volumes/External CWD;
# work from inside the cache dir using basenames.
PWD_SAVE=$(pwd)
cd "$CACHE"
for p in $(seq -f "%04g" "$FIRST_PAGE" "$LAST_PAGE"); do
  if [ ! -s "p${p}.txt" ]; then
    tesseract "p${p}.png" "p${p}" -l grc+lat --psm 4 >/dev/null 2>&1 || true
    NEW=$((NEW+1))
  fi
done
cd "$PWD_SAVE"
echo "  OCR'd pages:      ${NEW} new"

# Concatenate with page markers
{
  echo "# Theodoret of Cyrus, Commentary on Daniel — PG 81 cols ${FIRST_COL}-${LAST_COL}"
  echo "# Source: Migne PG 81 (1864), archive.org Google Books scan"
  echo "# Tag: ${TAG}"
  echo "# Extracted $((LAST_PAGE - FIRST_PAGE + 1)) PDF pages via pdftoppm 200dpi + tesseract grc+lat psm 4"
  echo "# Generated $(date '+%Y-%m-%d %H:%M:%S')"
  echo "# WARNING: OCR-quality. Greek and Latin parallel text are interleaved."
  echo "# Citations should use whitespace + typographic-normalized matching."
  echo
  for p in $(seq -f "%04g" "$FIRST_PAGE" "$LAST_PAGE"); do
    txt="${CACHE}/p${p}.txt"
    if [ -s "$txt" ]; then
      col_left=$(( (10#$p - 27) * 2 + 1 ))   # approximate left col of this page
      col_right=$(( col_left + 1 ))
      echo "==== PDF page ${p} (Migne PG 81 cols ~${col_left}-${col_right}) ===="
      cat "$txt"
      echo
    fi
  done
} > "$OUT"

set +e

size=$(wc -c <"$OUT" | tr -d ' ')
lines=$(wc -l <"$OUT" | tr -d ' ')
echo
echo "Output: $OUT"
echo "Size: ${size} bytes, ${lines} lines"
echo
echo "Daniel-7 marker check (lights up if Dan 7 content is captured):"
for kw in "Παλαι" "θρόν" "ημερων\|ἡμερῶν" "θηρ" "κερας\|κέρας" "ανθρωπου\|ἀνθρώπου"; do
  n=$(grep -ic "$kw" "$OUT")
  printf "  %-30s %d hits\n" "$kw" "$n"
done