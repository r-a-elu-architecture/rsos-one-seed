"""SEAL1 FIX1 (25 Nov 2026; PREREG note: seal1/PREREG_SEAL1_FIX1.md; hashes: seal1/SEAL_SEAL1_FIX1.txt).
Bug found at analysis: in seal1.py a "verify" unit sets laws6.ARMS = ["v5m"] and never restores it, so every
"laws_collect" unit that ran later in the same window collected only the v5m arm (analysis: KeyError 'v3').
This script changes nothing sealed. It finds the laws_collect units whose trace lacks any arm, keeps their old
folder as evidence (out/_fix1_old/), and re-runs each one in a FRESH Python process (laws6.ARMS as sealed).
Usage:  python seal1_fix1.py check        (lists the affected units)
        python seal1_fix1.py <window 0..3>   (four windows in parallel; each re-runs its share; resumable)
Then:   python seal1.py analyze"""
import os, sys, gzip, json, shutil, subprocess, time
ROOT = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(ROOT, "out")
ARMS = ["v3", "v5m", "report+popular", "round+round", "random+random", "B"]   # = laws6.ARMS (sealed)
SHADES = list(range(1, 22)); LAW_SEED = 5340

def complete(v):
    f = os.path.join(OUT, f"laws_collect_{v}", "diag", f"l6trace_v{v}.json.gz")
    if not os.path.exists(os.path.join(OUT, f"laws_collect_{v}", "DONE")) or not os.path.exists(f): return False
    with gzip.open(f, "rt") as fh: d = json.load(fh)
    return set(ARMS) <= set(d.get(str(LAW_SEED), {}))

def affected(): return [v for v in SHADES if not complete(v)]

if __name__ == "__main__":
    if sys.argv[1] == "check":
        a = affected(); print("affected laws_collect units:", a, "of", len(SHADES)); sys.exit(0)
    w = int(sys.argv[1]); todo = [v for i, v in enumerate(affected()) if i % 4 == w]
    print("FIX1 window", w, "units", todo, flush=True)
    for v in todo:
        if complete(v): print("skip", v, flush=True); continue
        old = os.path.join(OUT, f"laws_collect_{v}")
        if os.path.exists(old):
            keep = os.path.join(OUT, "_fix1_old", f"laws_collect_{v}")
            if not os.path.exists(keep): os.makedirs(os.path.dirname(keep), exist_ok=True); shutil.move(old, keep)
            else: shutil.rmtree(old)
        t0 = time.time(); print("start laws_collect", v, time.strftime("%H:%M"), flush=True)
        subprocess.run([sys.executable, "-c", f"import seal1; seal1.run_unit('laws_collect', {v})"], cwd=ROOT, check=True)
        print("done laws_collect", v, round((time.time() - t0) / 60, 1), "min", "complete" if complete(v) else "STILL INCOMPLETE", flush=True)
    print("FIX1 WINDOW", w, "FINISHED", flush=True)
