"""Diagnostic after the run (not a prediction): T2 accuracy per field at 30% and 50% loss."""
import json, numpy as np, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "experiments"))
import sc1_tasks as SC
D = 10_000; rng = np.random.default_rng(7)
values = {"x": [str(i) for i in range(10)], "y": [str(i) for i in range(10)], "height_mm": [str(i * 100) for i in range(1, 51)],
          "owner": SC.ROBOTS, "room": SC.ROOMS, "on": SC.SURFACES}
bip = lambda: rng.choice(np.array([-1, 1], dtype=np.int8), size=D)
O = {o: bip() for o in SC.OBJECTS}; F = {f: bip() for f in SC.FIELDS}; V = {(f, v): bip() for f, vs in values.items() for v in vs}
per = {}
for s in range(16):
    st = SC.make_task(900 + s)["init"]; tot = np.zeros(D, np.int32)
    for k, v in st.items():
        o, f = k.split("."); tot += (O[o] * F[f] * V[(f, v)]).astype(np.int32)
    holo = np.sign(tot).astype(np.int8); holo[holo == 0] = 1
    for loss in (0.3, 0.5):
        h = holo.astype(np.int32).copy(); h[rng.choice(D, int(loss * D), replace=False)] = 0
        for k, v in st.items():
            o, f = k.split("."); u = h * (O[o] * F[f]).astype(np.int32)
            best = max(values[f], key=lambda c: int(u @ V[(f, c)].astype(np.int32)))
            r = per.setdefault(f"{loss}:{f}", [0, 0]); r[0] += best == v; r[1] += 1
out = {k: round(a / b, 4) for k, (a, b) in sorted(per.items())}
print(json.dumps(out, indent=0)); json.dump(out, open("DIAG_T2.json", "w"), indent=1)
