"""A3b: the White Dragon designs the hologram palace in ONE call (PREREGISTRATION_A3B.md).

The dragon gets the palace's places, P's exact formats with one real A3 step, A3's measured cost per place, the
tent's total only (not its formats: the dragon has no teacher, D90 17:12), the constraints and a cross-domain
library. It returns landings + exact wire formats + predicted channel size and integrity. Saved verbatim.

    python experiments/a3b_dragon.py
"""

import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import a1_agents as A                      # noqa: E402
from a2_dragon import DRAGON_MODEL         # noqa: E402

OUT = os.path.join(A.ROOT, "results", "a3b_dragon_design.json")
SYSM = ("You are the White Dragon: a cross-domain systems engineer who transplants proven mechanisms from other "
        "fields into AI agent workflows. Be concrete and executable.")
LIBRARY = ["holography (every fragment holds the whole; reconstruction by a reference beam)",
           "DNA coding, replication proofreading and mismatch repair", "error-correcting and error-detecting codes",
           "information theory and source coding (entropy, dictionary and context coding)",
           "predictive coding (send only the surprise against a shared predictor)",
           "rocketry telemetry and mission control (frame sync, minor/major frames)",
           "double-entry bookkeeping and audit", "military brevity codes and mission command",
           "music notation (a score is a compressed performance)", "immunology (self/non-self markers)",
           "control theory and cybernetics", "linguistics (anaphora, ellipsis, given/new)"]


def example_step():
    for line in open(os.path.join(A.ROOT, "results", "a3_transcripts.jsonl")):
        t = json.loads(line)
        if t["cond"] == "P" and t["seed"] == 100:
            ms = [m for m in t["msgs"] if m["step"] in (0, 2)]
            return "\n\n".join(f"[{m['from']} -> {m['to']}, {m['kind']}, {m['tok']} tok]\n{m['text']}" for m in ms)


def prompt():
    init = A.text_of(A.make_task(100)["init"])
    return f"""HOST: three LLM agents (planner -> worker -> checker) apply 14 natural-language change requests to a
30-line configuration state (lines 'service.field = value'; services {A.SERVICES}; fields {A.FIELDS} plus
max_conn (1-4 digits) and tier (gold|silver|bronze) that can be added; owners {A.OWNERS}; regions {A.REGIONS};
log levels {A.LEVELS}). Lines can be changed, added at the end, or deleted. Each agent holds its own copy of the
state ("book"). At steps 4, 8 and 12 one untouched line of the worker's working book is silently corrupted before
the worker runs (any other copy, e.g. a snapshot of the last approved state, is not touched).

THE PALACE (condition P) and its five places, with exact current formats:
- INSTRUCTION (planner -> worker): '@state#<8-hex sha256 of the planner's book>' then the planner's free-text
  instruction (an LLM writes it; it names every key and final value and often restates state lines).
- WALLS (green dots): the 8-hex hashes; the worker compares its own book's hash before its LLM call; on mismatch a
  heal runs (the worker sends its 6-hex hashes of 4-line chunks, the planner returns the differing chunks in full).
- EDITS (worker -> checker): '@state#<base hash>', then line edits ('i' or 'i1,i2', then '|new line' rows), then
  '=<8-hex hash of the new state>'. The checker applies them to its own book and checks the hash.
- DOOR (checker -> worker): a JSON verdict {{"verdict": "approve"|"reject", "reason": "<free text>"}} on every attempt.
  The worker needs the reason only after a reject (it is put in its retry prompt).
- FORWARD (checker -> planner): the approved edits message, so the planner updates its book.
- INSIDE: the state itself and the texts the LLMs read.

Real example (A3, seed 100, steps 0 and 2):
{example_step()}

Initial state of seed 100 (shared out of band at the start, like every initial book):
{init}

MEASURED COST in A3 (mean channel tokens per task, 16 tasks, 14 steps, ~1 retry and 3 drift heals per task):
instruction 1,349; edits 196; door 854; forward 187; heal 114; total P = 2,699. The palace's integrity layer
(hashes, dots, heals) is ~340 of that. The baseline compact protocol ("the tent") measured 1,468 tokens per task
with 16/16 exact successes but no drift detection (40 of 48 corruptions stayed in the worker's copy). The owner's
target: the hologram palace is lighter and smaller, the tent about 5 times its size: <= 0.2 x 1,468 = 294 tokens per
task, with full integrity: every drift healed before the worker's LLM call (0 model calls), every copy correct at
the end, every truncated message detected, and heal cost per drift <= 24 tokens.

METRIC: channel tokens = count of regex matches of \\w+|[^\\w\\s] over every message (primary). Guard: the same
messages are also counted in BPE tokens (tiktoken o200k_base) and bytes; a design that wins only on the regex proxy
(e.g. long base62 blobs or long hex runs that the regex counts as one token) is scored as a failure.

HARD CONSTRAINTS:
1. Lossless: the receiver must reconstruct EXACTLY the texts the LLMs read in P (the planner's instruction
   verbatim, the checker's reject reason verbatim, the state after edits). The LLM prompts are not changed.
2. No extra LLM calls. The codec is deterministic code running beside each agent.
3. Out of band only: the initial books plus fixed tables you define now (their one-time size is reported, not
   counted per task). The codec may use any history both sides have already seen in this task (earlier messages,
   books, snapshots of the last approved state).
4. Drift in the worker's book must be detected and healed before the worker's LLM call; every truncation of a
   worker -> checker message must be detected (the receiver's strict decode must reject it).
5. You do not see the tent's formats; design from all domains.

CROSS-DOMAIN LIBRARY (use any, or others you know): {"; ".join(LIBRARY)}.

TASK: design the hologram palace. Decide where to land (places), at which depth, in which order, from which
domain and mechanism. For EVERY edge (instruction, edits, door approve, door reject, forward, heal) give the exact
wire format as a grammar a programmer can implement without guessing, and a worked example using the example
step above. Define every table you need (or the rule that builds it from the initial books). Then predict the
channel tokens per task (regex proxy, total and per edge) and in BPE tokens, and the integrity you expect
(drifts healed with 0 model calls out of 48, copies correct out of 16, truncations detected, heal tokens per drift).
Be honest: if the target cannot be met under the constraints, say by how much, and predict the true number."""


SCHEMA = {"type": "object", "properties": {
    "landings": {"type": "array", "items": {"type": "object", "properties": {
        "order": {"type": "integer"}, "place": {"type": "string",
                                                "enum": ["instruction", "walls", "edits", "door", "forward",
                                                         "heal", "paintings", "inside"]},
        "depth": {"type": "string"}, "domain": {"type": "string"}, "source_mechanism": {"type": "string"},
        "mechanism": {"type": "string"}},
        "required": ["order", "place", "depth", "domain", "source_mechanism", "mechanism"]}},
    "tables": {"type": "string", "description": "every out-of-band table or the exact rule that builds it"},
    "edges": {"type": "array", "items": {"type": "object", "properties": {
        "edge": {"type": "string", "enum": ["instruction", "edits", "door_approve", "door_reject", "forward",
                                           "heal"]},
        "grammar": {"type": "string"}, "encode": {"type": "string"}, "decode_and_checks": {"type": "string"},
        "example": {"type": "string"}}, "required": ["edge", "grammar", "encode", "decode_and_checks", "example"]}},
    "predicted_channel_tok_per_task": {"type": "number"},
    "predicted_per_edge_tok_per_task": {"type": "object", "properties": {
        k: {"type": "number"} for k in ["instruction", "edits", "door", "forward", "heal"]},
        "required": ["instruction", "edits", "door", "forward", "heal"]},
    "predicted_bpe_tok_per_task": {"type": "number"},
    "predicted_one_time_table_tok": {"type": "number"},
    "predicted_integrity": {"type": "object", "properties": {
        "drift_healed_zero_call_of_48": {"type": "integer"}, "replica_consistent_of_16": {"type": "integer"},
        "truncation_detected_pct": {"type": "number"}, "heal_tok_per_drift": {"type": "number"}},
        "required": ["drift_healed_zero_call_of_48", "replica_consistent_of_16", "truncation_detected_pct",
                     "heal_tok_per_drift"]},
    "target_assessment": {"type": "string"}},
    "required": ["landings", "tables", "edges", "predicted_channel_tok_per_task", "predicted_per_edge_tok_per_task",
                 "predicted_bpe_tok_per_task", "predicted_one_time_table_tok", "predicted_integrity",
                 "target_assessment"]}


def main():
    if os.path.exists(OUT):
        sys.exit("design already exists: one call only")
    p = prompt()
    # one attempt, long timeout (A.llm's 180 s timeout + retries killed the first attempts before any output;
    # those attempts returned nothing and are recorded in the report)
    cmd = ["claude", "-p", "--output-format", "json", "--model", DRAGON_MODEL, "--system-prompt", SYSM,
           "--tools", "", "--no-session-persistence", "--json-schema", json.dumps(SCHEMA)]
    t0 = time.time()
    pr = subprocess.run(cmd, input=p, capture_output=True, text=True, timeout=1500, cwd="/tmp")
    d = json.loads(pr.stdout)
    if d.get("is_error"):
        sys.exit("dragon call error: " + str(d.get("result"))[:500])
    text, so, rec = d.get("result") or "", d.get("structured_output"), d.get("usage")
    rec = {"usage": rec, "cost": d.get("total_cost_usd"), "api_ms": d.get("duration_api_ms")}
    design = so or A.parse_json(text)
    json.dump({"model": DRAGON_MODEL, "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "system": SYSM,
               "prompt": p, "schema": SCHEMA, "raw_text": text, "design": design, "call": rec,
               "sec": time.time() - t0}, open(OUT, "w"), indent=1)
    print(json.dumps(design, indent=1))


if __name__ == "__main__":
    main()
