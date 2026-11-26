"""MAP1 runner (PREREG_MAP1.md). python3 -I run_map1.py <out.json>. Standard library only."""
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hosts import HOSTS, episode  # noqa: E402
from mechanisms import MECHANISMS, M  # noqa: E402

SEEDS = range(1000, 1030)


class Zero(M):
    def act(self, y):
        return 0.0


class One(M):
    def act(self, y):
        return 1.0


def score(hc, mc):
    return sum(episode(hc, mc, s) for s in SEEDS) / len(SEEDS)


def main(out):
    nodes = list(HOSTS)
    J = {h: {m: score(HOSTS[h], MECHANISMS[m]) for m in nodes} for h in nodes}
    base = {h: {"none": score(HOSTS[h], Zero), "always": score(HOSTS[h], One)} for h in nodes}
    ranks, wins = {}, 0
    for h in nodes:
        order = sorted(nodes, key=lambda m: J[h][m])
        ranks[h] = order.index(h) + 1
        mism = sorted(J[h][m] for m in nodes if m != h)
        med = (mism[6] + mism[7]) / 2
        wins += J[h][h] < med
    rank_of = {h: {m: sorted(nodes, key=lambda x: J[h][x]).index(m) + 1 for m in nodes} for h in nodes}
    obs = sum(ranks.values())
    rng = random.Random(21112026)
    as_low = 0
    for _ in range(10000):
        perm = nodes[:]
        rng.shuffle(perm)
        if sum(rank_of[h][m] for h, m in zip(nodes, perm)) <= obs:
            as_low += 1
    p = as_low / 10000
    res = {"P1_wins": wins, "P1_pass": wins >= 11, "P2_rank_sum": obs, "P2_expected_random": 15 * 8, "P2_p": p,
           "P2_pass": p < 0.05, "MAP1_pass": wins >= 11 and p < 0.05, "matched_rank": ranks,
           "J": J, "baselines": base}
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k not in ("J", "baselines")}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
