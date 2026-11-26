"""Q1 quick test (exploratory, development seeds 100-299; no colour depends on it). Owner 22 Nov 16:56: Part 0.8a of
map/STRUCTURAL_MAP_22NOV.md - every change is a structural change that can be EXPLAINED (named) and FOUND (located).
World: 13 quarks (root -> 3 nodes -> 3 subnodes each), each with channels V A K O G firing in its own order (U157);
tubes parent-child plus 4 side relations carry G between quarks; linear dynamics with process and observation noise.
One change is injected at a random time (20-35) of one of four types, never seen by the readers before:
  kick (a channel's value jumps), order (two letters of one quark's VAKOG order swap), operator (one quark's coupling
  changes), relation (one tube's weight changes).
Readers see only the observed trajectory (60 steps):
  STRUCTURE reader: knows the structure (generator), not the change; scores every structural hypothesis by one-step
    residuals after the onset it detects, and names type + place.
  BLIND reader: no structure; per-channel AR(1) fitted on the first 15 steps; names the quark with the largest residual
    and the most common type.
Prediction (fixed before running): STRUCTURE locates >= 80 % and names the type >= 70 %; BLIND locates <= 50 %, type ~25 %."""
import numpy as np, itertools, json
CH = "VAKOG"; Q = 13
PAR = {i: 0 for i in range(1, 4)}; PAR.update({4 + 3 * j + k: 1 + j for j in range(3) for k in range(3)})

def world(rng):
    edges = {(c, p): 0.3 for c, p in PAR.items()}
    side = [e for e in itertools.combinations(range(1, Q), 2) if e not in edges and (e[1], e[0]) not in edges]
    for i in rng.choice(len(side), 4, replace=False): edges[side[i]] = 0.25
    return {"order": [list(rng.permutation(5)) for _ in range(Q)], "c": rng.uniform(0.3, 0.6, Q), "a": 0.6, "edges": edges}

def step(S, x, noise):
    y = np.zeros_like(x); inflow = np.zeros(Q)
    for (u, v), w in S["edges"].items(): inflow[u] += w * x[v, 4]; inflow[v] += w * x[u, 4]
    for q in range(Q):
        prev = None
        for k in S["order"][q]:
            y[q, k] = S["a"] * x[q, k] + (inflow[q] if prev is None else S["c"][q] * y[q, prev]) + noise[q, k]; prev = k
    return y

def simulate(S, T, t0, change, rng):
    x = rng.normal(0, 1, (Q, 5)); X = []
    for t in range(T):
        if t == t0: S = apply(S, change)
        x = step(S, x, rng.normal(0, 0.3, (Q, 5)))
        if t == t0 and change[0] == "kick": x[change[1], change[2]] += change[3]
        X.append(x + rng.normal(0, 0.05, (Q, 5)))
    return np.array(X)

def apply(S, ch):
    S = {"order": [o[:] for o in S["order"]], "c": S["c"].copy(), "a": S["a"], "edges": dict(S["edges"])}
    if ch[0] == "order": o = S["order"][ch[1]]; o[ch[2]], o[ch[3]] = o[ch[3]], o[ch[2]]
    if ch[0] == "operator": S["c"][ch[1]] = ch[2]
    if ch[0] == "relation": S["edges"][ch[1]] = ch[2]
    return S

def resid(S, X, t):  # one-step residuals at time t under structure S (zero noise prediction)
    return X[t] - step(S, X[t - 1], np.zeros((Q, 5)))

def structure_reader(S, X):
    T = len(X); base = np.array([np.sum(resid(S, X, t) ** 2) for t in range(1, T)])
    thr = np.median(base[:15]) * 3; onset = next((t + 1 for t, v in enumerate(base) if t >= 15 and v > thr), 30)
    W = range(onset, min(T, onset + 15)); best = (np.inf, None)
    r0 = resid(S, X, onset)  # kick: largest single residual at onset, explained away only at that step
    q, k = np.unravel_index(np.argmax(np.abs(r0)), r0.shape)
    kick_err = sum(np.sum(resid(S, X, t) ** 2) for t in W) - r0[q, k] ** 2
    best = (kick_err, ("kick", int(q), int(k)))
    hyps = [("order", q, i, j) for q in range(Q) for i, j in itertools.combinations(range(5), 2)]
    hyps += [("operator", q, v) for q in range(Q) for v in np.linspace(0.05, 1.0, 20)]
    hyps += [("relation", e, v) for e in S["edges"] for v in np.linspace(0.0, 0.8, 17)]
    for h in hyps:
        Sh = apply(S, h); err = sum(np.sum(resid(Sh, X, t) ** 2) for t in W)
        if err < best[0]: best = (err, h)
    return best[1]

def blind_reader(X):
    pre = X[:16]; R = np.zeros(X.shape[1:])
    for q in range(Q):
        for k in range(5):
            s = pre[:, q, k]; phi = np.dot(s[1:], s[:-1]) / max(1e-9, np.dot(s[:-1], s[:-1]))
            r = X[16:, q, k] - phi * X[15:-1, q, k]; R[q, k] = np.max(np.abs(r)) / (np.std(s[1:] - phi * s[:-1]) + 1e-9)
    q, k = np.unravel_index(np.argmax(R), R.shape); return ("kick", int(q), int(k))

def place(h): return h[1] if h[0] != "relation" else tuple(h[1])
def located(h, ch):
    if ch[0] == "relation": return place(h) == ch[1] if h[0] == "relation" else h[1] in ch[1]
    return h[0] != "relation" and h[1] == ch[1] or (h[0] == "relation" and ch[1] in h[1] and False)

res = {"structure": {"loc": 0, "type": 0}, "blind": {"loc": 0, "type": 0}, "n": 0, "by_type": {}}
for seed in range(100, 300):
    rng = np.random.default_rng(seed); S = world(rng); typ = ["kick", "order", "operator", "relation"][seed % 4]
    q = int(rng.integers(Q)); t0 = int(rng.integers(20, 36))
    if typ == "kick": ch = ("kick", q, int(rng.integers(5)), float(rng.choice([-1, 1]) * rng.uniform(2, 4)))
    elif typ == "order": i, j = rng.choice(5, 2, replace=False); ch = ("order", q, int(min(i, j)), int(max(i, j)))
    elif typ == "operator": ch = ("operator", q, float(np.clip(S["c"][q] + rng.choice([-1, 1]) * rng.uniform(0.25, 0.4), 0.05, 1.0)))
    else: e = list(S["edges"])[int(rng.integers(len(S["edges"])))]; ch = ("relation", e, float(rng.uniform(0.55, 0.8) if S["edges"][e] < 0.4 else 0.0))
    X = simulate(S, 60, t0, ch, rng)
    hs, hb = structure_reader(S, X), blind_reader(X)
    d = res["by_type"].setdefault(typ, {"n": 0, "s_loc": 0, "s_type": 0, "b_loc": 0})
    d["n"] += 1; res["n"] += 1
    for name, h in (("structure", hs), ("blind", hb)):
        L, Ty = located(h, ch), h[0] == ch[0]
        res[name]["loc"] += L; res[name]["type"] += Ty
        if name == "structure": d["s_loc"] += L; d["s_type"] += Ty
        else: d["b_loc"] += L
print(json.dumps(res, indent=1)); json.dump(res, open("q1_result.json", "w"), indent=1)
