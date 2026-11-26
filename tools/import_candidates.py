"""Validate corpus findings (JSONL, registry/candidates.schema.json) and report them; with --write, add new candidates
to registry/candidates.json for review in a pull request. Corpus text is never accepted: only hashes and references.

  python3 tools/import_candidates.py findings.jsonl            validate and summarise
  python3 tools/import_candidates.py findings.jsonl --write    append valid new rows to registry/candidates.json
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "registry", "candidates.json")
REQ = ["candidate_id", "symbolic_name", "source", "first_seen", "verbatim_sha256", "scan_run_id", "scanner_version",
       "proposed_status"]
ALLOWED = set(REQ) | {"mirror_of", "alias_of", "note"}


def validate(row):
    errs = [f"missing {k}" for k in REQ if k not in row]
    errs += [f"unexpected field {k} (corpus text is not accepted)" for k in set(row) - ALLOWED]
    if row.get("proposed_status") != "proposed":
        errs.append("proposed_status must be 'proposed'")
    if not re.fullmatch(r"[0-9a-f]{64}", str(row.get("verbatim_sha256", ""))):
        errs.append("verbatim_sha256 must be 64 hex digits")
    if not re.fullmatch(r"X-\d+", str(row.get("candidate_id", ""))):
        errs.append("candidate_id must look like X-123")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(row.get("first_seen", ""))):
        errs.append("first_seen must be YYYY-MM-DD")
    s = row.get("source")
    if not (isinstance(s, dict) and set(s) == {"chat", "turn", "role"} and s.get("role") in ("owner", "assistant")):
        errs.append("source must be {chat, turn, role: owner|assistant}")
    if len(str(row.get("note", ""))) > 280 or len(str(row.get("symbolic_name", ""))) > 120:
        errs.append("note or symbolic_name too long (no corpus text)")
    return errs


def main(argv):
    if not argv:
        print(__doc__); return 2
    rows, bad = [], 0
    for i, line in enumerate(open(argv[0], encoding="utf-8"), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        e = validate(row)
        if e:
            bad += 1; print(f"line {i}: " + "; ".join(e))
        else:
            rows.append(row)
    alias_core = sum(1 for r in rows if str(r.get("alias_of") or "").startswith("C-"))
    alias_reg = sum(1 for r in rows if str(r.get("alias_of") or "").startswith("U"))
    new = len(rows) - alias_core - alias_reg
    print(f"{len(rows)} valid, {bad} rejected; aliases of Core {alias_core}, of the register {alias_reg}, new {new}")
    if "--write" in argv and rows:
        have = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else []
        known = {r["candidate_id"] for r in have}
        have += [r for r in rows if r["candidate_id"] not in known]
        json.dump(have, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        print(f"registry/candidates.json: {len(have)} candidates")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
