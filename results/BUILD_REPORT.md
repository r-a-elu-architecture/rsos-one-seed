# Build report: T1–T12 in the owner's timeline order (16 Nov 2026)

Built autonomously at the owner's request ("we do everything, then we identify where it needs to be changed"). Every
experiment was pre-registered before it ran. Every negative is reported next to the positives. `./reproduce.sh`
reruns all of it. 73 tests pass.

## What exists now

| Step | Built | Where |
|---|---|---|
| **Language core** | 90 statements covering all 87 operator-register rows. Meanings in three tiers: fixed core (D80), declared bindings, search. Host checks, diagnostics, IR with lineage and units, spec | `src/rsoslang/`, `spec/LANGUAGE.md`, `spec/REFERENCE.md` |
| **Runtime** | Every operator has its own effect (pierce ≠ attach, region ≠ point, direction matters, heal, beam, flows, colour state, route by state, re-host…) | `src/rsoslang/runtime/`, `spec/SEMANTICS.md` |
| **T1 Safety** | The cue framework's own Spine (seven virtues), safety modes and wording flags, connected read-only. Consent required for person-facing operations (E018). Forbidden wording blocked (E019). Modes enforced (E020). Return to baseline always added. Hash-chained audit | `src/rsoslang/governance.py` |
| **T2 Mind runtime** | A program for a person compiles into a practice session in the owner's own words: heal, beam down, protect, gather, grey, mental models, choose, route, anchor, scent, three futures, schedules; baseline last | `src/rsoslang/mind/session.py` |
| **T3 Body channel** | The session is written as an RSX program and compiled by the cue framework's own RSX compiler into a timeline of visual, auditory, vibration, smell and taste events. Vibration codes are validated by that compiler | same |
| **T4 Identity** | Seven levels; archetypes from the cue framework; built persons (synthetic); host-specific Override (70 + heart attack → calmness; drive blocked by the Spine as predicted harm); seeded population | `src/rsoslang/identity.py` |
| **T5 Worlds and hosts** | Body–society world (chat 1 T66) in the language; chat 2's same-dot experiment re-run on real data | `examples/body_society.rsl`, `results/T5_REPORT.md` |
| **T6 Painting** | Program ⇄ painting compiler. **Browser editor** (`docs/editor.html`): gestures by click, the live RSOS program, effects from 800 measured runs, shareable links. Automatic painting of LangGraph-style agent graphs, with gestures → graph-edit patches | `src/rsoslang/painting/`, `docs/editor.html` |
| **T7 Communication protocol** | Structural carrier + one accent layer per participant; decoding by structure vs by names | `src/rsoslang/protocol.py` |
| **T8 House of rooms, two runtimes** | One program (the robot-head house) runs as a person's session and as an agent, with equivalence checks | `src/rsoslang/house.py` |
| **T9 Discovery** | Search over placements; removal test; induction of a placement rule; transfer to another host | `src/rsoslang/discovery.py` |
| **T10 Time and video** | Recorded runs as frames: play, slow, pause, rewind, cut, branch (counterfactual); a painting at every frame | `src/rsoslang/timeline.py` |
| **T11 Population and Earth** | 100 built persons on the cue framework's person simulator → households → market, cash conserved | `experiments/t11_earth.py` |
| **T12 Launch package (prepared, private)** | LICENSE (Apache 2.0), NOTICE, CITATION.cff, `reproduce.sh`, landing page `docs/index.html`, release whitelist | repo root, `docs/` |

## Every pre-registered result

| Test | Result | Pass |
|---|---|---|
| R-003 chat 1 move + pierce interaction positive | **Negative** in 40/40 random worlds (−0.103); pierce below attach in 39/40 | **No** |
| R-003 rotation rewires many links; codec | Median 114 links vs 1; 256/256 | Yes |
| R-004 car-seat program structure | 4 → 7 → 49, as in chat 1 | Yes |
| R-004 triangle > point, internal > whole, forward > reversed, diverse search > random | 10/40, 10/40, 13/40, 5/12 | **No** |
| Round 2 (owner's rules R1–R11) | 4 of 5 predictions; grey turns −1.155 into −0.149 | Mostly |
| PAINT-1 the place decides (head / heart / brain / near) | 4 distinct outcomes per guest; near leaves the node untouched; grey 6.2% → 0% crashes; composed program **0.488 → 0.780** held-out accuracy | Yes (5/5) |
| T5 same dot changes sign across real hosts (chat 2 EXP-014) | No interval excludes 0 (wine at ceiling); one rank correlation −0.30 matches chat 2's −0.28 | **No** |
| T7 structure carries meaning, names do not | **98.3% vs 3.3%**; carrier constant with a third participant | Yes |
| T7 graceful under 10% relation noise | **47.5%** | **No** |
| T8 one program, two runtimes | Person: 5 steps, 37 timeline events. Agent: **0.488 → 0.762**; without analogical reasoning 0.668. Intent, trace and causal equivalence pass | Yes |
| T9 the discovered program holds on held-out data | 0.681 vs the best possible 0.689 | Yes |
| T9 the removal test locates what carries the function | Every gesture carries some (≥ 0.015); the "carries nothing" arm fails | **No** |
| T9 the induced placement rule transfers to another host | **0.339 → 0.805** | Yes |
| T11 cueing propagates person → household → market | Distress −4.73 [−5.11, −4.39]; spending changes | Yes |
| T11 cash conserved | Exactly, every day | Yes |
| T11 the market's sign is set by the distress → spending relation | **−53,192 vs +52,811**, as chat 3 (−6,142 vs +3,662) | Yes |
| T11 fixed vs adaptive | Fixed better on distress (0.31 vs 5.05), adaptive better on agency (9.81 vs 9.50), as chat 3 | (reported) |

## Hard truth

1. **The language, the two runtimes and the safety layer are real, connected and tested.** One program can now become
   an agent change and a person's practice session, compiled by the cue framework's own compiler. That is the
   assembly no other system has. It is the strongest thing built.
2. **The strongest measured results are in hosts we built:**
   - the support agent (PAINT-1, T8, T9);
   - the cue framework's person simulator (T11).

   They show the operators have exact, place-dependent, measurable meanings, and that rules found by search transfer
   to another host.
3. **Where the test was outside our own design, the claims from the chats did not reproduce:**
   - random worlds (R-003, R-004);
   - real datasets with a simple learner (T5).
4. **Not done, and not possible in this session:**
   - studies with people;
   - different AI models reading the same shapes (needs API access);
   - an outside reproduction;
   - the speed test (needs the owner as the first user: protocol in `spec/SPEED_TEST.md`).

## What to review first (proposed)

1. The negative results: R-003/R-004 (random worlds), T5 (real data), T7 noise, T9 removal. Change the logic in
   rounds with the owner, test on new held-out hosts.
2. The speed test with the owner (`spec/SPEED_TEST.md`).
3. The publication decision (D81): the whitelist in `RELEASE_WHITELIST.txt`.

## After the build (16 Nov 2026, evening)

| Test | Result | Pass |
|---|---|---|
| T7b tolerant decoder | 10% noise 47.5% → 89.2%; clean 93.3% (target 95%) | Noise yes, clean no |
| **T7c exact first, tolerant fallback (now the protocol's decoder)** | Clean **98.3%**, 10% noise **93.3%**, 20% 68.3%, 30% 66.7% | **Yes** |
| **X1 a system built outside this session** (the cue framework's agent repair loop), steered only by the fixed entry-side meanings | Top = supervisory → meta repair fixes **92.7%**; side = lateral 74.0%; surface 39.0%. Top − surface +0.537 [+0.477, +0.593], with less budget (2.16 vs 3.35 repairs) | **Yes** |

**Reading of X1:** the repair strategies are the cue framework's own. The language's part is that its fixed meanings
(D80) chose them, and that the "top = supervisory" meaning selected the best one. Limitation: the automatic painter
did not recognise the archetype names (all painted as paths); a role dictionary for archetypes is needed.

**MCP server:** 7 tools, tested in-process and end-to-end over stdio (`python -m rsoslang.mcp_server`).
**Speed test:** ready in the editor (timed tasks, export) with a code-arm timer. It waits for the owner, as the first
user.
