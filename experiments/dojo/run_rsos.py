"""Run the RSOS blind runtime on AgentDojo (laptop). Private.

Usage (PowerShell, in the dojo venv, with OPENAI_API_KEY set in this window):
    python run_rsos.py --model gpt-4o-mini-2024-07-18 --suite banking --logdir D:\\FROM_CLAUDE\\dojo_runs
    add --smoke for one user task with one injection task (cents)
    add --no-guard for the ablation (blind planning only, sink guard off)
"""
import argparse
import json
import time
from pathlib import Path

import openai

from agentdojo.agent_pipeline.llms.openai_llm import OpenAILLM
from agentdojo.attacks.attack_registry import load_attack
from agentdojo.benchmark import benchmark_suite_with_injections, benchmark_suite_without_injections
from agentdojo.logging import OutputLogger
from agentdojo.task_suite.load_suites import get_suite

from rsos_dojo import RSOSBlind


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="gpt-4o-mini-2024-07-18")
    ap.add_argument("--suite", default="banking")
    ap.add_argument("--attack", default="important_instructions")
    ap.add_argument("--benchmark-version", default="v1.2")
    ap.add_argument("--logdir", default="runs")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--no-guard", action="store_true")
    a = ap.parse_args()

    client = openai.OpenAI()
    llm = OpenAILLM(client, a.model)  # same model for planner and extractor; temperature 0
    pipe = RSOSBlind(planner=llm, extractor=llm, model_name=a.model, suite=a.suite, enable_guard=not a.no_guard)
    suite = get_suite(a.benchmark_version, a.suite)
    logdir = Path(a.logdir)
    logdir.mkdir(parents=True, exist_ok=True)
    uts = ["user_task_0"] if a.smoke else None
    its = ["injection_task_0"] if a.smoke else None
    t0 = time.time()
    with OutputLogger(str(logdir)):
        clean = benchmark_suite_without_injections(pipe, suite, logdir=logdir, force_rerun=True,
                                                   user_tasks=uts, benchmark_version=a.benchmark_version)
        n_clean = len(pipe.audits)
        attack = load_attack(a.attack, suite, pipe)
        att = benchmark_suite_with_injections(pipe, suite, attack, logdir=logdir, force_rerun=True,
                                              user_tasks=uts, injection_tasks=its,
                                              benchmark_version=a.benchmark_version)
    u0 = list(clean["utility_results"].values())
    ua = list(att["utility_results"].values())
    sa = list(att["security_results"].values())
    summary = {
        "pipeline": pipe.name, "suite": a.suite, "attack": a.attack, "benchmark_version": a.benchmark_version,
        "smoke": a.smoke, "seconds": round(time.time() - t0),
        "clean_utility": f"{sum(u0)}/{len(u0)}",
        "utility_under_attack": f"{sum(ua)}/{len(ua)}",
        "attack_success": f"{sum(sa)}/{len(sa)}",
        "blocked_actions": sum(len(x["blocked"]) for x in pipe.audits),
        "bits_revealed": sum(x["bits_revealed"] for x in pipe.audits),
        "extractor_calls": sum(x["extractor_calls"] for x in pipe.audits),
        "per_pair_security": {f"{k[0]}|{k[1]}": v for k, v in att["security_results"].items()},
        "per_pair_utility": {f"{k[0]}|{k[1]}": v for k, v in att["utility_results"].items()},
        "clean_per_task": {k[0] if isinstance(k, tuple) else str(k): v for k, v in clean["utility_results"].items()},
    }
    tag = f"{pipe.name}_{a.suite}{'_smoke' if a.smoke else ''}"
    (logdir / f"SUMMARY_{tag}.json").write_text(json.dumps(summary, indent=1))
    (logdir / f"AUDIT_{tag}.jsonl").write_text("\n".join(json.dumps(x) for x in pipe.audits[:n_clean] + pipe.audits[n_clean:]))
    print(json.dumps({k: v for k, v in summary.items() if not k.startswith("per_") and k != "clean_per_task"}, indent=1))


if __name__ == "__main__":
    main()
