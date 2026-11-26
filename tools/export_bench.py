"""Export RSOS-StateBench v1: the tasks of A5/A7 (S1, S2) and A7b (L1 56 steps, L2 224 steps, L3 300 keys) as plain JSONL, so any framework can be scored.
    PYTHONPATH=src python tools/export_bench.py        # -> bench/statebench_v1_S1.jsonl, _S2.jsonl
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "experiments"))


def export(set_name):
    import a1_agents as A
    import a5_run as R5
    import a7_tasks as T
    import sc1_tasks as SC
    import sc2_tasks as SC2
    import sc2c_tasks as SC2C
    seeds = {**R5.SEEDS, **T.SEEDS, **SC.SEEDS, **SC2.SEEDS, **SC2C.SEEDS}
    if set_name == "S2":
        import a4_latent as A4
        A4.patch()
    if set_name in T.CELLS:
        T.patch(set_name)
    if set_name in SC.CELLS:
        SC.patch(set_name)
    if set_name in SC2.CELLS:
        SC2.patch(set_name)
    if set_name in SC2C.CELLS:
        SC2C.patch(set_name)
    out = []
    for seed in seeds[set_name]:
        t = A.make_task(seed)
        drift = A.drift_plan(t, t["truths"])
        out.append({"set": set_name, "seed": seed, "init": dict(t["init"]), "requests": list(t["requests"]),
                    "final": dict(t["final"]), "truths": [dict(x) for x in t["truths"]],
                    "drift": [{"before_step": k, "agent": "worker", "key": v[0], "wrong_value": v[1]}
                              for k, v in sorted(drift.items())]})
    p = os.path.join(ROOT, "bench", f"statebench_v1_{set_name}.jsonl")
    with open(p, "w") as f:
        for r in out:
            f.write(json.dumps(r) + "\n")
    return p


if __name__ == "__main__":
    # S2 patches the generator in-process, so each set runs in its own process
    if len(sys.argv) > 1:
        print(export(sys.argv[1]))
    else:
        for s in ("S1", "S2", "L1", "L2", "L3", "SC1"):
            subprocess.run([sys.executable, __file__, s], check=True,
                           env={**os.environ, "PYTHONPATH": os.path.join(ROOT, "src")})
