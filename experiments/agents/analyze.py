"""Paired analysis per task: the RSOS arm vs each baseline (exact McNemar = one-sided sign test on the discordant
tasks), Holm over the baselines, per model and pooled over models. Also accuracy, mean calls and tokens per arm.
Usage: python analyze.py results.jsonl rsos_<code> [out.json]"""
import sys, json, collections
from scipy.stats import binomtest

def holm(ps):
    o = sorted(range(len(ps)), key=lambda i: ps[i]); out = [0] * len(ps); run = 0
    for j, i in enumerate(o): run = max(run, min(1, (len(ps) - j) * ps[i])); out[i] = run
    return out

def analyze(path, target):
    R = [json.loads(l) for l in open(path)]
    by = collections.defaultdict(dict)
    for r in R: by[(r["model"], r["arm"])][r["task"]] = r
    models = sorted({r["model"] for r in R}); arms = sorted({r["arm"] for r in R})
    acc = {f"{m}|{a}": {"acc": sum(x["correct"] for x in by[(m, a)].values()) / max(1, len(by[(m, a)])), "n": len(by[(m, a)]),
                         "calls": sum((x["calls"] or 0) for x in by[(m, a)].values()) / max(1, len(by[(m, a)])),
                         "tokens": sum((x["tokens"] or 0) for x in by[(m, a)].values()) / max(1, len(by[(m, a)])),
                         "errors": sum(1 for x in by[(m, a)].values() if x["error"])} for m in models for a in arms}
    base = [a for a in arms if not a.startswith("rsos_")]; out = {"accuracy": acc, "per_model": {}, "pooled": {}}
    def test(pairs):
        b = sum(1 for x, y in pairs if x and not y); c = sum(1 for x, y in pairs if y and not x)
        return {"rsos_only": b, "base_only": c, "n": len(pairs), "p": float(binomtest(b, b + c, 0.5, alternative="greater").pvalue) if b + c else 1.0}
    for scope in models + ["pooled"]:
        ms = models if scope == "pooled" else [scope]; res = {}
        for a in base:
            pairs = [(by[(m, target)][t]["correct"], by[(m, a)][t]["correct"]) for m in ms for t in by[(m, target)] if t in by[(m, a)]]
            res[a] = test(pairs)
        h = holm([res[a]["p"] for a in base])
        for a, x in zip(base, h): res[a]["holm"] = x
        res["all_pass"] = all(res[a]["holm"] < 0.05 for a in base)
        (out["pooled"] if scope == "pooled" else out["per_model"]).update(res if scope == "pooled" else {scope: res})
    return out

if __name__ == "__main__":
    o = analyze(sys.argv[1], sys.argv[2]); print(json.dumps(o, indent=1))
    if len(sys.argv) > 3: json.dump(o, open(sys.argv[3], "w"), indent=1)
