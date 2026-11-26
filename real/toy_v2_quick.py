"""REAL3 v2 interface check on the toy (development cells 1-4 only; no claim). Prints: REAL1/REAL2 modes on Toy and
ToyLand (must equal the numbers before v2), seed3v1, seed3 (v2) on ToyOps (every hook bound) and on plain Toy (no new
hooks: operators not bound, the run must still work), operator use, rooms, membrane check (v2 objective >= default's),
time per row. Set SEED3_POOL_OUT / SEED3_POOL_IN to save / load the TRANSPLANT pool."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seed, seed3, host_toy as T

def obj(o, n=30): return o["result"] * n - 0.01 * o["resource"]      # the toy's objective at the end (sum - 0.01 used)
print("REAL1/REAL2 modes (unchanged code paths):")
for cls in (T.Toy, T.ToyLand):
    for mode in ("default", "seed", "seed_noland", "rollout"):
        print(f"  {cls.__name__:8s} {mode:12s}", [(round(o["result"], 6), o["resource"]) for o in (seed.run(cls(), c, mode) for c in (1, 2, 3, 4))])
for cls in (T.ToyOps, T.Toy):
    print(f"\n{cls.__name__}:"); tot = {}; tt = {"v1": 0, "v2": 0}
    for c in (1, 2, 3, 4):
        d = seed.run(cls(), c, "default"); v1 = seed3.run(cls(), c, "seed3v1"); v2 = seed3.run(cls(), c, "seed3")
        tt["v1"] += v1["seconds"]; tt["v2"] += v2["seconds"]
        print(f"  cell {c}: default {d['result']:.6f}/{d['resource']}  seed3v1 {v1['result']:.6f}/{v1['resource']}"
              f"  seed3v2 {v2['result']:.6f}/{v2['resource']}  obj v2-default {obj(v2)-obj(d):+.4f}  v2-v1 {obj(v2)-obj(v1):+.4f}"
              f"  membrane(v2>=default) {obj(v2) >= obj(d)}  time v1 {v1['seconds']}s v2 {v2['seconds']}s")
        print("     chosen", {k: v for k, v in v2["ops_used"].items() if v}, "rooms", v2["rooms"],
              "rollouts v1/ops", v2["rollouts_v1"], v2["rollouts_ops"], "vetoed", v2["vote_vetoed"])
        for k, v in v2["ops_used"].items(): tot[k] = tot.get(k, 0) + v
    print("  total chosen", tot); print(f"  time v1 {tt['v1']:.2f}s v2 {tt['v2']:.2f}s ratio {tt['v2']/tt['v1']:.2f}")
    print("  bound", json.dumps(v2["ops_bound"]))
    print("  tried", v2["ops_tried"]); print("  passed membrane", v2["ops_passed_membrane"])
    print("  colour", v2["colour_counts"], "zoom scales", v2["zoom_scale_decisions"], "enter depth", v2["enter_depth"],
          "fallback", v2["op_fallback"], "inherit", v2["inherit_entries"], "shapes", v2["shape_keys"],
          "pool in", v2["pool_loaded_from"], "pool out", v2["pool_saved"])
