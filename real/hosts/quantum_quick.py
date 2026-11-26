"""REAL3 row 4 quick test (development cells 1..4 only; 2 shared CPUs here). Modes per cell: seed3 (REAL3 v2 =
seed3.run(..., "seed3"): v1 choice + seed operators bound by the v2 hooks), seed3v1 (REAL3 v1 exactly), seed (REAL2 seed
with landing), rollout (plain rollout), default (Neyman standard), strongest (Quantum("strongest") = the same Neyman
code; see quantum.py docstring). Fixed-budget row: pass = result > standard at the same shots. The seed3 and seed3v1
chains each keep their own v1 family pool across cells (seed3.POOL / OFF swapped per chain), so the two modes do not
feed each other. SEED3_POOL_IN / SEED3_POOL_OUT: the v2 TRANSPLANT pool is loaded at import / saved after every v2 run.
Joint-setting shots cost their hardware width (COST); REAL3_QUANTUM_WIDTH_FREE=1 is the labelled width-free variant.
Usage: python3 quantum_quick.py [cells...]   (cells >= 100 are refused: they are not development cells)"""
import os, sys, time, copy, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seed, seed3
from quantum import Quantum, WIDTH_FREE

CH = {}
def run3(h, cell, mode):
    """one seed3 chain per mode: its own v1 family pool and apoptosis state across cells"""
    pool, off = CH.get(mode, ({}, {}))
    seed3.POOL.clear(); seed3.POOL.update(copy.deepcopy(pool)); seed3.OFF.clear(); seed3.OFF.update(copy.deepcopy(off))
    o = seed3.run(h, cell, mode); CH[mode] = (copy.deepcopy(seed3.POOL), copy.deepcopy(seed3.OFF)); return o

host, strong = Quantum(), Quantum(standard="strongest")
cells = [int(c) for c in sys.argv[1:]] or [1, 2, 3, 4]
assert all(c < 100 for c in cells), "development cells only (cells >= 100 are held out)"
print(f"width_free {WIDTH_FREE}")
tot = {}
for cell in cells:
    t0 = time.time(); out = {}
    for label, h, mode in (("seed3", host, "seed3"), ("seed3v1", host, "seed3v1"), ("seed", host, "seed"),
                           ("rollout", host, "rollout"), ("default", host, "default"), ("strongest", strong, "default")):
        t1 = time.time()
        o = run3(h, cell, mode) if mode.startswith("seed3") else seed.run(h, cell, mode); out[label] = o
        print(f"cell {cell} {label:9s} result {o['result']:.5f} resource {o['resource']:.0f} rmse {o['rmse']:.5f} "
              f"joint_shots {o['joint_shots']} choices {o['choices']}")
        if label == "seed3":
            used = {k: v for k, v in o["ops_used"].items() if v}
            for k, v in used.items(): tot[k] = tot.get(k, 0) + v
            print(f"   v2 ops_used {used} rooms {o['rooms']} colour {o['colour_counts']} vetoed {o['vote_vetoed']} "
                  f"carried_shots {o['carried_shots']}")
            print(f"   v2 passed_membrane {o['ops_passed_membrane']} tried {o['ops_tried']}")
            print(f"   v2 rollouts v1/ops {o['rollouts_v1']}/{o['rollouts_ops']} zoom {o['zoom_scale_decisions']} "
                  f"enter {o['enter_depth']} op_fallback {o['op_fallback']} inherit {o['inherit_entries']} "
                  f"shapes {o['shape_keys']} pool_in {o['pool_loaded_from']} pool_out {o['pool_saved']}")
        if label.startswith("seed3"): print(f"   {label} seconds {time.time() - t1:.1f}")
    d, st = out["default"]["result"], out["strongest"]["result"]
    print(f"cell {cell} pass(result > default / > strongest): " + " ".join(
        f"{m}={'WIN' if out[m]['result'] > d else 'no'}/{'WIN' if out[m]['result'] > st else 'no'}"
        for m in ("seed3", "seed3v1", "seed", "rollout")),
        f"v2-v1 {out['seed3']['result'] - out['seed3v1']['result']:+.5f}", f"time {time.time() - t0:.1f}s")
print("ops_bound", json.dumps(out["seed3"]["ops_bound"]))
print("ops_used total (v2, all cells)", tot)
