"""A2: the knowing White Dragon (D84, U107 knowing TRANSPLANT) on the A1 host.

Pre-registration: experiments/PREREGISTRATION_A2.md. Host = A1 condition C (summaries + retrieval), decomposed into
planner, worker, checker, memory, channel. Three arms land 4 transplants each, cumulatively, measured after each:
  knowing  : a strong model sees each part's function and measured A1 performance + a cross-domain library and
             returns the ordered landings (part x depth x order, predicted gain, dependencies) = the 3D map;
  blind    : random part, random depth, random domain (payload written by the same model, no performance data);
  weighted : F1b: random part and depth, domain drawn by weights reinforced with the measured gain.
Plus the knowing landings in a shuffled order (prefixes 1-3) to test the map's order.

    python experiments/a2_dragon.py run
"""

import json
import os
import random
import sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import a1_agents as A                      # noqa: E402

DRAGON_MODEL = "claude-opus-5-5"
SEEDS = list(range(200, 206))
BUDGET = 4
RNG_SEED = 300
DOMAINS = ["rocketry and mission control", "immunology", "chemistry", "socio-technical safety (aviation crew "
           "resource management, surgical checklists)", "quantum error correction", "control theory and cybernetics",
           "genetics (DNA replication proofreading and repair)", "double-entry bookkeeping and audit",
           "military mission command", "ecology"]
PARTS = {
    "planner": "reads the change request and the retrieved memory lines; writes one precise instruction",
    "worker": "reads the instruction and the top-8 retrieved memory lines; outputs JSON writes + a summary",
    "checker": "reads request, instruction, writes and top-8 retrieved memory lines; approves or rejects (max 2 "
               "retries)",
    "memory": "shared store of all state lines; retrieval returns the top-8 lines by keyword overlap; approved "
              "writes are committed to it",
    "channel": "JSON messages between agents: planner->worker {instruction, summary}, worker->checker {writes, "
               "summary}, checker->planner {verdict, summary, reason}",
}
STRUCT = {"memory": ["memory_journal", "retrieval_k16"], "checker": ["checker_full_view", "second_checker"],
          "worker": ["worker_full_view"], "planner": ["planner_go_nogo"], "channel": ["readback"]}
STRUCT_DOC = {
    "memory_journal": "memory keeps a per-line checksum and a journal of approved writes; before every step any "
                      "line whose checksum does not match the journal is restored",
    "retrieval_k16": "retrieval returns the top-16 lines instead of 8",
    "checker_full_view": "the checker sees every memory line instead of the top-8",
    "second_checker": "an independent second checker must also approve",
    "worker_full_view": "the worker sees every memory line instead of the top-8",
    "planner_go_nogo": "after the checker approves, the planner gives go / no-go on the writes before commit",
    "readback": "the worker's writes are read back to the planner, who confirms them before the checker sees them",
}
DEPTHS = {"surface": "text added to that agent's system prompt",
          "procedure": "a procedure block the agent must follow, inserted in every prompt it receives",
          "structure": "a change to the workflow graph, chosen from the structural menu"}
OUT = os.path.join(A.ROOT, "results", "a2_runs.json")


def valid_depths(part):
    return (["structure"] if part in ("memory", "channel") else ["surface", "procedure", "structure"])


def to_mods(landings):
    mods = {"sys": {}, "proc": {}, "struct": []}
    for L in landings:
        if L["depth"] == "structure":
            mods["struct"].append(L["primitive"])
        elif L["depth"] == "surface":
            mods["sys"][L["part"]] = (mods["sys"].get(L["part"], "") + " " + L["payload"]).strip()
        else:
            mods["proc"][L["part"]] = (mods["proc"].get(L["part"], "") + " " + L["payload"]).strip()
    return mods


def ask(prompt, schema):
    sysm = ("You are the White Dragon: a cross-domain systems engineer who transplants proven mechanisms from other "
            "fields into AI agent workflows. Be concrete and executable.")
    old = A.MODEL
    A.MODEL = DRAGON_MODEL
    try:
        text, so, rec = A.llm(sysm, prompt, schema)
    finally:
        A.MODEL = old
    return so or A.parse_json(text), rec


L_SCHEMA = {"type": "object", "properties": {"landings": {"type": "array", "items": {"type": "object", "properties": {
    "order": {"type": "integer"}, "part": {"type": "string", "enum": list(PARTS)},
    "depth": {"type": "string", "enum": list(DEPTHS)}, "domain": {"type": "string"},
    "source_mechanism": {"type": "string"}, "primitive": {"type": "string"}, "payload": {"type": "string"},
    "predicted_error_reduction_per_task": {"type": "number"}, "predicted_token_change_pct": {"type": "number"},
    "depends_on": {"type": "array", "items": {"type": "integer"}}},
    "required": ["order", "part", "depth", "domain", "source_mechanism", "primitive", "payload",
                 "predicted_error_reduction_per_task", "predicted_token_change_pct", "depends_on"]}}},
    "required": ["landings"]}
P_SCHEMA = {"type": "object", "properties": {"source_mechanism": {"type": "string"}, "payload": {"type": "string"}},
            "required": ["source_mechanism", "payload"]}


def host_profile():
    a1 = json.load(open(os.path.join(A.ROOT, "results", "a1_agents.json")))
    t = a1["table"]["C"]
    runs = [r for r in json.load(open(os.path.join(A.ROOT, "results", "a1_runs.json")))["runs"] if r["cond"] == "C"]
    by_role = {}
    for r in runs:
        for c in r["per_call"]:
            by_role.setdefault(c["role"], []).append(c["in"] + c["cache_w"] + c["cache_r"] + c["out"])
    return {"tasks": t["tasks"], "exact_success": t["success"], "line_accuracy": round(t["line_acc_mean"], 3),
            "wrong_final_lines_per_task": round(sum(len(v) for v in t["final_errors"].values()) / t["tasks"], 2),
            "injected_drift_caught": f"{t['drift_caught']}/{t['drift_events']}",
            "drift_reaching_final_state": t["drift_silent_in_final"], "steps_failed_after_retries": t["steps_failed"],
            "calls_per_task": t["calls_mean"], "billed_tokens_per_task": round(t["billed_tok_mean"]),
            "mean_billed_tokens_per_call_by_role": {k: round(sum(v) / len(v)) for k, v in by_role.items()}}


def knowing_map():
    prof = host_profile()
    prompt = (
        "HOST: a three-agent LLM workflow that applies 14 natural-language change requests to a 30-line "
        "configuration state, with injected silent corruption of memory lines at steps 4, 8 and 12.\n\nPARTS and "
        "functions:\n" + "\n".join(f"- {k}: {v}" for k, v in PARTS.items()) +
        "\n\nMEASURED PERFORMANCE of this host in A1 (8 tasks):\n" + json.dumps(prof, indent=1) +
        "\n\nCROSS-DOMAIN LIBRARY: " + "; ".join(DOMAINS) +
        "\n\nDEPTHS: " + "; ".join(f"{k} = {v}" for k, v in DEPTHS.items()) +
        "\nSTRUCTURAL MENU (primitive names, by part): " +
        "; ".join(f"{p}: " + ", ".join(f"{x} ({STRUCT_DOC[x]})" for x in v) for p, v in STRUCT.items()) +
        "\nmemory and channel accept only structure. For surface/procedure set primitive to \"\" and write the "
        "payload text (at most 80 words); for structure set payload to \"\" and primitive to a menu name.\n\n"
        f"TASK: find the weakest parts and choose exactly {BUDGET} transplants (distinct), each the best equivalent "
        "mechanism from the library for that part, the depth, the order of landing, dependencies between them, and "
        "the predicted reduction in wrong final lines per task (baseline as measured) and token change in %. The "
        "goal is fewer wrong final lines; tokens are secondary. Return the ordered map.")
    d, rec = ask(prompt, L_SCHEMA)
    L = sorted(d["landings"], key=lambda x: x["order"])[:BUDGET]
    for x in L:
        if x["depth"] == "structure" and x["primitive"] not in STRUCT.get(x["part"], []):
            x["invalid"] = True
    return L, prof, prompt, rec


def write_payload(part, depth, domain):
    if depth == "structure":
        return None
    d, _ = ask(f"Part of an LLM agent workflow: {part} — {PARTS[part]}.\nDepth: {depth} ({DEPTHS[depth]}).\n"
               f"Transplant the best mechanism from {domain} into this part at this depth. Return the source "
               "mechanism and the payload text (at most 80 words) the agent will receive.", P_SCHEMA)
    return d


def random_landing(rng, domain, used):
    while True:
        part = rng.choice(list(PARTS))
        depth = rng.choice(valid_depths(part))
        prim = rng.choice(STRUCT[part]) if depth == "structure" else ""
        key = (part, depth, prim)
        if key not in used:
            used.add(key)
            break
    L = {"part": part, "depth": depth, "domain": domain, "primitive": prim, "payload": ""}
    if depth != "structure":
        d = write_payload(part, depth, domain)
        L.update(source_mechanism=d["source_mechanism"], payload=d["payload"])
    else:
        L["source_mechanism"] = f"{prim} framed from {domain}"
    return L


def measure(tag, landings, workers):
    mods = to_mods(landings)
    with ThreadPoolExecutor(workers) as ex:
        runs = list(ex.map(lambda s: A.run_task("C", s, mods, tag), SEEDS))
    return {"tag": tag, "landings": landings, "mods": mods, "runs": runs,
            "errors_per_task": sum(len(r["final_errors"]) for r in runs) / len(runs),
            "success": sum(r["success"] for r in runs), "billed_mean": sum(r["billed_tok"] for r in runs) / len(runs),
            "drift_caught": sum(e["caught"] for r in runs for e in r["drift"])}


def main():
    A.TRANSCRIPTS = os.path.join(A.ROOT, "results", "a2_transcripts.jsonl")
    rng = random.Random(RNG_SEED)
    out = {"dragon_model": DRAGON_MODEL, "agent_model": A.MODEL, "seeds": SEEDS, "budget": BUDGET}
    know, prof, prompt, rec = knowing_map()
    out.update(host_profile=prof, dragon_prompt=prompt, knowing_map=know, dragon_call=rec)
    json.dump(out, open(OUT, "w"), indent=1)
    print("MAP", json.dumps(know, indent=1), flush=True)
    stages = {"baseline": measure("baseline", [], 6)}
    print("baseline", stages["baseline"]["errors_per_task"], flush=True)
    perm = list(range(BUDGET))
    rng.shuffle(perm)
    while perm == list(range(BUDGET)):
        rng.shuffle(perm)
    out["shuffle_perm"] = perm
    blind, weighted, used_b, used_w = [], [], set(), set()
    w = {d: 1.0 for d in DOMAINS}
    prev = {"knowing": stages["baseline"]["errors_per_task"], "blind": stages["baseline"]["errors_per_task"],
            "weighted": stages["baseline"]["errors_per_task"]}
    for k in range(BUDGET):
        blind.append(random_landing(rng, rng.choice(DOMAINS), used_b))
        dom = rng.choices(DOMAINS, weights=[w[d] for d in DOMAINS])[0]
        weighted.append(random_landing(rng, dom, used_w))
        jobs = [("knowing", know[:k + 1]), ("blind", list(blind)), ("weighted", list(weighted))]
        if k < BUDGET - 1:
            jobs.append(("shuffled", [know[i] for i in perm[:k + 1]]))
        with ThreadPoolExecutor(len(jobs)) as ex:
            res = list(ex.map(lambda j: measure(f"{j[0]}_{k + 1}", j[1], 3), jobs))
        for (arm, _), r in zip(jobs, res):
            stages[r["tag"]] = r
            if arm in prev:
                gain = prev[arm] - r["errors_per_task"]
                r["gain"] = gain
                prev[arm] = r["errors_per_task"]
                if arm == "weighted":
                    w[weighted[-1]["domain"]] += max(0.0, gain)
            print(r["tag"], r["errors_per_task"], r["success"], round(r["billed_mean"]), flush=True)
        out["stages"] = {t: {kk: v for kk, v in s.items() if kk != "runs"} for t, s in stages.items()}
        out["runs"] = {t: s["runs"] for t, s in stages.items()}
        out["weights_final"] = w
        json.dump(out, open(OUT, "w"), indent=1)


if __name__ == "__main__":
    main()
