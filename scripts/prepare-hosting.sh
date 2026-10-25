#!/usr/bin/env bash
# Only the public app belongs in the Hosting upload, never the repository root.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p dist
# Fail rather than publish unexpected files left by an earlier build.
if find dist -mindepth 1 ! -name index.html -print -quit | read -r unexpected; then
  echo 'dist contains unexpected files. Use a fresh checkout before publishing.' >&2
  exit 1
fi
cp index.html dist/index.html
