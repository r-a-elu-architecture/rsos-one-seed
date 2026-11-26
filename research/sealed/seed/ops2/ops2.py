"""OPS2 analysis and run. Predictions: PREREG_OPS2.md (sha256 98bde57f…f1e, commit a103a09), sealed before this file.
Usage: python3 ops2.py"""
import json
import multiprocessing as mp
import os
import random
import sqlite3
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PUB = "/home/claude/rsos-language"


def r1():
    eps = 10 / 7125
    pair_obs, scan_obs = 2 / 1193, 19 / 823
    sc2 = json.load(open(os.path.join(PUB, "results", "sc2.json")))
    flow = sc2["rate_by_kind"]["FLOW"]
    b = lambda n: 1 - (1 - eps) ** n
    return {"eps": round(eps, 6),
            "pair": {"observed": round(pair_obs, 5), "bound": round(b(2), 5), "pass": pair_obs <= b(2)},
            "scan": {"observed": round(scan_obs, 5), "bound_n19": round(b(19), 5), "bound_mean_n122": round(b(122), 5),
                     "pass": scan_obs <= b(19)},
            "R1b_sc2_flow": {"observed": round(flow, 5), "bound_n300": round(b(300), 5), "pass": flow <= b(300)}}


PATH = "/tmp/ops2_db.sqlite"


def writer(seed, stop):
    r = random.Random(seed)
    w = sqlite3.connect(PATH, timeout=5, isolation_level=None); w.execute("PRAGMA synchronous=OFF")
    while not stop.is_set():
        try:
            w.execute("BEGIN IMMEDIATE")
            w.execute("update kv set v=? where k=?", (str(r.random()), f"k{r.randrange(300)}"))
            w.execute("COMMIT")
        except sqlite3.OperationalError:
            try:
                w.execute("ROLLBACK")
            except sqlite3.OperationalError:
                pass
        time.sleep(0.01)


def r2():
    if os.path.exists(PATH):
        os.remove(PATH)
    c = sqlite3.connect(PATH); c.execute("PRAGMA journal_mode=DELETE")
    c.execute("create table kv(k text primary key, v text)")
    c.executemany("insert into kv values(?,?)", [(f"k{i}", str(i)) for i in range(300)]); c.commit(); c.close()
    stop = mp.Event(); p = mp.Process(target=writer, args=(1, stop)); p.start(); time.sleep(0.5)
    rd = sqlite3.connect(PATH, timeout=0, isolation_level=None)
    g = random.Random(2026)
    fams = [1, 2, 5, 20, 300]
    jobs = [(n, mode) for n in fams for mode in ("pull", "blind") for _ in range(1000)]
    g.shuffle(jobs)
    res = {f"{m}|{n}": [0, 0] for n in fams for m in ("pull", "blind")}
    partial_served = 0
    for n, mode in jobs:
        keys = [f"k{i}" for i in g.sample(range(300), n)]
        got, fail = [], False
        if mode == "pull":
            for k in keys:
                try:
                    got.append(rd.execute("select v from kv where k=?", (k,)).fetchone())
                except sqlite3.OperationalError:
                    fail = True; break
        else:
            try:
                got = rd.execute(f"select v from kv where k in ({','.join('?' * n)})", keys).fetchall()
            except sqlite3.OperationalError:
                fail = True
        served = None if fail else got                                   # Law 0: no partial result is served
        partial_served += int(fail and served is not None)
        res[f"{mode}|{n}"][0] += int(fail); res[f"{mode}|{n}"][1] += 1
    stop.set(); p.join()
    rates = {k: round(a / b, 5) for k, (a, b) in res.items()}
    eps = rates["pull|1"]
    bound = {n: round(1 - (1 - eps) ** n, 5) for n in fams}
    v = {
        "S1": rates["pull|1"] < rates["pull|2"] < rates["pull|5"] < rates["pull|20"] <= rates["pull|300"],
        "S2": all(rates[f"pull|{n}"] <= bound[n] + 0.03 for n in (2, 5, 20)),
        "S3": rates["blind|20"] <= 2 * eps and rates["blind|300"] <= 2 * eps and rates["pull|20"] >= 5 * eps,
        "S4": partial_served == 0,
    }
    return {"rates": rates, "eps": eps, "law1_bound": bound, "partial_served": partial_served, "verdicts": v}


if __name__ == "__main__":
    out = {"R1": r1(), "R2": r2()}
    json.dump(out, open(os.path.join(HERE, "RESULTS_OPS2.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))
