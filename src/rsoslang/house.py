"""The house of rooms runs (T8): one program, two runtimes.

The same RSOS program (house → rooms = states → objects → parts carrying models, the control panel choosing a model)
runs:
  - in a person: the practice session (mind/session.py, compiled by the cue framework's RSX compiler);
  - in an agent: each model's components switch on executable components of the agent.

Equivalence (manual §8; T8 of the review list), checked on every run:
  intent  the same model lines are present in both runtimes;
  trace   both runtimes visit the house in the same order (room → part → components → choice);
  causal  changing a model's components changes what runs in both runtimes.
"""

from .mind.session import compile_session

# Component library for the support-agent host (defined here, by us; components outside it do nothing in the agent).
AGENT_COMPONENTS = {
    "analogical_reasoning": ("PIERCE synonym_expander THROUGH classify.brain", "use what is similar"),
    "associated": ("PIERCE spell_corrector THROUGH classify.head", "read closely, from inside"),
    "top_view": ("PIERCE cache THROUGH memory.heart", "see the pattern from above"),
    "future_pacing": ("PIERCE fast_retry THROUGH act.heart", "rehearse the next attempt"),
    "confidence": ("HEAL act", "one more recovery attempt"),
    "dissociated": ("SHIFT act TO grey", "watch the risky part from outside"),
}


def house_trace(ir):
    trace = []
    for op in ir["ops"]:
        if op["op"] == "model":
            trace.append(("model", op["args"]["part"], tuple(op["args"]["components"]), op["clauses"].get("in")))
        elif op["op"] == "selectmodel":
            trace.append(("choose", op["args"]["part"]))
    return trace


def agent_program(ir, chosen=None):
    """The agent's gestures from the models (only the chosen model, if the control panel chose one)."""
    lines = []
    for op in ir["ops"]:
        if op["op"] != "model" or (chosen and op["args"]["part"] != chosen):
            continue
        for comp in op["args"]["components"]:
            if comp in AGENT_COMPONENTS and AGENT_COMPONENTS[comp][0] not in lines:
                lines.append(AGENT_COMPONENTS[comp][0])
    return "\n".join(lines) + ("\n" if lines else "")


def run_both(ir, workflow, tickets, seed=0):
    chosen = next((op["args"]["part"] for op in ir["ops"] if op["op"] == "selectmodel"), None)
    from .painting.scene import apply
    gestures = agent_program(ir, chosen)
    wf, changes = apply(workflow, gestures)
    agent = wf.evaluate(tickets, seed)
    session = compile_session(ir)
    trace = house_trace(ir)
    person_marks = [s["op"] for s in session["steps"] if s["op"] in ("model", "selectmodel")]
    agent_marks = [t[0] for t in trace]
    eq = {"intent": all(any(f"at {t[1].replace('_', ' ').replace('.', ' → ')}" in " ".join(x[1] for x in s["lines"])
                            for s in session["steps"]) for t in trace if t[0] == "model"),
          "trace": [m.replace("selectmodel", "choose") for m in person_marks] == agent_marks}
    return {"agent": agent, "gestures": gestures, "changes": changes, "session_steps": len(session["steps"]),
            "timeline_events": len(session["timeline"]["events"]), "trace": trace, "equivalence": eq}
