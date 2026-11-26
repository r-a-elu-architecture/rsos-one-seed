#!/usr/bin/env bash
# Stage the "One Seed, Many Domains" release into $1 (default /tmp/rsos-public-seed). Stages only; never pushes or
# publishes. Builds on tools/stage_public.sh (RELEASE_WHITELIST.txt, D85 exclusions, sensitive-term guard) and adds the
# paper and the sealed REAL/SEAL runs. corpus/ is never staged.
set -euo pipefail
cd "$(dirname "$0")/.."
REPO="$PWD"; OUT="${1:-/tmp/rsos-public-seed}"
bash tools/stage_public.sh "$OUT"
cd "$REPO"
# the release README leads; the language README stays as README_LANGUAGE.md
mv "$OUT/README.md" "$OUT/README_LANGUAGE.md"; cp README_RELEASE.md "$OUT/README.md"
# the paper and the sealed runs
for p in paper/WHITEPAPER_DRAFT.md paper/PAPER_1_ONE_SELECTOR.md paper/PAPER_2_SRCX5.md paper/PAPER_3_BLIND_PLANNING.md \
         paper/pdf/PAPER_1_ONE_SELECTOR.pdf paper/pdf/PAPER_2_SRCX5.pdf paper/pdf/PAPER_3_BLIND_PLANNING.pdf real seal1 seal2 cloud/real1_unit.py cloud/real3_unit.py cloud/real3_unit_fix1.py \
         cloud/real3_fix1_units.json \
         .github/workflows/rsos_real1.yml .github/workflows/rsos_real1b.yml .github/workflows/rsos_real3_s1.yml \
         .github/workflows/rsos_real3_s2.yml .github/workflows/rsos_real3_fix1.yml .github/workflows/rsos_seal2.yml \
         paper/PRIOR_ART_26NOV.md cloud/struct1_unit.py cloud/conf1_unit.py cloud/conf2_unit.py cloud/conf3_unit.py \
         cloud/conf4_unit.py cloud/abl1_unit.py cloud/conf5_unit.py cloud/conf6_unit.py \
         reproduce_conf4.sh reproduce_abl1.sh reproduce_conf5.sh reproduce_conf6.sh \
         .github/workflows/rsos_struct1.yml .github/workflows/rsos_conf1_space.yml .github/workflows/rsos_conf1_ai.yml \
         .github/workflows/rsos_conf1_fix1.yml .github/workflows/rsos_conf2.yml .github/workflows/rsos_conf3.yml \
         .github/workflows/rsos_conf4.yml .github/workflows/rsos_abl1.yml .github/workflows/rsos_pilot1.yml \
         .github/workflows/rsos_pilot2.yml .github/workflows/rsos_conf5.yml .github/workflows/rsos_conf6.yml \
         .github/workflows/rsos_tle_freeze.yml protocol; do
  [ -e "$p" ] && cp -r --parents "$p" "$OUT/"
done
cp CITATION_RELEASE.cff "$OUT/CITATION.cff"   # the release cites paper 1; the language CITATION stays in RSOS-Language
python3 tools/build_public_site.py "$OUT/site"; cp site/seed/mark.svg "$OUT/site/mark.svg"
mkdir -p "$OUT/.github/workflows"; cp .github/workflows/site_pages.yml "$OUT/.github/workflows/"
cd "$OUT"
rm -rf corpus real/out3/_tmp experiments/genealogy 2>/dev/null || true
rm -f protocol/SEAL_SRCX5.txt   # private v1.3 seal of the 11-entry log; the public seal is protocol/SEAL_SRCX5_PUBLIC.txt
rm -f protocol/.github/workflows/anchor.yml   # sealed v1.4 workflow kept private; anchor_v141.yml replaces it (tests/v14/RELEASE_NOTE.md)
# third-party data stays out until its licence is confirmed (DATA_LICENCES.md); the fetch scripts recreate it
rm -f real/hosts/data/walmart_sales_weekly.csv real/hosts/data/household_load_uci_hourly.csv
find real/hosts/data/topical_chat -type f ! -name .gitignore -delete 2>/dev/null || true   # fetched at run time, never staged
rm -rf real/outs1 2>/dev/null || true
find . -name __pycache__ -prune -exec rm -rf {} +
# guards: no corpus, no secrets, no owner-chat references, no sensitive terms
[ ! -e corpus ] || { echo "STOP: corpus staged"; exit 1; }
if grep -rqE --exclude=stage_public*.sh "sk-or-v1-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|BEGIN (RSA|OPENSSH) PRIVATE KEY" .; then
  echo "STOP: secret-like string found"; exit 1; fi
if grep -rqiE --exclude=stage_public*.sh --exclude=build_hf.sh "suicid|psychos|schizo|depress|PTSD|hospital" .; then
  echo "STOP: sensitive term found"; grep -rliE --exclude=stage_public*.sh --exclude=build_hf.sh "suicid|psychos|schizo|depress|PTSD|hospital" . | head; exit 1; fi
grep -rlE --exclude=stage_public*.sh --exclude=PRIVATE_REFERENCES.md "owner_turns|corpus/|turns_2[0-9]nov" . | sort > /tmp/refs.txt || true
echo "files citing the private record (each listed in PRIVATE_REFERENCES.md): $(wc -l < /tmp/refs.txt)"
echo "staged: $OUT ($(find . -type f | wc -l) files, $(du -sh . | cut -f1))"
