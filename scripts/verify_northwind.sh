#!/usr/bin/env bash
set -euo pipefail

DB_PATH="${1:-data/raw/northwind.db}"
EXPECTED_SHA="2f4f5c68dfcd33ba27373eae48c7a4869800c68095ee0f9f0da494f83382a877"
EXPECTED_MIN_SIZE=24000000

if [ ! -f "$DB_PATH" ]; then
  echo "ERROR: file not found: $DB_PATH"
  exit 1
fi

ACTUAL_SIZE=$(wc -c < "$DB_PATH" | tr -d ' ')
ACTUAL_SHA=$(sha256sum "$DB_PATH" | awk '{print $1}')

echo "File: $DB_PATH"
echo "Size: $ACTUAL_SIZE bytes"
echo "SHA-256: $ACTUAL_SHA"

if [ "$ACTUAL_SIZE" -lt "$EXPECTED_MIN_SIZE" ]; then
  echo "ERROR: file size is smaller than expected"
  exit 1
fi

if [ "$ACTUAL_SHA" != "$EXPECTED_SHA" ]; then
  echo "ERROR: SHA-256 mismatch"
  exit 1
fi

echo "OK: Northwind database verified"