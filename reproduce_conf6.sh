#!/usr/bin/env bash
# Reproduce CONF6 (real/PREREG_CONF6.md). Anyone can run this.
#   bash reproduce_conf6.sh                       verify every fingerprint, recompute the result table from the committed outputs
#   bash reproduce_conf6.sh <models> <first> <last>   re-run cells 1401-1600 (needs OPENROUTER_API_KEY)
#   bash reproduce_conf6.sh mock                  interface check of every arm without any model (mock path; not a result)
set -euo pipefail
cd "$(dirname "$0")"
echo "1. fingerprints:"; grep -v '^#' real/SEAL_CONF6.txt | sed 's/ /  /' | sha256sum -c --quiet && echo "   all $(grep -vc '^#' real/SEAL_CONF6.txt) files match the seal"
echo "2. result table from the committed outputs:"; python3 real/analyze_conf6.py | sed -n 3,3p
if [ "${1:-}" = mock ]; then tmp=$(mktemp -d); cp -r real/outc6 "$tmp/" 2>/dev/null || true; CONF6_SMOKE=1 python3 cloud/conf6_unit.py "mock:0,mock:0" 1401 1401; rm -f real/outc6/ai_ai_1401_1401.json; cp "$tmp"/outc6/* real/outc6/ 2>/dev/null || true
elif [ $# -ge 3 ]; then python3 cloud/conf6_unit.py "$@"; fi
