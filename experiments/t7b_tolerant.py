"""T7b: noise-tolerant decoding. See PREREGISTRATION_T7B.md."""
import numpy as np

from common import save
from rsoslang.protocol import world, vocabulary, message, decode_by_names, decode_tolerant, RELATIONS
from t7_protocol import connected_concepts


def trial(seed, noise):
    rng = np.random.default_rng(seed)
    g = world(rng)
    shared = {c: f"s{c}" for c in g.nodes}
    sender, receiver = vocabulary(rng, 30, shared), vocabulary(rng, 30, shared)
    concepts = connected_concepts(g, rng)
    msg = message(g, concepts, sender)
    nrng = np.random.default_rng(seed + 500)
    if noise:
        msg["carrier"] = [(a, b, RELATIONS[nrng.integers(len(RELATIONS))] if nrng.random() < noise else r)
                          for a, b, r in msg["carrier"]]
    truth = {sender[c]: c for c in concepts}
    acc = lambda d: float(np.mean([d.get(n) == c for n, c in truth.items()]))
    return acc(decode_by_names(msg, receiver)), acc(decode_tolerant(msg, g))


def main():
    seeds = range(1000, 1020)
    res = {nz: [trial(s, nz) for s in seeds] for nz in (0.0, 0.1, 0.2, 0.3)}
    m = {nz: round(float(np.mean([r[1] for r in v])), 3) for nz, v in res.items()}
    names = round(float(np.mean([r[0] for r in res[0.0]])), 3)
    summary = {"H1_clean": {"accuracy": m[0.0], "pass": m[0.0] >= 0.95},
               "H2_noise_10": {"accuracy": m[0.1], "t7_exact_matcher": 0.475, "pass": m[0.1] >= 0.70},
               "H3_more_noise": {"20%": m[0.2], "30%": m[0.3]},
               "H4_names": {"accuracy": names, "pass": names < 0.10}}
    path, digest = save("T7B-TOLERANT", {"summary": summary})
    print(path, digest)
    for k, v in summary.items():
        print(k, v)


if __name__ == "__main__":
    main()
