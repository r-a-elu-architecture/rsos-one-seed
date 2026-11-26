"""U171 violet organism: hubs (Mathematics, Distributed systems, Level C) = pure violet centre joined to every shade
by a sphere-tube bridge (one step); the other 21 nodes re-placed on the dark->light line by the same spectral method.
Relation distance: hub pair = 1 (one bridge); two shades = min(line distance, 2 via the centre).
Check against the documented connections; disclosure: the hub choice used that record."""
import json, itertools, numpy as np, importlib.util
spec = importlib.util.spec_from_file_location("s1", "shades.py"); src = open("shades.py").read()
N = eval(src[src.index("N = {") + 4: src.index("}\nnames") + 1])
HUBS = ["Mathematics", "Distributed systems", "Level C"]
names = [n for n in N if n not in HUBS]
F = {n: set("law:" + a for a in N[n].split("|")[0].split(",")) | set("pl:" + b for b in N[n].split("|")[1].split(",")) for n in N}
S = np.array([[len(F[a] & F[b]) / len(F[a] | F[b]) for b in names] for a in names])
L = np.diag(S.sum(1)) - S; w, V = np.linalg.eigh(L); order = [names[i] for i in np.argsort(V[:, 1])]
sh = {n: k + 1 for k, n in enumerate(order)}
def dist(a, b):
    if a in HUBS or b in HUBS: return 1
    return min(abs(sh[a] - sh[b]), 2)
def dline(a, b): return abs(sh[a] - sh[b])
chk = json.load(open("BRIDGE_CHECK.json")); pairs = [tuple(p) for p in chk["pairs"]]
nodes = sorted({n for p in pairs for n in p})
obs = np.mean([dist(*p) for p in pairs]); allp = np.mean([dist(a, b) for a, b in itertools.combinations(nodes, 2)])
nonhub = [p for p in pairs if not set(p) & set(HUBS)]
obs_line = np.mean([dline(*p) for p in nonhub]); nh_nodes = sorted({n for p in nonhub for n in p})
all_line = np.mean([dline(a, b) for a, b in itertools.combinations(nh_nodes, 2)])
rng = np.random.default_rng(0); vals = [sh[n] for n in nh_nodes]; perm = []
for _ in range(20000):
    s2 = dict(zip(nh_nodes, rng.permutation(vals))); perm.append(np.mean([abs(s2[a] - s2[b]) for a, b in nonhub]))
p = float(np.mean(np.array(perm) <= obs_line))
out = {"centre": HUBS, "shades": [{"shade": f"v{sh[n]}", "node": n} for n in order],
       "check": {"organism_mean_connected": obs, "organism_mean_all": allp, "line_only_nonhub_connected": obs_line,
                 "line_only_nonhub_all": all_line, "perm_p_nonhub": p, "n_pairs": len(pairs), "n_nonhub_pairs": len(nonhub)}}
json.dump(out, open("SHADES_v2.json", "w"), indent=1)
print("centre:", HUBS); [print(f"v{sh[n]}", n) for n in order]; print(json.dumps(out["check"], indent=1))
