"""OPS1: seed operators executed under Law 0; Law 1 and Law 2 on three hosts (layer 2).
Predictions: PREREG_OPS1.md, sha256 c55a9b2b56a92c8138b83c8883d39121fad43517082e86a368c3230094fe013f, commit d851821,
sealed before this file. Usage: python3 ops1.py part1 | part2 | report"""
import hashlib
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOTS = os.path.abspath(os.path.join(HERE, "..", "..", "roots"))
sys.path.insert(0, ROOTS)
import t2c as H  # noqa: E402  (hologram store and readers; codebooks identical to T2c)

SC = H.SC
SCENES = list(range(900, 916))


# ------------------------------------------------------------------------------------------------ Law 0 monitor
class Monitor:
    """Every effect passes here before it takes effect. `violation` is the ground truth (injected or not)."""

    def __init__(self):
        self.c = {}

    def gate(self, op, allowed, violation):
        k = self.c.setdefault(op, {"inj": 0, "inj_refused": 0, "legit": 0, "legit_refused": 0})
        if violation:
            k["inj"] += 1; k["inj_refused"] += int(not allowed)
        else:
            k["legit"] += 1; k["legit_refused"] += int(not allowed)
        return allowed


MON = Monitor()


def in_range(key, val):
    return val in H.VALUES[key.split(".")[1]]


def book_root(book):
    return hashlib.sha256(json.dumps(book, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


# ------------------------------------------------------------------------------------------------ O1 CARRY + READY
def o1(n_msgs=2000):
    g = np.random.default_rng(101)
    base = SC.make_task(900)["init"]
    keys = sorted(base)
    wrong = delivered = refusals = n_bad = 0
    for m in range(n_msgs):
        sender = dict(base)
        receiver = dict(base)
        if g.random() < 0.05:                                       # receiver's book outdated (drift)
            k = keys[g.integers(len(keys))]; f = k.split(".")[1]
            receiver[k] = H.VALUES[f][(H.VALUES[f].index(receiver[k]) + 1) % len(H.VALUES[f])]
        chg = [keys[i] for i in g.choice(len(keys), 3, replace=False)]
        entries = {}
        for k in chg:
            f = k.split(".")[1]; entries[k] = H.VALUES[f][g.integers(len(H.VALUES[f]))]
        bad_sender = g.random() < 0.02                              # an out-of-range value from the sender
        if bad_sender:
            entries[chg[0]] = "999999"; n_bad += 1
        sender.update(entries)
        msg_root = book_root(sender)
        ok = False
        for attempt in range(4):                                    # first send + up to 3 resends
            ent = dict(entries)
            tampered = False
            for hop in range(3):
                if g.random() < 0.05:
                    k = chg[g.integers(len(chg))]; f = k.split(".")[1]
                    if in_range(k, ent[k]):
                        ent[k] = H.VALUES[f][(H.VALUES[f].index(ent[k]) + 1) % len(H.VALUES[f])]
                    tampered = True
            trial = dict(receiver); trial.update(ent)
            range_ok = all(in_range(k, v) for k, v in ent.items())
            verified = book_root(trial) == msg_root
            violation = tampered or bad_sender or trial != sender
            allowed = MON.gate("O1_open", verified and range_ok, violation)
            if allowed:
                receiver = trial; ok = True
                wrong += int(receiver != sender)
                break
            refusals += 1
            if attempt == 0 and not bad_sender:                     # receiver syncs its book (diff by key)
                for k in keys:
                    if k not in entries and receiver[k] != base[k]:
                        receiver[k] = base[k]
        delivered += int(ok and not bad_sender)
    return {"messages": n_msgs, "bad_sender": n_bad, "delivered_legit": delivered,
            "delivered_share": round(delivered / (n_msgs - n_bad), 5), "wrong_adoptions": wrong, "refusals": refusals}


# ------------------------------------------------------------------------------------------------ O2 LAND
def o2():
    arm = H.ARMS["LivNR"]
    out = {"landings": 0, "on_flipped": 0, "flipped": 0, "recovered": 0, "acc_before": [0, 0], "acc_after": [0, 0]}
    for seed in SCENES:
        fo, ff, fv = H.facts(seed)
        R, codes, h = H.holo_store(arm, fo, ff, fv)
        g = np.random.default_rng([seed, 202])
        fl = np.zeros(H.D, bool); fl[g.choice(H.D, H.D // 10, replace=False)] = True
        hf = h.copy(); hf[fl] *= -1
        alive = np.ones(H.D, bool)
        v, w, _ = H.holo_read(arm, hf, alive, R, ff, codes)
        out["acc_before"][0] += int((v == fv).sum()); out["acc_before"][1] += len(fv)
        S = (w @ H.bindings(R, ff, v, codes).astype(np.int32)).astype(np.float64)
        rec = H.sgn(S)
        need = (rec != hf) & (np.abs(S) >= S.std())                  # contradicted with margin: the measured need
        cand = np.where(need)[0]
        for p in cand:                                               # legitimate landings
            if MON.gate("O2_land", bool(need[p]), False):
                hf[p] = rec[p]
        for p in g.choice(np.where(~need)[0], 100, replace=False):  # injected: landing where nothing is needed
            MON.gate("O2_land", bool(need[p]), True)
        out["landings"] += len(cand); out["on_flipped"] += int(fl[cand].sum()); out["flipped"] += int(fl.sum())
        out["recovered"] += int((hf[fl] == h[fl]).sum())
        v2, _, _ = H.holo_read(arm, hf, alive, R, ff, codes)
        out["acc_after"][0] += int((v2 == fv).sum()); out["acc_after"][1] += len(fv)
    return {"precision": round(out["on_flipped"] / out["landings"], 5),
            "recall": round(out["on_flipped"] / out["flipped"], 5),
            "acc_before": round(out["acc_before"][0] / out["acc_before"][1], 5),
            "acc_after": round(out["acc_after"][0] / out["acc_after"][1], 5), "landings": out["landings"]}


# ------------------------------------------------------------------------------------------------ O3 ISOLATE
def merkle(leaves):
    lv = [[hashlib.sha256(x.encode()).digest() for x in leaves]]
    while len(lv[-1]) > 1:
        a = lv[-1]; lv.append([hashlib.sha256(a[i] + a[i + 1]).digest() for i in range(0, len(a), 2)])
    return lv


def o3():
    g = np.random.default_rng(303)
    res = {}
    for k in (1, 4, 16):
        located = trials = 0; checks_max = 0; served_isolated = 0
        for t in range(50):
            replica = [str(int(x)) for x in g.integers(0, 10**6, 4096)]
            store = list(replica)
            bad = set(int(i) for i in g.choice(4096, k, replace=False))
            for i in bad:
                store[i] = store[i] + "x"
            A, B = merkle(store), merkle(replica)
            checks = 0; frontier = [(len(A) - 1, 0)]; found = set()
            while frontier:                                          # forensic descent
                lvl, i = frontier.pop()
                checks += 1
                if A[lvl][i] == B[lvl][i]:
                    continue
                if lvl == 0:
                    found.add(i); continue
                frontier += [(lvl - 1, 2 * i), (lvl - 1, 2 * i + 1)]
            isolated = found
            for i in g.choice(4096, 100, replace=False):            # reads before healing
                inside = int(i) in isolated
                if MON.gate("O3_serve", not inside, int(i) in bad):
                    served_isolated += int(int(i) in bad)
            for i in isolated:                                       # heal from the replica, then alive
                store[i] = replica[i]
            located += int(found == bad); trials += 1; checks_max = max(checks_max, checks)
        res[str(k)] = {"located": located, "trials": trials, "checks_max": checks_max,
                       "bound": 2 * k * 12, "served_from_isolated": served_isolated}
    return res


# ------------------------------------------------------------------------------------------------ O4 GROW
def o4():
    acc = {"plain": [0, 0], "grow": [0, 0]}
    for seed in SCENES:
        fo, ff, fv = H.facts(seed)
        alive = ~H.erase(seed, 0.5, 0)
        for name, r6 in (("plain", False), ("grow", True)):
            arm = dict(codes="rand", r6=r6, heal=False, gate=False)
            R, codes, h = H.holo_store(arm, fo, ff, fv)
            MON.gate("O4_budget", h.size <= H.D, False)
            MON.gate("O4_budget", h.size + 64 <= H.D, True)           # injected: growth that would exceed the budget
            v, _, _ = H.plain_read(h * alive.astype(np.int8), R, ff, codes)
            acc[name][0] += int((v == fv).sum()); acc[name][1] += len(fv)
    return {k: round(a / b, 5) for k, (a, b) in acc.items()}


# ------------------------------------------------------------------------------------------------ O5 SEE
def o5():
    tot = {"errors": 0, "flagged": 0, "flagged_errors": 0, "acc1": [0, 0], "acc3": [0, 0], "passes_max": 0}
    for seed in SCENES:
        fo, ff, fv = H.facts(seed)
        R, codes, h = H.holo_store(dict(codes="rand", r6=False, heal=False, gate=False), fo, ff, fv)
        alive = ~H.erase(seed, 0.5, 0)
        hd = h * alive.astype(np.int8)
        v1, gap, sup = H.plain_read(hd, R, ff, codes)                # seer 1
        flag = gap < 2 * np.sqrt(np.maximum(sup, 1))                  # seer 2
        err = v1 != fv
        tot["errors"] += int(err.sum()); tot["flagged"] += int(flag.sum()); tot["flagged_errors"] += int((flag & err).sum())
        sigma = np.sqrt(2 * int(flag.sum()) + 1)
        v = v1.copy(); passes = 0
        for passes in range(1, 4):                                   # witness, with its stop rule
            vn = H.explain_read(hd, alive.astype(np.float32), R, ff, codes, v, np.ones(len(ff), np.int32), sigma)
            nv = v.copy(); nv[flag] = vn[flag]
            if np.array_equal(nv, v):
                break
            v = nv
        tot["passes_max"] = max(tot["passes_max"], passes)
        tot["acc1"][0] += int((v1 == fv).sum()); tot["acc1"][1] += len(fv)
        tot["acc3"][0] += int((v == fv).sum()); tot["acc3"][1] += len(fv)
    return {"recall": round(tot["flagged_errors"] / max(tot["errors"], 1), 5),
            "precision": round(tot["flagged_errors"] / max(tot["flagged"], 1), 5),
            "acc_seer1": round(tot["acc1"][0] / tot["acc1"][1], 5),
            "acc_witness": round(tot["acc3"][0] / tot["acc3"][1], 5), "passes_max": tot["passes_max"]}


# ------------------------------------------------------------------------------------------------ O6 LOOP
def read_gate(h, alive, R, ff, codes, thr):
    arm = dict(codes="rand", r6=True, heal=True, gate=True)
    hd = h * alive.astype(np.int8)
    v, gap, sup = H.plain_read(hd, R, ff, codes)
    n_low = int((gap < 2 * np.sqrt(np.maximum(sup, 1))).sum())
    held = n_low > thr * len(ff)
    sigma = np.sqrt(2 * n_low + 1); ones = np.ones(len(ff), np.int32)
    for _ in range(4):
        w = H.writer_weights(R, ff, v, codes) if not held else ones
        vn = H.explain_read(hd, alive.astype(np.float32), R, ff, codes, v, w, sigma)
        if np.array_equal(vn, v):
            break
        v = vn
    return v


def gate_score(seeds, thr, losses=(0.7, 0.9)):
    out = {}
    for loss in losses:
        a = [0, 0]
        for seed in seeds:
            fo, ff, fv = H.facts(seed)
            R, codes, h = H.holo_store(H.ARMS["LivNRg"], fo, ff, fv)
            v = read_gate(h, ~H.erase(seed, loss, 0), R, ff, codes, thr)
            a[0] += int((v == fv).sum()); a[1] += len(fv)
        out[str(loss)] = round(a[0] / a[1], 5)
    return out


def o6():
    see = {str(t): gate_score(range(800, 808), t) for t in (0.5, 0.7, 0.9)}                 # see
    best = max(see, key=lambda t: see[t]["0.7"] + see[t]["0.9"])                             # build
    held_best = gate_score(range(920, 928), float(best)); held_old = gate_score(range(920, 928), 0.5)
    accept = held_best["0.7"] > held_old["0.7"] and held_best["0.9"] >= held_old["0.9"] - 0.01  # decide
    if best == "0.5":
        accept = False
    return {"see_calibration": see, "built": best, "held_out_best": held_best, "held_out_old": held_old,
            "accepted": accept}


# ------------------------------------------------------------------------------------------------ Part 2: hosts
FAMILIES = {"key": 1, "pair": 2, "condition": 50, "scan": 300}


def memory_host():
    res = {f: [0, 0] for f in FAMILIES}
    g = np.random.default_rng(404)
    arm = dict(codes="rand", r6=False, heal=False, gate=False)
    for seed in SCENES:
        fo, ff, fv = H.facts(seed)
        R, codes, h = H.holo_store(arm, fo, ff, fv)
        for fam, n in FAMILIES.items():
            for op in range(200):
                dead = np.zeros(H.D, bool); dead[g.choice(H.D, int(0.3 * H.D), replace=False)] = True
                v, _, _ = H.plain_read(h * (~dead).astype(np.int8), R, ff, codes)
                if fam == "condition":
                    fi = g.integers(6); idx = np.where(ff == fi)[0]
                else:
                    idx = g.choice(len(ff), n, replace=False)
                res[fam][0] += int((v[idx] != fv[idx]).any()); res[fam][1] += 1
    return {f: round(a / b, 5) for f, (a, b) in res.items()}


class GE:
    def __init__(self, g):
        self.g, self.bad = g, False

    def send(self):
        self.bad = (self.g.random() < 0.30) != self.bad if self.bad else (self.g.random() < 0.05)
        return self.g.random() >= (0.50 if self.bad else 0.01)


def net_element(ch):
    return ch.send() or ch.send()                                    # one retry


def network_host():
    g = np.random.default_rng(505); ch = GE(g)
    pull = {f: [0, 0] for f in FAMILIES}; blind = {f: [0, 0] for f in FAMILIES}
    for _ in SCENES:
        for fam, n in FAMILIES.items():
            for op in range(200):
                for _ in range(10):
                    ch.send()
                fail = False
                for _ in range(n):
                    if not net_element(ch):
                        fail = True
                pull[fam][0] += int(fail); pull[fam][1] += 1
                for _ in range(10):
                    ch.send()
                bfail = not (net_element(ch) and net_element(ch))     # request + reply
                blind[fam][0] += int(bfail); blind[fam][1] += 1
    return ({f: round(a / b, 5) for f, (a, b) in pull.items()}, {f: round(a / b, 5) for f, (a, b) in blind.items()})


class Ledger:
    def __init__(self, g):
        self.g, self.down = g, [False, False]

    def epoch(self):
        self.down = [(self.g.random() < 0.8) if d else (self.g.random() < 0.05) for d in self.down]
        up = 0
        for r in range(5):
            rack = 0 if r < 3 else 1
            up += int((not self.down[rack]) and self.g.random() >= 0.1)
        return up >= 3


def ledger_host():
    g = np.random.default_rng(606); L = Ledger(g)
    pull = {f: [0, 0] for f in FAMILIES}; blind = {f: [0, 0] for f in FAMILIES}
    for _ in SCENES:
        for fam, n in FAMILIES.items():
            for op in range(200):
                for _ in range(10):
                    L.epoch()
                fail = False
                for _ in range(n):
                    if not L.epoch():
                        fail = True
                pull[fam][0] += int(fail); pull[fam][1] += 1
                for _ in range(10):
                    L.epoch()
                blind[fam][0] += int(not L.epoch())
                blind[fam][1] += 1
    return ({f: round(a / b, 5) for f, (a, b) in pull.items()}, {f: round(a / b, 5) for f, (a, b) in blind.items()})


def law1(obs):
    eps = obs["key"]
    return {f: round(1 - (1 - eps) ** n, 5) for f, n in FAMILIES.items()}


def main(part):
    out_path = os.path.join(HERE, f"RESULTS_OPS1_{part}.json")
    if part == "part1":
        out = {"O1": o1(), "O2": o2(), "O3": o3(), "O4": o4(), "O5": o5()}
        print(json.dumps(out), flush=True)
        out["O6"] = o6()
        out["monitor"] = MON.c
    else:
        mem = memory_host()
        npull, nblind = network_host()
        lpull, lblind = ledger_host()
        out = {"memory": {"observed": mem, "law1": law1(mem)},
               "network": {"observed": npull, "law1": law1(npull), "blind": nblind},
               "ledger": {"observed": lpull, "law1": law1(lpull), "blind": lblind}}
    json.dump(out, open(out_path, "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
