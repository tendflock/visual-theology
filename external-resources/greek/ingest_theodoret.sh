#!/bin/bash
# Incremental OCR ingestor for Theodoret on Daniel screenshot folders.
#
# Usage:
#   external-resources/greek/ingest_theodoret.sh
#
# Scans ~/Desktop/Theodorus, ~/Desktop/Theodorus2, ~/Desktop/Theodorus3, …
# in order. For each PNG, upscales to 1800px height (sips) and OCRs with
# tesseract using the `grc` (Ancient Greek) traineddata. Caches per-image
# OCR output under /tmp/theod-ocr/txt/pNNN.txt; only OCRs new images.
# Concatenates the full result into
# external-resources/greek/theodoret-daniel-pg81-ocr.txt.
#
# Reports current Migne-PG-81 column range and a Daniel-7 marker check.
#
# Why ASCII rename: macOS screenshot filenames have a non-breaking space
# (U+00A0) before "PM" that breaks tesseract+leptonica's path handling.

set -e
# (set +e for the diagnostic tail at the end — grep returning 0 matches is
# normal early in capture and must not abort the script.)

OUT=/Volumes/External/Logos4/external-resources/greek/theodoret-daniel-pg81-ocr.txt
CACHE=/tmp/theod-ocr
mkdir -p "$CACHE/up" "$CACHE/txt"

i=0
folders_found=0
for dir in ~/Desktop/Theodorus ~/Desktop/Theodorus2 ~/Desktop/Theodorus3 \
           ~/Desktop/Theodorus4 ~/Desktop/Theodorus5; do
  if [ ! -d "$dir" ]; then continue; fi
  folders_found=$((folders_found + 1))
  cd "$dir"
  for f in Screen*.png; do
    [ ! -e "$f" ] && continue
    i=$((i + 1))
    printf -v idx '%03d' "$i"
    if [ ! -s "$CACHE/up/p${idx}.png" ]; then
      sips -s format png --resampleHeight 1800 "$f" --out "$CACHE/up/p${idx}.png" >/dev/null 2>&1
    fi
  done
done
echo "Folders ingested: $folders_found"
echo "Total screenshots: $i"

cd "$CACHE/up"
new=0
for f in p*.png; do
  out="$CACHE/txt/${f%.png}.txt"
  if [ ! -s "$out" ]; then
    tesseract "$f" "${out%.txt}" -l grc --psm 6 2>/dev/null
    new=$((new + 1))
  fi
done
echo "Newly OCR'd: $new"

# Concatenate
{
  echo "# Theodoret of Cyrus, In visiones Danielis prophetae (TLG 4089.028 / Migne PG 81)"
  echo "# OCR of $i screenshots from Migne PG 81 captured via TLG/Scribd"
  echo "# Tesseract 5.5.2 with grc traineddata, --psm 6, 1800px upscale"
  echo "# Generated $(date '+%Y-%m-%d %H:%M:%S') by ingest_theodoret.sh"
  echo "# WARNING: OCR-quality Greek. Polytonic accents and a few characters may be miscaptured."
  echo "# Citations against this text MUST use whitespace + typographic-normalized matching"
  echo "# (see tools/citations.py:_normalize)."
  echo
  for j in $(seq -f "%03g" 1 "$i"); do
    if [ -s "$CACHE/txt/p${j}.txt" ]; then
      echo "==== screenshot p${j} ===="
      cat "$CACHE/txt/p${j}.txt"
      echo
    fi
  done
} > "$OUT"

# Status report
size=$(wc -c <"$OUT" | tr -d ' ')
lines=$(wc -l <"$OUT" | tr -d ' ')
echo
echo "Output: $OUT"
echo "Size: $size bytes, $lines lines"
set +e   # diagnostic tail: zero matches is acceptable, don't abort

echo
echo "Migne PG 81 column range covered:"
grep -oE '\([0-9]{4}\)' "$OUT" \
  | tr -d '()' \
  | awk '$1>=1250 && $1<=1550' \
  | sort -un \
  | awk 'NR==1{f=$1}{l=$1}END{print "  first col:", f; print "  last col:", l; print "  unique cols:", NR}'

echo
echo "Daniel-7 marker check (Theodotion-OG distinctive phrases; OCR-tolerant)."
echo "Note: column numbers are NOT a reliable proxy for Daniel-chapter coverage —"
echo "Theodoret's per-chapter density varies. Use these phrase checks to confirm"
echo "Dan 7 is actually present in the OCR text:"
# Use loose accent-insensitive matching: strip accents from the search term and
# from the file content, then compare. Tesseract's grc model often misreads or
# drops polytonic accents, so an exact-accent grep returns false 0s.
for pair in \
  "Παλαι.{0,3}ς τ.ν ημερων|Ancient of Days (Dan 7:9, 13, 22)" \
  "θρονοι ετεθησαν|thrones were set (Dan 7:9)" \
  "υι.ς ανθρωπου|son of man (Dan 7:13)" \
  "εως καιρου και καιρων|time and times (Dan 7:25)" \
  "κερας|horn (Dan 7:8 etc.)" \
  "θηρι[αο]|beasts (Dan 7:3-7)" \
  ; do
    pat="${pair%|*}"; desc="${pair#*|}"
    # Strip accents from the OCR file via iconv, then match
    n=$(iconv -f UTF-8 -t ASCII//TRANSLIT "$OUT" 2>/dev/null | tr 'A-Z' 'a-z' | grep -cE "$pat")
    printf "  %-50s %d hits\n" "$desc" "$n"
  done
