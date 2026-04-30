#!/bin/bash
# Tests for tools/extract_ocr.sh.
#
# Each test exercises a specific dispatch / validation / error-handling
# path. Smoke tests that touch the network or the PG 81 PDF live in
# Phase-3 verification rather than this suite — this suite is offline.
#
# Run:   bash tools/tests/test_extract_ocr.sh
# Exits non-zero if any test fails; prints a summary.

set -u

HERE=$(cd "$(dirname "$0")" && pwd)
SCRIPT="${HERE}/../extract_ocr.sh"

PASS=0
FAIL=0
FAILED_NAMES=()

# Run a test. Args: name, expected-exit-code, command...
run_test() {
  local name=$1
  local expected_exit=$2
  shift 2
  local out
  local actual_exit
  out=$("$@" 2>&1) && actual_exit=$? || actual_exit=$?
  if [ "$actual_exit" = "$expected_exit" ]; then
    PASS=$((PASS+1))
    printf "  OK  %s\n" "$name"
  else
    FAIL=$((FAIL+1))
    FAILED_NAMES+=("$name")
    printf "  FAIL %s (expected exit %s, got %s)\n" "$name" "$expected_exit" "$actual_exit"
    printf "       output: %s\n" "$(printf '%s' "$out" | head -3)"
  fi
}

# Run a test and grep its output for an expected substring.
run_test_with_grep() {
  local name=$1
  local expected_exit=$2
  local needle=$3
  shift 3
  local out
  local actual_exit
  out=$("$@" 2>&1) && actual_exit=$? || actual_exit=$?
  if [ "$actual_exit" = "$expected_exit" ] && printf '%s' "$out" | grep -qF -- "$needle"; then
    PASS=$((PASS+1))
    printf "  OK  %s\n" "$name"
  else
    FAIL=$((FAIL+1))
    FAILED_NAMES+=("$name")
    printf "  FAIL %s (expected exit %s containing %q; got exit %s)\n" \
           "$name" "$expected_exit" "$needle" "$actual_exit"
    printf "       output: %s\n" "$(printf '%s' "$out" | head -3)"
  fi
}

echo "Testing tools/extract_ocr.sh"
echo

echo "[1] Help & dispatcher"
run_test_with_grep "no args prints usage" 2 "Usage:" "$SCRIPT"
run_test_with_grep "--help prints usage"  0 "Subcommands:" "$SCRIPT" --help
run_test_with_grep "-h prints usage"      0 "Subcommands:" "$SCRIPT" -h
run_test_with_grep "help prints usage"    0 "Subcommands:" "$SCRIPT" help
run_test_with_grep "unknown subcommand"   2 "unknown subcommand" "$SCRIPT" frobnicate

echo
echo "[2] Argument count / shape"
run_test_with_grep "pdf needs 3 positional"          2 "need <url>" \
                   "$SCRIPT" pdf https://example.com/x.pdf eng
run_test_with_grep "pdf-columns needs 5 positional"  2 "need <url>" \
                   "$SCRIPT" pdf-columns https://example.com/x.pdf 1 2 grc
run_test_with_grep "archive-text needs 2 positional" 2 "need <archive-id>" \
                   "$SCRIPT" archive-text only-one-arg
run_test_with_grep "html needs 2 positional"         2 "need <url>" \
                   "$SCRIPT" html only-one-arg

echo
echo "[3] URL hygiene"
# https-only
run_test_with_grep "rejects http://" 2 "must start with https" \
                   "$SCRIPT" pdf "http://example.com/x.pdf" eng /tmp/x.txt
run_test_with_grep "rejects file://" 2 "must start with https" \
                   "$SCRIPT" pdf "file:///etc/passwd" eng /tmp/x.txt
run_test_with_grep "rejects javascript:" 2 "must start with https" \
                   "$SCRIPT" pdf "javascript:alert(1)" eng /tmp/x.txt
# shell metacharacter rejection
run_test_with_grep "rejects URL with backtick" 2 "shell metacharacters" \
                   "$SCRIPT" pdf 'https://example.com/`whoami`.pdf' eng /tmp/x.txt
run_test_with_grep "rejects URL with semicolon" 2 "shell metacharacters" \
                   "$SCRIPT" pdf 'https://example.com/x.pdf;rm' eng /tmp/x.txt
run_test_with_grep "rejects URL with dollar" 2 "shell metacharacters" \
                   "$SCRIPT" pdf 'https://example.com/$(id).pdf' eng /tmp/x.txt
run_test_with_grep "rejects URL with pipe" 2 "shell metacharacters" \
                   "$SCRIPT" pdf 'https://example.com/x.pdf|cat' eng /tmp/x.txt
# html mode also validates
run_test_with_grep "html rejects http://" 2 "must start with https" \
                   "$SCRIPT" html "http://example.com/" /tmp/x.txt

echo
echo "[4] Output-path hygiene"
run_test_with_grep "pdf rejects ../ output" 2 "contains '..'" \
                   "$SCRIPT" pdf https://example.com/x.pdf eng /tmp/../etc/x.txt
run_test_with_grep "html rejects ../ output" 2 "contains '..'" \
                   "$SCRIPT" html https://example.com/ /tmp/../etc/x.txt
run_test_with_grep "archive-text rejects ../ output" 2 "contains '..'" \
                   "$SCRIPT" archive-text some-id /tmp/../etc/x.txt

echo
echo "[5] archive-id hygiene"
run_test_with_grep "rejects archive-id with slash" 2 "unsafe characters" \
                   "$SCRIPT" archive-text 'foo/bar' /tmp/x.txt
run_test_with_grep "rejects archive-id with backtick" 2 "unsafe characters" \
                   "$SCRIPT" archive-text 'foo`bar' /tmp/x.txt
run_test_with_grep "rejects archive-id with space" 2 "unsafe characters" \
                   "$SCRIPT" archive-text 'foo bar' /tmp/x.txt

echo
echo "[6] pdf-columns input validation"
run_test_with_grep "rejects non-numeric first-col" 2 "first-col must be integer" \
                   "$SCRIPT" pdf-columns https://example.com/x.pdf abc 100 grc /tmp/x.txt
run_test_with_grep "rejects last < first"          2 "last-col < first-col" \
                   "$SCRIPT" pdf-columns https://example.com/x.pdf 200 100 grc /tmp/x.txt
run_test_with_grep "rejects malicious col-formula" 2 "pure integer arithmetic" \
                   "$SCRIPT" pdf-columns https://example.com/x.pdf 1 2 grc /tmp/x.txt --col-formula "import os"

echo
echo "[7] Language pack validation"
run_test_with_grep "missing tesseract lang reported" 2 "language pack" \
                   "$SCRIPT" pdf https://example.com/x.pdf zzz_nonexistent /tmp/x.txt
run_test_with_grep "missing tesseract lang in pdf-columns" 2 "language pack" \
                   "$SCRIPT" pdf-columns https://example.com/x.pdf 1 2 zzz_bogus /tmp/x.txt

echo
echo "[8] Unknown flags are rejected"
run_test_with_grep "pdf rejects --bogus" 2 "unknown flag" \
                   "$SCRIPT" pdf https://example.com/x.pdf eng /tmp/x.txt --bogus
run_test_with_grep "pdf-columns rejects --bogus" 2 "unknown flag" \
                   "$SCRIPT" pdf-columns https://example.com/x.pdf 1 2 grc /tmp/x.txt --bogus

echo
echo "[9] --pages flag shape"
# Bad --pages format requires getting past lang validation; use eng + a reachable bogus URL.
# We can't reach the URL; we just need the parser to emit the right error
# before the fetch. The order is: validate_url -> validate_output_path ->
# require_tesseract_langs -> require_command pdftoppm -> parse --pages.
# So we need --pages misformat to be caught before any network call.
run_test_with_grep "rejects --pages without dash" 2 "must be N-M" \
                   "$SCRIPT" pdf https://example.com/x.pdf eng /tmp/x.txt --pages 100

echo
echo "============================================================"
echo "Tests passed: $PASS"
echo "Tests failed: $FAIL"
if [ "$FAIL" -gt 0 ]; then
  echo "Failed:"
  for n in "${FAILED_NAMES[@]}"; do
    echo "  - $n"
  done
  exit 1
fi
echo "All tests passed."
