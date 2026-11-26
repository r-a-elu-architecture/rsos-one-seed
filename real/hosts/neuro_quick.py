"""REAL3 v2 (25 Nov): modes seed3 (seed3.run "seed3" = v2: v1 choice + seed operators bound by the host hooks), seed3v1
(REAL3 v1 exactly), seed (REAL2 seed with landing), rollout, default (greedy Kalman sensor selection = the standard and
the strongest method of this row, see neuro.py) and uniform (round robin, second baseline); development cells 1-4 only
(never cells >= 100). One process per (cell, mode) (maxtasksperchild=1): the seed's shared pools (seed3.POOL, the
operator pool) then hold only that run's trace, so seed3 and seed3v1 never see each other and a line does not depend on
which runs a worker did before. SEED3_POOL_IN is loaded at import (every worker); with SEED3_POOL_OUT set, each seed3
(v2) run saves its pool to <out>.cell<c> and the parent merges them (cell order) into <out> at the end.
Without a data argument: STAND-IN data (interface check only, never for results). With an argument: the .npz written
by neuro_fetch.py (DANDI:000140 MC_Maze_Small). Only cells that exist in the recording are run.
Usage: python3 real/hosts/neuro_quick.py [<data.npz> | -] [1-4] [modes, e.g. seed3,seed3v1,default]
Seed own future: the REAL TREE (blocks of the recording's own calibration past; see neuro.py OWN FUTURE)."""
import os, sys, time, json
from multiprocessing import Pool
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from seed import run as run1
import seed3
from neuro import Neuro

data = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != "-" else None
spec = sys.argv[2] if len(sys.argv) > 2 else "1-4"
RUNS = {"seed3": ("greedy", "seed3"), "seed3v1": ("greedy", "seed3v1"), "seed": ("greedy", "seed"),
        "rollout": ("greedy", "rollout"), "default": ("greedy", "default"), "uniform": ("uniform", "default")}
MODES = sys.argv[3].split(",") if len(sys.argv) > 3 else list(RUNS)
OUT = os.environ.get("SEED3_POOL_OUT")

def one(job):
    cell, label = job; std, mode = RUNS[label]; host = Neuro(data=data, standard=std); t0 = time.time()
    if mode == "seed3" and OUT: os.environ["SEED3_POOL_OUT"] = f"{OUT}.cell{cell}"
    elif OUT: os.environ.pop("SEED3_POOL_OUT", None)
    o = seed3.run(host, cell, mode) if mode.startswith("seed3") else run1(host, cell, mode)
    line = (f"cell {cell} {label:8s} result {o['result']:.5f} resource {o['resource']:.0f} R {o['R']:.4e} "
            f"[{o['data']}] time {time.time() - t0:.1f}s choices {o['choices']}")
    if mode == "seed3":
        line += (f"\ncell {cell} {label:8s} ops_used { {k: v for k, v in o['ops_used'].items() if v} } rooms {o['rooms']} vetoed {o['vote_vetoed']} "
                 f"tried {o['ops_tried']} passed_membrane {o['ops_passed_membrane']} colour {o['colour_counts']} "
                 f"zoom {o['zoom_scale_decisions']} enter_depth {o['enter_depth']} rollouts v1/ops {o['rollouts_v1']}/"
                 f"{o['rollouts_ops']} fallback {o['op_fallback']} inherit {o['inherit_entries']} shapes {o['shape_keys']} "
                 f"pool_in {o['pool_loaded_from']} pool_out {o['pool_saved']}"
                 f"\ncell {cell} {label:8s} ops_bound {json.dumps(o['ops_bound'])}")
    return cell, label, o["result"], o["resource"], time.time() - t0, line

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
    wanted = [c for part in spec.split(",") for c in (range(int(part.split("-")[0]), int(part.split("-")[1]) + 1)
                                                       if "-" in part else [int(part)])]
    assert all(c < 100 for c in wanted), "development cells only (never cells >= 100)"
    h = Neuro(data=data); cells = h.cells(wanted)
    if h.windows is not None:
        print(f"recording: {h.data.shape[0]} bins x {h.N} channels = {h.windows} windows of {h.CAL + h.T} bins; "
              f"cells run {cells}; beyond the recording (skipped) {[c for c in wanted if c not in cells]}", flush=True)
    jobs = [(c, m) for m in MODES for c in cells]; res = {}
    with Pool(max(1, min(len(jobs), os.cpu_count() or 1)), maxtasksperchild=1) as p:
        for cell, label, r, rs, t, line in p.imap_unordered(one, jobs):
            res[(cell, label)] = (r, rs, t); print(line, flush=True)
    print("\nTABLE result (resource) [seconds]; delta = mode - default")
    for c in cells:
        d = res.get((c, "default"), (None,))[0]
        print(f"cell {c}: " + "  ".join(f"{m} {res[(c, m)][0]:.5f} ({res[(c, m)][1]:.0f}) [{res[(c, m)][2]:.0f}s]"
              + (f" d{res[(c, m)][0] - d:+.5f}" if d is not None and m != "default" else "") for m in MODES if (c, m) in res))
    if OUT and "seed3" in MODES:
        n, k = merge_pools(cells); print(f"pool saved {OUT}: {n} operator entries, {k} shape keys")
