"""A3c: the White Dragon designs H-pred (deterministic shared predictor) and H-local (local LM) in ONE call.

PREREGISTRATION_A3C.md. Examples come only from the smoke seed 999 (A3b smoke transcripts). Saved verbatim to
results/a3c_dragon_design.json; one call only.

    python experiments/a3c_dragon.py
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
from a3b_dragon import LIBRARY, SYSM       # noqa: E402

OUT = os.path.join(A.ROOT, "results", "a3c_dragon_design.json")


def smoke():
    for line in open(os.path.join(A.ROOT, "results", "a3b_smoke_transcripts.jsonl")):
        t = json.loads(line)
        if t["cond"] == "Hd":
            return t


def examples():
    t = smoke()
    pl = [c for c in t["calls"] if c["system"].startswith("You are the PLANNER")]
    first = pl[0]["prompt"]
    outs = "\n\n".join(f"[step {i}] {c['text'].strip()}" for i, c in enumerate(pl))
    wires = "\n".join(f"[step {m['step']}, {m['from']} -> {m['to']}, {m['tok']} regex / {m['bpe']} BPE] {m['text']}"
                      for m in t["msgs"] if m["step"] in (0, 1, 5))
    return first, outs, wires


def prompt():
    first, outs, wires = examples()
    return f"""HOST (unchanged from A3b): three LLM agents (planner -> worker -> checker, all claude-haiku-5-5) apply 14
natural-language change requests to a 30-line configuration state (lines 'service.field = value'; services
{A.SERVICES}; fields {A.FIELDS} plus max_conn and tier that can be added; owners {A.OWNERS}; regions {A.REGIONS};
log levels {A.LEVELS}). Each agent holds its own copy (book). At steps 4, 8, 12 one untouched line of the worker's
working book is corrupted before the worker runs. The planner sees the change request and its book and writes free
prose; the WORKER DOES NOT SEE THE CHANGE REQUEST, only the decoded instruction and its own book (the checker sees
request + instruction + decoded changes). LLM prompts and outputs must stay exactly as they are.

WHAT YOUR LAST DESIGN (A3b, "H-dragon") ACHIEVED, measured on 16 tasks: 932 channel tokens per task (regex proxy;
1,023 BPE o200k), 0.64x the tent baseline (1,468 regex / 1,860 BPE), with full integrity: 48/48 drifts healed at 0
model calls (local repair from the snapshot of the last approved state, verified by a hash), 16/16 copies correct,
0/1,140 truncations accepted (6-digit check value chk6 = sha256 mod 10^6 of the new state, strict decode).
Per edge (regex / BPE tokens per task): instruction 808 / 817; edits 44 / 85 (word ops 'i value', 'xi', 'akk value',
then chk6); door 32 / 32 ('+' approve; '-' + the reject reason coded like an instruction; 0.25 rejects per task,
reasons ~400 characters); forward 49 / 89 (checker -> planner sends chk6; when the planner's codec has not predicted
the approved state from the instruction it replies '?' and the edits are re-sent; 131 of 224 approvals missed);
heal 0. Instruction coding was: fixed templates for frequent sentence shapes, § macros for keys/values found in the
shared book (§kcy = `cache.retries`, §vcy = its value, §Sa = auth, ...), an adaptive dictionary of earlier literals
(D1..D99, rarely re-used), everything else as literal text in « ». 11,405 of 12,934 instruction tokens (88%) were
literal prose. The planner writes ~4,500 characters of prose per task (14 instructions, ~320 characters each), and
rarely repeats a sentence verbatim, but it re-states keys and current/final values from the book constantly and
re-uses a small set of phrasings ("Leave every other key unchanged", "Change no other keys", "currently", ...).

The owner's target is <= 0.2 x the tent = 294 regex tokens per task (and <= 372 BPE) with the same integrity. The
non-prose places already cost ~124 tokens per task; the prose is the floor to break.

EXAMPLE (smoke seed 999, not a test seed). First planner prompt:
{first}

All 14 planner outputs of that task, in order (each is followed by worker edits and checker approval; the book
changes after each approved step):
{outs}

A3b H-dragon wire messages for steps 0, 1 and 5 of that task:
{wires}

METRIC: channel tokens = regex matches of \\w+|[^\\w\\s] over every message (primary). Guard, binding: the same
messages are counted in BPE tokens (tiktoken o200k_base) and a pass on regex counts only if it also holds in BPE (so a
dense base62/hex blob gains nothing). MEASURED FACT about the metric: o200k_base has 47,424 tokens of the form
' ' + two or more lowercase ASCII letters; any space-separated sequence of such words costs exactly 1 regex token and
1 BPE token per word (measured on 2,000 random ones: 2,000 regex, 2,000 BPE).

TWO NEW ARMS TO DESIGN (A3c):
1. H-PRED: a DETERMINISTIC, NON-NEURAL shared predictor for the prose (instruction and reject reasons), identical on
   both sides, e.g. a context model / dictionary built from the shared book, the fixed tables and the task's own
   history. 0 model calls.
2. H-LOCAL (a separate, labelled claim): the same coding with a small local open language model as the shared
   predictor (identical weights on both sides, deterministic inference). Its forward passes are counted as local
   model calls. Compute: 4 CPU cores, 15 GB RAM, no GPU; python with numpy, torch (CPU) and transformers; model
   weights can be downloaded from the Hugging Face hub; the whole live run (16 tasks, ~230 instructions, each
   encoded and decoded) should finish in about 2 hours.

HARD CONSTRAINTS:
1. Lossless: the worker reconstructs the planner's instruction byte-exactly; the worker reconstructs the checker's
   reject reason byte-exactly; the state after edits exactly. Asserted on every message.
2. No extra hosted LLM calls; LLM prompts unchanged. The integrity layer of A3b (snapshot repair, chk6, strict
   edits decode, truncation detection on worker -> checker) stays, unless you replace it with something at least as
   strong; you may also redesign edits, door and forward.
3. Out of band, fixed before the run: the initial books, the A3b tables, and any table or PRIMING CORPUS you define.
   A priming corpus may contain planner and checker prose ONLY from seeds 500-531 (disjoint from the test seeds),
   generated before the run with the same agents and prompts (full A3b H-dragon task runs on those seeds are
   available, ~43 Haiku calls each; up to 32 runs). Its one-time size is reported, not counted per task. The codec
   may use any history both sides have already seen in the task (earlier messages, books, snapshots).
4. Floating point: encoder and decoder run on the same machine; you must say how you make the predictor's
   probabilities bit-identical on both sides (and what happens if they are not).

CROSS-DOMAIN LIBRARY (use any, or others you know): {"; ".join(LIBRARY)}; also arithmetic / range coding, PPM and
context mixing, LZ77/LZ78 and preset dictionaries (zstd, Brotli), grammar-based compression, CTW, speech codecs
(analysis by synthesis), video codecs (motion compensation: predict from the reference frame).

TASK: design both arms. For each: landings (place, depth, order, domain, mechanism); the predictor exactly (model
order, contexts, how the shared book and history enter, escape/backoff, how probabilities are quantised, how the
priming corpus is built if you use one); the coder (arithmetic/range coder precision, termination, length
signalling); how the coded bits become channel text (alphabet, packing) and its cost in regex and BPE tokens; the
exact wire format per edge (instruction, edits, door approve, door reject, forward, heal) as a grammar a programmer
can implement without guessing; for H-local which model (exact Hugging Face id), what context it is given, top-k or
full-vocabulary distribution, quantisation and determinism. Then predict, for each arm, channel tokens per task
(regex and BPE, total and per edge), bits per character of the coded prose, and the integrity. Be honest: if the
target cannot be met, say by how much and predict the true number."""


SCHEMA = {"type": "object", "properties": {
    "landings": {"type": "array", "items": {"type": "object", "properties": {
        "arm": {"type": "string", "enum": ["H-pred", "H-local", "both"]}, "order": {"type": "integer"},
        "place": {"type": "string"}, "depth": {"type": "string"}, "domain": {"type": "string"},
        "source_mechanism": {"type": "string"}, "mechanism": {"type": "string"}},
        "required": ["arm", "order", "place", "depth", "domain", "source_mechanism", "mechanism"]}},
    "priming_corpus": {"type": "string", "description": "whether used, and the exact rule to build it"},
    "h_pred_predictor": {"type": "string"}, "h_local_predictor": {"type": "string"},
    "h_local_model_id": {"type": "string"},
    "coder": {"type": "string"}, "packing": {"type": "string"}, "determinism": {"type": "string"},
    "edges": {"type": "array", "items": {"type": "object", "properties": {
        "arm": {"type": "string", "enum": ["H-pred", "H-local", "both"]},
        "edge": {"type": "string", "enum": ["instruction", "edits", "door_approve", "door_reject", "forward", "heal"]},
        "grammar": {"type": "string"}, "encode": {"type": "string"}, "decode_and_checks": {"type": "string"},
        "example": {"type": "string"}}, "required": ["arm", "edge", "grammar", "encode", "decode_and_checks",
                                                      "example"]}},
    "predictions": {"type": "object", "properties": {arm: {"type": "object", "properties": {
        "channel_tok_per_task": {"type": "number"}, "bpe_tok_per_task": {"type": "number"},
        "per_edge_tok_per_task": {"type": "object", "properties": {
            k: {"type": "number"} for k in ["instruction", "edits", "door", "forward", "heal"]},
            "required": ["instruction", "edits", "door", "forward", "heal"]},
        "bits_per_char_prose": {"type": "number"}, "one_time_table_bytes": {"type": "number"},
        "drift_healed_zero_call_of_48": {"type": "integer"}, "replica_consistent_of_16": {"type": "integer"},
        "truncation_detected_pct": {"type": "number"}},
        "required": ["channel_tok_per_task", "bpe_tok_per_task", "per_edge_tok_per_task", "bits_per_char_prose",
                     "one_time_table_bytes", "drift_healed_zero_call_of_48", "replica_consistent_of_16",
                     "truncation_detected_pct"]} for arm in ["H-pred", "H-local"]},
        "required": ["H-pred", "H-local"]},
    "target_assessment": {"type": "string"}, "risks": {"type": "string"}},
    "required": ["landings", "priming_corpus", "h_pred_predictor", "h_local_predictor", "h_local_model_id", "coder",
                 "packing", "determinism", "edges", "predictions", "target_assessment", "risks"]}


def main():
    if os.path.exists(OUT):
        sys.exit("design already exists: one call only")
    p = prompt()
    if len(sys.argv) > 1 and sys.argv[1] == "show":
        print(p); return
    cmd = ["claude", "-p", "--output-format", "json", "--model", DRAGON_MODEL, "--system-prompt", SYSM,
           "--tools", "", "--no-session-persistence", "--json-schema", json.dumps(SCHEMA)]
    t0 = time.time()
    pr = subprocess.run(cmd, input=p, capture_output=True, text=True, timeout=2400, cwd="/tmp")
    d = json.loads(pr.stdout)
    if d.get("is_error"):
        sys.exit("dragon call error: " + str(d.get("result"))[:500])
    text, so = d.get("result") or "", d.get("structured_output")
    rec = {"usage": d.get("usage"), "cost": d.get("total_cost_usd"), "api_ms": d.get("duration_api_ms")}
    design = so or A.parse_json(text)
    json.dump({"model": DRAGON_MODEL, "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "system": SYSM,
               "prompt": p, "schema": SCHEMA, "raw_text": text, "design": design, "call": rec,
               "sec": time.time() - t0}, open(OUT, "w"), indent=1)
    print(json.dumps(design, indent=1))


if __name__ == "__main__":
    main()
