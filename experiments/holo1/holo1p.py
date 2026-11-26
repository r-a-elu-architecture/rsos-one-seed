"""HOLO1-P: the whole-state hypothesis (U148-U152) tested fully in layer 2, inside the workspace.

Layer-2 system: a character-level recurrent language network (echo-state reservoir + trained readout),
numpy only. Its WHOLE state at every character is one vector we can freeze, copy, inject and compare.
Agents A and B = two copies of the same network, each with its own context ("body + environment").

Usage: python holo1p.py <reservoir_seed> <outdir> [--small]
The sealed run uses reservoir_seed=1. Seed 999 is the dev seed (smoke test only, never reported).
"""
import sys, json, hashlib, time
import numpy as np

SEED = int(sys.argv[1]); OUT = sys.argv[2]; SMALL = "--small" in sys.argv
LEAK = float(sys.argv[3]) if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else 0.5
RHO = float(sys.argv[4]) if len(sys.argv) > 4 and not sys.argv[4].startswith("--") else 0.95
rng_corpus = np.random.default_rng(12345)          # corpus is fixed across seeds

# ---------------------------------------------------------------- corpus (neutral: no state->wording link)
DOM = {
 "kitchen":   ["soup", "spoon", "table", "pot", "bread", "salt"],
 "computer":  ["screen", "code", "chip", "wifi", "server", "pixel"],
 "company":   ["email", "project", "money", "contract", "office", "market"],
 "family":    ["mother", "child", "home", "father", "gift", "toy"],
 "school":    ["teacher", "grade", "lesson", "book", "class", "exam"],
 "philosophy":["buddha", "temple", "idea", "belief", "mind", "truth"],
 "chemistry": ["atom", "molecule", "salt", "acid", "heat", "ion"],
 "biology":   ["cell", "blood", "neuron", "liver", "heart", "vein"],
}
TPL = ["the {a} changes the {b}.", "when the {a} is warm, the {b} moves.", "he sees the {a} near the {b}.",
       "the {a} sends a signal to the {b}.", "after the {a}, the {b} feels calm.", "the {a} and the {b} are one family.",
       "she remembers the {a} and the {b}.", "the {a} carries a trace of the {b}.", "go to the {a} and look at the {b}.",
       "the {b} depends on the {a}."]
STATES = {
 "tired":   ["a is tired after a long day.", "a sits slowly, eyes heavy.", "a yawns and rests."],
 "happy":   ["a is happy and laughing.", "a smiles at the sun.", "a sings a short song."],
 "angry":   ["a is angry and loud.", "a hits the table hard.", "a shouts at the wall."],
 "worried": ["a is worried about money.", "a checks the phone again.", "a thinks about the exam."],
 "hungry":  ["a is hungry and cold.", "a smells the kitchen.", "a waits for bread."],
 "calm":    ["a is calm and quiet.", "a breathes slowly.", "a looks at the garden."],
}
PARA = ["go eat the soup.", "come and eat the soup.", "the soup is ready, go eat.", "go to the table and eat soup.",
        "eat the soup now.", "go have some soup.", "your soup is waiting, go eat.", "please go eat the soup.",
        "the soup is hot, come eat.", "go and eat your soup."]
VILLAGE = ["b remembers the village soup with friends, warm and good.", "b smells the old village kitchen and smiles.",
           "b feels the warm soup of the village in the chest.", "b sees the friends at the village table again.",
           "b tastes the village soup and feels relief."]
NEUTRAL = ["b reads the street sign by the road.", "b counts the windows of the building.",
           "b looks at the grey wall of the hall.", "b walks past the parked cars slowly.",
           "b notes the time on the station clock."]

def make_corpus(n_lines):
    lines = []
    allstate = [s for v in STATES.values() for s in v]
    for _ in range(n_lines):
        r = rng_corpus.random()
        if r < 0.45:
            d = rng_corpus.choice(list(DOM)); a, b = rng_corpus.choice(DOM[d], 2, replace=False)
            lines.append(rng_corpus.choice(TPL).format(a=a, b=b))
        elif r < 0.75:   # dialogue: state lines (any) then message (any paraphrase, independent of state)
            st = " ".join(rng_corpus.choice(allstate, 2, replace=False))
            lines.append(st + " a says to b: " + rng_corpus.choice(PARA))
        elif r < 0.9:
            lines.append(rng_corpus.choice(VILLAGE + NEUTRAL))
        else:
            lines.append("message: " + rng_corpus.choice(PARA) + " " + rng_corpus.choice(TPL).format(
                a=rng_corpus.choice(DOM["kitchen"]), b=rng_corpus.choice(DOM["family"])))
    return " ".join(lines)

CORPUS = make_corpus(2500 if SMALL else 6000)
CH = sorted(set(CORPUS) | set("abcdefghijklmnopqrstuvwxyz .,:'"))
IDX = {c: i for i, c in enumerate(CH)}; V = len(CH)

# ---------------------------------------------------------------- layer-2 system
N = 300 if SMALL else 700
rs = np.random.default_rng(SEED)
Win = rs.uniform(-0.6, 0.6, (N, V))
W = rs.normal(0, 1, (N, N)) * (rs.random((N, N)) < 0.08)
W *= RHO / max(abs(np.linalg.eigvals(W)))
bias = rs.uniform(-0.2, 0.2, N)

def step(x, c):
    u = np.zeros(V); u[IDX[c]] = 1.0
    return (1 - LEAK) * x + LEAK * np.tanh(Win @ u + W @ x + bias)

def run(x, text, keep=False):
    traj = []
    for c in text:
        x = step(x, c)
        if keep: traj.append(x)
    return (x, np.array(traj)) if keep else x

# readout: ridge regression state -> next char
def train_readout():
    L = len(CORPUS) - 1; cut = int(0.9 * L)
    Y = np.array([IDX[c] for c in CORPUS[1:]])
    A = np.zeros((N + 1, N + 1)); B = np.zeros((N + 1, V)); x = np.zeros(N); held = []
    buf = []
    for t, c in enumerate(CORPUS[:-1]):
        x = step(x, c); xa = np.append(x, 1.0)
        if t >= cut: held.append(xa)
        buf.append(xa)
        if len(buf) == 5000 or t == L - 1:
            Xb = np.array(buf); Tb = np.zeros((len(buf), V)); Tb[np.arange(len(buf)), Y[t - len(buf) + 1:t + 1]] = 1
            A += Xb.T @ Xb; B += Xb.T @ Tb; buf = []
    Wout = np.linalg.solve(A + 1e-2 * np.eye(N + 1), B)
    # softmax temperature beta fitted on the last 10% (log-likelihood); readout trained on all text
    Z = np.array(held) @ Wout
    best = max([4, 6, 8, 10, 14, 18, 24], key=lambda b: np.mean(
        (b * Z)[np.arange(len(Z)), Y[cut:]] - np.log(np.exp(b * Z).sum(1))))
    acc = np.mean(Z.argmax(1) == Y[cut:])
    return Wout, best, acc

t0 = time.time()
Wout, BETA, ACC = train_readout()

def probs(x):
    z = BETA * (np.append(x, 1) @ Wout); z -= z.max(); p = np.exp(z); return p / p.sum()

def generate(x, n, rng, stop="."):
    out = ""
    for _ in range(n):
        c = CH[rng.choice(V, p=probs(x))]
        out += c; x = step(x, c)
        if c == stop: break
    return x, out

def x0(): return np.zeros(N)
def warm(): return run(x0(), "the day begins. ")

R = {"seed": SEED, "leak": LEAK, "rho": RHO, "N": N, "V": V, "beta": BETA, "readout_heldout_acc": round(float(ACC), 4),
     "corpus_chars": len(CORPUS), "corpus_sha256": hashlib.sha256(CORPUS.encode()).hexdigest()}

def nc_cv_acc(F, y, k=5, rng=None):   # nearest-centroid, standardized, k-fold
    F = (F - F.mean(0)) / (F.std(0) + 1e-12)
    idx = np.arange(len(y)); (rng or np.random.default_rng(0)).shuffle(idx)
    folds = np.array_split(idx, k); correct = 0
    for f in folds:
        tr = np.setdiff1d(idx, f); labs = np.unique(y[tr])
        C = np.array([F[tr][y[tr] == l].mean(0) for l in labs])
        d = ((F[f][:, None, :] - C[None]) ** 2).sum(-1)
        correct += np.sum(labs[d.argmin(1)] == y[f])
    return correct / len(y)

def perm_p(F, y, obs, n=1000):
    r = np.random.default_rng(7); cnt = 0
    for _ in range(n):
        if nc_cv_acc(F, r.permutation(y)) >= obs: cnt += 1
    return (cnt + 1) / (n + 1)

NSEEDS = 12 if SMALL else 40
SNAMES = list(STATES)
def a_state(s): return run(warm(), " ".join(STATES[s]) + " ")

# ---------------------------------------------------------------- H1 unique snapshot (instrument)
_, tr = run(warm(), " ".join(STATES["calm"]) + " a says to b: go eat the soup.", keep=True)
d = np.linalg.norm(np.diff(tr, axis=0), axis=1)
R["H1"] = {"snapshots": len(tr), "identical_consecutive": int(np.sum(d == 0)), "min_dist": float(d.min()),
           "median_dist": float(np.median(d))}

# ---------------------------------------------------------------- H2 same words, different whole state
fin = {s: run(a_state(s), "a says to b: go eat the soup.") for s in SNAMES}
pd = [np.linalg.norm(fin[a] - fin[b]) for i, a in enumerate(SNAMES) for b in SNAMES[i + 1:]]
R["H2"] = {"pairs": len(pd), "identical_pairs": int(np.sum(np.array(pd) == 0)), "min_dist": float(min(pd)),
           "mean_dist": float(np.mean(pd))}

# ---------------------------------------------------------------- H3 hologram through words (O channel)
CUE = "a says to b: "
msgs, labels = [], []
for k in range(NSEEDS):
    for si, s in enumerate(SNAMES):
        _, m = generate(run(a_state(s), CUE), 60, np.random.default_rng(1000 + k))  # common random numbers
        msgs.append(m); labels.append(si)
labels = np.array(labels)
bprime = run(warm(), NEUTRAL[0] + " ")
FB = np.array([run(bprime, CUE + m) for m in msgs])
acc3 = nc_cv_acc(FB, labels); p3 = perm_p(FB, labels, acc3)
FB0 = np.array([run(bprime, CUE + "go eat the soup.") for _ in msgs])   # identical-words control
acc0 = float(np.max(np.linalg.norm(FB0 - FB0[0], axis=1)))  # max state distance under identical words
distinct = len(set(msgs))
R["H3"] = {"messages": len(msgs), "distinct_messages": distinct, "chance": round(1 / len(SNAMES), 4),
           "acc_words_free": round(float(acc3), 4), "perm_p": round(float(p3), 5),
           "maxdist_identical_words_control": round(float(acc0), 4),
           "examples": {SNAMES[i]: msgs[i] for i in range(len(SNAMES))}}

# ---------------------------------------------------------------- H5 the full hologram (state injected)
TAIL = " b sits at the table and looks at the bowl."
HPRE = np.array([run(a_state(SNAMES[l]), CUE) for l in labels])          # the whole state that produced the words
HPOST = np.array([run(a_state(SNAMES[l]), CUE + m) for m, l in zip(msgs, labels)])
V_A = HPRE - HPRE.mean(0)
rr = np.random.default_rng(99)
RV = rr.normal(0, 1, V_A.shape); RV *= (np.linalg.norm(V_A, axis=1) / np.linalg.norm(RV, axis=1))[:, None]
def after_tail(F, h): return np.array([run(f, TAIL[:h]) for f in F])
prof = {}
for h in (0, 5, 10, 20, len(TAIL)):
    prof[h] = [round(float(nc_cv_acc(after_tail(F, h), labels)), 4) for F in (FB, FB + V_A, FB + RV)]
Fw = after_tail(FB, 10); Fh = after_tail(FB + V_A, 10); Fr = after_tail(FB + RV, 10)
aw, ah, ar = nc_cv_acc(Fw, labels), nc_cv_acc(Fh, labels), nc_cv_acc(Fr, labels)
ph = perm_p(Fh, labels, ah)
cos = lambda X, Y: float(np.mean(np.sum(X * Y, 1) / (np.linalg.norm(X, axis=1) * np.linalg.norm(Y, axis=1))))
R["H5"] = {"acc_decode_A_pre": round(float(nc_cv_acc(HPRE, labels)), 4),
           "acc_decode_A_post": round(float(nc_cv_acc(HPOST, labels)), 4), "horizon_chars": 10, "profile_words_holo_random_by_horizon": prof, "acc_words_only": round(float(aw), 4), "acc_words_plus_hologram": round(float(ah), 4),
           "acc_words_plus_random_same_norm": round(float(ar), 4), "perm_p_hologram": round(float(ph), 5),
           "align_to_A_words": round(cos(Fw - Fw.mean(0), V_A), 4),
           "align_to_A_hologram": round(cos(Fh - Fh.mean(0), V_A), 4)}

# ---------------------------------------------------------------- H4 receiver decides (G)
msg4 = [m for m, l in zip(msgs, labels) if l == SNAMES.index("calm")]
def deltas(prime):
    xb = run(warm(), prime + " ")
    return np.array([run(xb, CUE + m) - xb for m in msg4])
DV = [deltas(p).mean(0) for p in VILLAGE]; DN = [deltas(p).mean(0) for p in NEUTRAL]
effect = np.linalg.norm(np.mean(DV, 0) - np.mean(DN, 0))
# noise floor: split of neutral primes vs other neutral primes (all 2|3 splits), and village vs village
floor = []
from itertools import combinations
for grp in (DN, DV):
    for c in combinations(range(5), 2):
        rest = [i for i in range(5) if i not in c]
        floor.append(np.linalg.norm(np.mean([grp[i] for i in c], 0) - np.mean([grp[i] for i in rest], 0)))
R["H4"] = {"effect": float(effect), "noise_floor_median": float(np.median(floor)),
           "ratio": round(float(effect / np.median(floor)), 3), "messages": len(msg4)}

# ---------------------------------------------------------------- H6 cascade through domains
CHAIN = ["kitchen", "computer", "company", "family", "school"]
PRIME = {d: "in the {} the {} is near the {}. ".format(d, DOM[d][0], DOM[d][1]) for d in CHAIN}
def cascade(first_prime, k):
    xs, texts, prev = [], [], ""
    for i, d in enumerate(CHAIN):
        p = first_prime if i == 0 else PRIME[d]
        x = run(warm(), p + ("message: " + prev + " " if prev else "") + "message: ")
        x, m = generate(x, 50, np.random.default_rng(5000 + 10 * k + i))
        xs.append(x); texts.append(m); prev = m
    return xs, texts
base_p = PRIME["kitchen"]; pert_p = base_p.replace("soup", "soap")
NC = 12 if SMALL else 40
reach, dists, tdiff = [], [], []
for k in range(NC):
    xa, ta = cascade(base_p, k); xb, tb = cascade(pert_p, k)
    dists.append([float(np.linalg.norm(a - b)) for a, b in zip(xa, xb)])
    tdiff.append([ta[i] != tb[i] for i in range(5)])
dists, tdiff = np.array(dists), np.array(tdiff)
md = dists.mean(0)
R["H6"] = {"trials": NC, "frac_text_changed_per_node": [round(float(v), 3) for v in tdiff.mean(0)],
           "mean_state_dist_per_node": [round(float(v), 4) for v in md],
           "reached_node5_frac": round(float(tdiff[:, 4].mean()), 3),
           "amplify_nodes": [CHAIN[i] for i in range(1, 5) if md[i] > md[i - 1]],
           "dampen_nodes": [CHAIN[i] for i in range(1, 5) if md[i] < md[i - 1]]}

# ---------------------------------------------------------------- H7 infinite seed (lineage weights)
TURNS = ["a is hungry and cold.", "a smells the kitchen.", "go to the pot and look at the bread.",
         "the buddha and the temple are one family.", "the email changes the project.",
         "the child remembers the gift.", "the teacher sends a signal to the class.", "a says to b: go eat the soup."]
FILL = lambda t: "".join("x" if c not in " ." else c for c in t)
full = run(warm(), " ".join(TURNS))
eff = []
for i in range(len(TURNS)):
    T2 = list(TURNS); T2[i] = FILL(TURNS[i])
    eff.append(float(np.linalg.norm(full - run(warm(), " ".join(T2)))))
R["H7"] = {"effect_per_turn_oldest_first": eff, "zero_effects": int(np.sum(np.array(eff) == 0.0)),
           "min_effect": min(eff)}

# ---------------------------------------------------------------- H8 one family
D8 = list(DOM)
def rdm(d):
    S = []
    for t in TPL:
        fs = [run(warm(), t.format(a=DOM[d][j], b=DOM[d][(j + 1) % 6])) for j in range(3)]
        S.append(np.mean(fs, 0))
    S = np.array(S); S = S - S.mean(0)
    C = np.corrcoef(S); return C[np.triu_indices(len(TPL), 1)]
from scipy.stats import spearmanr
RD = {d: rdm(d) for d in D8}
pairs = [(a, b) for i, a in enumerate(D8) for b in D8[i + 1:]]
obs8 = np.mean([spearmanr(RD[a], RD[b])[0] for a, b in pairs])
iu = np.triu_indices(len(TPL), 1); r8 = np.random.default_rng(8); null = []
def unvec(v):
    M = np.eye(len(TPL)); M[iu] = v; M.T[iu] = v; return M
MAT = {d: unvec(RD[d]) for d in D8}
for _ in range(1000):
    sh = {}
    for d in D8:
        pm = r8.permutation(len(TPL)); sh[d] = MAT[d][pm][:, pm][iu]
    null.append(np.mean([spearmanr(sh[a], sh[b])[0] for a, b in pairs]))
p8 = (np.sum(np.array(null) >= obs8) + 1) / 1001
R["H8"] = {"mean_cross_domain_rdm_spearman": round(float(obs8), 4), "null_mean": round(float(np.mean(null)), 4),
           "null_95pct": round(float(np.percentile(null, 95)), 4), "perm_p": round(float(p8), 5)}

R["runtime_s"] = round(time.time() - t0, 1)
json.dump(R, open(OUT, "w"), indent=1)
print(json.dumps(R, indent=1))
