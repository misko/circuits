#!/bin/bash
# Assemble the immutable release: fab package + pdfs + verification evidence
# + MANIFEST (sha256, exact git sha). Run ONLY at a green gate on a clean
# tree. Usage: bash 03_src/make_release.sh v1.0-2026-07-19
set -euo pipefail
cd "$(dirname "$0")/.."
VER="${1:?usage: make_release.sh vX.Y-YYYY-MM-DD}"
REL="07_releases/$VER"
[ -e "$REL" ] && { echo "$REL exists (releases are immutable)"; exit 1; }
mkdir -p "$REL/pdf" "$REL/verification"

cp 06_build/fab/cook_hub_gerbers.zip "$REL/"
cp 06_build/fab/bom_jlc.csv "$REL/bom.csv"
cp 06_build/fab/cpl_jlc.csv "$REL/cpl.csv"
cp 06_build/pdf/schematic.pdf 06_build/pdf/pcb_layers.pdf \
   06_build/pdf/assembly_top.pdf "$REL/pdf/"
cp 06_build/twin/twin_report.csv "$REL/verification/"
cp 06_build/twin/twin_top.png 06_build/twin/twin_iso_nw.png \
   "$REL/verification/" 2>/dev/null || true
cp 06_build/drc/gate.json "$REL/verification/drc_gate.json"
[ -f 06_build/pin_review.md ] && cp 06_build/pin_review.md "$REL/verification/" || true

GIT_SHA=$(git rev-parse --short HEAD)
DIRTY=$(git status --porcelain -- . | grep -v '^??' | head -1 && echo true || echo false)
{
  echo "board:        cook_hub"
  echo "version:      $VER"
  echo "git_sha:      $GIT_SHA"
  echo "kicad:        $(kicad-cli version 2>/dev/null)"
  echo "sha256:"
  (cd "$REL" && find . -type f ! -name MANIFEST.txt -print0 | sort -z | \
     xargs -0 sha256sum | sed 's/^/  /')
} > "$REL/MANIFEST.txt"
echo "release assembled at $REL (append board/gate metadata to MANIFEST.txt)"
