# Seals: priority without disclosure

Every claim in RSOS carries its layer: layer 1 is physical reality (true by measurement with instruments), layer 2 is
the reality of AI and computation (true by execution: built, run and measured). The sealed tests below are layer 2.

A seal is the SHA-256 hash of a private document, published with a timestamp. The document stays private; the hash
proves that this exact text existed at the time of the commit that published it. If its content is later claimed by
anyone, the author can open the document and anyone can check it against the hash below.

| Sealed (UTC) | What | SHA-256 |
|---|---|---|
| 2026-11-19 19:29 | The White Dragon discovery loop (from question to pre-registered, beacon-drawn, confirmed prediction), the ordering law of the operation table, and RSOS lineage forensics. Author: R. A. Elu | `60c65ef3fd4452898e5a596c2b7acfca5c852ace22ffdf3cea1fbcad16e1e09f` |
| 2026-11-19 22:20 (predictions), 22:23 (results) | The roots structure, version 1: a spatial nested integrity structure with forensic roots; predictions, code and results. Hash of the four files concatenated in this order: PREREG, code, results data, results text | `5446a57023da3b454c95bff96591baaa28087d0d1602b372fb3212da816286c2` |
| 2026-11-19 22:23 | The roots hypothesis, version 2: design of a physical test of instant and of permanent, spreading influence | `a29539803673726561335ae6fd6b1a5dfb6ba6c2cb6c5c8cc8009a605291c28e` |
| 2026-11-19 22:27 (predictions), 22:29 (results) | The roots hypothesis, version 2b in layer 2: a simulation of how one tiny change grows and persists (predictions, code, results, diagnostic; six files concatenated in that order) | `f8054ea1e598b4b1ab53da49c04afb6de3dc8f76a0e99c8f0464e245c6b2bb73` |
| 2026-11-19 22:52 (predictions), 22:53 (results) | Layer-2 tests of a spatial blockchain and forensics design: four hypotheses (predictions, code, results; four files concatenated) | `398234211eb54be3d807e0970bbf0286f216c308a7a4038a5c1eefe26a35a344` |
| 2026-11-19 23:36 (register and predictions), 23:37 (results) | A register of 29 hypotheses in two layers, and three layer-2 tests: knowing the events of a world, a quantum structure as a chain of nodes, a holographic representation (register, predictions, code, results, diagnostic; seven files concatenated) | `abdca42bc31c39a236f73ab191416f62d2c9df3b428f9480ddcaf50d6b17b5f6` |

Check: `sha256sum <document>` (for the roots structure, of the four files concatenated) must print the hash above. The sealed documents are long and specific, and the first also contains a random nonce, so no hash can be
reproduced by guessing its text.
