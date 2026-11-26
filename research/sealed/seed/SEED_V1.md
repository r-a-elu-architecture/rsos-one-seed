# The RSOS seed, version 1 (formal draft for the owner's correction)

Written 20 Nov 2026, ~04:15 Vilnius. Private (`corpus/sealed/`). Owner's direction (03:58–04:06): find the seed of
everything, its sub-nodes and sub-sub-nodes, the level where domains start; the two layers are one environment joined
by flows and beams (D106, pending approval); go to level C.

## 0. Seed

**A relation in action**: a dot with a flow, in a space, on a host, seen by a mirror.

## 1. Sub-nodes (level 1) and formal definitions

Let **X** be a space: positions with a metric and a nesting order (rooms inside houses, parts inside objects).

1. **Component** `c = (id, φ, s, ℓ, P, x)`: identity; fingerprint φ ∈ code space (unique, as in T2c roads); state s
   (colour: black → grey → green; a value); level ℓ (zoom); ports P (interfaces); position x ∈ X.
   A **world** W is a finite map from components to states.
2. **Operator** `o = (R, Wr, f)`: a read set R (which states it consults), a write set Wr (which it changes) and a
   transformation f: S^R → S^Wr. The read regime of o is one of: nothing · one key · two keys · condition · whole
   state (scan) (the operation table, D102). Families: read/write; transform (FLOW, compress, fuse); protect (heal,
   contain, seal); transfer (beam, inherit, transplant, re-host).
3. **Grammar** `π`: operators placed in X and ordered; a program is the sequence of objects in the scene. Topology
   (rooms, roads, nesting), depth (layers) and time (order of execution) are its parts. Execution = composition in
   that order.
4. **Host** `H = (E, O_H, B, D, ε)`: an executor E: (π, W) → W'; the operators the host allows O_H; a budget B
   (energy, bits, time); a damage channel D (what destroys or flips states); a per-element read error ε (how often
   the executor misreads one element it must consult). **The host decides how a bundle behaves.**
5. **Mirror** `M`: measurement m: W → observations; reading through relations (inferring a component from the
   components related to it, rule 5); proof (seal, roots); return (feedback edges, mirror and return). The **beam**
   between layers is a mirror whose host is physical: it is *executed, with result* when its effect is measured.

## 2. Sub-sub-nodes (level 2)

| Node | Sub-sub-nodes |
|---|---|
| Component | identity / fingerprint · state / colour · level / zoom · interface / ports |
| Operator | read/write · transform · protect · transfer |
| Grammar | sequence · topology · depth · time |
| Host | substrate · allowed operators · budget · damage · read error |
| Mirror | reading through relations · proof · return · beam |

## 3. Level 3: domains

**A domain = a host × the operators it allows × what it measures.** Physics: host "matter and fields". Chemistry:
"molecules". Biology and medicine: "organisms, bodies". Mind: "the house". Computing: "machines". Finance: "markets".
Earth and space: "planets, orbits, missions". Mathematics: the language of the seed itself. Each field's laws are its
host's rules. A change in the seed or its level-2 nodes reaches every level-3 domain by construction.

## 4. Laws to test (stated before any multi-host test)

- **Law 1 (read scope).** For an operator o on host H, the chance of failure grows with o's effective read scope:
  P(fail) ≈ 1 − (1 − ε_H)^{n_eff(o)}, where n_eff counts the elements the executor must consult. Consequence: the
  ordering nothing < one key < two keys < condition < scan holds on every host whose ε_H > 0.
- **Law 2 (structure/value separation, "blind operation").** If the planner of a program consults only structure
  (keys, roles, positions) and a deterministic executor resolves the values, the planner's failure no longer depends on
  the values' count, and the program's failure reduces to the executor's ε (0 for a deterministic runtime).
- **Law 3 (living structure).** A world stored with reading through relations, healing and selection keeps its states
  under repeated damage while each round's damage stays inside the reading threshold; beyond the threshold it degrades
  gradually instead of collapsing.

## 5. Where existing results sit (coverage, level 2)

| Node | Executed result |
|---|---|
| Operator · read/write | blind planning 318/320 (Law 2, LLM host) |
| Operator · read/write → failure | operation-table ordering 0.00 / 0.14 / 0.17 / 2.31 % (Law 1, LLM host) |
| Operator · transform | FLOW (derive_where), SC2 |
| Operator · protect + Mirror · relations | T2b, T2c (Law 3, hologram host) |
| Mirror · proof | roots v1; seven public seals |
| Host · damage | T2c: erasures, silent flips, load |
| Grammar · topology + Host · mind | the house (practised by the owner) |
| Mirror · beam | none executed |

## 6. Honest notes

- Law 1 in its bare form is the arithmetic of compounding errors and will hold almost everywhere; its value is the
  unification and the per-host prediction, not novelty. Law 2 and Law 3 are the distinctive ones.
- Related frameworks that claimed a structure under all sciences: general systems theory, cybernetics, category
  theory, process calculi, constructor theory. RSOS differs by starting from sealed, measured predictions; the formal
  comparison is still to be written.
