#!/usr/bin/env bash
# Reproduce ABL1 (real/PREREG_ABL1.md). Anyone can run this.
#   bash reproduce_abl1.sh            verify every fingerprint, recompute the result table from the committed outputs (seconds)
#   bash reproduce_abl1.sh space      also re-run the whole satellite row offline on this machine (minutes; no API key)
#   bash reproduce_abl1.sh <row> <model> <first> <last>   re-run any cells (AI rows need OPENROUTER_API_KEY)
set -euo pipefail
cd "$(dirname "$0")"
echo "1. fingerprints:"; grep -v '^#' real/SEAL_ABL1.txt | sed 's/ /  /' | sha256sum -c --quiet && echo "   all $(grep -vc '^#' real/SEAL_ABL1.txt) files match the seal"
echo "2. result table from the committed outputs:"; python3 real/analyze_abl1.py | sed -n 3,3p
cp real/hosts/data/space_tle_frozen.txt real/hosts/data/space_tle.txt
if [ "${1:-}" = space ]; then
  tmp=$(mktemp -d); cp -r real/outa1 "$tmp/committed"; rm -f real/outa1/space_*
  for c in 901 913 925 937; do python3 cloud/abl1_unit.py space - $c $((c+11)); done
  python3 - "$tmp/committed" <<'PY'
import json, glob, sys, os
for f in sorted(glob.glob("real/outa1/space_*.json")):
    a = json.load(open(f))["cells"]; b = json.load(open(os.path.join(sys.argv[1], os.path.basename(f))))["cells"]
    same = all(abs(a[k][arm]["result"] - b[k][arm]["result"]) < 1e-9 for k in a for arm in a[k] if isinstance(a[k][arm], dict) and "result" in a[k][arm])
    print("  ", os.path.basename(f), "identical to the committed run" if same else "DIFFERS")
PY
elif [ $# -ge 4 ]; then python3 cloud/abl1_unit.py "$@"; fi
