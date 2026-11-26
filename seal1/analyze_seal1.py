"""SEAL1 analysis: decides the colours exactly as PREREG_SEAL1.md says; writes seal1/RESULTS_SEAL1.json and .md."""
import os, sys, json, glob, gzip, shutil, subprocess
ROOT = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(ROOT); OUT = os.environ.get("SEAL1_OUT") or os.path.join(ROOT, "out")
ORG8_ROWS = {"Information theory": [20], "Protocol theory": [18], "Databases": [9], "Ledgers, finance, economics": [7],
             "Human reasoning (the house)": [5], "Linguistics, human-AI comms": [16], "Earth and space sciences": [11],
             "B · protocol between machines; first beam": [19], "Mathematics: operator algebra, theorems, zoom": "all",
             "Distributed systems": "all", "Mathematics (domain)": "all", "C · same laws on many hosts": "all"}

def merged(name):
    d = os.path.join(OUT, name, "diag"); os.makedirs(d, exist_ok=True); return d

def main():
    import seal1 as S1; R = {}
    # road 8
    d = merged("beam_merged"); [shutil.copy(f, d) for f in glob.glob(os.path.join(OUT, "beam_*", "diag", "beam6_p*.json"))]
    import beam6 as B6; os.chdir(os.path.dirname(d)); B6.analyze(); R["road8"] = json.load(open(os.path.join(d, "QUICK_BEAM6.json")))
    # road 10
    d = merged("partners_merged"); rows = []
    for f in glob.glob(os.path.join(OUT, "partners_*", "diag", "partners5_p0.json")):
        if "merged" not in f: rows += json.load(open(f))
    json.dump(rows, open(os.path.join(d, "partners5_p0.json"), "w"))
    import partners5 as P5; os.chdir(os.path.dirname(d)); P5.analyze(); R["road10"] = json.load(open(os.path.join(d, "QUICK_PARTNERS5.json")))
    # laws
    d = merged("laws_merged"); shutil.copy(os.path.join(REPO, "experiments", "laws", "diag", "exact.json"), d)
    for v in S1.SHADES:
        shutil.copy(os.path.join(OUT, f"laws_collect_{v}", "diag", f"l6trace_v{v}.json.gz"), d)
        shutil.copy(os.path.join(OUT, f"laws_local_{v}", "diag", "l6local_p0.json.gz"), os.path.join(d, f"l6local_p{v}.json.gz"))
    import laws6 as M; M.SEEDS = [S1.LAW_SEED]; M.SHADES = S1.SHADES; os.chdir(os.path.dirname(d)); M.analyze()
    R["laws"] = json.load(open(os.path.join(d, "QUICK_LAWS6.json")))["summary"]
    ver = []
    for v in S1.VERIFY:
        tr = json.load(gzip.open(os.path.join(OUT, f"verify_{v}", "diag", f"l6trace_v{v}.json.gz"), "rt"))[str(S1.LAW_SEED)]["v5m"]["trace"]
        n = sum(len(t["need"]) for t in tr); off = sum(not x for t in tr for x in t["need"]); ver.append({"v": v, "precision": 1 - off / max(1, n), "landings": n})
    R["law4_noise_free"] = {"shades": ver, "pass": sum(x["precision"] >= 0.90 for x in ver) >= 10}
    # ORG8 re-check
    os.chdir(os.path.join(REPO, "experiments", "allnodes")); subprocess.run([sys.executable, "analyze_org8.py"], check=True)
    o = json.load(open("RESULTS_ORG8.json")); green = {int(k): v["green"] for k, v in o["shades"].items()}
    R["org8"] = {"n_green": o["n_green"], "green": green,
                 "rows": {row: (all(green.values()) if sh == "all" else all(green[s] for s in sh)) for row, sh in ORG8_ROWS.items()}}
    C = {"8 Physical layer and first beam": R["road8"]["ROW_PASS"], "10 Domains with partners": R["road10"]["ROW_PASS"],
         "All laws as mathematics": R["laws"]["ROW_PASS"] and R["law4_noise_free"]["pass"]}
    C.update({f"{row} (re-check)": ok for row, ok in R["org8"]["rows"].items()})
    R["COLOURS"] = {row: ("turquoise" if ok else "not turquoise") for row, ok in C.items()}
    json.dump(R, open(os.path.join(ROOT, "RESULTS_SEAL1.json"), "w"), indent=1, default=str)
    with open(os.path.join(ROOT, "RESULTS_SEAL1.md"), "w") as f:
        f.write("# SEAL1 results (decided by analyze_seal1.py as PREREG_SEAL1.md says)\n\n| Row | Colour |\n|---|---|\n")
        for row, c in R["COLOURS"].items(): f.write(f"| {row} | {c} |\n")
    print(json.dumps(R["COLOURS"], indent=1))
