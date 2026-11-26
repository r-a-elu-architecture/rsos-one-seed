"""Interface check only (no claim): a toy allocation host. N units lose level by random demand each step; budget K
refills per step; standard method = refill the K lowest units. Objective = mean level - 0.01 * refills used."""
import numpy as np, copy
class Toy:
    horizon = 10; samples = 3
    def __init__(s, N=12, K=3, T=30): s.N, s.K, s.T = N, K, T
    def reset(s, cell):
        return {"t": 0, "cell": cell, "x": np.ones(s.N), "rng": np.random.default_rng(cell), "used": 0, "sum": 0.0}
    def done(s, st): return st["t"] >= s.T
    def default(s, st): return list(np.argsort(st["x"])[:s.K])
    def branches(s, st):
        out = []
        for g in range(3):   # focus on one third of the units
            part = list(range(g * s.N // 3, (g + 1) * s.N // 3)); out.append((f"focus{g}", sorted(part, key=lambda i: st["x"][i])[:s.K]))
        return out
    def valid(s, st, a): return list(dict.fromkeys(int(i) for i in a))[:s.K]
    def step(s, st, a):
        st = dict(st); st["x"] = st["x"].copy(); st["x"][a] = np.minimum(1.0, st["x"][a] + 0.5); st["used"] += len(a)
        st["x"] -= st["rng"].exponential(0.08 * (1 + np.arange(s.N) % 3), s.N); st["x"] = np.maximum(st["x"], 0)
        st["t"] += 1; st["sum"] += st["x"].mean(); return st
    def fork(s, st, j):   # the host's own model: same dynamics, independent randomness (never the real rng)
        f = dict(st); f["x"] = st["x"].copy(); f["rng"] = np.random.default_rng([st["cell"], st["t"], j, 9173]); return f
    def objective(s, st): return st["sum"] - 0.01 * st["used"]
    def report(s, st): return {"result": st["sum"] / max(1, st["t"]), "resource": st["used"]}

class ToyLand(Toy):
    """Toy with the Law 4 landing interface (interface check only)."""
    def landings(s, st, a): return list(a)
    def without(s, st, a, L): return [u for u in a if u != L]
    def targets(s, st, a, L): return [int(i) for i in np.argsort(st["x"]) if int(i) not in a][:3]
    def retarget(s, st, a, L, T): return [T if u == L else u for u in a]

class ToyOps(ToyLand):
    """Toy bound to every REAL3 v2 seed operator hook (interface check only; Toy and ToyLand are unchanged, so the
    REAL1/REAL2 modes give identical numbers). Parts = the three thirds of the units (tuples of unit ids); sub-parts =
    halves of a third. An action is a list of unit ids, optionally with the marker "C" (carry: the step's unused refills
    are banked for the next step, bank <= K; the bank may be spent on top of K)."""
    def reset(s, cell):
        st = Toy.reset(s, cell); st["bank"] = 0; return st
    def _units(s, a): return [int(i) for i in a if i != "C"]
    def valid(s, st, a):
        u = list(dict.fromkeys(s._units(a)))[:s.K + st.get("bank", 0)]
        return u + (["C"] if "C" in a else [])
    def step(s, st, a):
        u = s._units(a); bank = st.get("bank", 0); extra = max(0, len(u) - s.K); bank -= extra
        if "C" in a: bank = min(s.K, bank + max(0, s.K - len(u)))
        st = Toy.step(s, st, u); st["bank"] = max(0, bank); return st
    def landings(s, st, a): return s._units(a)
    def without(s, st, a, L): return [u for u in a if u != L]
    def targets(s, st, a, L): return [int(i) for i in np.argsort(st["x"]) if int(i) not in s._units(a)][:3]
    # ---- REAL3 v2 hooks
    def parts(s, st, within=None):
        if within is None: return [tuple(range(g * s.N // 3, (g + 1) * s.N // 3)) for g in range(3)]
        h = len(within) // 2; return [tuple(within[:h]), tuple(within[h:])]
    def merge(s, st, d):
        out, named = [], set()
        for p, a in d.items():
            out += [u for u in s._units(a) if u in p]; named |= set(p)
        out += [u for u in s.default(st) if u not in named]
        return list(dict.fromkeys(int(u) for u in out))
    def part_objective(s, st, p): return float(st["x"][list(p)].mean())
    def focus(s, st, p): return sorted(p, key=lambda i: st["x"][i])[:s.K]
    def joint(s, st): return [("one-per-part", [min(p, key=lambda i: st["x"][i]) for p in s.parts(st)])]
    def carry(s, st, a):
        pool = list(dict.fromkeys(s._units(a) + [int(i) for i in np.argsort(st["x"])]))[:s.K + st.get("bank", 0)]
        return [u for u in pool if st["x"][u] < 0.6] + ["C"]
    def map_part(s, st, a, pf, pt):
        rf = sorted(pf, key=lambda i: st["x"][i]); rt = sorted(pt, key=lambda i: st["x"][i])
        return [rt[rf.index(u)] for u in s._units(a) if u in pf and rf.index(u) < len(rt)]
    def op_of(s, fam): return None   # the seed's COMMON table covers this host's families (focus -> beam)
