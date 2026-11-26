"""The registry is the single source of truth: it validates, agrees with the code, every test it names exists,
the publication rule holds, and the generated operator reference is up to date."""
import json
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).parents[2]


def tool(*args):
    return subprocess.run([sys.executable, str(ROOT / "tools/registry.py"), *args], capture_output=True, text=True)


def test_registry_check_passes():
    r = tool("check")
    assert r.returncode == 0, r.stdout + r.stderr


def test_operator_reference_is_generated_and_current():
    r = tool("docs", "--check")
    assert r.returncode == 0, r.stdout


def test_publication_rule():
    reg = json.loads((ROOT / "registry/operators.json").read_text())
    core = {e["tech_name"] for e in reg["entries"] if e["status"] in ("tested", "executed") and e["evidence"]}
    assert "copy" not in core  # tested, never executed in an experiment: research layer until it is
    assert {"set", "delete", "derive", "sum_into", "multiply", "select_if", "reassign_where"} <= core


def test_registry_matches_schema():
    jsonschema = pytest.importorskip("jsonschema")
    reg = json.loads((ROOT / "registry/operators.json").read_text())
    jsonschema.validate(reg, json.loads((ROOT / "registry/operators.schema.json").read_text()))


def test_candidate_import_rejects_corpus_text(tmp_path):
    good = {"candidate_id": "X-1", "symbolic_name": "restore", "source": {"chat": "c1", "turn": "T14", "role": "owner"},
            "first_seen": "2025-05-01", "verbatim_sha256": "a" * 64, "alias_of": "C-102", "scan_run_id": "r1",
            "scanner_version": "0.1", "proposed_status": "proposed"}
    bad = dict(good, candidate_id="X-2", verbatim="the actual words")
    f = tmp_path / "f.jsonl"
    f.write_text(json.dumps(good) + "\n" + json.dumps(bad) + "\n")
    r = subprocess.run([sys.executable, str(ROOT / "tools/import_candidates.py"), str(f)], capture_output=True, text=True)
    assert r.returncode == 1 and "corpus text is not accepted" in r.stdout and "aliases of Core 1" in r.stdout
