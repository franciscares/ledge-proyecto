#!/usr/bin/env bash
set -euo pipefail

URL="https://raw.githubusercontent.com/jpwhite3/northwind-SQLite3/4f56e7f5906dfd23b25244c5bfe8fb5da6402efd/dist/northwind.db"
TARGET="data/raw/northwind.db"

mkdir -p data/raw

if [ -f "$TARGET" ]; then
  echo "Northwind DB already exists at $TARGET"
else
  echo "Downloading Northwind DB..."
  curl -L "$URL" -o "$TARGET"
fi

./scripts/verify_northwind.sh "$TARGET"