"""FUSE1 (PREREG_FUSE1.md). python3 -I fuse1.py <dir with conversations-*.json> <out.json>. Standard library only."""
import glob
import json
import os
import random
import re
import statistics
import sys

STOP = set("""the and for that this with you are was but not have has had they them their what when where which who
will would can could should from into onto about there here then than also just only very your yours our ours his her
its it's i'm you're don't can't won't all any each every some more most much many such own same other into over under
again once both few out off how why let lets yes yeah okay ok one two three been being were did does doing done make
made like now well get got see say said use used way may might must shall need want know think thing things""".split())
N = 8
tok = lambda s: re.findall(r"\w+", s.lower())


def main_path(conv):
    mp, node, path = conv["mapping"], conv.get("current_node"), []
    while node:
        n = mp.get(node) or {}
        m = n.get("message")
        if m and m.get("content", {}).get("content_type") == "text":
            role = m["author"]["role"]
            text = "\n".join(p for p in m["content"].get("parts", []) if isinstance(p, str))
            if role in ("user", "assistant") and text.strip():
                path.append((role, text))
        node = n.get("parent")
    path.reverse()
    merged = []
    for role, text in path:
        if merged and merged[-1][0] == role:
            merged[-1] = (role, merged[-1][1] + "\n" + text)
        else:
            merged.append((role, text))
    return merged


def grams(t):
    return {tuple(t[i:i + N]) for i in range(len(t) - N + 1)}


def own_mask(u, a_grams):
    cov = [False] * len(u)
    for i in range(len(u) - N + 1):
        if tuple(u[i:i + N]) in a_grams:
            for k in range(i, i + N):
                cov[k] = True
    return cov


def content(ws):
    return {w for w in ws if len(w) >= 3 and w.isalpha() and w not in STOP}


def score(convs):
    rows = []
    for ci, msgs in enumerate(convs):
        seen = set()
        toks = [tok(t) for _, t in msgs]
        for i, (role, _) in enumerate(msgs):
            t = toks[i]
            if role == "user" and i > 0 and msgs[i - 1][0] == "assistant" and len(t) >= 20:
                ag = grams(toks[i - 1])
                cov = own_mask(t, ag)
                shared = any(cov)
                own = [w for w, c in zip(t, cov) if not c]
                kind = "fused" if shared and len(own) >= 20 else ("unfused" if not shared else None)
                after = [toks[j] for j in range(i + 1, len(msgs)) if msgs[j][0] == "assistant"][:5]
                new = content(own) - seen
                if kind and len(new) >= 3 and after:
                    lag = [len(new & set(a)) / len(new) for a in after]
                    carry = len(new & set().union(*map(set, after))) / len(new)
                    rows.append({"c": ci, "kind": kind, "carry": carry, "lag": lag, "n_new": len(new)})
            seen |= content(t)
    return rows


def ratio(rows):
    f = [r["carry"] for r in rows if r["kind"] == "fused"]
    u = [r["carry"] for r in rows if r["kind"] == "unfused"]
    return (statistics.mean(f) / statistics.mean(u)) if f and u and statistics.mean(u) > 0 else None


def main(src, out):
    convs = []
    for f in sorted(glob.glob(os.path.join(src, "conversations-*.json"))):
        for conv in json.load(open(f, encoding="utf-8")):
            convs.append(main_path(conv))
    rows = score(convs)
    r = ratio(rows)
    rng = random.Random(21112026)
    by = {}
    for x in rows:
        by.setdefault(x["c"], []).append(x)
    keys = list(by)
    boots = []
    for _ in range(2000):
        s = [x for k in (rng.choice(keys) for _ in keys) for x in by[k]]
        b = ratio(s)
        if b is not None:
            boots.append(b)
    boots.sort()
    ci = (boots[int(0.025 * len(boots))], boots[int(0.975 * len(boots)) - 1]) if boots else (None, None)
    paired = []
    for k, xs in by.items():
        f = [x["carry"] for x in xs if x["kind"] == "fused"]
        u = [x["carry"] for x in xs if x["kind"] == "unfused"]
        if len(f) >= 3 and len(u) >= 3 and statistics.mean(u) > 0:
            paired.append(statistics.mean(f) / statistics.mean(u))
    above = sum(p > 1 for p in paired)
    from math import comb
    n = len(paired)
    p_sign = sum(comb(n, j) for j in range(above, n + 1)) / 2 ** n if n else 1.0

    def decay(kind):
        xs = [x for x in rows if x["kind"] == kind and len(x["lag"]) == 5]
        l1 = statistics.mean(x["lag"][0] for x in xs) if xs else 0
        l5 = statistics.mean(x["lag"][4] for x in xs) if xs else 0
        return (l5 / l1 if l1 else None), len(xs)

    res = {"conversations": len(convs), "scored_fused": sum(x["kind"] == "fused" for x in rows),
           "scored_unfused": sum(x["kind"] == "unfused" for x in rows),
           "mean_carry_fused": statistics.mean([x["carry"] for x in rows if x["kind"] == "fused"] or [0]),
           "mean_carry_unfused": statistics.mean([x["carry"] for x in rows if x["kind"] == "unfused"] or [0]),
           "F1_ratio": r, "F1_ci95": ci, "F1_pass": bool(r and r >= 1.5 and ci[0] is not None and ci[0] > 1.0),
           "F2_conversations": n, "F2_above_1": above, "F2_median": statistics.median(paired) if paired else None,
           "F2_p_sign": p_sign, "F2_pass": bool(paired and statistics.median(paired) > 1 and p_sign < 0.05),
           "F3_decay_fused_l5_over_l1": decay("fused"), "F3_decay_unfused_l5_over_l1": decay("unfused")}
    df, du = res["F3_decay_fused_l5_over_l1"][0], res["F3_decay_unfused_l5_over_l1"][0]
    res["F3_pass"] = bool(df is not None and du is not None and df > du)
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
