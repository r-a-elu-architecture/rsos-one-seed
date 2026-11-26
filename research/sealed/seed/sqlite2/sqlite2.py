"""SQLITE2: error-events law on real SQLite. Predictions: PREREG_SQLITE2.md (sealed first)."""
import json
import multiprocessing as mp
import os
import random
import sqlite3
import time

HERE = os.path.dirname(os.path.abspath(__file__))
DB = "/tmp/sqlite2_db.sqlite"
FAM = [1, 2, 50, 300]


def writer(stop):
    r = random.Random(1); w = sqlite3.connect(DB, timeout=5, isolation_level=None); w.execute("PRAGMA synchronous=OFF")
    while not stop.is_set():
        try:
            w.execute("BEGIN IMMEDIATE"); w.execute("update kv set v=? where k=?", (str(r.random()), f"k{r.randrange(300)}"))
            w.execute("COMMIT")
        except sqlite3.OperationalError:
            try:
                w.execute("ROLLBACK")
            except sqlite3.OperationalError:
                pass
        time.sleep(0.01)


def main():
    if os.path.exists(DB):
        os.remove(DB)
    c = sqlite3.connect(DB); c.execute("PRAGMA journal_mode=DELETE"); c.execute("create table kv(k text primary key, v text)")
    c.executemany("insert into kv values(?,?)", [(f"k{i}", str(i)) for i in range(300)]); c.commit(); c.close()
    stop = mp.Event(); p = mp.Process(target=writer, args=(stop,)); p.start(); time.sleep(0.5)
    rd = sqlite3.connect(DB, timeout=0, isolation_level=None)
    g = random.Random(2026)
    jobs = [(n, s) for n in FAM for s in ("fast", "slow") for _ in range(600)]; g.shuffle(jobs)
    res = {f"{s}|{n}": [0, 0] for n in FAM for s in ("fast", "slow")}
    for n, s in jobs:
        fail = False
        for k in g.sample(range(300), n):
            try:
                rd.execute("select v from kv where k=?", (f"k{k}",)).fetchone()
            except sqlite3.OperationalError:
                fail = True; break
            if s == "slow":
                time.sleep(0.001)
        res[f"{s}|{n}"][0] += int(fail); res[f"{s}|{n}"][1] += 1
    stop.set(); p.join()
    r = {k: round(a / b, 5) for k, (a, b) in res.items()}
    e1 = r["slow|1"]
    bound = {n: round(1 - (1 - e1) ** n, 5) for n in FAM}
    v = {"Q1": abs(r["fast|300"] - r["fast|1"]) <= 0.05,
         "Q2": r["slow|1"] < r["slow|50"] < r["slow|300"] and r["slow|300"] >= r["slow|1"] + 0.20,
         "Q3": all(r[f"slow|{n}"] <= bound[n] + 0.03 for n in (50, 300))}
    out = {"rates": r, "slow_bound": bound, "verdicts": v}
    json.dump(out, open(os.path.join(HERE, "RESULTS_SQLITE2.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
