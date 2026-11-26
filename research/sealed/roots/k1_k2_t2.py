"""Layer-2 tests K1, K2, T2 (PREREG_K1_K2_T2.md, sealed before this file)."""
import json
import os
import secrets
import sys

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
HERE = os.path.dirname(os.path.abspath(__file__))


# ------------------------------------------------------------------ K1: the structure knows the events of its world
def k1():
    import sc1_tasks as SC
    out = {}
    outside = np.random.default_rng(int.from_bytes(secrets.token_bytes(8), "big"))   # not derivable from any rule
    for f in (0.0, 0.25, 0.5, 0.75, 1.0):
        hits = total = 0
        for seed in range(900, 916):
            rule = SC.make_task(seed)["requests"]                       # what the structure knows from rule + seed
            other = SC.make_task(int(outside.integers(10**9, 10**12)))["requests"]   # events from outside the rule
            world = [o if outside.random() < f else r for r, o in zip(rule, other)]   # what actually happens
            predicted = rule                                            # the structure names every event beforehand
            hits += sum(p == w for p, w in zip(predicted, world)); total += len(world)
        out[f] = {"events": total, "named_correctly": hits, "accuracy": round(hits / total, 4), "expected": 1 - f}
    ok = all(abs(v["accuracy"] - v["expected"]) <= 0.03 for v in out.values()) and out[0.0]["accuracy"] == 1.0
    return {"by_outside_fraction": out, "pass": ok}


# ------------------------------------------------------------------ K2: quantum structure as a chain of small nodes
def mps(psi, n, tol=1e-10):
    """Successive SVD into a matrix product state; returns the site tensors."""
    tensors, rest, chi = [], psi.reshape(1, -1), 1
    for i in range(n - 1):
        m = rest.reshape(chi * 2, -1)
        u, s, vh = np.linalg.svd(m, full_matrices=False)
        keep = max(1, int(np.sum(s > tol * s[0])))
        tensors.append(u[:, :keep].reshape(chi, 2, keep))
        rest = (s[:keep, None] * vh[:keep])
        chi = keep
    tensors.append(rest.reshape(chi, 2, 1))
    return tensors


def contract(tensors):
    v = tensors[0]
    for t in tensors[1:]:
        v = np.tensordot(v, t, axes=([v.ndim - 1], [0]))
    return v.reshape(-1)


def states(n, rng):
    d = 2 ** n
    prod = np.array([1.0 + 0j])
    for _ in range(n):
        q = rng.normal(size=2) + 1j * rng.normal(size=2); prod = np.kron(prod, q / np.linalg.norm(q))
    ghz = np.zeros(d, complex); ghz[0] = ghz[-1] = 1 / np.sqrt(2)
    w = np.zeros(d, complex)
    for i in range(n):
        w[1 << i] = 1 / np.sqrt(n)
    ts = [rng.normal(size=(1 if i == 0 else 2, 2, 1 if i == n - 1 else 2)) +
          1j * rng.normal(size=(1 if i == 0 else 2, 2, 1 if i == n - 1 else 2)) for i in range(n)]
    rmps = contract(ts); rmps /= np.linalg.norm(rmps)
    haar = rng.normal(size=d) + 1j * rng.normal(size=d); haar /= np.linalg.norm(haar)
    return {"product": prod, "GHZ": ghz, "W": w, "tensor_network_bond2": rmps, "random_haar": haar}


def k2():
    rng = np.random.default_rng(20261120)
    rows = []
    for n in (4, 8, 12, 16, 20):
        for name, psi in states(n, rng).items():
            ts = mps(psi, n)
            size = sum(t.size for t in ts)
            back = contract(ts)
            overlap = float(abs(np.vdot(psi, back)) ** 2 / (np.vdot(back, back).real))
            rows.append({"n": n, "state": name, "amplitudes": 2 ** n, "nodes_size": int(size),
                         "ratio": round(size / 2 ** n, 6), "max_bond": max(t.shape[2] for t in ts),
                         "overlap": overlap})
    s20 = [r for r in rows if r["n"] == 20 and r["state"] != "random_haar"]
    rnd = [r for r in rows if r["state"] == "random_haar" and r["n"] >= 12]
    ok = all(r["ratio"] <= 0.001 and r["overlap"] >= 1 - 1e-9 for r in s20) and all(r["ratio"] >= 0.25 for r in rnd)
    return {"rows": rows, "pass": ok}


# ------------------------------------------------------------------ T2: the true hologram
def t2(D=10_000, scenes=16):
    import sc1_tasks as SC
    rng = np.random.default_rng(7)
    values = {"x": [str(i) for i in range(10)], "y": [str(i) for i in range(10)],
              "height_mm": [str(i * 100) for i in range(1, 51)], "owner": SC.ROBOTS, "room": SC.ROOMS,
              "on": SC.SURFACES}
    bip = lambda: rng.choice(np.array([-1, 1], dtype=np.int8), size=D)
    O = {o: bip() for o in SC.OBJECTS}; F = {f: bip() for f in SC.FIELDS}
    V = {(f, v): bip() for f, vs in values.items() for v in vs}
    acc = {0.0: [0, 0], 0.1: [0, 0], 0.3: [0, 0], 0.5: [0, 0]}
    bytes_json = bytes_vec = 0
    for s in range(scenes):
        state = SC.make_task(900 + s)["init"]
        total = np.zeros(D, np.int32)
        for key, val in state.items():
            o, f = key.split(".")
            total += (O[o] * F[f] * V[(f, val)]).astype(np.int32)
        holo = np.sign(total).astype(np.int8); holo[holo == 0] = 1
        bytes_json += len(json.dumps(state, sort_keys=True, separators=(",", ":")).encode()); bytes_vec += D // 8
        for loss in acc:
            h = holo.astype(np.int32).copy()
            dead = rng.choice(D, size=int(loss * D), replace=False); h[dead] = 0           # destroyed components
            for key, val in state.items():
                o, f = key.split(".")
                u = h * (O[o] * F[f]).astype(np.int32)                                  # unbind the role
                best = max(values[f], key=lambda v: int(u @ V[(f, v)].astype(np.int32)))
                acc[loss][0] += best == val; acc[loss][1] += 1
    res = {str(k): round(v[0] / v[1], 5) for k, v in acc.items()}
    ok = res["0.0"] >= 0.99 and res["0.1"] >= 0.99 and res["0.3"] >= 0.99 and res["0.5"] >= 0.95 \
        and bytes_vec / bytes_json <= 0.25
    return {"fields_read": acc[0.0][1], "accuracy_by_loss": res, "bytes_ratio": round(bytes_vec / bytes_json, 4),
            "pass": ok}


if __name__ == "__main__":
    out = {"K1": k1()}; print("K1", json.dumps(out["K1"]))
    out["T2"] = t2(); print("T2", json.dumps(out["T2"]))
    out["K2"] = k2()
    for r in out["K2"]["rows"]:
        print("K2", r)
    print("K2 pass", out["K2"]["pass"])
    json.dump(out, open(os.path.join(HERE, "RESULTS_K1_K2_T2.json"), "w"), indent=1, default=str)
