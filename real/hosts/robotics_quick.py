"""REAL3 v2 (25 Nov): modes seed3 (seed3.run "seed3" = v2: v1 choice + seed operators bound by the host hooks), seed3v1
(REAL3 v1 exactly), seed (REAL2 seed with landing), rollout, default (energy swing-up + LQR, also the strongest method of this row, see robotics.py); development cells 1-4 only (never cells
>= 100). One process per (cell, mode) (maxtasksperchild=1): the seed's shared pools (seed3.POOL, the operator pool) then
hold only that run's trace, so seed3 and seed3v1 never see each other and a line does not depend on which runs a worker
did before. SEED3_POOL_IN is loaded at import (every worker); with SEED3_POOL_OUT set, each seed3 (v2) run saves its pool
to <out>.cell<c> and the parent merges them (cell order) into <out> at the end.
Row kind: free-resource (Pareto: result >= default AND resource <= default, one strictly).
Usage: python3 real/hosts/robotics_quick.py [cells, e.g. 1-4 or 1,3] [modes, e.g. seed3,seed3v1,default]"""
import os, sys, time, json
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from seed import run as run1
import seed3
from robotics import Robotics
MODES_ALL = ("seed3", "seed3v1", "seed", "rollout", "default")
MODES = sys.argv[2].split(",") if len(sys.argv) > 2 else list(MODES_ALL)
OUT = os.environ.get("SEED3_POOL_OUT")
def cells_of(spec):
    return [c for p in spec.split(",") for c in (range(int(p.split("-")[0]), int(p.split("-")[1]) + 1) if "-" in p else [int(p)])]
def one(job):
    cell, mode = job; host = Robotics(); t0 = time.time()
    if mode == "seed3" and OUT: os.environ["SEED3_POOL_OUT"] = f"{OUT}.cell{cell}"
    elif OUT: os.environ.pop("SEED3_POOL_OUT", None)
    o = seed3.run(host, cell, mode) if mode.startswith("seed3") else run1(host, cell, mode)
    line = f"{cell} {mode:8s} result {{o['result']}} resource {round(o['resource'], 3)} R {round(o['R'], 7)} return {round(o['return'], 1)} time {time.time() - t0:.0f}s choices {o['choices']}"
    if mode == "seed3":
        line += (f"\n{cell} {mode:8s} ops_used { {k: v for k, v in o['ops_used'].items() if v} } rooms {o['rooms']} vetoed {o['vote_vetoed']} "
                 f"tried {o['ops_tried']} passed_membrane {o['ops_passed_membrane']} colour {o['colour_counts']} "
                 f"zoom {o['zoom_scale_decisions']} enter_depth {o['enter_depth']} rollouts v1/ops {o['rollouts_v1']}/"
                 f"{o['rollouts_ops']} fallback {o['op_fallback']} inherit {o['inherit_entries']} shapes {o['shape_keys']} "
                 f"pool_in {o['pool_loaded_from']} pool_out {o['pool_saved']}"
                 f"\n{cell} {mode:8s} ops_bound {json.dumps(o['ops_bound'])}")
    return cell, mode, o["result"], o["resource"], time.time() - t0, line
def merge_pools(cells):
    ops, shapes = {}, {}
    for c in cells:
        p = f"{OUT}.cell{c}"
        if not os.path.exists(p): continue
        d = json.load(open(p))
        for k, v in d.get("ops", {}).items(): ops.setdefault(k, []).extend(v)
        for k, v in d.get("shapes", {}).items():
            for e, cc in v.items():
                cur = shapes.setdefault(k, {}).setdefault(e, [0, 0]); cur[0] += cc[0]; cur[1] += cc[1]
        os.remove(p)
    json.dump({"ops": {k: v[-200:] for k, v in ops.items()}, "shapes": shapes}, open(OUT, "w"), sort_keys=True)
    return sum(len(v) for v in ops.values()), len(shapes)
if __name__ == "__main__":
    cells = cells_of(sys.argv[1] if len(sys.argv) > 1 else "1-4")
    assert all(c < 100 for c in cells), "development cells only (never cells >= 100)"
    jobs = [(c, m) for m in MODES for c in cells]; res = {}
    with Pool(max(1, min(len(jobs), os.cpu_count() or 1)), maxtasksperchild=1) as p:
        for cell, mode, r, rs, t, line in p.imap_unordered(one, jobs):
            res[(cell, mode)] = (r, rs, t); print(line, flush=True)
    print("\nTABLE result (resource) [seconds]; d = result - default")
    for c in cells:
        d = res.get((c, "default"), (None,))[0]
        print(f"cell {c}: " + "  ".join(f"{m} {res[(c, m)][0]:.4f} ({res[(c, m)][1]:.1f}) [{res[(c, m)][2]:.0f}s]"
              + (f" d{res[(c, m)][0] - d:+.4f}" if d is not None and m != "default" else "") for m in MODES if (c, m) in res))
    if OUT and "seed3" in MODES:
        n, k = merge_pools(cells); print(f"pool saved {OUT}: {n} operator entries, {k} shape keys")
