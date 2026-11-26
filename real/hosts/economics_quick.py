"""REAL3 v2 row quick test (economics, a PRICED row: pass per cell = result > standard). Development cells only (1..4 by
default; cells >= 100 are refused). Modes: seed3 (REAL3 v2: seed3.run(..., "seed3"), the seed operators bound through
the v2 hooks), seed3v1 (REAL3 v1 exactly), seed (REAL2 seed with the Law 4 landing step), rollout (plain rollout),
default (the standard method) and strongest (the default of a host built with standard="strongest"). Per cell and mode:
result, resource, R, result vs default and vs strongest, seconds; for seed3 / seed3v1 the families chosen; for seed3 the
operators chosen, rooms, rollouts, vetoes and (once) ops_bound. SEED3_POOL_OUT=path.json writes the TRANSPLANT pool at
the end of every seed3 run; SEED3_POOL_IN=path.json loads one at import.
Usage: python economics_quick.py [cells, e.g. 1-4 or 1,2] [--modes default,strongest,seed,rollout,seed3v1,seed3] [--T n]
seed3 and seed3v1 share seed3's in-process family pool across runs: run them in separate processes to compare them clean
(--T shortens the episode for a local smoke run only; the row's episode is T = 26 weeks; the header prints T)."""
import os, sys, json, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from seed import run
import seed3
from economics import Economics

ALL = ("default", "strongest", "seed", "rollout", "seed3v1", "seed3")   # run order (baselines first)
def parse(argv):
    cells, modes, T = [1, 2, 3, 4], list(ALL), None; i = 0
    while i < len(argv):
        x = argv[i]
        if x == "--modes": modes = argv[i + 1].split(","); i += 2; continue
        if x == "--T": T = int(argv[i + 1]); i += 2; continue
        cells = list(range(int(x.split("-")[0]), int(x.split("-")[1]) + 1)) if "-" in x else [int(c) for c in x.split(",")]
        i += 1
    if any(c >= 100 for c in cells): raise SystemExit("cells >= 100 are not development cells: refused")
    return cells, modes, T

def fams(choices):
    fam = {}
    for key, n in choices.items():
        f = key.split("|")[0]; fam[f] = fam.get(f, 0) + n
    return dict(sorted(fam.items(), key=lambda x: -x[1]))

if __name__ == "__main__":
    cells, modes, T = parse(sys.argv[1:])
    kw = {} if T is None else {"T": T}
    host = Economics(**kw); strong = Economics(standard="strongest", **kw)
    print(f"economics quick: T = {host.T} weeks, cells {cells}, modes {modes}, pool in {os.environ.get('SEED3_POOL_IN')} "
          f"out {os.environ.get('SEED3_POOL_OUT')}", flush=True)
    shown = False
    for cell in cells:
        o = {}
        for m in modes:
            t0 = time.time()
            if m in ("seed3", "seed3v1"): o[m] = seed3.run(host, cell, m)
            elif m == "strongest": o[m] = run(strong, cell, "default")
            else: o[m] = run(host, cell, m)
            o[m]["_sec"] = round(time.time() - t0, 1)
            r = o[m]; rd = o.get("default", {}).get("result"); rs = o.get("strongest", {}).get("result")
            vs = (f" vs default {r['result'] - rd:+.3f}" if rd is not None else "") + \
                 (f" vs strongest {r['result'] - rs:+.3f}" if rs is not None else "")
            extra = ""
            if m in ("seed3", "seed3v1"): extra += f" chosen {fams(r['choices'])} disabled {r['disabled']}"
            if m == "seed3":
                extra += (f" ops_used {{{', '.join(f'{k}: {v}' for k, v in r['ops_used'].items() if v)}}} rooms {r['rooms']}"
                          f" vetoed {r['vote_vetoed']} rollouts v1/ops {r['rollouts_v1']}/{r['rollouts_ops']}"
                          f" passed {{{', '.join(f'{k}: {v}' for k, v in r['ops_passed_membrane'].items() if v)}}}"
                          f" colour {r['colour_counts']} zoom {r['zoom_scale_decisions']} enter {r['enter_depth']}"
                          f" fallback {r['op_fallback']} inherit {r['inherit_entries']} shapes {r['shape_keys']}"
                          f" pool_saved {r['pool_saved']}")
            print(f"cell {cell} {m:9s} result {r['result']:.3f} resource {r['resource']:.3f} R {r['R']:.5f}{vs}"
                  f" seconds {r['_sec']}{extra}", flush=True)
            if m == "seed3" and not shown:
                print("  ops_bound " + json.dumps(r["ops_bound"]), flush=True); shown = True
