#!/usr/bin/env bash
# Reproduce every result: the tests, then each experiment. Results land in results/*.json with a results_sha256
# (a hash of the numbers only), so a rerun can be compared with the published one.
# Governance, sessions and T11 need the RSOS Multimodal Cue Framework: set RSOS_CUE_FRAMEWORK to its folder.
set -euo pipefail
cd "$(dirname "$0")"
python3 -m pytest -q
cd experiments
for e in r003 r004 round2 paint1 t5_dots t7_protocol t8_two_runtimes t9_discovery t11_earth x1_external c1_communication e1_dragon v1_vakog h1_predictive_heal h2_inward h3_evolve_links h3c_filter f1_feedback f1b_feedback; do
  echo "== $e"; python3 "$e.py" | head -1
done
