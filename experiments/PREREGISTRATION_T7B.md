# T7b pre-registration: a noise-tolerant structural decoder (written before running)

T7 failed H3: with 10% of relations flipped, exact structural decoding fell to 47.5%. A tolerant decoder
(`decode_tolerant`) accepts near-matches. It anchors one message object on each candidate object in the receiver's
world, extends along the message's relations (preferring the same relation type, but accepting another), and keeps
the mapping that agrees on the most typed relations.

Same 20 worlds, same messages, same seeds as T7 (1000–1019).

| # | Hypothesis | Pass rule |
|---|---|---|
| H1 | Clean messages are not hurt | ≥ 95% at 0% noise |
| H2 | Graceful under noise (T7's failed H3) | ≥ 70% at 10% noise |
| H3 | Reported, no threshold | Accuracy at 20% and 30% noise |
| H4 | Names stay useless | Name decoding < 10% |
