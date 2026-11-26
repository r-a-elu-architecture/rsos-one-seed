# Program as painting: how to make it work (design, 16 Nov 2026)

**The goal (owner, round 3):**
- a program or AI platform is shown as a full painting, with every functional property, operation and line of
  reasoning in it;
- a person moves, pierces, enters, colours and connects objects;
- every change acts on the program: on the nearest parts, or on the whole system.

## The principle that makes it work

**The painting is not a picture of the program; it is a second, exact form of it.** Painting ⇄ program has to be a
two-way compiler:
- program → painting (encode);
- painting change → program change (compile the operator);
- program run → painting update (show the effects).

Chat 1's cipher (encode → transform → decode) and our codec check (256/256 in R-003) are the first pieces.

## Five layers

| # | Layer | What it does | Built on |
|---|---|---|---|
| 1 | **Program model** | Reads the program into a typed graph: modules, functions, data and control flow, state, configuration, tools, prompts, policies. Runtime traces add what really runs: paths taken, frequency, latency, errors | Static analysis (Python `ast`, call graph) + run traces |
| 2 | **Codebook: program element → scene object** | Each element gets an object whose nature matches its function, and the scene's grammar carries the structure. Defaults below; **every person or company can bind their own symbols** (D66; MEANING bindings by profile) | The language's meanings: core (D80) + bindings + search |
| 3 | **Gestures = operators = program transformations** | Every gesture is an RSOS statement, and every statement has a defined transformation for this kind of program (table below). The result is a versioned code or configuration change | Language core (step 1), runtime (step 2) |
| 4 | **Effect preview by running** | Before a change is kept, the program (or a sandbox twin) runs with it: tests, a benchmark, traces. The painting then shows the chain: which objects vibrate, change colour or move. Effects are measured, never invented | Steps 3–5 (experiment harness, discovery engine) |
| 5 | **Governance** | Every change is a branch. The Spine checks it, tests must pass, the human approves, and return to baseline is always one step | Chat 3 hierarchy (D70, D71) |

## Default codebook (owner's grammar → program structure)

| In the painting | In the program | Source |
|---|---|---|
| Up / down in the scene | Abstraction layer: supervisor and policy above, workers and I/O below | Owner: vertical = hierarchy (c1 T44, T88) |
| Distance between objects | Coupling: how often and how strongly two modules call each other | Owner: placement makes contact |
| Size | Load or power: traffic, compute | R5: effect follows power |
| Colour | State: healthy / degraded / failing; black = only destructive, grey = risky but contained | c1 T95, c2 T35, c2 T53 |
| Lines, paths, rivers | Data and control flow, with direction | c1 T108 |
| Inside an object (body, blood cell with code) | Implementation levels: module → function → code block | c2 T35 surface → body → sub-code |
| Background, sky, light | Runtime environment and domain | c1 T106 room light = domain |
| Legs touching the land | Dependencies on infrastructure (libraries, services) | Owner, round 3 |
| People standing in the scene | Users, agents, callers | Owner, round 3 |
| Sound, a roar | An event that matters: alerts, which modules attend to | R12 |

## Gesture → program transformation (agent-workflow programs first)

| Gesture | Transformation |
|---|---|
| **MOVE** an object closer to another | Route more of its traffic there, or add a direct edge (coupling up) |
| **TOUCH** at the top | Attach at the supervisory entry: the module sees and steers every surface step (D80) |
| **PIERCE** the engine into the bird **at the top of the head** | Insert the module at the agent's input/attention stage: it raises alerts and can redirect where the agent goes |
| … **in place of the heart** | Insert or replace it in the agent's core loop: the cycle runs faster, "or not" (measured) |
| … **in the middle of the brain** | Insert it at the memory and retrieval core: recall paths change from the centre |
| … **near** the bird | No insertion: a side channel that affects neighbouring modules (shared resources, events) |
| **ENTER** / **ZOOM** | Open the module's inner graph: functions, then code blocks |
| **LINE** through objects | An ordered pipeline or an analysis route (where to trace, at what pace) |
| **REGION** from the centre | Select a set of modules to change together |
| **SHIFT** to grey | Sandbox a risky module: it runs, with its permissions contained |
| **DOT** | Add a capability inside a module without replacing it (a hook, a tool, a check) |
| **HEAL** | Apply a repair: retry policy, input cleaning, or a fix from the test results |
| **COLOUR** / **TIME** slow | Show or filter a state; replay a run slowly to inspect it |

Each row is a compile target that must be defined per program type. Agent workflows (typed nodes and edges) come
first, because insertion points and re-wiring are well defined there. Arbitrary code comes later.

## The hard parts, stated plainly

1. **Any program or platform can be painted through what it exposes (owner, 16 Nov 2026: "Claude" was only an
   example).** Three layers are paintable for every product, Claude included:
   - its **user interface**: screens, controls, panels, flows between them;
   - its **functions**: features, tools, capabilities, settings;
   - its **communication layer**: messages and turns, files and attachments, APIs and protocols.

   What stays closed is only a closed model's weights (open-weights models could later be painted down to layers and
   attention heads). For our own programs, the code itself is painted too.
2. **A painting cannot show everything at once.** Zoom and ENTER levels carry the detail: the whole platform as a
   landscape, a module as an object, a function as its body, code as the blood cell.
3. **Every gesture needs an exact program meaning.** Without one, the painting is decoration. The compile-target
   table above has to be implemented and tested per program type.
4. **Systemic effects are known only by running.** The preview shows measured effects, with their uncertainty.

## First working version (fits steps 4–7 of the roadmap)

1. **A real program:** a 12-module agent workflow (like chat 2's EXP-019) written in our runtime, with tests and a
   benchmark.
2. **Program → painting automatically,** with the default codebook.
3. **Gestures in the browser:** MOVE, PIERCE at a chosen place (head / heart / brain / near), ENTER, LINE, SHIFT
   grey, DOT. Each gesture compiles to a patch.
4. **Run → painting update:** the chain of effects shown on the painting.
5. **Proof:** the same improvement tasks done by editing the painting vs editing the code; time, correctness,
   benchmark result.
6. **Second example, from the outside:** a chat assistant's user interface, functions and communication layer as a
   painting (the conversation, messages, tools, files, settings), with gestures that compile to its documented
   options and API calls.
