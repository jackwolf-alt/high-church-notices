#!/usr/bin/env bash
# Stage a separate marketing site. Never copy the app, credentials or drafts here.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ -e dist-public ]]; then
  echo 'dist-public already exists. Use a fresh checkout before publishing.' >&2
  exit 1
fi
mkdir -p dist-public/assets
cp public/index.html public/privacy.html public/styles.css public/site.js \
  public/robots.txt public/sitemap.xml dist-public/
cp public/assets/churchpress-logo.png public/assets/manrope.woff \
  public/assets/dashboard-example.webp public/assets/FONT-LICENCES.txt dist-public/assets/
