# PAINT-1 report: a real program edited as a painting

Pre-registration: `experiments/PREREGISTRATION_PAINT1.md` (committed `8df3b0c`, before running). Results:
`results/PAINT-1.json` (results_sha256 8cff158e…, identical on rerun); paintings and all numbers:
`results/PAINT-1.html`.

## What was built

- **The program:** a 12-module support-ticket agent workflow: intake, normalize, classify, extract, memory, priority,
  plan, policy, act (tool, with a retry loop), verify, respond, log. Every node has four places: head (its input),
  heart (how it works), brain (its knowledge) and near (beside it, acting on what flows on to its neighbours).
- **The painting:** the workflow drawn by the default codebook:
  - left to right = the flow;
  - height = layer (policy at the top as the sky, input and output on the ground);
  - size = cost;
  - colour = state;
  - symbols by role (door, path, bird, lake, sky, engine, owl, bridge).
- **Gestures in the RSOS Language,** compiled to exact program changes:
  - PIERCE guest THROUGH node.head | heart | brain;
  - PLACE guest NEAR node;
  - DOT;
  - SHIFT node TO grey (sandbox: keeps the node's power, contains its crashes);
  - HEAL (one more recovery attempt);
  - MOVE (re-order).
- **Effects measured by running the program** on 1,000 held-out tickets (30% typos, 30% phrasing never seen).

## Results (held-out A; B in the HTML)

| Hypothesis | Result | Pass |
|---|---|---|
| H1 the place decides | The spell corrector and the synonym expander each give **4 different outcomes** at head / heart / brain / near | Yes |
| H2 near acts on the neighbours, not the node | The spell corrector near classify: classify errors 220 → 220 (unchanged) | Yes |
| H3 grey contains crashes | Crashes 6.2% → **0%**; accuracy 0.488 → 0.502 (A), 0.528 → 0.538 (B) | Yes |
| H4 the cache lowers cost where it has meaning | Cost per ticket: head 11.99 (no gain) · heart 11.36 · brain 10.29 · baseline 11.79 | Yes |
| H5 a composed program beats the baseline | Accuracy **0.488 → 0.780**; score 0.370 → 0.662 (A), 0.410 → 0.705 (B) | Yes |

**The place really decides.** The same spell corrector:
- in the **head** of classify (correcting what it reads): accuracy 0.664, cost 13.29;
- in its **heart** (how it matches): accuracy 0.672, cost 14.29;
- in its **brain** (learned once into its knowledge): accuracy 0.672, **cost unchanged** (11.79): the best place;
- **near** it: accuracy unchanged (0.488), because it corrects only what flows on, after classify has already
  decided.

This is the owner's round 3 rule, measured on a real program: "each of the places will have different result".

## Hard truth

- **This shows that the painting's gestures have exact, distinct and measurable meanings in a real program.** It does
  **not** show that editing the painting beats editing code. The guest modules were written by us, so their benefits
  were expected by design. The test was that the painting delivers them exactly, at the right place and only there.
- **Speed and quality against a programmer editing code is the proof run** (roadmap step 7).
- **The painting is still a diagram** (circles and symbols on a landscape). Step 6 makes it a real scene that a person
  can draw on in the browser.
