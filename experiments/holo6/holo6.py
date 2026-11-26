"""HOLO6: the particle lands live, at the letter itself (owner 13:00, U159-U164; follows the HOLO5 fever).
HOLO5 found that a healing choice exists at ~27 % of letters, but no bucketed address predicts it (0 landings).
So here the address is the letter itself: at every dispatch with disagreeing lenses, inside the world being run,
the world is frozen (present), every different choice is run forward to the end from its own copy (futures), and the
particle lands on the choice that heals the whole with no channel worse (U164). Otherwise the unhealed quark runs.
The host, channels, lenses and heal() are imported unchanged from the sealed holo5.py (hash-checked).
Layer note: in layer 2 the frozen copy contains the world's own future; a layer-1 scheduler does not know future
bursts and would need a model of the future in their place.
Usage: python holo6.py test [densities] [part]"""
import sys, json, copy, hashlib, importlib.util
import numpy as np
HERE = __file__.rsplit("/", 1)[0] if "/" in __file__ else "."
P5 = f"{HERE}/../holo5/holo5.py"
assert hashlib.sha256(open(P5, "rb").read()).hexdigest() == "dbf92de4660fa9276f5c2025dd8b35a982e10e34b421cb0214c9f9669603470b"
sys_argv = sys.argv; sys.argv = ["holo5", "import"]
sp = importlib.util.spec_from_file_location("h5", P5); h5 = importlib.util.module_from_spec(sp); sp.loader.exec_module(h5)
sys.argv = sys_argv

def run_live(d, seed, coupled=True, H=60):
    w = h5.World(d, seed, "quark", h5.DNA0, coupled)
    landed = letters = futures = 0
    while w.alive():
        ready = w.pre()
        chosen = None
        if ready and len(ready) >= 2:
            ids = {r.id for r in ready}
            fr = copy.deepcopy(w); fr_ready = [p for p in fr.procs if p.id in ids]
            picks = {L: fr.lens_pick(L, fr_ready) for L in ["rr", "hist", "rel"]}
            q = w.lens_pick("quark", ready)                   # the real quark (its K state flows as unhealed)
            alts = {L: p.id for L, p in picks.items() if p.id != q.id}
            if alts:
                letters += 1
                base = copy.deepcopy(w)
                c0 = h5.future(base, q.id, H); futures += 1
                best = None
                for L, pid in alts.items():
                    if best and pid == best[1]: continue
                    c = h5.future(base, pid, H); futures += 1
                    if h5.heals(c, c0) and (best is None or c["G_whole"] > best[2]): best = (L, pid, c["G_whole"])
                if best:
                    landed += 1; chosen = next(p for p in ready if p.id == best[1])
            if chosen is None: chosen = q
        elif ready: chosen = w.choose(ready)
        w.post(chosen)
    return w.G(), {"letters": letters, "landed": landed, "futures": futures}

if __name__ == "__main__" and sys.argv[1] == "test":
    dens = [int(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else h5.DENS
    TS = list(range(500, 516)); H4 = json.load(open(f"{HERE}/../holo4/DNA_healed.json"))["DNA_healed"]
    out = {}
    for d in dens:
        rows = []
        for s in TS:
            b = max(h5.simulate(d, s, "rr"), h5.simulate(d, s, "hist"))
            g, info = run_live(d, s, True)
            gu = run_live(d, s, False)[0] if d == 5 else None
            rows.append({"seed": s, "best_baseline": b, "live": g, "live_uncoupled": gu,
                         "unhealed": h5.simulate(d, s, "quark", h5.DNA0), "holo4": h5.simulate(d, s, "quark", H4), **info})
            print(d, s, round(g - b, 4), info, flush=True)
        out[d] = rows
    json.dump(out, open(f"{HERE}/RAW_HOLO6_{'_'.join(map(str, dens))}.json", "w"), indent=1)
