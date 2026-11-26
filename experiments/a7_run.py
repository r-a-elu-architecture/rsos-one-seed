"""A7 runner. PREREGISTRATION_A7.md section 7. Runs on the owner's Claude plan through the A5 call (`claude -p`).

    python experiments/a7_run.py replaycheck S1|S2               # offline, 0 model calls, before any live call
    python experiments/a7_run.py smoke S1|S2 [ARMS]              # seed 999
    python experiments/a7_run.py run S1|S2 [ARMS]                # 16 seeds per arm, resumable
    A7_THINK=off python experiments/a7_run.py run S1|S2          # A7b cell: thinking off for every arm

Results: results/a7_results_<set>_<think>.jsonl, transcripts results/a7_transcripts_<set>_<think>.jsonl.
"""

import json
import os
import re
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import a1_agents as A                      # noqa: E402
import a5_run as R5                        # noqa: E402
import a7_arms as S                        # noqa: E402
import a7_tasks as T                       # noqa: E402
import sc1_tasks as SC                     # noqa: E402
import sc2_tasks as SC2                    # noqa: E402
import sc2c_tasks as SC2C                  # noqa: E402

R = os.path.join(A.ROOT, "results")
SEEDS = {**R5.SEEDS, **T.SEEDS, **SC.SEEDS, **SC2.SEEDS, **SC2C.SEEDS}                          # S1, S2 (A5 generator); L1-L3 (A7b long tasks)
THINK = os.environ.get("A7_THINK", "default")
BACKEND = os.environ.get("A7_BACKEND", "cli")           # cli (claude -p) or ollama (A7c, local model)
LABEL = os.environ.get("A7_LABEL", THINK)                # results file label, e.g. local_qwen15
_lock = threading.Lock()
FROZEN = ["a1_agents.py", "a3_run.py", "a3b_hologram.py", "a3b_hdragon.py", "a4_latent.py", "a4_analyse.py",
          "a5_arms.py", "a5_run.py", "a5_llm.py", "a5_cost.py", "a5_analyse.py", "a5_prices.json"]


def scaffold(set_name, phase):
    if BACKEND in ("ollama", "openai", "codex"):         # no Claude CLI, no scaffold: every token is the agent's own
        return
    """Null calls: the CLI scaffold of this machine, removed in the api basis (as A5). Own file, A5's untouched."""
    import a5_llm as L
    rows = []
    for i in range(3):
        _, _, r = L.raw_call("x", f"Reply OK. {i}")
        rows.append(r["in"] + r["cache_w"] + r["cache_r"])
    with _lock:
        with open(os.path.join(R, "a7_scaffold.jsonl"), "a") as f:
            f.write(json.dumps({"set": set_name, "phase": phase, "think": LABEL, "tokens": rows}) + "\n")


def setup(set_name):
    if set_name == "S2":
        import a4_latent as A4
        A4.patch()
    if set_name in T.CELLS or set_name in SC.CELLS or set_name in SC2.CELLS or set_name in SC2C.CELLS:
        (SC2C.patch if set_name in SC2C.CELLS else SC2.patch if set_name in SC2.CELLS else
         SC.patch if set_name in SC.CELLS else T.patch)(set_name)
        import a5_llm as L                               # long plans: allow 15 minutes per call (A5: 3)
        raw = L.raw_call
        L.raw_call = lambda system, prompt, model=None, legacy=False, timeout=900: raw(system, prompt, model,
                                                                                         legacy, 900)
    S.thinking(THINK)
    if BACKEND == "ollama":
        import a7_local
        a7_local.install()
    if BACKEND == "openai":
        import a7_openai
        a7_openai.install()
    if BACKEND == "codex":
        import a7_codex
        a7_codex.install()


def run_one(arm, set_name, seed, tag=None):
    res, task = S.run_plan(arm, set_name, seed, tag=tag, think=THINK)
    if set_name == "S2":
        res["computes"] = R5.computes_of(task, res["final_state"])
    res["set"] = set_name
    res["label"], res["backend"] = LABEL, BACKEND
    return res


# ---------------------------------------------------------------- replay check (0 model calls)

def oracle_patch(task, k):
    a, b = task["truths"][k], task["truths"][k + 1]
    out = [{"op": "remove", "path": "/" + x} for x in a if x not in b]
    out += [{"op": "replace" if x in a else "add", "path": "/" + x, "value": b[x]} for x in b if a.get(x) != b[x]]
    return json.dumps(out)


def replaycheck(set_name):
    setup(set_name)
    os.environ.pop("A7_TRANSCRIPTS", None)
    rows = []
    for arm in S.ARMS:
        for seed in SEEDS[set_name]:
            task = A.make_task(seed)

            def planner(prompt, ctx, task=task, arm=arm):
                out = []
                for line in prompt.split("\n"):
                    m = re.match(r"^#(\d+) (.*)$", line)
                    if m:
                        k = int(m.group(1)) - 1
                        body = oracle_patch(task, k) if arm in ("B2", "B2s") else R5.oracle_ops(m.group(2))
                        out.append(f"#{k + 1}\n{body}")
                return "\n".join(out)

            def auditor(prompt, ctx):
                return "\n".join(f"{m} ok" for m in re.findall(r"^#(\d+) ", prompt, re.M))

            seen = {}

            def planner_spy(prompt, ctx, f=planner):
                seen.setdefault("prompt", prompt)
                return f(prompt, ctx)

            res, _ = S.run_plan(arm, set_name, seed, planner=planner_spy, auditor=auditor, think=THINK)
            p = seen.get("prompt", "")
            leak = arm == "X5b" and any(f"{k} = " in p or f"={v}" in p for k, v in task["init"].items())
            rows.append({"arm": arm, "seed": seed, "success": res["success"], "replica": res["replica_success"],
                         "healed0": sum(e["healed_zero_call"] for e in res["drift"]), "invalid": res["invalid_ops"],
                         "drifts": len(res["drift"]), "calls": res["n_calls"], "blind_leak": leak,
                         "audited": sum(1 for s in res["steps"] if s["audited"])})
    diff = subprocess.run(["git", "-C", A.ROOT, "diff", "origin/main", "--"] + [f"experiments/{f}" for f in FROZEN],
                          capture_output=True, text=True).stdout
    per = {a: [r for r in rows if r["arm"] == a] for a in S.ARMS}
    out = {"set": set_name, "think": THINK, "frozen_files_diff_vs_main_empty": diff == "",
           "oracle": {a: {"tasks": len(v), "success": sum(r["success"] and r["replica"] for r in v),
                          "healed_zero_call": sum(r["healed0"] for r in v), "drifts": sum(r["drifts"] for r in v),
                          "invalid": sum(r["invalid"] for r in v),
                          "calls_per_task": sum(r["calls"] for r in v) / len(v),
                          "audited_steps": [r["audited"] for r in v]} for a, v in per.items()},
           "x5b_value_leaks": sum(r["blind_leak"] for r in rows),
           "same_audit_selection_all_arms": len({tuple(r["audited"] for r in v) for v in per.values()}) == 1}
    out["pass"] = (out["frozen_files_diff_vs_main_empty"] and out["x5b_value_leaks"] == 0
                   and out["same_audit_selection_all_arms"]
                   and all(o["success"] == o["tasks"] == 16 and o["invalid"] == 0 and o["healed_zero_call"] == o["drifts"] > 0
                           for o in out["oracle"].values()))
    json.dump(out, open(os.path.join(R, f"a7_replay_check_{set_name}_{LABEL}.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "oracle"} |
                     {"oracle": {a: {k: v for k, v in o.items() if k != "audited_steps"}
                                 for a, o in out["oracle"].items()}}, indent=1))
    return out["pass"]


# ---------------------------------------------------------------- smoke and live

def smoke(set_name, arms):
    setup(set_name)
    os.environ["A7_TRANSCRIPTS"] = os.path.join(R, "a7_smoke_transcripts.jsonl")
    out = []
    with ThreadPoolExecutor(len(arms)) as ex:
        futs = [ex.submit(run_one, a, set_name, 999, os.environ.get("A7_SMOKE_TAG", "smoke")) for a in arms]
        for fu in as_completed(futs):
            out.append(fu.result())
    with open(os.path.join(R, "a7_smoke_results.jsonl"), "a") as f:
        for r in out:
            f.write(json.dumps(r) + "\n")
    for r in sorted(out, key=lambda r: S.ARMS.index(r["arm"])):
        print(r["arm"], {k: r.get(k) for k in ("success", "replica_success", "n_calls", "in_tok", "out_tok",
                                               "think_tok", "invalid_ops", "steps_wrong", "steps_failed")})


def main_run(set_name, arms):
    setup(set_name)
    res_path = os.path.join(R, f"a7_results_{set_name}_{LABEL}.jsonl")
    os.environ["A7_TRANSCRIPTS"] = os.path.join(R, f"a7_transcripts_{set_name}_{LABEL}.jsonl")
    done = set()
    if os.path.exists(res_path):
        for line in open(res_path):
            r = json.loads(line)
            done.add((r["arm"], r["seed"]))
    todo = [(a, s) for a in arms for s in SEEDS[set_name] if (a, s) not in done]
    print(f"{set_name} label={LABEL} backend={BACKEND}: done {len(done)}, live {len(todo)}", flush=True)
    if not todo:
        return
    scaffold(set_name, "start")
    with ThreadPoolExecutor(int(os.environ.get("A7_WORKERS", "1" if BACKEND == "ollama" else "2" if BACKEND in ("openai", "codex") else "4"))) as ex:
        futs = {ex.submit(run_one, a, set_name, s): (a, s) for a, s in todo}
        errors = []
        for fu in as_completed(futs):
            try:
                r = fu.result()
            except Exception as e:  # noqa: BLE001  a provider error stops one task, never the others' results
                errors.append({"arm": futs[fu][0], "seed": futs[fu][1], "error": str(e)[:300]})
                print(f"{set_name} {futs[fu][0]} {futs[fu][1]} NOT RUN: {str(e)[:120]}", flush=True)
                continue
            with _lock:
                with open(res_path, "a") as f:
                    f.write(json.dumps(r) + "\n")
        if errors:
            with open(os.path.join(R, f"a7_errors_{set_name}_{LABEL}.jsonl"), "a") as f:
                for e in errors:
                    f.write(json.dumps(e) + "\n")
            print(f"{len(errors)} task(s) not run (provider errors); run the same command again later to resume")
    scaffold(set_name, "end")


if __name__ == "__main__":
    cmd, set_name = sys.argv[1], sys.argv[2]
    arms = sys.argv[3].split(",") if len(sys.argv) > 3 else list(S.ARMS)
    if cmd == "replaycheck":
        sys.exit(0 if replaycheck(set_name) else 1)
    elif cmd == "smoke":
        smoke(set_name, arms)
    elif cmd == "run":
        main_run(set_name, arms)
