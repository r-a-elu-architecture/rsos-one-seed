# ORG-FINAL: confirmatory repeat of ORG5, sealed before run (owner "seal", 22 Nov 2026 05:49)
orgfinal.py = org5.py with ONLY seeds and output file names changed (diff recorded below); analyze_final.py =
analyze_org5.py with only file names changed. Rules, thresholds, arms, structures, tree: exactly PREREG_ORG5.md.
Untouched seeds: twin selection 10400-10401, evaluation 10410-10421, worlds 10900, births 10700-10701, random
structures 10800+, real selection 10500-10501, real evaluation 10600-10607, real random 10850+.
This run alone decides the colours of the rows tested in ORG5 (official green = passes here). No code change, no
re-run, no further seeds after this run.
Critic package (critic_final.py), reported separately, does not decide colours: real data, transferred structure vs
the small-loss noisy-label baseline (with and without decaying rate) that is given the true 25 % noise rate.
Also reported openly: the family's global structure (arm 'glob') and claim B.
1c1
< """ORG5: STRUCTURE crosses the bridge (owner 22 Nov 2026 04:13; advice accepted, "seal" 04:17). Layer 2 twins + real data.
---
> """ORG-FINAL (exact ORG5 code, untouched seeds only; see PREREG_FINAL.md). ORG5: STRUCTURE crosses the bridge (owner 22 Nov 2026 04:13; advice accepted, "seal" 04:17). Layer 2 twins + real data.
16,17c16,17
< Seeds (fresh): twin selection 9400-9401; twin evaluation 9410-9421 (12); new worlds 9900; births 9700-9701;
<   random structures 9800+; real selection 9500-9501; real evaluation 9600-9607.
---
> Seeds (FINAL, untouched): twin selection 10400-10401; twin evaluation 10410-10421 (12); new worlds 10900; births
>   10700-10701; random structures 10800+; real selection 10500-10501; real evaluation 10600-10607.
30c30
< NV = G.NV; SEL, EV, RW, RB = [9400, 9401], list(range(9410, 9422)), 9900, [9700, 9701]
---
> NV = G.NV; SEL, EV, RW, RB = [10400, 10401], list(range(10410, 10422)), 10900, [10700, 10701]
56c56
<     json.dump(out, open(f"RAW5_select_{tag}.json", "w"))
---
>     json.dump(out, open(f"RAWF_select_{tag}.json", "w"))
60c60
<     for f in sorted(gl.glob("RAW5_select_w*.json")): T.update({int(a): b for a, b in json.load(open(f)).items()})
---
>     for f in sorted(gl.glob("RAWF_select_w*.json")): T.update({int(a): b for a, b in json.load(open(f)).items()})
77c77
<             rng = np.random.default_rng(9800 + 100 * v + i)
---
>             rng = np.random.default_rng(10800 + 100 * v + i)
94c94
<     json.dump(out, open(f"RAW5_eval_{tag}.json", "w"))
---
>     json.dump(out, open(f"RAWF_eval_{tag}.json", "w"))
108c108
<     json.dump(out, open(f"RAW5_births_{tag}.json", "w"))
---
>     json.dump(out, open(f"RAWF_births_{tag}.json", "w"))
134c134
<     for n in D: T[n] = {c: float(np.mean([real_st(n, s, c) for s in (9500, 9501)])) for c in RSTRUCTS}; print("real select", n, flush=True)
---
>     for n in D: T[n] = {c: float(np.mean([real_st(n, s, c) for s in (10500, 10501)])) for c in RSTRUCTS}; print("real select", n, flush=True)
138,139c138,139
<         for i, s in enumerate(range(9600, 9608)):
<             rng = np.random.default_rng(9850 + 10 * D.index(n) + i)
---
>         for i, s in enumerate(range(10600, 10608)):
>             rng = np.random.default_rng(10850 + 10 * D.index(n) + i)
145c145
<     json.dump({"tables": T, "rows": rows}, open("RAW5_real.json", "w"))
---
>     json.dump({"tables": T, "rows": rows}, open("RAWF_real.json", "w"))
1c1
< """ORG5 analysis exactly as PREREG_ORG5.md."""
---
> """ORG-FINAL analysis: analyze_org5.py unchanged except file names (PREREG_FINAL.md)."""
11c11
< E = sum([json.load(open(f)) for f in sorted(glob.glob("RAW5_eval_w*.json"))], [])
---
> E = sum([json.load(open(f)) for f in sorted(glob.glob("RAWF_eval_w*.json"))], [])
32c32
< B = sum([json.load(open(f)) for f in sorted(glob.glob("RAW5_births_w*.json"))], [])
---
> B = sum([json.load(open(f)) for f in sorted(glob.glob("RAWF_births_w*.json"))], [])
34c34
< RL = json.load(open("RAW5_real.json"))["rows"]
---
> RL = json.load(open("RAWF_real.json"))["rows"]
40c40
< json.dump(out, open("RESULTS_ORG5.json", "w"), indent=1)
---
> json.dump(out, open("RESULTS_FINAL.json", "w"), indent=1)
