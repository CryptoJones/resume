#!/usr/bin/env bash
# Build the Cyberdeck code-showcase PDF: crisp, image-based (no selectable text),
# watermarked, < 25 MB.
#   gather -> render HTML -> Chrome print-to-pdf -> rasterize -> reassemble
#   -> compress if needed -> copy to repo root as Clark-Aaron-K-Portfolio.pdf
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PY="${SHOWCASE_PY:-python3}"
DPI="${DPI:-200}"
BUDGET=$((25 * 1024 * 1024))
FINAL_NAME="Clark-Aaron-K-Portfolio.pdf"

WORK="$(mktemp -d)"
UDD="$WORK/chrome-profile"
trap 'rm -rf "$WORK"' EXIT

cd "$HERE"
rm -rf pages; mkdir -p pages

echo "[1/6] gather samples"
"$PY" gather.py

echo "[2/6] render HTML"
"$PY" render.py

# Chrome print-to-pdf with a hard watchdog so a render can never hang the build.
chrome_pdf () {  # $1=input.html  $2=output.pdf
  rm -f "$2"
  "$CHROME" --headless=old --disable-gpu --no-pdf-header-footer \
    --no-sandbox --disable-extensions --hide-scrollbars \
    --user-data-dir="$UDD" --no-first-run --no-default-browser-check \
    --print-to-pdf="$2" "file://$1" >/dev/null 2>&1 &
  local pid=$! waited=0
  while kill -0 "$pid" 2>/dev/null; do
    sleep 1; waited=$((waited+1))
    if [ "$waited" -ge 75 ]; then
      echo "      watchdog: killing stalled Chrome after ${waited}s" >&2
      kill -9 "$pid" 2>/dev/null || true
      break
    fi
  done
  wait "$pid" 2>/dev/null || true
  [ -s "$2" ] || { echo "ERROR: Chrome produced no PDF for $1" >&2; return 1; }
}

echo "[3/6] HTML -> PDF (Chrome)"
chrome_pdf "$HERE/showcase.html" "$WORK/showcase_text.pdf"

echo "[4/6] rasterize @ ${DPI}dpi (kills selectable text)"
pdftoppm -r "$DPI" -png "$WORK/showcase_text.pdf" "pages/p"
NPAGES=$(ls pages/p-*.png | wc -l | tr -d ' ')
echo "      $NPAGES page images"

echo "[5/6] reassemble image PDF"
{
  echo '<!DOCTYPE html><html><head><meta charset="utf-8"><style>'
  echo '@page{size:letter;margin:0} html,body{margin:0;padding:0;background:#07090f}'
  echo 'img{display:block;width:8.5in;height:11in;page-break-after:always}'
  echo '</style></head><body>'
  for f in $(ls pages/p-*.png | sort -t- -k2 -n); do
    echo "<img src=\"file://$HERE/$f\">"
  done
  echo '</body></html>'
} > "$WORK/pages.html"
chrome_pdf "$WORK/pages.html" "$WORK/showcase_img.pdf"

echo "[6/6] fit budget (< 25 MB), preserving crispness"
SRC="$WORK/showcase_img.pdf"
SIZE=$(stat -f%z "$SRC")
echo "      raw image PDF: $((SIZE/1024/1024)) MB"
# Flat dark pages compress well; only step down image quality if we must.
if [ "$SIZE" -gt "$BUDGET" ]; then
  for SETTING in /printer /ebook /screen; do
    gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.5 -dPDFSETTINGS="$SETTING" \
       -dNOPAUSE -dQUIET -dBATCH \
       -sOutputFile="$WORK/compressed.pdf" "$SRC" 2>/dev/null
    CS=$(stat -f%z "$WORK/compressed.pdf")
    echo "      gs $SETTING -> $((CS/1024/1024)) MB"
    SRC="$WORK/compressed.pdf"; SIZE="$CS"
    [ "$SIZE" -le "$BUDGET" ] && break
  done
fi

cp "$SRC" "$ROOT/$FINAL_NAME"
FINAL=$(stat -f%z "$ROOT/$FINAL_NAME")
echo
echo "DONE: $ROOT/$FINAL_NAME"
echo "size: $((FINAL/1024/1024)) MB ($FINAL bytes)  pages: $NPAGES"
[ "$FINAL" -le "$BUDGET" ] && echo "budget: OK (< 25 MB)" || { echo "budget: OVER 25 MB"; exit 1; }
