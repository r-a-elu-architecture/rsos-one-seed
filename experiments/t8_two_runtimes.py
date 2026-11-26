"""T8: the robot-head house runs in a person (session) and in an agent; equivalence and causal check."""
from common import compile_source, save, ROOT
from rsoslang.house import run_both
from rsoslang.agents.workflow import build
from rsoslang.agents.tickets import make_tickets

A = make_tickets(500, 2, typo_rate=0.3, unseen_rate=0.3)
src = open(f"{ROOT}/examples/robot_head.rsl").read()
alt = src.replace("MODEL robot.head = associated + confidence + analogical_reasoning",
                  "MODEL robot.head = associated + confidence")          # causal check: one component removed


def main():
    base = build().evaluate(A, 2)
    r1 = run_both(compile_source(src).ir, build(), A, 2)
    r2 = run_both(compile_source(alt).ir, build(), A, 2)
    causal = r1["agent"]["accuracy"] != r2["agent"]["accuracy"] and r1["session_steps"] >= 1
    summary = {"baseline_accuracy": base["accuracy"], "house_accuracy": r1["agent"]["accuracy"],
               "without_analogy": r2["agent"]["accuracy"], "agent_gestures": r1["gestures"].strip().split("\n"),
               "person_session_steps": r1["session_steps"], "person_timeline_events": r1["timeline_events"],
               "equivalence": {**r1["equivalence"], "causal": causal}}
    path, digest = save("T8-TWO-RUNTIMES", {"summary": summary})
    print(path, digest)
    for k, v in summary.items():
        print(k, v)


if __name__ == "__main__":
    main()
