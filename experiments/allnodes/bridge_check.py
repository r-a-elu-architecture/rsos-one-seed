"""Blue-side check of the U169 shade order: the owner's 21 Nov 17:54 document lists 65 known cross-domain
connections (layer-1 record). Map the domains that correspond to placed nodes; compare shade distance of
connected pairs with all pairs (permutation test over node labels)."""
import json, itertools, numpy as np
sh = {o["node"]: int(o["shade"][1:]) for o in json.load(open("SHADES.json"))["order"]}
M = {"Mathematics": "Mathematics", "Physics": "Physics (layer 2)", "Quantum Physics": "Physics (layer 2)", "Chemistry": "Chemistry",
     "Materials Science": "Chemistry", "Biology": "Biology, medicine", "Neuroscience": "Biology, medicine", "Medicine": "Biology, medicine",
     "Psychology": "Human reasoning", "Cognitive Science": "Human reasoning", "Linguistics": "Linguistics", "Economics": "Ledgers, finance",
     "Cosmology": "Cosmology", "Astrophysics": "Cosmology", "Astronomy": "Cosmology", "Planetary Science": "Earth and space",
     "Geology": "Earth and space", "Information Theory": "Information theory", "Telecommunications": "Network",
     "Space Engineering": "Networks, satellites", "Aerospace Engineering": "Networks, satellites", "Cybersecurity": "Protocol theory",
     "Computer Science": "Distributed systems"}
conn = [("Mathematics","Physics"),("Physics","Chemistry"),("Chemistry","Biology"),("Biology","Neuroscience"),("Neuroscience","Psychology"),
        ("Cosmology","Astrophysics"),("Astronomy","Planetary Science"),("Planetary Science","Geology"),("Geology","Chemistry"),
        ("Information Theory","Telecommunications"),("Telecommunications","Space Engineering"),("Aerospace Engineering","Physics"),
        ("Materials Science","Physics"),("Quantum Physics","Computer Science"),("Cybersecurity","Mathematics"),("Mathematics","Computer Science"),
        ("Linguistics","Cognitive Science"),("Medicine","Psychology"),("Economics","Psychology"),("Mathematics","Information Theory")]
pairs = {tuple(sorted((M[a], M[b]))) for a, b in conn if M[a] != M[b]}
nodes = sorted({n for p in pairs for n in p})
d = lambda p, s: abs(s[p[0]] - s[p[1]])
obs = np.mean([d(p, sh) for p in pairs]); allp = np.mean([d(p, sh) for p in itertools.combinations(nodes, 2)])
rng = np.random.default_rng(0); vals = [sh[n] for n in nodes]; perm = []
for _ in range(20000):
    s2 = dict(zip(nodes, rng.permutation(vals))); perm.append(np.mean([d(p, s2) for p in pairs]))
p = float(np.mean(np.array(perm) <= obs))
print(f"{len(pairs)} distinct connected pairs over {len(nodes)} placed nodes")
print(f"mean shade distance: connected {obs:.2f}, all pairs {allp:.2f}, permutation p (connected closer) = {p:.3f}")
for q in sorted(pairs, key=lambda q: d(q, sh)): print(f"  {q[0]} (v{sh[q[0]]}) - {q[1]} (v{sh[q[1]]}): {d(q, sh)}")
json.dump({"pairs": [list(q) for q in pairs], "mean_connected": obs, "mean_all": allp, "p": p}, open("BRIDGE_CHECK.json", "w"), indent=1)
