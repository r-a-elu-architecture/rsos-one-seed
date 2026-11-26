"""SPHERE1: seven nodes of the seed connected in one run. Predictions: PREREG_SPHERE1.md (sha256 d68b2c49…f8,
commit edd9943), sealed before this file."""
import copy
import json
import math
import multiprocessing as mp
import os
import random
import sqlite3
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SEED = os.path.abspath(os.path.join(HERE, ".."))
for sub in ("ops", "engine", "engine2", "protocol"):
    sys.path.insert(0, os.path.join(SEED, sub))
import ops1  # noqa: E402
import engine2 as E2  # noqa: E402
import protocol_v0 as P  # noqa: E402

H = E2.H; E1 = E2.E1
FAM = {"key": 1, "pair": 2, "condition": 50, "scan": 300}
N_OPS = 400


def rates(counts):
    return {f: round(a / b, 5) for f, (a, b) in counts.items()}


def bound(eps, n):
    return 1 - (1 - eps) ** n


# ------------------------------------------------------------------------------------------------ nodes
def n1_memory(g):
    c = {f: [0, 0] for f in FAM}
    for fam, n in FAM.items():
        for _ in range(200):
            s = int(g.integers(900, 904)); ff, fv, R, codes, h = E1.store(s, 0)
            dead = np.zeros(H.D, bool); dead[g.choice(H.D, int(0.3 * H.D), replace=False)] = True
            v, _, _ = H.plain_read(h * (~dead).astype(np.int8), R, ff, codes)
            idx = np.where(ff == g.integers(6))[0] if fam == "condition" else g.choice(len(ff), n, replace=False)
            c[fam][0] += int((v[idx] != fv[idx]).any()); c[fam][1] += 1
    return c


def n2_network(g):
    ch = ops1.GE(g); c = {f: [0, 0] for f in FAM}
    for fam, n in FAM.items():
        for _ in range(N_OPS):
            for _ in range(10):
                ch.send()
            c[fam][0] += int(not all(ops1.net_element(ch) for _ in range(n))); c[fam][1] += 1
    return c, ch


def n3_ledger(g):
    L = ops1.Ledger(g); c = {f: [0, 0] for f in FAM}
    for fam, n in FAM.items():
        for _ in range(N_OPS):
            for _ in range(10):
                L.epoch()
            c[fam][0] += int(not all(L.epoch() for _ in range(n))); c[fam][1] += 1
    return c


DB = "/tmp/sphere1_db.sqlite"


def _writer(stop):
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


def n4_database(g):
    if os.path.exists(DB):
        os.remove(DB)
    c0 = sqlite3.connect(DB); c0.execute("PRAGMA journal_mode=DELETE"); c0.execute("create table kv(k text primary key, v text)")
    c0.executemany("insert into kv values(?,?)", [(f"k{i}", str(i)) for i in range(300)]); c0.commit(); c0.close()
    stop = mp.Event(); p = mp.Process(target=_writer, args=(stop,)); p.start(); time.sleep(0.5)
    rd = sqlite3.connect(DB, timeout=0, isolation_level=None)
    jobs = [f for f in FAM for _ in range(N_OPS)]; random.Random(7).shuffle(jobs)
    c = {f: [0, 0] for f in FAM}
    rk = random.Random(11)
    for fam in jobs:
        fail = False
        for k in rk.sample(range(300), FAM[fam]):
            try:
                rd.execute("select v from kv where k=?", (f"k{k}",)).fetchone()
            except sqlite3.OperationalError:
                fail = True; break
        c[fam][0] += int(fail); c[fam][1] += 1
    stop.set(); p.join()
    return c


def n5_chem_read(g):
    return g.poisson(4) > 0


def n5_chemistry(g):
    c = {f: [0, 0] for f in FAM}
    for fam, n in FAM.items():
        for _ in range(N_OPS):
            c[fam][0] += int(not all(n5_chem_read(g) for _ in range(n))); c[fam][1] += 1
    return c


def n6_orbit(g):
    c = {f: [0, 0] for f in FAM}
    for fam, n in FAM.items():
        for _ in range(N_OPS):
            t0 = g.uniform(0, 100)
            fail = any(((t0 + i * 0.01) % 100) >= 70 for i in range(n))
            c[fam][0] += int(fail); c[fam][1] += 1
    return c


def n7_slots(g):
    c = {f: [0, 0] for f in FAM}
    field_elems = [list(range(f, 300, 6)) for f in range(6)]
    for fam, n in FAM.items():
        for _ in range(N_OPS):
            down = set(int(x) for x in g.choice(300, 10, replace=False))
            idx = field_elems[g.integers(6)] if fam == "condition" else [int(x) for x in g.choice(300, n, replace=False)]
            c[fam][0] += int(any(i in down for i in idx)); c[fam][1] += 1
    return c


def classify(r):
    eps = r["key"]
    return "element" if r["pair"] - eps >= eps / 2 else "time"


# ------------------------------------------------------------------------------------------------ S2 cross-node healing
def s2():
    g = np.random.default_rng(2020)
    a = {"alone": [0, 0], "with_N3": [0, 0]}
    for s in range(1020, 1028):
        ff, fv, R, codes, h = E1.store(s, 1)
        alive = ~H.erase(s, 0.95, 0)
        known = g.random(len(ff)) < 0.30
        idxs = {fi: np.where(ff == fi)[0] for fi in range(6)}

        def prior(Pd):
            lp = {}
            for fi, ix in idxs.items():
                arr = np.zeros((len(ix), E2.NV[H.FIELDS[fi]]))
                for r, k in enumerate(ix):
                    if known[k]:
                        arr[r, :] = -30.0; arr[r, fv[k]] = 0.0
                lp[fi] = arr
            return lp
        v0, _, _ = E2.soft_read(h, alive, R, ff, codes)
        v1, _, _ = E2.soft_read(h, alive, R, ff, codes, prior=prior)
        u = ~known
        a["alone"][0] += int((v0[u] == fv[u]).sum()); a["alone"][1] += int(u.sum())
        a["with_N3"][0] += int((v1[u] == fv[u]).sum()); a["with_N3"][1] += int(u.sum())
    return {k: round(x / y, 5) for k, (x, y) in a.items()}


# ------------------------------------------------------------------------------------------------ S3 DISAGREE on chemistry
def s3():
    g = np.random.default_rng(3030)
    err = flg = hit = 0
    for _ in range(4000):
        v = int(g.integers(10))
        read = lambda: int(np.clip(round((g.poisson(10 + 12 * v) - 10) / 12), 0, 9))
        r1, r2 = read(), read()
        e = r1 != v; f = r1 != r2
        err += e; flg += f; hit += e and f
    return {"recall": round(hit / err, 5), "precision": round(hit / flg, 5), "errors": int(err)}


# ------------------------------------------------------------------------------------------------ S4 sphere-level zoom
def s4_sphere(g, ch, eps):
    L = ops1.Ledger(g); fail = 0; n = 400
    for _ in range(n):
        s = int(g.integers(900, 904)); ff, fv, R, codes, h = E1.store(s, 0)
        dead = np.zeros(H.D, bool); dead[g.choice(H.D, int(0.3 * H.D), replace=False)] = True
        v, _, _ = H.plain_read(h * (~dead).astype(np.int8), R, ff, codes); k = int(g.integers(len(ff)))
        ok_mem = v[k] == fv[k]
        for _ in range(10):
            L.epoch()
        ok = ok_mem and L.epoch() and n5_chem_read(g) and all(ops1.net_element(ch) for _ in range(3))
        fail += int(not ok)
    b = 1 - (1 - eps["N1"]) * (1 - eps["N3"]) * (1 - eps["N5"]) * (1 - eps["N2"]) ** 3
    return {"observed": round(fail / n, 5), "bound": round(b, 5)}


# ------------------------------------------------------------------------------------------------ S5/S6 protocol
def s5_s6(g, ch):
    base = SC_BOOK
    keys = sorted(base); nodes = ["N1", "N2", "N3", "N4", "N5", "N6", "N7"]
    safe = lambda k, v: v in H.VALUES[k.split(".")[1]]
    st = {"legit": 0, "delivered": 0, "wrong": 0, "legit_refused_clean": 0, "inj": 0, "inj_refused": 0}
    seen_by = {n: set() for n in nodes}
    accepted_envs = []
    for m in range(2000):
        snd, rcv = g.choice(nodes, 2, replace=False)
        roll = g.random()
        k1, k2 = keys[g.integers(len(keys))], keys[g.integers(len(keys))]
        f1 = k1.split(".")[1]
        if roll < 0.02:
            ops = [{"op": "SET", "key": k1, "value": "999"}]; kind = "out_of_range"
        elif roll < 0.03:
            ops = [{"op": "WIPE"}]; kind = "unknown_op"
        elif roll < 0.04 and accepted_envs:
            kind = "replay"
        else:
            kind = "legit"
            ops = [{"op": "SET", "key": k1, "value": H.VALUES[f1][g.integers(len(H.VALUES[f1]))]}]
        if kind == "replay":
            env0, rbook, rnode = accepted_envs[g.integers(len(accepted_envs))]
            st["inj"] += 1
            _, verdict = P.receive(dict(rbook), env0, safe, seen_by[rnode])
            st["inj_refused"] += int(verdict != "accepted")
            continue
        receiver_book = dict(base)
        if g.random() < 0.05:
            kd = keys[g.integers(len(keys))]; fd = kd.split(".")[1]; vals = H.VALUES[fd]
            receiver_book[kd] = vals[(vals.index(receiver_book[kd]) + 1) % len(vals)]
        env = P.envelope(snd, rcv, "sphere", base, ops, m, safe)
        intended, _ = P.apply(base, ops, safe)
        delivered = False; inj_accepted = False
        if kind != "legit":
            st["inj"] += 1
        else:
            st["legit"] += 1
        for attempt in range(4):
            e = copy.deepcopy(env); tampered = False
            for hop in range(3):
                if not ops1.net_element(ch):
                    e = None; break
                if g.random() < 0.05:
                    e["seq"] = e["seq"] + 1; tampered = True
            if e is None:
                continue
            new, verdict = P.receive(receiver_book, e, safe, seen_by[rcv])
            if verdict == "accepted":
                if kind != "legit":
                    inj_accepted = True; break
                delivered = True; st["wrong"] += int(new != intended)
                accepted_envs.append((e, receiver_book, rcv)); break
            if kind == "legit" and not tampered and verdict not in ("refused:not_ready",):
                st["legit_refused_clean"] += 1
            if verdict == "refused:not_ready":
                receiver_book = dict(base)                         # verified sync from the sender's book
        if kind == "legit":
            st["delivered"] += int(delivered)
        else:
            st["inj_refused"] += int(not inj_accepted)
    st["delivered_share"] = round(st["delivered"] / st["legit"], 5)
    return st


SC_BOOK = H.SC.make_task(900)["init"]


def main():
    g = np.random.default_rng(1120)
    out = {"nodes": {}}
    c1 = n1_memory(g); out["nodes"]["N1"] = rates(c1); print("N1", out["nodes"]["N1"], flush=True)
    c2, ch = n2_network(g); out["nodes"]["N2"] = rates(c2)
    out["nodes"]["N3"] = rates(n3_ledger(g))
    out["nodes"]["N4"] = rates(n4_database(g))
    out["nodes"]["N5"] = rates(n5_chemistry(g))
    out["nodes"]["N6"] = rates(n6_orbit(g))
    out["nodes"]["N7"] = rates(n7_slots(g))
    for nd, r in out["nodes"].items():
        r["class"] = classify(r)
        r["bound"] = {f: round(bound(r["key"], n), 5) for f, n in FAM.items()}
        print(nd, r, flush=True)
    eps = {nd: out["nodes"][nd]["key"] for nd in out["nodes"]}
    out["S2"] = s2(); print("S2", out["S2"], flush=True)
    out["S3"] = s3(); print("S3", out["S3"], flush=True)
    out["S4_sphere"] = s4_sphere(g, ch, eps); print("S4", out["S4_sphere"], flush=True)
    out["S5_S6"] = s5_s6(g, ch); print("S5S6", out["S5_S6"], flush=True)
    N = out["nodes"]
    v = {}
    v["S1"] = (N["N5"]["class"] == "element" and N["N6"]["class"] == "time"
               and abs(N["N5"]["condition"] - N["N5"]["bound"]["condition"]) <= max(0.03, 0.3 * N["N5"]["bound"]["condition"])
               and abs(N["N6"]["scan"] - N["N6"]["key"]) <= 0.03)
    v["S2"] = out["S2"]["with_N3"] >= out["S2"]["alone"] + 0.05
    v["S3"] = out["S3"]["recall"] >= 0.90 and out["S3"]["precision"] >= 0.45
    v["S4"] = all(N[nd][f] <= N[nd]["bound"][f] + 0.03 for nd in ("N1", "N2", "N3", "N4", "N5", "N6") for f in FAM) \
        and out["S4_sphere"]["observed"] <= out["S4_sphere"]["bound"] + 0.03
    p = out["S5_S6"]
    v["S5"] = p["wrong"] == 0 and p["delivered_share"] >= 0.99
    v["S6"] = p["inj_refused"] == p["inj"] and p["legit_refused_clean"] == 0
    v["S8"] = (N["N7"]["condition"] > N["N7"]["bound"]["condition"] and N["N7"]["scan"] > N["N7"]["bound"]["scan"]
               and all(N[nd][f] <= N[nd]["bound"][f] + 0.03 for nd in ("N1", "N2", "N3", "N4", "N5", "N6")
                       for f in ("condition", "scan")))
    out["verdicts"] = v
    json.dump(out, open(os.path.join(HERE, "RESULTS_SPHERE1.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
