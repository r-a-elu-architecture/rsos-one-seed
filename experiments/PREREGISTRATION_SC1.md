# Pre-registration SC1: a grounded robot scene as shared state

Fixed 19 Nov 2026, before any model call on SC1. Author: R. A. Elu. Every prediction below is published before the run;
results, confirming or not, go to `experiments/SC1_REPORT.md`, `experiments/FAILURES_MAP.md` and `NEXT_TESTS.md`.

## 1. Question

A7 and A8 measured blind planning on configuration state. A fair critique: the RSOS spatial-symbolic language claims a
use for robots and visual or multi-agent communication, and formal robotics languages already ground spatial
predicates and scene graphs and publish their numbers. SC1 grounds one robot scene and measures, under the A7/A8
conditions:

1. what is transmitted (bytes and tokens) when robots keep one shared scene, for the RSOS program against a scene-graph
   sync and a value delta (JSON Patch), with correct content in every encoding (0 model calls, section 5);
2. exactness, drift repair and model calls when real models plan the changes (sections 4 and 6).

SC1 tests the transfer of the measured protocol to a spatial world. It does not test physical robots, perception or
motion, and it does not measure the RSOS painting syntax (section 8).

## 2. The scene and its mapping to state

A warehouse/kitchen scene shared by six robots: 50 objects, each with six attributes, flattened to the StateBench form
`object.field = value` (300 keys), so the A7/A8 runtime, arms and audit rule apply unchanged.

| State key | Scene meaning | Values | Scene-graph form (baseline G) |
|---|---|---|---|
| `object.x` | grid column of a 10 × 10 floor-plan occupancy grid | 0–9 | node attribute `x` |
| `object.y` | grid row | 0–9 | node attribute `y` |
| `object.height_mm` | height of the object's base above the floor | 100–5000 | node attribute `height_mm` |
| `object.owner` | robot responsible for the object | rover, drone, arm, crane, loader, scout | edge `owned_by` |
| `object.room` | room | kitchen, lab, dock, hall | edge `in_room` |
| `object.on` | supporting surface | table, shelf, floor, cart | edge `on` |
| `object.grip`, `object.weight_g` | added during a task | soft, firm, vacuum; 16–256 | node attributes |

Objects: cup, mug, tray, box, crate, drill, wrench, hammer, bolt, cable, lamp, sensor, bottle, jar, plate, bowl, kettle,
pallet, bin, tote, ladder, helmet, glove, tape, pump, valve, hose, filter, fan, motor, gear, spring, brick, plank, pipe,
panel, screen, camera, battery, charger, radio, beacon, marker, cone, sign, flag, rope, chain, hook, bag.

Requests, as the robots receive them, and the RSOS operation each one compiles to:

| Request (example) | Scene meaning | RSOS | Core |
|---|---|---|---|
| Everything owned by rover is now owned by drone. | hand-over of every object one robot is responsible for | `REHOST owner rover drone` | `reassign_where` |
| Set cup.x to tray.x plus 2, capped at 9. | place the cup two cells right of the tray, clamped to the grid | `INHERIT cup.x tray.x +2 CAP 9` | `derive` |
| Set cup.height_mm to shelf.height_mm plus 500. | 500 mm above | `INHERIT … +500` | `derive` |
| Set plate.x to sign.x + battery.x, capped at 9. | offset composition | `FUSE … CAP 9` | `sum_into` |
| Double crate.y, capped at 9. | scale a coordinate | `SCALE crate.y 2 CAP 9` | `multiply` |
| If cup.room is lab, set cup.on to shelf; otherwise set it to table. | route by state | `ROUTE …` | `select_if` |
| Make tote.height_mm equal to cup.height_mm. | align | `INHERIT tote.height_mm cup.height_mm` | `derive` |
| Remove the line motor.on entirely. | drop a relation | `DEL motor.on` | `delete` |

Generator: `experiments/sc1_tasks.py` (seeded; the A7b long-task rules: 56 requests, dependency chains of depth 4,
three drift events on one robot's copy). Tasks exported to `bench/statebench_v1_SC1.jsonl`, 16 tasks, seeds 900–915,
sha256 `db6b59e77c0e4ca78aa3aaa8e771468a87b3893f4395b50c36e0ad51989b7fc5`. Per task: the start state, the requests,
the true state after every step and the drift events, so any framework can be scored (`bench/score.py`).

Composition of the 896 requests: 504 `derive`, 135 `set`, 95 `sum_into`, 50 `select_if`, 44 `reassign_where`
(hand-overs), 38 `multiply`, 30 `delete`.

## 3. Harness check before any model call (done)

`python experiments/a7_run.py replaycheck SC1` (0 model calls): with oracle plans every arm (B2, X5r, X5b, B2s) ends
exact on 16/16 tasks, all 48 injected drifts are repaired with 0 model calls, no state value reaches the blind planner,
the audit selection is identical across arms, and the frozen A5 files are unchanged (`results/a7_replay_check_SC1_default.json`,
`pass: true`). The existing StateBench files are byte-identical after adding SC1.

## 4. Arms, models and settings

Identical to A8 (`PREREGISTRATION_A8.md`, amendments 4–6 and 8): arms **B2** (one-call JSON Patch with literal values
from the full state, one audit call) and **X5b** (RSOS blind: operations over key names, no state values shown);
prompts byte-identical to A8 (they describe "a configuration state of lines `service.field = value`"; the requests
carry the scene). Temperature 0, top_p 1, `A7_WORKERS=2`.

| Model | Label | Backend | Cost basis |
|---|---|---|---|
| Mistral Large 4 (`mistral-large-4-0`) | `mistral_large40` | `openai`, base `https://api.mistral.ai/v1` | USD at the A8 price sheet (input 1.36, output 4.18 per million) and tokens |
| Gemini 3.8 Flash (`gemini-3.8-flash`) | `gemini_38flash` | `openai`, base `https://generativelanguage.googleapis.com/v1beta/openai` | tokens |

Order: Mistral, then Gemini. A cell cut short (quota, connection) is reported as incomplete with its completed tasks
and rerun with the resume command; nothing is dropped. Further models (GPT-6.2 Sol via Codex, Claude) may follow only
under the same cell, arms and predictions.

## 5. Channel measurement (0 model calls; measured now, not predicted)

`python experiments/sc1_channel.py` → `results/sc1_channel.json`, sha256
`f5a7a3ae6e39401aecff2c1b154aedcd6b722f4114574eedcedc189854d81d6c`. For every step of every task, the message one robot
sends so the others' copies match, with correct content from the ground truth:

| Encoding, all 896 steps | Bytes | Regex tokens | vs JSON Patch (bytes / tokens) |
|---|---|---|---|
| **G** full scene-graph sync (nodes + `on`/`owned_by`/`in_room` edges, compact JSON) | 7,089,308 | 4,750,518 | 90.7× / 124× |
| **P** JSON Patch delta with values + 12-digit state digest | 78,197 | 38,310 | 1 |
| **R** RSOS program + 12-digit state digest | **38,439** | **8,337** | **0.49× / 0.22×** |
| **C** the same program in Core syntax + digest | 50,998 | 16,388 | 0.65× / 0.43× |

| Also measured | RSOS | Baseline | Ratio (bytes / tokens) |
|---|---|---|---|
| Replica check per task: state digest vs full scene | 12 hex digits (48 bits) | full scene graph | 0.0015× / 0.0002× |
| Planner input (A7/A8 protocol): X5b (requests only) vs B2 (full state) | 42,319 B | 122,924 B | 0.34× / 0.35× |

By operation (bytes, R vs P): `reassign_where` **0.059×** (a hand-over is one line instead of one patch entry per
object), `set` 0.49×, `delete` 0.53×, `multiply` 0.66×, `derive` 0.74×, `sum_into` 0.84×, and **`select_if` 1.20×:
RSOS is larger on conditional steps**, because the program carries both branches while the patch carries one result.
Tokens are the regex count used since A1; BPE (o200k) counts are computed on the run machine (P7).

## 6. Predictions (fixed before the run)

Scored by `experiments/sc1_analyse.py` (written before any run) → `results/sc1.json`. A model counts when both arms
complete 16/16 tasks.

| ID | Prediction | Pass when |
|---|---|---|
| **P1** | Blind planning stays exact in the scene | X5b exact on 16/16 on every complete model |
| **P2** | One-call JSON Patch does not | B2 ≤ 15/16 on at least one complete model |
| **P3** | Its failures are the state-dependent kind, as in A7/A8 | every B2 failed step is `derive`, `sum_into`, `multiply`, `select_if` or `reassign_where`; X5b has 0 failed steps |
| **P4** | **Named hand-over steps** (as G9) | B2 fails at least one of these five steps on at least one complete model: seed 913 step 53 (29 objects change robot), 908 step 53 (23), 913 step 49 (20), 909 step 54 (20), 913 step 39 (19); steps 1-based |
| **P5** | Cheaper per correct task | X5b tokens per correct task ≤ 0.7× B2 on every complete model, and USD per correct ≤ 0.7× on Mistral |
| **P6** | Drift repaired without the model | every injected drift healed with 0 model calls, both arms, every complete model |
| **P7** | The channel result holds in BPE tokens | o200k: R ≤ 0.6× P over all steps, and R > P on `select_if` steps (the loss holds too) |

Basis: A8 L3 (same size): X5b 16/16 on Mistral and Gemini; B2 12/16 and 15/16, every failure state-dependent, and the
named step that broke three model families was an owner transfer. P4 names the hand-overs with the most objects to
re-assign; it is a stronger test than G9 because these steps were never run on any model.

## 7. What would count against RSOS

P1 failing (a blind plan wrong on a scene task) is the most important possible result and is reported first. P2 and
P4 failing mean JSON Patch handles the scene as well as RSOS on exactness, and the case rests on cost, data exposure
and the channel. A P7 failure means the compactness claim is a property of the regex count, not of model tokens.

## 8. Limits stated in advance

- A simulated scene: no perception, motion, physics or timing. The state is the scene graph that robots would share.
- Same request templates as A7b, so SC1 tests the protocol in a spatial world, not new kinds of operations; spatial
  relations are attributes and edges, not geometry (no "left of" computed from coordinates).
- The RSOS painting syntax (scenes composed as objects and places) is not measured here; what is transmitted is the RSOS
  operation program. A painting-syntax encoding is a later, separate test.
- One task cell, 16 tasks per model, two models planned.

## 9. Run (owner's machine)

```
python experiments/a7_run.py replaycheck SC1                 # must print "pass": true; 0 model calls
python experiments/sc1_channel.py                            # adds o200k counts where tiktoken is installed
A7_BACKEND=openai A7_OPENAI_BASE=https://api.mistral.ai/v1 A7_OPENAI_MODEL=mistral-large-4-0 \
  A7_LABEL=mistral_large40 A7_WORKERS=2 A7_OPENAI_KEY=… python experiments/a7_run.py run SC1 B2,X5b
A7_BACKEND=openai A7_OPENAI_BASE=https://generativelanguage.googleapis.com/v1beta/openai \
  A7_OPENAI_MODEL=gemini-3.8-flash A7_LABEL=gemini_38flash A7_WORKERS=2 A7_OPENAI_KEY=… \
  python experiments/a7_run.py run SC1 B2,X5b
python experiments/sc1_analyse.py                            # 0 model calls -> results/sc1.json
```
