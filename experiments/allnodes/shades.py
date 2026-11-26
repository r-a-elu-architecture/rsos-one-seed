"""U169 shade placement: each open node's features (main laws, particle placements) from
map/STRUCTURE_MAP_21NOV_1730.md; similarity = Jaccard over features; order = spectral (Fiedler vector of the
similarity graph Laplacian), which puts the most related nodes next to each other on one line; v1 = darkest."""
import numpy as np, json, hashlib
N = {
 "Law 1 read scope": "L1|above,line", "Law 2 blind operation": "L2|outside",
 "Information theory": "L5|inside,tube", "Operator algebra": "L0,COMP|line,pierced",
 "Physics (layer 2)": "L4|inside,tube", "Distributed systems": "L2,ERR|tube",
 "Protocol theory": "L0|pierced", "Physical comm layer": "L4|line", "Network": "ERR|tube",
 "Databases": "ERR|above,inside", "Networks, satellites": "L5|line,tube", "Ledgers, finance": "L0,L4|inside,above",
 "Chemistry": "L5|pierced,tube", "Mathematics": "L1B|line", "Human reasoning": "L3|inside,above",
 "Linguistics": "L5|inside,tube", "Cosmology": "L4|tube", "AI chips (layer 2)": "ERR|inside",
 "Biology, medicine": "L3|inside,tube", "Earth and space": "L5|tube", "Level B": "L0|pierced",
 "Level C": "L0,L1,L2,L3,L4,L5,ERR|inside,above,outside,pierced,line,tube", "Level D": "GEN|inside,line",
 "Level E (layer 2)": "L3|inside"}
names = list(N); F = [set(("law:"+a for a in N[n].split("|")[0].split(","))) | set(("pl:"+b for b in N[n].split("|")[1].split(","))) for n in names]
S = np.array([[len(a & b) / len(a | b) for b in F] for a in F])
L = np.diag(S.sum(1)) - S; w, V = np.linalg.eigh(L); f = V[:, 1]
order = [names[i] for i in np.argsort(f)]
out = [{"shade": f"v{k+1}", "node": n, "features": sorted(F[names.index(n)])} for k, n in enumerate(order)]
json.dump({"code_sha256": hashlib.sha256(open(__file__, "rb").read()).hexdigest(), "order": out}, open("SHADES.json", "w"), indent=1)
for o in out: print(o["shade"], o["node"], "|", ", ".join(o["features"]))
nb = [S[names.index(order[k]), names.index(order[k+1])] for k in range(len(order) - 1)]
rnd = [np.mean([S[i, j] for i, j in zip(p[:-1], p[1:])]) for p in [np.random.default_rng(s).permutation(len(names)) for s in range(1000)]]
print("mean neighbour similarity: placed %.3f, random orders %.3f" % (np.mean(nb), np.mean(rnd)))
