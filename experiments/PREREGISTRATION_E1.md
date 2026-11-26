# E1 pre-registration: the metric balls under the White Dragon's light

Written before the run. Owner, 17 Nov 2026: every RSOS metric and echo metric is a ball (a sub-node of the RSOS
node). The White Dragon's white light heals (each archetype with its own style: lion = courage, tiger =
precision); the golden light finds the best paths between balls, domains and the unseen; green particles land at
an exact place, become part of it, open that place's library, and spread green flow to every connected domain;
the effect is largest where the lack has lasted longest. Claim to check: the metrics then work as a creative,
cross-domain, cybernetic language module that grows exponentially, and the same happens inside each sub-ball.

## Model (`src/rsoslang/dragon.py`)

- **Balls**: 48 metrics (43-metric log, 27-metric echo log, ledger additions), each with relations read from its
  2025 definition (`data/metric_balls.json`) and an object.
- **Observable**: a relation is observable when a built RSOS test measures it (drift C1, recovery C1, compression
  C1, integrity T7c, propagation R-003, persistence and lineage U1, containment and ethics T1/U1, coupling and
  resonance S1, depth U1); anticipation, autonomy, awareness, bias and balance are not yet observable; nothing on
  object `model` is observable from outside. **Deficit** = share of a ball's relations that are not observable
  (1.0 for object `model`).
- **Library**: 8 domains × 6 measures with relations (`data/domain_books.json`): biology, neuroscience,
  economics, physics, chemistry, aerodynamics, socio-technical, communication.
- **Golden light**: a path ball → measure exists when they share ≥ 1 relation (structure mapping).
- **Green particle**: lands on the shared relation; the child ball = ball × measure with the union of relations,
  a readable definition and the RSOS observable that measures it. Child deficit counted on its own relations.
- **White light (filter)**: keep a child only if it is measurable (has an observable relation, object not `model`
  unless the measure supplies an observable), its relation signature is new, and it passes the good-intention
  rule: a child with `bias` must also carry `ethics` or `containment`.
- **Styles**: lion = the path adding the most new relations (boldest); tiger = the path sharing the most
  relations and adding the fewest (most precise).

## Predictions

- P1: unfiltered growth is exponential: generation sizes rise by ≥ 3× from gen 0 → 1 and gen 1 → 2.
- P2: with the white-light filter growth stays bounded (gen 2 survivors < 3× gen 1 survivors) and still creates
  new signatures (gen 2 survivors > 0).
- P3: with a budget of 20 particles, landing in proportion to deficit reduces total deficit ≥ 1.5× more than
  uniform landing (200 seeds). Partly true by construction (gain ≤ deficit); reported as a consistency check.
- P4: gen 1 survivors cover ≥ 6 of the 8 domains.
- P5: lion reaches more distinct domains per 20 particles than tiger; tiger children have lower mean deficit.
- P6: every ball with deficit > 0 gets at least one measurable child in gen 1 (heal coverage).

This tests the mechanism (growth, healing coverage, cross-domain reach), not whether each fused metric is
scientifically valid; that needs data per child.
