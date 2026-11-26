# CONF4 domain descriptions (identical for every agent, RSOS and control)

You write decision programs for four real domains. For each domain write one Python file defining
`MOVES = {name: function}` with AT MOST 5 programs. Each function takes the state view `st` (a dict, described below)
and returns ONE action (formats below) or None when it does not apply. Python standard library only; no imports from
the repository; pure functions of `st`. Each program is offered to a decision engine that values it in model futures of
the domain and takes it only if it is at least as good as the standard action, so a program only needs to be a strong
candidate; it may route by state internally (different behaviour in different situations). A short comment above each
program says what it does. Files: `<dir>/ai_agents_moves.py`, `<dir>/ai_human_moves.py`, `<dir>/ai_ai_moves.py`,
`<dir>/space_moves.py`. You may check syntax with `python3 -c "import ast; ast.parse(open(F).read())"`; do not run
any repository code.

## Domain 1: AI agents solving tool-use tasks (an episode = 4 tasks; one decision = what to do next on the current task)
State: `st["ti"]` current task (0..3); `st["calls"]`, `st["tok"]` model calls and tokens used on this task (budget per
task: 12 calls, 16,000 tokens); `st["br"]` list (1 to 3) of reasoning branches (independent attempts), each with `"id"`,
`"temp"` (0 or 0.7), `"answer"` (None while unanswered, else a string), `"calls"`, `"tok"`, `"errors"` (error
observations so far), `"restarts"` (0 or 1).
Actions:
- `("step", b)`: the next ReAct step of unanswered branch b (one model call).
- `("new",)`: open a fresh attempt at temperature 0.7 (at most 3 branches) and take its first step.
- `("restart", b)`: restart branch b afresh at temperature 0.7 (allowed only in some states).
- `("cross", b, src)`: branch b's next step, told the answer of branch src.
- `("commit",)`: end the task now with the majority answer (no call).
- `("blind", b)`: plan mode on branch slot b: ONE model call writes the whole tool plan for the task, naming only which
  data keys to use; a deterministic runtime then executes the plan and computes every value (no further model calls on
  that branch).
- `("reuse", b)`: run a stored plan of the same task shape on slot b at zero model calls (only works when such a plan
  exists; otherwise it falls back to the standard).
Invalid actions fall back to the standard. Standards: ReAct (step branch 0 until it answers, then commit) and
self-consistency (up to 3 attempts one after another, majority answer). Value: accuracy first, then fewer tokens.

## Domain 2: AI replying to a person in a real human-to-human conversation (the model plays agent_2; up to 8 replies)
State: `st["conv"]` list of (speaker, message) pairs of the conversation SO FAR, ending with the person's current
message; `st["t"]` index of the current reply.
Actions:
- `("direct",)`: the standard reply (the model sees the conversation history).
- `("mention", w1, w2, ...)`: a reply of the same length budget asked to mention these lowercase content words from the
  conversation so far (others are dropped).
- `("holo", w1, ..., w6)`: compact-state reply: instead of the history the model receives a compact description of the
  conversation's whole state, and is asked to mention up to 6 given words.
- `("holomin", w1, ..., w6)`: the same with a minimal compact state (fewest input tokens).
Value: how well the reply covers what the person says next (word overlap with the person's next message), first; then
fewer tokens (input + output).

## Domain 3: two AI agents, A and B, answer one 4-hop question; each holds about half of 60 facts; you decide A's message
Facts are keys (relation, subject): "manager", "mentor", "team", "home" (subject = person; values person, person, team,
city), "office" (subject = team; value office), "city" (subject = office; value city). State: `st["question"]` = "In
which city is the office of the team of the manager of X?"; `st["x"]` = X; `st["mine"]` = {(relation, subject): value} of
A's own facts; `st["unsent"]` A's facts not yet sent (fixed order); `st["received"]` = {(relation, subject): value} facts B
has sent; `st["sent_A"]` facts A has sent; `st["t"]` round (0..5). Each round A sends at most 2 slots, then B sends up to
2 facts; both then try to answer; the first round with an answer ends the episode.
Actions (a list):
- `[k1, k2]`: up to 2 fact keys from `st["unsent"]`, sent as sentences; empty slots are filled with the standard's next
  facts.
- `[("#", "H"), k1, k2]`: the same facts sent in compact form "rel(subject)=object" (fewer tokens).
- `[("#", "H"), ("?", rel, subject), k1]`: compact form with a KEY in one slot: a question for one hop A cannot resolve
  (a hop B holds); B's standard ranking then sends facts about that subject first.
Standard: the 2 most relevant unsent facts as sentences (subject X first, then subjects in the question or messages, then
relation words in the question). Value: the right answer first, then fewer tokens.

## Domain 4: an Earth-observation satellite downlinking data over real ground-station passes; one decision per pass
State: `st["t"]` index of the current pass; `st["passes"]` all passes (start_hour, end_hour, capacity_MB), known in
advance; `st["queue"]` items on board, each {"id", "cls" ("alert"/"science"/"bulk"), "arr" (arrival hour), "size" (MB),
"value", "deadline" (hour)}; typical alert 20-80 MB, value 8-12, deadline 3-6 h after arrival; science 100-300 MB, 3-6,
12-24 h; bulk 300-600 MB, 1-2, 36-48 h; more items arrive later. An item counts only if its last byte reaches the ground
before its deadline; rate 2 MB/s from the pass start, in the order sent.
Action: an ordered list of item ids for this pass; packed greedily into capacity; items that cannot make their deadline
in that order are skipped; the rest of the pass is filled with the standard's next items. A token `1000000000 + id`
anywhere in the list fills the pass tail (capacity no whole item fits) with a FRAGMENT of item `id`; the rest of that item
is sent at later passes and counts when its last byte arrives before its deadline.
Standard: value per MB, highest first. Value: total value delivered before deadlines.
