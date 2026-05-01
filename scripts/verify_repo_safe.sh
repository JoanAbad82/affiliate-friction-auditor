#!/usr/bin/env bash
set -euo pipefail

echo "====================================================================="
echo "VERIFY REPO SAFE"
echo "====================================================================="

echo ""
echo "1) Git status"
git status --short --branch

echo ""
echo "2) Checking forbidden tracked files"
FORBIDDEN_TRACKED="$(git ls-files | grep -E '(^outputs/[^.]|\.zip$|\.log$|destination_screenshots|screenshots|__pycache__|\.pyc$|^\.env)' || true)"
if [ -n "$FORBIDDEN_TRACKED" ]; then
  echo "ERROR: forbidden tracked files detected:"
  echo "$FORBIDDEN_TRACKED"
  exit 1
fi
echo "OK: no forbidden tracked files."

echo ""
echo "3) Checking examples are sanitized"
if grep -R "nolodejesescapar.com\|Nolodejesescapar" examples >/tmp/affiliate_friction_auditor_example_leaks.txt 2>/dev/null; then
  echo "ERROR: real site reference found in examples:"
  cat /tmp/affiliate_friction_auditor_example_leaks.txt
  exit 1
fi
echo "OK: examples sanitized."

echo ""
echo "4) Python syntax"
python3 -m py_compile scripts/phase0_7_destination_posts.py scripts/phase0_8_opportunity_matrix.py scripts/phase0_9_product_offer.py
find . -type d -name "__pycache__" -prune -exec rm -rf {} +
echo "OK: Python syntax valid."

echo ""
echo "VERIFY COMPLETE"
