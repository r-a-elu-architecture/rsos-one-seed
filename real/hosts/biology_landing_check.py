"""REAL3 biology: CHECK of the REAL2 landing artefact (owner/brief REAL3: "does accuracy really rise when groups are
withheld, on held-out test data?").

REAL2 log (quick_logs/biology_real2.txt): the seed with Law 4 landing withheld almost every class group (resource
105-215 examples against 3300-3600 for the standard) and still reported a higher TEST accuracy on cells 1-2.
This script reruns that seed exactly (seed.run(host, cell, "seed"), unchanged; the host only records the action of
every REAL step, which changes nothing in the run) and then trains, on the same real batches (the batch sampler is the
host's own rng, independent of the action), these controls:
  default     : the standard (small-loss + decay), all 300 x k examples
  rand_same   : at every step the SAME NUMBER of examples the seed landed, chosen uniformly at random from that step's
                real batch (5 repeats, rng [cell, t, rep, 4242])
  small_same  : the same number per step, the lowest-loss ones of the batch (the standard truncated)
  warm_only   : no training after the warm start (2 examples per class; 0 examples landed)
All accuracies are on the clean TEST split (held out; never read by any method), with validation shown beside.
Usage: python3 real/hosts/biology_landing_check.py [cells, e.g. 1-4]"""
import os, sys, time
from multiprocessing import Pool
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seed as S
from biology import Biology

class Rec(Biology):
    def reset(s, cell): s.log = []; return super().reset(cell)
    def step(s, st, a):
        if not st["model"]: s.log.append([int(i) for i in s.valid(st, a)])
        return super().step(st, a)

def acc(h, st):
    D = st["D"]; c = st["clf"]
    return float(np.mean(c.predict(D[4]) == D[5])), float(np.mean(c.predict(D[2]) == D[3]))

def replay(h, cell, pick):
    st = h.reset(cell)
    while not h.done(st): st = h.step(st, pick(st))
    te, va = acc(h, st); return te, va, st["used"]

def one(cell):
    t0 = time.time(); h = Rec(); o = S.run(h, cell, "seed"); acts = h.log; n = [len(a) for a in acts]
    out = [f"{cell} [{'/'.join(o['host'].split('/'))}] seed(landing) test {o['result']:.4f} resource {o['resource']:.0f} "
           f"(REAL2 log check) steps with 0 examples {sum(1 for x in n if x == 0)}/300; examples per step hist "
           f"{dict(sorted({k: n.count(k) for k in set(n)}.items()))}"]
    b = Biology()
    te, va, u = replay(b, cell, lambda st: b.default(st)); out.append(f"{cell} default     test {te:.4f} val {va:.4f} resource {u}")
    te, va, u = replay(b, cell, lambda st: list(acts[st['t']])); out.append(f"{cell} seed_replay test {te:.4f} val {va:.4f} resource {u}")
    rs = []
    for rep in range(5):
        def pick(st, rep=rep):
            k = n[st["t"]]; g = np.random.default_rng([cell, st["t"], rep, 4242])
            return [int(i) for i in g.choice(st["batch"], k, replace=False)] if k else []
        rs.append(replay(b, cell, pick))
    out.append(f"{cell} rand_same   test mean {np.mean([r[0] for r in rs]):.4f} [" + " ".join(f"{r[0]:.4f}" for r in rs)
               + f"] val mean {np.mean([r[1] for r in rs]):.4f} resource {rs[0][2]}")
    te, va, u = replay(b, cell, lambda st: b.default(st)[: n[st["t"]]]); out.append(f"{cell} small_same  test {te:.4f} val {va:.4f} resource {u}")
    te, va, u = replay(b, cell, lambda st: []); out.append(f"{cell} warm_only   test {te:.4f} val {va:.4f} resource {u}")
    return out + [f"{cell} time {time.time() - t0:.0f}s"]

if __name__ == "__main__":
    spec = sys.argv[1] if len(sys.argv) > 1 else "1-4"
    cells = [c for p in spec.split(",") for c in (range(int(p.split("-")[0]), int(p.split("-")[1]) + 1) if "-" in p else [int(p)])]
    with Pool(min(len(cells), 2)) as p:
        for lines in p.imap(one, cells): print("\n".join(lines), flush=True)
