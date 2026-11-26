"""A4: does latent drift become wrong answers? PREREGISTRATION_A4.md.

The A3 harness (a1_agents.run_task for P, D, E, A) and the A3b hologram (a3b_hologram.run_task + HDragon) are
imported unchanged. A4 swaps three attributes of a1_agents inside this process only (make_task, drift_plan,
SYS["planner"]); both run_task functions read them at call time, so all five conditions see the same change.

    python experiments/a4_latent.py replaycheck     # offline: A3b H-dragon replay (before any live call)
    python experiments/a4_latent.py tasks           # offline: print the 16 generated tasks
    python experiments/a4_latent.py smoke COND      # seed 999
    python experiments/a4_latent.py run [CONDS]     # seeds 400-415, resumable
"""

import json
import os
import random
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import a1_agents as A                      # noqa: E402
import a3b_hologram as H                   # noqa: E402
from a3b_hdragon import HDragon            # noqa: E402

SEEDS = list(range(400, 416))
CONDS = ["Hd", "P", "D", "E", "A"]
RES = os.path.join(A.ROOT, "results", "a4_results.jsonl")
TRANS = os.path.join(A.ROOT, "results", "a4_transcripts.jsonl")
PREFIX = "Worker-computed: "
COMPUTABLE = ["replicas", "retries", "timeout_ms", "owner", "region"]
DRIFT_READ = {4: 0, 6: 0, 8: 1, 10: 1, 12: 2, 13: 2}       # compute step -> drift key index
CLEAN = (1, 2)
PLANNER_A4 = (A.SYS["planner"] + " Exception: a request that begins with 'Worker-computed:' reads values for which "
              "only the worker's state is authoritative. Do not look up, compute or state any value for it: restate "
              "its operation word for word (without the prefix), and the worker computes the result from its own "
              "state.")
CHECKER_A4 = (A.SYS["checker"] + " For a request that begins with 'Worker-computed:', the worker's state is "
              "authoritative for the values it reads: verify that exactly the named target key changed and nothing "
              "else, and do not reject because you cannot see the source values.")   # amendment 1
_tl = threading.local()
_lock = threading.Lock()


class Truth(dict):
    """Ground-truth final state. `final == truth` in run_task calls Truth.__eq__ first (subclass priority), which
    records the authoritative final state without touching the frozen harness."""

    def __eq__(self, other):
        self.seen.append(dict(other))
        return dict.__eq__(self, other)

    __hash__ = None


# ---------------------------------------------------------------- A4 task generator

def _num(v):
    return int(v)


def compute_op(rng, state, frozen, src, wrong, field):
    """One compute request reading src. wrong = drifted value of src (None for a clean compute).
    Returns (text, target, f(state), f(state with src=wrong) or None) or None if impossible."""
    tgt_same = [k for k in state if k.endswith("." + field) and k != src and k not in frozen]
    tgt_log = [k for k in state if k.endswith(".log_level") and k not in frozen]
    ops = ["copy"]
    if field in ("replicas", "retries"):
        ops += ["add", "sum"]
    if field == "timeout_ms":
        ops += ["add"]
    if field in ("region", "owner"):
        ops += ["xref", "xref"]
    rng.shuffle(ops)
    for op in ops:
        for _ in range(20):
            if op == "xref":
                if not tgt_log:
                    break
                t = rng.choice(sorted(tgt_log))
                x = rng.choice([state[src], wrong]) if wrong else rng.choice(
                    [state[src]] + [v for v in (A.OWNERS if field == "owner" else A.REGIONS) if v != state[src]])
                l1, l2 = rng.sample(A.LEVELS, 2)
                f = lambda v: l1 if v == x else l2      # noqa: E731
                text = f"If {src} is {x}, set {t} to {l1}; otherwise set it to {l2}."
                sources = [src]
            else:
                if not tgt_same:
                    break
                t = rng.choice(sorted(tgt_same))
                if op == "copy":
                    f = lambda v: v                      # noqa: E731
                    text = f"Make {t} equal to {src}."
                    sources = [src]
                elif op == "add" and field == "timeout_ms":
                    f = lambda v: str(_num(v) + 500)     # noqa: E731
                    text = f"Set {t} to {src} plus 500."
                    sources = [src]
                elif op == "add":
                    d = rng.randint(1, 2)
                    f = lambda v, d=d: str(min(_num(v) + d, 9))   # noqa: E731
                    text = f"Set {t} to {src} plus {d}, capped at 9."
                    sources = [src]
                else:
                    s2c = [k for k in state if k.endswith("." + field) and k not in (src, t) and k not in DRIFTKEYS(frozen)]
                    if not s2c:
                        break
                    s2 = rng.choice(sorted(s2c))
                    f = lambda v, s2=s2: str(min(_num(v) + _num(state[s2]), 9))   # noqa: E731
                    text = f"Set {t} to {src} + {s2}, capped at 9."
                    sources = [src, s2]
            ft = f(state[src])
            fw = f(wrong) if wrong else None
            if ft == state[t] or (wrong and fw == ft) or not A.valid_line(f"{t} = {ft}"):
                continue
            return {"op": op, "text": text, "target": t, "sources": sources, "f_true": ft, "f_wrong": fw}
    return None


def DRIFTKEYS(frozen):
    return frozen.get("__drift__", set()) if isinstance(frozen, dict) else set()


def normal_op(rng, state, frozen):
    """A3's request kinds, resolved by the planner, restricted to non-frozen keys. Returns (text, touched)."""
    keys = [k for k in state if k not in frozen]
    kind = rng.choice(["set", "set", "inc", "double", "owner", "add", "delete", "cond", "copy"])
    if kind in ("inc", "double"):
        cand = [k for k in keys if k.endswith(("replicas", "retries"))]
        if not cand:
            kind = "set"
    if kind == "owner":
        bad = {state[k] for k in state if k in frozen and k.endswith(".owner")}
        present = sorted({v for k, v in state.items() if k.endswith(".owner")} - bad)
        if not present:
            kind = "set"
    if kind == "cond":
        s = rng.choice(A.SERVICES)
        if f"{s}.region" not in state or f"{s}.log_level" not in state or f"{s}.log_level" in frozen:
            kind = "set"
    if kind == "copy":
        f = rng.choice(["timeout_ms", "retries", "replicas"])
        srcs = [s for s in A.SERVICES if f"{s}.{f}" in state]
        dsts = [s for s in srcs if f"{s}.{f}" not in frozen]
        if len(srcs) < 2 or not dsts:
            kind = "set"
    if kind == "set":
        k = rng.choice(keys); f = k.split(".")[1]; v = A.rand_value(f, rng)
        while v == state[k]:
            v = A.rand_value(f, rng)
        text = rng.choice([f"Set {k} to {v}.", f"Change the {f} of {k.split('.')[0]} to {v}.",
                           f"{k.split('.')[0]} needs {f} = {v} from now on."])
        state[k] = v; return text
    if kind in ("inc", "double"):
        k = rng.choice(cand); old = int(state[k])
        if kind == "inc":
            d = rng.randint(1, 2); new = min(old + d, 9); text = f"Increase {k} by {d} (cap at 9)."
        else:
            new = min(old * 2, 9); text = f"Double {k}, capped at 9."
        state[k] = str(new); return text
    if kind == "owner":
        a = rng.choice(present); b = rng.choice([o for o in A.OWNERS if o != a])
        for k in [k for k, v in state.items() if k.endswith(".owner") and v == a]:
            state[k] = b
        return f"Everything owned by {a} is now owned by {b}."
    if kind == "add":
        s = rng.choice(A.SERVICES); f = rng.choice(["max_conn", "tier"]); k = f"{s}.{f}"
        v = A.rand_value(f, rng)
        text = f"Set {k} to {v}." if k in state else f"Add a new line {k} = {v} at the end."
        state[k] = v; return text
    if kind == "delete":
        k = rng.choice(keys); del state[k]; return f"Remove the line {k} entirely."
    if kind == "cond":
        r = rng.choice(A.REGIONS); l1, l2 = rng.sample(A.LEVELS, 2)
        state[f"{s}.log_level"] = l1 if state[f"{s}.region"] == r else l2
        return f"If {s}.region is {r}, set {s}.log_level to {l1}; otherwise set it to {l2}."
    b = rng.choice(dsts); a = rng.choice([s for s in srcs if s != b])
    state[f"{b}.{f}"] = state[f"{a}.{f}"]
    return f"Make {b}.{f} equal to {a}.{f}."


def make_task(seed):
    rng = random.Random(seed)
    state = {f"{s}.{f}": A.rand_value(f, rng) for s in A.SERVICES for f in A.FIELDS}   # A3's initial state
    init = dict(state)
    g = random.Random(seed * 7 + 1)
    for _ in range(200):                                   # draw drift keys until every compute is constructible
        trial = _build(seed, dict(init), g)
        if trial:
            return trial
    raise RuntimeError(f"no A4 task for seed {seed}")


def _build(seed, state, g):
    init = dict(state)
    cand = sorted(k for k in state if k.split(".")[1] in COMPUTABLE)
    dk = g.sample(cand, 3)
    drift = []
    for k in dk:
        f = k.split(".")[1]; w = A.rand_value(f, g)
        while w == state[k]:
            w = A.rand_value(f, g)
        drift.append((k, w))
    frozen = {"__drift__": set(dk)}
    for k in dk:
        frozen[k] = 1
    reqs, truths, computes = [], [dict(state)], []
    for st in range(A.STEPS):
        if st in DRIFT_READ or st in CLEAN:
            if st in DRIFT_READ:
                src, wrong = drift[DRIFT_READ[st]]
            else:
                pool = sorted(k for k in state if k.split(".")[1] in COMPUTABLE and k not in frozen)
                src, wrong = g.choice(pool), None
            c = compute_op(g, state, frozen, src, wrong, src.split(".")[1])
            if c is None:
                return None
            state[c["target"]] = c["f_true"]; frozen[c["target"]] = 1
            c.update({"step": st, "drift_idx": DRIFT_READ.get(st), "kind": "drift" if wrong else "clean"})
            computes.append(c)
            reqs.append(PREFIX + c["text"])
        else:
            reqs.append(normal_op(g, state, frozen))
        truths.append(dict(state))
    for k, w in drift:
        assert all(t[k] == init[k] for t in truths)
    final = Truth(state)
    final.seen = []
    return {"seed": seed, "init": init, "requests": reqs, "touched": [[] for _ in reqs], "final": final,
            "truths": truths, "drift": drift, "computes": computes}


def drift_plan(task, truths):
    return {4: task["drift"][0], 8: task["drift"][1], 12: task["drift"][2]}


def _make_task_tl(seed):
    t = make_task(seed)
    _tl.task = t
    return t


def patch():
    A.make_task = _make_task_tl
    A.drift_plan = drift_plan
    A.SYS["planner"] = PLANNER_A4
    A.SYS["checker"] = CHECKER_A4


# ---------------------------------------------------------------- one run (live or replay)

def run_one(cond, seed, tag=None):
    if cond == "Hd":
        res = H.run_task(HDragon(), seed, tag=tag)
        if res.get("tag") is None:
            res["tag"] = tag
    else:
        res = A.run_task(cond, seed, tag=tag)
    t = _tl.task
    res["final_state"] = t["final"].seen[0]          # authoritative final state (first `final == truth`)
    return res


def replay(rec, fn):
    """Feed recorded LLM outputs back in order; every prompt must be identical."""
    queue = list(rec["calls"])
    real = A.llm

    def fake(system, prompt, schema=None, log=None):
        c = queue.pop(0)
        assert c["prompt"] == prompt and c["system"] == system[:40], "replay diverged"
        r = {k: c[k] for k in ("in", "cache_w", "cache_r", "out", "sec", "api_ms", "turns", "cost")}
        if log is not None:
            log.append(c)
        return c["text"], c["structured"], r

    A.llm = fake
    try:
        res = fn()
    finally:
        A.llm = real
    assert not queue, "unused recorded calls"
    res["wall_sec"] = sum(c["sec"] for c in rec["calls"])
    res["replayed"] = True
    return res


# ---------------------------------------------------------------- replay check (before any live call)

CHECK = ("success", "line_acc", "replica_success", "final_errors", "steps_failed", "n_calls", "channel_tok",
         "channel_bpe", "channel_bytes", "billed_tok", "out_tok", "drift")


def replaycheck():
    import subprocess
    import tempfile
    assert A.make_task is not _make_task_tl
    rec = {r["seed"]: r for r in map(json.loads, open(os.path.join(A.ROOT, "results", "a3b_results_hd.jsonl")))}
    os.environ["A_TRANSCRIPTS"] = os.devnull
    n, bad = 0, []
    for line in open(os.path.join(A.ROOT, "results", "a3b_transcripts_hd.jsonl")):
        t = json.loads(line)
        r = replay(t, lambda: H.run_task(HDragon(), t["seed"], tag=t["tag"]))
        o = rec[t["seed"]]
        n += 1
        for k in CHECK:
            if k == "drift":
                drop = ("recovery_sec",)
                a = [{x: y for x, y in e.items() if x not in drop} for e in r[k]]
                b = [{x: y for x, y in e.items() if x not in drop} for e in o[k]]
                if a != b:
                    bad.append((t["seed"], k))
            elif r[k] != o[k]:
                bad.append((t["seed"], k))
    del os.environ["A_TRANSCRIPTS"]
    diff = subprocess.run(["git", "-C", A.ROOT, "diff", "main", "--", "experiments/a1_agents.py", "experiments/a3_run.py",
                           "experiments/a3b_hologram.py", "experiments/a3b_hdragon.py"],
                          capture_output=True, text=True).stdout
    # a3b_analyse unchanged, in a clean worktree of HEAD, must give A3b's results hash
    wt = tempfile.mkdtemp(prefix="a4wt_")
    subprocess.run(["git", "-C", A.ROOT, "worktree", "add", "--detach", wt, "HEAD"], check=True, capture_output=True)
    try:
        p = subprocess.run([sys.executable, os.path.join(wt, "experiments", "a3b_analyse.py")], capture_output=True,
                           text=True, cwd=wt)
        sha = json.load(open(os.path.join(wt, "results", "a3b_hologram.json")))["results_sha256"]
        tail = p.stdout.strip().splitlines()[-1] if p.stdout.strip() else p.stderr[-400:]
    finally:
        subprocess.run(["git", "-C", A.ROOT, "worktree", "remove", "--force", wt], capture_output=True)
    want = "0ae0d0315ac392184128252c5d8b57eabfc9c977f10eb6e02b6f7eda20507120"
    out = {"hd_runs_replayed": n, "hd_mismatches": bad, "frozen_files_diff_vs_main_empty": diff == "",
           "a3b_analyse_sha": sha, "expected_sha": want, "sha_match": sha == want, "a3b_analyse_last_line": tail,
           "pass": not bad and diff == "" and sha == want and n == 16}
    json.dump(out, open(os.path.join(A.ROOT, "results", "a4_replay_check.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))
    return out["pass"]


# ---------------------------------------------------------------- runner

def main_run(conds):
    patch()
    done = {}
    if os.path.exists(RES):
        for line in open(RES):
            r = json.loads(line); done[(r["cond"], r["seed"])] = r
    os.environ["A_TRANSCRIPTS"] = os.devnull            # replays must not duplicate transcripts
    if os.path.exists(TRANS):
        for line in open(TRANS):
            t = json.loads(line)
            if (t["cond"], t["seed"]) not in done and t["seed"] in SEEDS:
                r = replay(t, lambda: run_one(t["cond"], t["seed"]))
                done[(r["cond"], r["seed"])] = r
                with open(RES, "a") as f:
                    f.write(json.dumps(r) + "\n")
    os.environ["A_TRANSCRIPTS"] = TRANS
    todo = [(c, s) for s in SEEDS for c in conds if (c, s) not in done]
    print(f"loaded {len(done)}, live {len(todo)}", flush=True)
    with ThreadPoolExecutor(int(os.environ.get("A4_WORKERS", "8"))) as ex:
        futs = [ex.submit(run_one, c, s) for c, s in todo]
        for fu in as_completed(futs):
            r = fu.result(); r["replayed"] = False; done[(r["cond"], r["seed"])] = r
            with _lock:
                with open(RES, "a") as f:
                    f.write(json.dumps(r) + "\n")
    runs = [done[(c, s)] for s in SEEDS for c in CONDS if (c, s) in done]
    json.dump({"model": A.MODEL, "runs": runs}, open(os.path.join(A.ROOT, "results", "a4_runs.json"), "w"), indent=1)
    print("wrote a4_runs.json", len(runs))


if __name__ == "__main__":
    if sys.argv[1] == "replaycheck":
        sys.exit(0 if replaycheck() else 1)
    elif sys.argv[1] == "tasks":
        for s in ([int(x) for x in sys.argv[2:]] or SEEDS + [999]):
            t = make_task(s)
            print(f"== seed {s} drift {t['drift']}")
            for i, r in enumerate(t["requests"]):
                c = next((c for c in t["computes"] if c["step"] == i), None)
                print(f"  {i:2d} {r}" + (f"   [true {c['f_true']} | drifted {c['f_wrong']}]" if c else ""))
    elif sys.argv[1] == "smoke":
        patch()
        os.environ["A_TRANSCRIPTS"] = os.path.join(A.ROOT, "results", "a4_smoke_transcripts.jsonl")
        r = run_one(sys.argv[2], 999, tag="smoke")
        print(json.dumps({k: v for k, v in r.items() if k not in ("per_call", "per_msg")}, indent=1))
    elif sys.argv[1] == "run":
        main_run(sys.argv[2].split(",") if len(sys.argv) > 2 else CONDS)
