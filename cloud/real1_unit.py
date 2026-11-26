"""REAL1 sealed unit: one row (and model), one chunk of 5 fresh cells, seed vs the domain's standard with the sealed seed.
Usage: python cloud/real1_unit.py <row> <model-or-> <chunk 0..3>. Writes real/out/<row>_<model>_<chunk>.json.
Cells (fixed in PREREG_REAL1.md): 101..120 (chunk k: 101+5k..105+5k); neuroscience: recording windows 9..28 (chunk k:
9+5k..13+5k), a window beyond the recording is recorded as "beyond recording" and not counted."""
import os, sys, json, time, hashlib
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for line in open(os.path.join(ROOT, "real", "SEAL_REAL1.txt")):
    h, f = line.split()
    if hashlib.sha256(open(os.path.join(ROOT, f), "rb").read()).hexdigest() != h: sys.exit(f"HASH MISMATCH {f}: stop")
sys.path[:0] = [os.path.join(ROOT, "real"), os.path.join(ROOT, "real", "hosts")]
from seed import run
row, model, k = sys.argv[1], sys.argv[2], int(sys.argv[3])
cells = list(range(9 + 5 * k, 14 + 5 * k)) if row == "neuro" else list(range(101 + 5 * k, 106 + 5 * k))
def hosts():
    if row == "quantum": from quantum import Quantum; return {"std": Quantum()}
    if row == "energy": from energy import Energy; return {"std": Energy()}
    if row == "economics": from economics import Economics; return {"std": Economics()}
    if row == "space": from space import Space; return {"std": Space("pq")}
    if row == "robotics": from robotics import Robotics; return {"std": Robotics()}
    if row == "biology": from biology import Biology; return {"std": Biology()}
    if row == "neuro": from neuro import Neuro; return {"std": Neuro(data="/tmp/neuro.npz")}
    if row == "ai_ai": from ai_ai import AiAi; return {"std": AiAi(model)}
    if row == "ai_human": from ai_human import AIHuman; return {"std": AIHuman(spec=model)}
    if row == "ai_agents": from ai_agents import AIAgents; return {"react": AIAgents(spec=model, standard="react"), "selfcons": AIAgents(spec=model, standard="selfcons")}
out = {"row": row, "model": model, "chunk": k, "cells": {}}
for name, h in hosts().items():
    for c in cells:
        t0 = time.time()
        try: r = {m: run(h, c, m) for m in ("seed", "default")}
        except (IndexError, ValueError) as e:
            if row == "neuro": r = {"skip": f"beyond recording: {e}"}
            else: raise
        for m in ("seed", "default"):
            if m in r: r[m] = {q: r[m][q] for q in ("result", "resource", "R", "choices") if q in r[m]}
        r["sec"] = round(time.time() - t0); out["cells"][f"{name}|{c}"] = r; print(name, c, json.dumps(r, default=str)[:300], flush=True)
safe = model.replace("/", "_").replace(":", "_").replace(",", "+")
os.makedirs(os.path.join(ROOT, "real", "out"), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, "real", "out", f"{row}_{safe}_{k}.json"), "w"), default=str, indent=1)
