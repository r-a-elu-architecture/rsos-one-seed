"""HOLO2: the quark (U153) on the computer host of owner 11:50, all 120 VAKOG orders (U157).
Host: a processor with temperature, load and two actuators (clock speed, fan).
Subnodes (owner's definitions, 11:50):
  V  sees the processor's temperature change
  A  hears the alarm and selects the protocol (none / fan / throttle / both)
  K  the OS policy applies the protocol in a specific structural order (graded ramp)
  O  the kernel smells something different from before (trace of past load), knows the change, computes ahead
  G  well fed and efficient: relief read from recent working condition, tempers the chain
Chain: a signal u passes through the five subnodes in the given order; each subnode reads the previous one.
G-endpoint (the machine's working condition per step) = work served - fan energy - overheating penalty.
Usage: python holo2.py <out.json>"""
import sys, json, itertools
import numpy as np

T_AMB, T_SET, T_MAX, STEPS = 30.0, 70.0, 85.0, 600

def world(seed):
    r = np.random.default_rng(seed)
    t = np.arange(STEPS)
    load = 0.55 + 0.3 * np.sin(2 * np.pi * t / 120)                     # a recurring cycle (O can learn it)
    for s in r.choice(STEPS - 20, 6, replace=False):                     # heat spikes
        load[s:s + 15] += r.uniform(0.3, 0.5)
    return np.clip(load, 0, 1.4), r.normal(0, 0.3, STEPS)

def step_T(T, load, speed, fan, noise):
    heat = 2.2 * min(load, speed)
    cool = (0.02 + 0.08 * fan) * (T - T_AMB)
    return T + heat - cool + noise

def g_point(T, load, speed, fan):
    return min(load, speed) - 0.15 * fan - 0.02 * max(0.0, T - T_MAX) ** 2

class Quark:
    """Five subnodes; order is the program."""
    def __init__(self, order, coupled=True):
        self.order, self.coupled = order, coupled
        self.Tprev = T_AMB; self.trace = np.zeros(120); self.proto = 0; self.speed = 1.0; self.fan = 0.0
        self.relief = 0.0; self.out = {k: 0.0 for k in "VAKOG"}
    def V(self, u, T, load, t): return u + 0.8 * (T - self.Tprev) / 2.0
    def O(self, u, T, load, t):
        ahead = self.trace[(t + 10) % 120]; now = self.trace[t % 120]   # what was different before at this phase
        return u + 1.5 * (ahead - now)
    def A(self, u, T, load, t):
        self.proto = 0 if u < 0 else (1 if u < 0.6 else (2 if u < 1.2 else 3)); return u
    def K(self, u, T, load, t):
        tf = {0: 0.0, 1: 0.7, 2: 1.0, 3: 1.0}[self.proto]; ts = {0: 1.0, 1: 1.0, 2: 0.85, 3: 0.6}[self.proto]
        self.fan += 0.5 * (tf - self.fan); self.speed += 0.5 * (ts - self.speed); return u
    def G(self, u, T, load, t): return u * (1 - 0.3 * np.tanh(self.relief))
    def act(self, T, load, t):
        u0 = (T - T_SET) / 10.0; u = u0
        for m in self.order:
            inp = u if self.coupled else u0
            u = getattr(self, m)(inp, T, load, t); self.out[m] = u
        self.Tprev = T
        self.trace[t % 120] = 0.7 * self.trace[t % 120] + 0.3 * load      # O's memory of the outcome
        return self.speed, self.fan
    def feel(self, gp): self.relief = 0.9 * self.relief + 0.1 * gp

class PI:
    def __init__(self): self.i = 0.0
    def act(self, T, load, t):
        e = (T - T_SET) / 10.0; self.i = np.clip(self.i + 0.05 * e, -1, 2); c = 0.8 * e + self.i
        return float(np.clip(1.0 - 0.3 * max(0, c - 1), 0.6, 1.0)), float(np.clip(c, 0, 1))
    def feel(self, gp): pass

def run(ctrl, seed, kick=None, record=False):
    load, noise = world(seed); T = 60.0; G = 0.0; rec = []
    for t in range(STEPS):
        if kick is not None and t == kick[0]: kick[1](ctrl)
        s, f = ctrl.act(T, load[t], t)
        gp = g_point(T, load[t], s, f); G += gp; ctrl.feel(gp)
        T = step_T(T, load[t], s, f, noise[t])
        if record: rec.append([ctrl.out[m] for m in "VAKOG"])
    return G / STEPS, np.array(rec) if record else None

ORDERS = ["".join(p) for p in itertools.permutations("VAKOG")]
SEEDS = list(range(100, 120))
R = {"orders": len(ORDERS), "seeds": SEEDS}

# P2/P3: G for every order, coupled; uncoupled; plain PI
Gc = np.array([[run(Quark(o), s)[0] for s in SEEDS] for o in ORDERS])
Gu = np.array([run(Quark("VAKOG", coupled=False), s)[0] for s in SEEDS])
Gp = np.array([run(PI(), s)[0] for s in SEEDS])
mean_o = Gc.mean(1); best = int(mean_o.argmax()); med = int(np.argsort(mean_o)[len(ORDERS) // 2])
from scipy.stats import binomtest, kruskal
def sign_p(a, b): w = int(np.sum(a > b)); return w, float(binomtest(w, len(a), 0.5, alternative="greater").pvalue)
R["G_mean"] = {"best_order": ORDERS[best], "best": float(mean_o[best]), "median_order": ORDERS[med],
               "median": float(mean_o[med]), "worst_order": ORDERS[int(mean_o.argmin())], "worst": float(mean_o.min()),
               "uncoupled": float(Gu.mean()), "plain_PI": float(Gp.mean()),
               "computer_order_VAKOG": float(mean_o[ORDERS.index("VAKOG")]),
               "person_order_VOKGA": float(mean_o[ORDERS.index("VOKGA")])}
R["P2"] = {"best_vs_uncoupled": sign_p(Gc[best], Gu), "best_vs_PI": sign_p(Gc[best], Gp),
           "median_vs_uncoupled": sign_p(Gc[med], Gu), "median_vs_PI": sign_p(Gc[med], Gp)}
# selection bias guard: best order chosen on seeds 100-119; re-checked on fresh seeds 200-219
FS = list(range(200, 220))
gb = np.array([run(Quark(ORDERS[best]), s)[0] for s in FS]); gu2 = np.array([run(Quark("VAKOG", coupled=False), s)[0] for s in FS])
gp2 = np.array([run(PI(), s)[0] for s in FS])
R["P2_fresh_seeds"] = {"best_vs_uncoupled": sign_p(gb, gu2), "best_vs_PI": sign_p(gb, gp2),
                       "best": float(gb.mean()), "uncoupled": float(gu2.mean()), "PI": float(gp2.mean())}
R["P3"] = {"kruskal_p": float(kruskal(*Gc).pvalue), "range": float(mean_o.max() - mean_o.min()),
           "seed_sd_median": float(np.median(Gc.std(1))),
           "top5": [(ORDERS[i], round(float(mean_o[i]), 4)) for i in np.argsort(-mean_o)[:5]],
           "bottom5": [(ORDERS[i], round(float(mean_o[i]), 4)) for i in np.argsort(mean_o)[:5]]}

# P1: trigger one subnode (O: the kernel's trace) at t=200; all five subnodes change; divergence early vs late
def kick_O(q): q.trace[:] += 0.3
reach, growth = [], []
for o in ORDERS:
    _, base = run(Quark(o), 100, record=True)
    _, pert = run(Quark(o), 100, kick=(200, kick_O), record=True)
    d = np.abs(pert - base)
    reach.append(bool(np.all(d[200:260].max(0) > 0)))
    early, late = d[201:211].mean(), d[250:300].mean()
    growth.append(float(late / early) if early > 0 else float("inf"))
R["P1"] = {"orders_all_five_changed": int(sum(reach)), "of": len(ORDERS),
           "growth_ratio_median": float(np.median(growth)), "orders_growing": int(np.sum(np.array(growth) > 1)),
           "growth_ratio_range": [float(min(growth)), float(max(growth))]}
json.dump(R, open(sys.argv[1], "w"), indent=1); print(json.dumps(R, indent=1))
