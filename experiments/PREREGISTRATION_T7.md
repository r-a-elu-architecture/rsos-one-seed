# T7 pre-registration: the communication protocol between agents (written before running)

Chat 2 S49–S61 (the owner):
- a constant main channel, the visual structure, the same for all participants;
- one accent layer per participant;
- a third participant adds a layer while the main channel stays the same;
- meaning carried by structure, so every model and every person can read it.

**Protocol (`src/rsoslang/protocol.py`).** A message is a small scene: objects and typed relations (above, inside,
pierces, flows to, same colour state). That is the carrier. Each participant also adds an accent layer: its own private
names for the objects.

**Test (between our own agents; different AI models need API access this session does not have).**
- 20 worlds, each a shared world of 30 concepts with typed relations.
- Each agent has a private vocabulary; 20% of its names coincide with another agent's by chance.
- A sender describes 6 related concepts.
- The receiver decodes either by **names** (looking the sender's names up in its own vocabulary) or by **structure**
  (finding where the scene's relational pattern sits in its own world).

| # | Hypothesis | Pass rule |
|---|---|---|
| H1 | Structure carries meaning that names do not (chat 2 EXP-008: 100% vs 19.85%) | Structural decoding ≥ 90% and at least 50 points above name decoding |
| H2 | The main channel stays constant when participants are added: each new accent layer leaves structural decoding unchanged | Accuracy with 3 participants within 2 points of 2 participants |
| H3 | Graceful under noise: 10% of relations flipped | Structural decoding ≥ 70% |
