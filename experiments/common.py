"""Shared harness: compile RSOS source, run it, record results with hashes."""

import hashlib
import json
import os
import subprocess
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from rsoslang import compile_source            # noqa: E402
from rsoslang.runtime import run               # noqa: E402

HEAD = "LANGUAGE RSOS 0.2\nWORLD w\n"
_cache = {}


def world_of(body, layouts, seed=0, choice=None):
    key = body
    if key not in _cache:
        res = compile_source(HEAD + body)
        if not res.ok:
            raise RuntimeError("\n".join(str(d) for d in res.errors) + "\n" + body)
        _cache[key] = res.ir
    return run(_cache[key], layouts, seed, choice).w


def bootstrap_ci(x, n=10000, seed=12345):
    x = np.asarray(x, float)
    rng = np.random.default_rng(seed)
    means = rng.choice(x, size=(n, len(x)), replace=True).mean(axis=1)
    return [float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))]


def git_head():
    try:
        return subprocess.check_output(["git", "-C", ROOT, "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def _plain(o):
    return o.item() if hasattr(o, "item") else (o.tolist() if hasattr(o, "tolist") else str(o))


def save(name, payload):
    payload = {"experiment": name, "code_commit": git_head(),
               "python": sys.version.split()[0], "numpy": np.__version__,
               "run_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **payload}
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    body = {k: v for k, v in payload.items() if k not in ("run_utc", "code_commit")}
    digest = hashlib.sha256(json.dumps(body, sort_keys=True, default=_plain).encode()).hexdigest()
    payload["results_sha256"] = digest       # hash of the numbers only, so reruns can be compared
    path = os.path.join(ROOT, "results", f"{name}.json")
    with open(path, "w") as f:
        json.dump(payload, f, indent=1, sort_keys=True, default=_plain)
    return path, digest
