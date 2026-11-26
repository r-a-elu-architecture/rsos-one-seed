"""A5 runner. PREREGISTRATION_A5.md section 7. One process per task set (S2 patches the A4 generator).

    python experiments/a5_run.py replaycheck S1|S2     # offline, before any live call
    python experiments/a5_run.py smoke S1|S2 [ARMS]     # seed 999
    python experiments/a5_run.py run S1|S2 [ARMS]       # 16 seeds, resumable, 8 workers
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
import a3b_hologram as H                   # noqa: E402
import a5_arms as X                        # noqa: E402
import a5_llm as L                         # noqa: E402
from a3b_hdragon import HDragon            # noqa: E402

R = os.path.join(A.ROOT, "results")
SEEDS = {"S1": list(range(100, 108)) + list(range(300, 308)), "S2": list(range(400, 416))}
_lock = threading.Lock()


def setup(set_name):
    if set_name == "S2":
        import a4_latent as A4
        A4.patch()
    X.install_b1()


def computes_of(task, final_state):
    if not task or "computes" not in task:
        return None
    out = []
    for c in task["computes"]:
        v = final_state.get(c["target"])
        cls = "correct" if v == c["f_true"] else ("traced" if c["f_wrong"] is not None and v == c["f_wrong"]
                                                  else "other_wrong")
        out.append({"step": c["step"], "kind": c["kind"], "op": c["op"], "target": c["target"], "true": c["f_true"],
                    "drifted": c["f_wrong"], "got": v, "class": cls})
    return out


def run_one(arm, set_name, seed, tag=None):
    if arm == "B1":
        res, task = X.run_b1(set_name, seed, tag=tag)
    elif arm == "X5":
        res, task = X.run_x5(set_name, seed, tag=tag)
    else:
        res, task = X.run_x(arm, set_name, seed, tag=tag)
    if set_name == "S2":
        res["computes"] = computes_of(task, res["final_state"])
    res["set"] = set_name
    return res


# ---------------------------------------------------------------- replay check

CHECK = ("success", "line_acc", "replica_success", "final_errors", "steps_failed", "n_calls", "channel_tok",
         "channel_bpe", "channel_bytes", "billed_tok", "out_tok", "drift")


def same(r, o):
    bad = []
    for k in CHECK:
        if k == "drift":
            a = [{x: y for x, y in e.items() if x != "recovery_sec"} for e in r[k]]
            b = [{x: y for x, y in e.items() if x != "recovery_sec"} for e in o[k]]
            if a != b:
                bad.append(k)
        elif r[k] != o[k]:
            bad.append(k)
    return bad


def replay_b1(t, set_name):
    """Recorded H-dragon outputs fed through A5's B1 wiring (reorder + fixed-call interface)."""
    queue = list(t["calls"])
    real = L.llm

    def fake(system, prompt, schema=None, log=None, model=None):
        c = queue.pop(0)
        s0, p0 = X.reorder(c["system_full"], c["prompt"])
        assert (system, prompt) == (s0, p0), "B1 wiring sent a different prompt"
        return c["text"], c["structured"], {k: c[k] for k in ("in", "cache_w", "cache_r", "out", "sec", "api_ms",
                                                              "turns", "cost")}

    L.llm = fake
    try:
        res, _ = X.run_b1(set_name, t["seed"], tag=t["tag"])
    finally:
        L.llm = real
    assert not queue, "unused recorded calls"
    return res


ORACLE = [
    (r"^Set (\S+) to (\S+) plus 500\.$", lambda m: f"INHERIT {m[1]} {m[2]} +500"),
    (r"^Set (\S+) to (\S+) plus (\d), capped at 9\.$", lambda m: f"INHERIT {m[1]} {m[2]} +{m[3]} CAP 9"),
    (r"^Set (\S+) to (\S+) \+ (\S+), capped at 9\.$", lambda m: f"FUSE {m[1]} {m[2]} {m[3]} CAP 9"),
    (r"^Set (\S+) to (\S+)\.$", lambda m: f"SET {m[1]} {m[2]}"),
    (r"^Change the (\S+) of (\S+) to (\S+)\.$", lambda m: f"SET {m[2]}.{m[1]} {m[3]}"),
    (r"^(\S+) needs (\S+) = (\S+) from now on\.$", lambda m: f"SET {m[1]}.{m[2]} {m[3]}"),
    (r"^Increase (\S+) by (\d) \(cap at 9\)\.$", lambda m: f"INHERIT {m[1]} {m[1]} +{m[2]} CAP 9"),
    (r"^Double (\S+), capped at 9\.$", lambda m: f"SCALE {m[1]} 2 CAP 9"),
    (r"^Everything owned by (\S+) is now owned by (\S+)\.$", lambda m: f"REHOST owner {m[1]} {m[2]}"),
    (r"^Add a new line (\S+) = (\S+) at the end\.$", lambda m: f"SET {m[1]} {m[2]}"),
    (r"^Remove the line (\S+) entirely\.$", lambda m: f"DEL {m[1]}"),
    (r"^If (\S+) is (\S+), set (\S+) to (\S+); otherwise set it to (\S+)\.$",
     lambda m: f"ROUTE {m[1]} = {m[2]} : {m[3]} {m[4]} | {m[5]}"),
    (r"^Make (\S+) equal to (\S+)\.$", lambda m: f"INHERIT {m[1]} {m[2]}"),
]


def oracle_ops(req):
    """TEST ONLY (replay check of the runtime): the generator's own templates. Never used by an arm."""
    r = req[len("Worker-computed: "):] if req.startswith("Worker-computed: ") else req
    for rx, f in ORACLE:
        m = re.match(rx, r)
        if m:
            return f(m)
    raise ValueError(req)


def replaycheck(set_name):
    setup(set_name)
    os.environ.pop("A5_TRANSCRIPTS", None)
    os.environ["A_TRANSCRIPTS"] = os.devnull
    sysm = {}
    for s in A.SYS.values():
        sysm[s[:40]] = s
    if set_name == "S1":
        rec = {r["seed"]: r for r in map(json.loads, open(os.path.join(R, "a3b_results_hd.jsonl")))}
        trs = [json.loads(x) for x in open(os.path.join(R, "a3b_transcripts_hd.jsonl"))]
    else:
        rec = {r["seed"]: r for r in map(json.loads, open(os.path.join(R, "a4_results.jsonl"))) if r["cond"] == "Hd"}
        trs = [t for t in map(json.loads, open(os.path.join(R, "a4_transcripts.jsonl")))
               if t["cond"] == "Hd" and t["seed"] in SEEDS["S2"] and t.get("tag") is None]
    n, bad = 0, []
    for t in trs:
        for c in t["calls"]:
            c["system_full"] = sysm[c["system"]]
        r = replay_b1(t, set_name)
        n += 1
        b = same(r, rec[t["seed"]])
        if b:
            bad.append((t["seed"], b))
    # oracle: the runtime given correct operations reaches the truth (and every audit sees the right result)
    orc = []
    for arm in X.X_ARMS:
        for seed in SEEDS[set_name]:
            def planner(prompt, ctx, seed=seed, arm=arm):
                req = prompt.split("\n", 1)[0][len("Change request: "):]
                ops = oracle_ops(req)
                return ("Instruction.\n---\n" + ops) if arm in ("X1", "X1s") else ops
            res, task = X.run_x(arm, set_name, seed, planner=planner, auditor=lambda p, c: "ok")
            cm = run_comp(set_name, task, res)
            orc.append({"arm": arm, "seed": seed, "success": res["success"], "replica": res["replica_success"],
                        "healed0": sum(e["healed_zero_call"] for e in res["drift"]), "invalid": res["invalid_ops"],
                        "audited": sum(1 for s in res["steps"] for a in s["attempts"] if a.get("audited")),
                        "traced": sum(1 for c in (cm or []) if c["class"] == "traced")})
    for seed in SEEDS[set_name]:
        def planner5(prompt, ctx):
            out = []
            for line in prompt.split("\n"):
                m = re.match(r"^#(\d+) (.*)$", line)
                if m:
                    out.append(f"#{m.group(1)}\n" + oracle_ops(m.group(2)))
            return "\n".join(out)
        def auditor5(prompt, ctx):
            return "\n".join(f"{m} ok" for m in re.findall(r"^#(\d+) ", prompt, re.M))
        res, task = X.run_x5(set_name, seed, planner=planner5, auditor=auditor5)
        cm = run_comp(set_name, task, res)
        orc.append({"arm": "X5", "seed": seed, "success": res["success"], "replica": res["replica_success"],
                    "healed0": sum(e["healed_zero_call"] for e in res["drift"]), "invalid": res["invalid_ops"],
                    "audited": sum(1 for s in res["steps"] if s.get("audited")),
                    "traced": sum(1 for c in (cm or []) if c["class"] == "traced"), "calls": res["n_calls"]})
    diff = subprocess.run(["git", "-C", A.ROOT, "diff", "origin/main", "--", "experiments/a1_agents.py",
                           "experiments/a3_run.py", "experiments/a3b_hologram.py", "experiments/a3b_hdragon.py",
                           "experiments/a4_latent.py", "experiments/a4_analyse.py"] +
                          [f"experiments/{f}" for f in os.listdir(HERE) if f.startswith("a3c_")],
                          capture_output=True, text=True).stdout
    out = {"set": set_name, "b1_runs_replayed": n, "b1_mismatches": bad, "frozen_files_diff_vs_main_empty": diff == "",
           "oracle_tasks": len(orc), "oracle_success": sum(o["success"] and o["replica"] for o in orc),
           "oracle_healed_zero_call": sum(o["healed0"] for o in orc), "oracle_invalid": sum(o["invalid"] for o in orc),
           "oracle_traced": sum(o["traced"] for o in orc),
           "oracle_audited_steps_per_task": {a: sum(o["audited"] for o in orc if o["arm"] == a) / len(SEEDS[set_name])
                                             for a in X.X_ARMS + ("X5",)},
           "oracle_x5_calls_per_task": sum(o.get("calls", 0) for o in orc if o["arm"] == "X5") / len(SEEDS[set_name])}
    out["pass"] = (not bad and n == 16 and diff == "" and out["oracle_success"] == len(orc)
                   and out["oracle_invalid"] == 0 and out["oracle_healed_zero_call"] == 3 * len(orc))
    json.dump(out, open(os.path.join(R, f"a5_replay_check_{set_name}.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))
    return out["pass"]


def run_comp(set_name, task, res):
    return computes_of(task, res["final_state"]) if set_name == "S2" else None


# ---------------------------------------------------------------- scaffold, smoke, live

def scaffold(set_name, phase):
    rows = []
    for i in range(3):
        _, _, r = L.raw_call("x", f"Reply OK. {i}")
        rows.append(r["in"] + r["cache_w"] + r["cache_r"])
    with _lock:
        with open(os.path.join(R, "a5_scaffold.jsonl"), "a") as f:
            f.write(json.dumps({"set": set_name, "phase": phase, "tokens": rows}) + "\n")
    return rows


def smoke(set_name, arms):
    setup(set_name)
    os.environ["A_TRANSCRIPTS"] = os.path.join(R, "a5_smoke_transcripts.jsonl")
    os.environ["A5_TRANSCRIPTS"] = os.path.join(R, "a5_smoke_transcripts.jsonl")
    out = []
    with ThreadPoolExecutor(len(arms)) as ex:
        futs = {ex.submit(run_one, a, set_name, 999, os.environ.get("A5_SMOKE_TAG", "smoke")): a for a in arms}
        for fu in as_completed(futs):
            r = fu.result()
            out.append(r)
    with open(os.path.join(R, "a5_smoke_results.jsonl"), "a") as f:
        for r in out:
            f.write(json.dumps(r) + "\n")
    for r in sorted(out, key=lambda r: X.ARMS.index(r["arm"])):
        print(r["arm"], {k: r.get(k) for k in ("success", "replica_success", "n_calls", "out_tok", "in_tok",
                                               "cost_usd", "invalid_ops", "steps_failed", "final_errors")})


def main_run(set_name, arms):
    setup(set_name)
    res_path = os.path.join(R, f"a5_results_{set_name}.jsonl")
    os.environ["A_TRANSCRIPTS"] = os.path.join(R, f"a5_transcripts_{set_name}.jsonl")
    os.environ["A5_TRANSCRIPTS"] = os.environ["A_TRANSCRIPTS"]
    done = set()
    if os.path.exists(res_path):
        for line in open(res_path):
            r = json.loads(line); done.add((r["arm"], r["seed"]))
    todo = [(a, s) for a in arms for s in SEEDS[set_name] if (a, s) not in done]
    print(f"{set_name}: done {len(done)}, live {len(todo)}", flush=True)
    if not todo:
        return
    scaffold(set_name, "start")
    with ThreadPoolExecutor(int(os.environ.get("A5_WORKERS", "8"))) as ex:
        futs = [ex.submit(run_one, a, set_name, s) for a, s in todo]
        for fu in as_completed(futs):
            r = fu.result()
            with _lock:
                with open(res_path, "a") as f:
                    f.write(json.dumps(r) + "\n")
    scaffold(set_name, "end")


if __name__ == "__main__":
    cmd, set_name = sys.argv[1], sys.argv[2]
    arms = sys.argv[3].split(",") if len(sys.argv) > 3 else list(X.ARMS)
    if cmd == "replaycheck":
        sys.exit(0 if replaycheck(set_name) else 1)
    elif cmd == "smoke":
        smoke(set_name, arms)
    elif cmd == "run":
        main_run(set_name, arms)
