#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$ROOT/static/css" "$ROOT/static/js" "$ROOT/static/fonts"

echo "⬇️  دانلود Bootstrap RTL CSS..."
curl -fL -o "$ROOT/static/css/bootstrap.rtl.min.css" \
  "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.rtl.min.css"

echo "⬇️  دانلود Bootstrap Bundle JS..."
curl -fL -o "$ROOT/static/js/bootstrap.bundle.min.js" \
  "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"

echo "⬇️  دانلود فونت وزیرمتن..."
for w in Regular Medium Bold; do
  curl -fL -o "$ROOT/static/fonts/Vazirmatn-$w.woff2" \
    "https://cdn.jsdelivr.net/npm/vazirmatn@33.0.3/fonts/webfonts/Vazirmatn-$w.woff2"
done

echo ""
echo "✅ همه فایل‌ها در static/ ذخیره شدند. از این به بعد سایت بدون اینترنت هم کار می‌کند."