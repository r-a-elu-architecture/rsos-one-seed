"""HOLO1-P K: the cascade re-run with a state event (U155: identity holds), replacing soup->soap.
Reuses the sealed holo1p.py system unchanged (hash-checked), up to the H1 block.
Usage: python holo1p_k.py <seed> <out.json> <leak> <rho>"""
import sys, hashlib, json
SRC = open("holo1p.py").read()
assert hashlib.sha256(SRC.encode()).hexdigest() == "9828a280cd0bab069ff34d6cff8593f3c3ea2a6541243314e702c57dab5457f1"
exec(SRC.split("# ---------------------------------------------------------------- H1")[0])
CHAIN = ["kitchen", "computer", "company", "family", "school"]
PRIME = {d: "in the {} the {} is near the {}. ".format(d, DOM[d][0], DOM[d][1]) for d in CHAIN}
EV_A = "in the kitchen the spoon is put on the table. "      # same objects, same identities
EV_B = "in the kitchen the spoon falls on the floor. "       # a different state event
def cascade(first, k):
    xs, texts, prev = [], [], ""
    for i, d in enumerate(CHAIN):
        p = first if i == 0 else PRIME[d]
        x = run(warm(), p + ("message: " + prev + " " if prev else "") + "message: ")
        x, m = generate(x, 50, np.random.default_rng(5000 + 10 * k + i))
        xs.append(x); texts.append(m); prev = m
    return xs, texts
rows, dist = [], []
for k in range(40):
    xa, ta = cascade(EV_A, k); xb, tb = cascade(EV_B, k)
    rows.append([int(ta[i] != tb[i]) for i in range(5)])
    dist.append([float(np.linalg.norm(a - b)) for a, b in zip(xa, xb)])
rows, dist = np.array(rows), np.array(dist); md = dist.mean(0)
from collections import Counter
R = {"seed": SEED, "leak": LEAK, "rho": RHO, "event_A": EV_A, "event_B": EV_B, "trials": 40,
     "frac_text_changed_per_node": [round(float(v), 3) for v in rows.mean(0)],
     "reached_node5_frac": round(float(rows[:, 4].mean()), 3),
     "patterns": {"".join(map(str, k)): v for k, v in Counter(map(tuple, rows)).items()},
     "mean_state_dist_per_node": [round(float(v), 4) for v in md],
     "amplify_nodes": [CHAIN[i] for i in range(1, 5) if md[i] > md[i - 1]],
     "dampen_nodes": [CHAIN[i] for i in range(1, 5) if md[i] < md[i - 1]]}
json.dump(R, open(OUT, "w"), indent=1); print(json.dumps(R, indent=1))
