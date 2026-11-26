"""T7: structure vs names between agents. See PREREGISTRATION_T7.md."""
import numpy as np
import networkx as nx

from common import save
from rsoslang.protocol import world, vocabulary, message, add_accent, decode_by_names, decode_by_structure, RELATIONS


def connected_concepts(g, rng, k=6):
    u = g.to_undirected()
    for _ in range(100):
        start = int(rng.integers(g.number_of_nodes()))
        comp = list(nx.bfs_tree(u, start, depth_limit=3))
        if len(comp) >= k:
            return comp[:k]
    return list(range(k))


def trial(seed, participants=2, noise=0.0):
    rng = np.random.default_rng(seed)
    g = world(rng)
    shared = {c: f"s{c}" for c in g.nodes}
    sender, receiver = vocabulary(rng, 30, shared), vocabulary(rng, 30, shared)
    concepts = connected_concepts(g, rng)
    msg = message(g, concepts, sender)
    for p in range(participants - 2):
        msg = add_accent(msg, f"p{p}", lambda x, p=p: f"{x}@{p}")
    if noise:
        msg["carrier"] = [(a, b, RELATIONS[rng.integers(len(RELATIONS))] if rng.random() < noise else r)
                          for a, b, r in msg["carrier"]]
    truth = {sender[c]: c for c in concepts}
    by_name = decode_by_names(msg, receiver)
    by_struct = decode_by_structure(msg, g)
    acc = lambda d: float(np.mean([d.get(n) == c for n, c in truth.items()]))
    return acc(by_name), acc(by_struct)


def main():
    seeds = range(1000, 1020)
    base = [trial(s) for s in seeds]
    three = [trial(s, participants=3) for s in seeds]
    noisy = [trial(s, noise=0.1) for s in seeds]
    names, struct = np.mean([b[0] for b in base]), np.mean([b[1] for b in base])
    summary = {
        "H1_structure_vs_names": {"names": round(float(names), 3), "structure": round(float(struct), 3),
                                  "pass": bool(struct >= 0.9 and struct - names >= 0.5)},
        "H2_constant_carrier": {"two": round(float(struct), 3), "three": round(float(np.mean([t[1] for t in three])), 3),
                                "pass": bool(abs(struct - np.mean([t[1] for t in three])) <= 0.02)},
        "H3_noise_10pct": {"structure": round(float(np.mean([n[1] for n in noisy])), 3),
                           "pass": bool(np.mean([n[1] for n in noisy]) >= 0.7)},
        "chat_reference": "EXP-008: relations 100% vs symbols 19.85%",
    }
    path, digest = save("T7-PROTOCOL", {"summary": summary})
    print(path, digest)
    for k, v in summary.items():
        print(k, v)


if __name__ == "__main__":
    main()
