# Level D births: structural diagnosis (23 Nov 2026 03:15, descriptive; data RAW5_births_w*.json, RAWF_births_w*.json)

Test (PREREG_ORG5): child structure = the best mean over BOTH parents' selection tables; pass if child > max(parentA,
parentB) in the child host, over pairs where the structures differ.

| Run | Rows "differ" | Child is a COPY of a parent | Copy: ties / losses | Truly new child: wins / losses |
|---|---|---|---|---|
| ORG5 | 28 | 18 | 17 / 1 | 7 / 3 |
| FINAL | 30 | 22 | 17 / 5 | 4 / 4 |
| Both | 58 | 40 | 34 / 6 | 11 / 7 |

Finding: 40 of 58 tested births were not births. The "child" was one parent's structure picked again, so it could only
tie or lose against max(parents); those rows decided the fail (7/11, 4/12 counted only strict wins vs losses).
Missing structure (map Part I):
1. Generation, not selection: the child is chosen from the parents' existing table; nothing new is composed (no role-by-role
   recombination, no new role). Births = differentiation needs a composition operator (I.4: inherit, fuse, add).
2. Development in the child's own host: the child is never tuned on its own host (selection used only the parents'
   hosts). "The seed grows itself" needs a short self-selection on a development seed of the child host.
3. Counter-shift (P1) was not yet in the organism (ORG5/FINAL predate ORG7); ORG7 showed it lifts every host.
Fix to build next: child = compose(parentA roles ∪ parentB roles) + counter-shift, then grow in the child host on its
own development seed; compare against both parents given the same growth step (fair) and against copy-of-best-parent.

## Quick test births v2 (23 Nov 04:10; development seeds: growth 7200, eval 7210-7212; 10 odd bridges; births2.py)
D1 child > max(transplanted parents): 15 wins / 14 losses / 1 tie (p 0.5). D2 child > max(grown parents): 2 / 14 / 14.
Mean gain over the best transplanted parent +0.002. Finding: growth in the same host makes child and parents express the
same structure (14 of 30 rows identical to a grown parent): the host decides the phenotype, the inherited genome barely
matters here. Second cause: ceiling (G 0.93-0.997 in the child host, the mean of two neighbours, is an easy host).
Not sealable. Structural question for the next build: a birth can beat both parents only where the child's host needs
what neither parent has alone (both lineages' pressures at once), not in an averaged host.
