#!/usr/bin/env bash
# Build the Hugging Face dataset and Space folders from the STAGED public tree (run tools/stage_public.sh first).
# Builds only; uploading is the owner's step (commands printed at the end).
set -euo pipefail
PUB="${1:-/tmp/rsos-public}"; OUT="${2:-/tmp/rsos-hf}"
[ -f "$PUB/README.md" ] || { echo "stage the public tree first: tools/stage_public.sh $PUB"; exit 1; }
rm -rf "$OUT"; mkdir -p "$OUT/dataset/experiments" "$OUT/space"
cp -r "$PUB/results" "$OUT/dataset/"
cp "$PUB"/experiments/PREREGISTRATION_*.md "$PUB"/experiments/*_REPORT.md "$OUT/dataset/experiments/" 2>/dev/null || true
cp "$PUB/tools/hf/dataset_README.md" "$OUT/dataset/README.md"
cp "$PUB/LICENSE" "$OUT/dataset/"
sed 's#href="index.html"#href="https://r-a-elu-architecture.github.io/RSOS-Language/"#' "$PUB/docs/editor.html" > "$OUT/space/index.html"
cp "$PUB/tools/hf/space_README.md" "$OUT/space/README.md"
if grep -rqiE "suicid|psychos|schizo|depress|PTSD|hospital" "$OUT"; then echo "STOP: sensitive term found"; exit 1; fi
echo "built: $OUT/dataset ($(find "$OUT/dataset" -type f | wc -l) files, $(du -sh "$OUT/dataset" | cut -f1)), $OUT/space"
cat <<MSG
Upload (owner, after: pip install huggingface_hub && hf auth login):
  hf upload <org>/rsos-experiments $OUT/dataset . --repo-type dataset
  hf upload <org>/rsos-editor $OUT/space . --repo-type space
MSG
