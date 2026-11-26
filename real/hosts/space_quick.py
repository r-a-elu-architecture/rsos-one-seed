"""REAL3 row 5 quick test (development cells 1..4 only; 2 shared CPUs here). Modes per cell: seed3 (REAL3 v2 =
seed3.run(..., "seed3"): v1 choice + seed operators bound by the v2 hooks), seed3v1 (REAL3 v1 exactly: primitives incl.
P4P5 exact planner + frame F:holo), seed (REAL2 seed with landing), rollout (plain rollout), default (value-density
priority queue, the standard and membrane bound), strongest (exact look-ahead MILP planner, Space("strongest") in default
mode). Fixed-budget row: pass = result > standard. Orbit: the marked STAND-IN here (stand_in=True). `--loss p` runs the
opt-in frame-loss variant (default 0 = the REAL1/REAL2 host); `--edf` also prints EDF in default mode. The seed3 and
seed3v1 chains each keep their own v1 family pool across cells (seed3.POOL / OFF swapped per chain).
SEED3_POOL_IN / SEED3_POOL_OUT: the v2 TRANSPLANT pool is loaded at import / saved after every v2 run.
Usage: python3 space_quick.py [cells...] [--loss p] [--edf]   (cells >= 100 are refused)"""
import sys, os, time, copy, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seed, seed3
from space import Space

CH = {}
def run3(h, cell, mode):
    pool, off = CH.get(mode, ({}, {}))
    seed3.POOL.clear(); seed3.POOL.update(copy.deepcopy(pool)); seed3.OFF.clear(); seed3.OFF.update(copy.deepcopy(off))
    o = seed3.run(h, cell, mode); CH[mode] = (copy.deepcopy(seed3.POOL), copy.deepcopy(seed3.OFF)); return o

args = sys.argv[1:]
loss = float(args[args.index("--loss") + 1]) if "--loss" in args else 0.0
if "--loss" in args: i = args.index("--loss"); args = args[:i] + args[i + 2:]
cells = [int(c) for c in args if not c.startswith("--")] or [1, 2, 3, 4]
assert all(c < 100 for c in cells), "development cells only (cells >= 100 are held out)"
host = Space("pq", loss=loss); strong = Space("strongest", loss=loss)
print(f"loss {loss}")
tot = {}
for cell in cells:
    t0 = time.time(); out = {}
    for label, h, mode in (("seed3", host, "seed3"), ("seed3v1", host, "seed3v1"), ("seed", host, "seed"),
                           ("rollout", host, "rollout"), ("default", host, "default"), ("strongest", strong, "default")):
        t1 = time.time()
        o = run3(h, cell, mode) if mode.startswith("seed3") else seed.run(h, cell, mode); out[label] = o
        print(f"cell {cell} {label:9s} result {o['result']:.2f} resource {o['resource']:.1f} lost {o['lost_value']:.1f}"
              f" frag_mb {o['frag_mb']:.0f} repair_mb {o['repair_mb']:.0f} rec/lost_frames {o['recovered_frames']}/"
              f"{o['lost_frames']}" + (f" stand_in={o['stand_in']}" if label == "default" else f" choices={o['choices']}"))
        if label == "seed3":
            used = {k: v for k, v in o["ops_used"].items() if v}
            for k, v in used.items(): tot[k] = tot.get(k, 0) + v
            print(f"   v2 ops_used {used} rooms {o['rooms']} colour {o['colour_counts']} vetoed {o['vote_vetoed']}")
            print(f"   v2 passed_membrane {o['ops_passed_membrane']} tried {o['ops_tried']}")
            print(f"   v2 rollouts v1/ops {o['rollouts_v1']}/{o['rollouts_ops']} zoom {o['zoom_scale_decisions']} "
                  f"enter {o['enter_depth']} op_fallback {o['op_fallback']} inherit {o['inherit_entries']} "
                  f"shapes {o['shape_keys']} pool_in {o['pool_loaded_from']} pool_out {o['pool_saved']}")
        if label.startswith("seed3"): print(f"   {label} seconds {time.time() - t1:.1f}")
    if "--edf" in args:
        o = seed.run(Space("edf", loss=loss), cell, "default")
        print(f"cell {cell} edf       result {o['result']:.2f} resource {o['resource']:.1f}")
    d, st = out["default"]["result"], out["strongest"]["result"]
    print(f"cell {cell} pass(result > default / > strongest): " + " ".join(
        f"{m}={'WIN' if out[m]['result'] > d else 'no'}/{'WIN' if out[m]['result'] > st else 'no'}"
        for m in ("seed3", "seed3v1", "seed", "rollout")) + f" strongest={'WIN' if st > d else 'no'}/-",
        f"v2-v1 {out['seed3']['result'] - out['seed3v1']['result']:+.2f}", f"time {time.time() - t0:.1f}s")
print("ops_bound", json.dumps(out["seed3"]["ops_bound"]))
print("ops_used total (v2, all cells)", tot)
