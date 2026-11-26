# RSOS Language 0.2: specification (draft, day 1)

The RSOS Language is a spatial-symbolic programming language for humans and AI. A program is written the way a
person composes it in the mind: objects in a scene, placed, touched, pierced, entered, coloured, connected by lines,
held in rooms of a house. The same program has two runtimes:
- **machines**: AI agent workflows, simulations, devices;
- **people**: a practised mental model, conditioned through the cue framework.

The full statement table, the core meanings and the diagnostics are generated from the code in
[`REFERENCE.md`](REFERENCE.md).

## 1. Principles

1. **Every element is an operator with functional properties.** Symbols are components with properties, functions,
   interfaces, levels and a colour state. Operators act on them. The order of objects in a scene is the program.
2. **The host decides.** Every operation runs on a declared host (a person, an agent team, a body, a planet, a
   company), and the host's kind, channels and states are checked. A cue on a channel the host does not have is an
   error (E016). A mental model needs a host that reasons.
3. **Meanings in three tiers**:
   - **core**: fixed default meanings, the same for everyone. The contact table of chat 2 T35 is the default (D80).
   - **binding**: a declared variation for a scope (state, host, world, profile). The most specific scope wins:
     state > host > world > profile.
   - **search**: a meaning left open on purpose. The runtime tries the candidates and keeps the best.

   Resolution: binding > search > core. Two different bindings in one scope are an error (E010). A key with no meaning
   at all is an error (E017). **Nothing is guessed, and nothing changes silently.**
4. **Every result can be traced.** Every statement links to the operator register (U1–U87). Every descendant
   carries its parents. Every compiled program has a SHA-256 digest of its IR.

## 2. Form

One statement per line: `KEYWORD positional… [CLAUSE value]…`. Keywords and clause words are written in capitals,
names in lower case. `#` starts a comment.

```
LANGUAGE RSOS 0.2
WORLD ai_room
HOST team KIND agent CHANNELS haptic, visual STATES eagle
OBJECT sol KIND note DOMAIN music
OBJECT remote KIND agent_family DOMAIN ai REPRESENTS langgraph.router
USE HOST team
PIERCE sol THROUGH remote FROM top DEPTH 3 AS remote_sol     # core: through = multi_layer, top = supervisory_entry
SEARCH contact.bottom OVER lateral, local_contact, multi_layer METRIC task_success
PIERCE sol THROUGH remote FROM bottom AS remote_sol_bottom    # open: resolved by search
MEANING contact.top = local_contact SCOPE state IN eagle      # a declared variation
USE STATE eagle
TOUCH sol ON remote AT top                                    # binding: local_contact
```

Values:
- names, and dotted paths for parts (`house.door.middle`);
- numbers and quoted text;
- lists (`a, b, c`);
- compositions (`associated + confidence + analogical_reasoning`);
- cases (`slumped -> problems ; agency -> communication_strategy`).

## 3. Statement families

| Family | Statements | Source in the corpus |
|---|---|---|
| Declarations | LANGUAGE, WORLD, HOST, PROFILE, USE, OBJECT, PART, PROPERTY, RELATION | Chat 1 components; chat 2 package |
| Mental models | HOUSE, ROOM, MODEL, DEDICATE, FORM, MATERIAL, ANCHOR, FUTUREPACE, SELECTMODEL, RELATE | Pillar 2 (D61–D66); chat 2 T25–T29 |
| Scene, colour, state, flow | SCENE, COLOUR, SHIFT, HEAL, BEAM, FLOW, ROUTE, RESONATE, BALL, COMPRESS, WEIGHT, RESCRIPT, LOCATE | Chat 1 T14–T108 (absent from the earlier VSFL package) |
| Contact | TOUCH, ATTACH, PIERCE, PASS, WRAP, MERGE, SPLIT, DOT, MOVE, ROTATE, FLIP, OVERLAY, PROTRUDE, FUSE | Chat 1 T106; chat 2 T33–T35 |
| Selection and navigation | SELECT, REGION, ENTER, ZOOM, LINE, WIDEN, TIME | Chat 1 T108; chat 2 T53–T57 |
| Host and transfer | TRANSPLANT, REHOST, EXTERNALISE, TRANSFER, UPGRADE, INPUT, HOSTLOOP | Chat 1 T94–T106; chat 3 T11 |
| Painting and cipher | LAYER, CUTPLACE, ENCODE, DECODE, EXTRACT | Chat 1 T104–T107; chat 2 T49, T53 |
| Governance | SPINE, WATCHDOG, ARCHITECT, OVERRIDE, GATE | Chat 3 T0; cue framework `rsxv/` |
| Compile targets | CUE, MESSAGE, PERSPECTIVE | The D69 interface to the cue framework |
| Meanings | MEANING, SEARCH | D80, T12 |
| Testing and growth | SNAPSHOT, COMPARE, TEST, REVERSE, ABLATE, BASELINE, INDUCE, REENTER | Chats 2–3 method |

## 4. The intermediate representation (IR)

`python -m rsoslang ir FILE` prints JSON with:
- the header and the world;
- `hosts`, `entities`, `parts`;
- `bindings`, `searches`;
- `lineage` (child, operator, parents);
- `ops`, one per statement.

Each entry in `ops` holds:
- the statement: `op`, `family`, `line`;
- its parameters: `args`, `clauses`;
- `refs`, its links to the register;
- the active `context` (world, host, state, profile);
- every resolved `meaning`, with its source;
- for operators that act, the **unit**: source, target, path, method, geometry, relation, host, colour_state,
  contract, environment, time, evidence (build inputs §1, private design record).

## 5. Status

| Part | Day | Status |
|---|---|---|
| Parser, statement table, diagnostics, meanings, hosts, IR, CLI | 1 | Built; tests pass |
| Executable operator semantics (simulation backend) | 2 | Next |
| Experiments re-run with seeds and hashes | 3 | — |
| Agent-workflow backend | 4 | — |
| Visual editor and mental-model builder | 5 | — |
