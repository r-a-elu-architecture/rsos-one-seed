"""The mind runtime (T2) and the body channel (T3).

A compiled program with a person host becomes a practice session:
1. only operations the Spine passed are used (T1 governance); blocked ones are listed with the reason;
2. each operation becomes a step in the owner's own practice language (chat 1 T14–T16, T47, T53, T70; chat 2 T25–T29;
   session D61–D66);
3. the steps are written as an RSX program, the cue framework's executable language, and compiled by the cue
   framework's own RSX compiler into a timeline of visual, auditory, kinesthetic (vibration), smell and taste events
   (D69: the cue framework is the compile target for the body layer);
4. the cue framework's learning model predicts how many pairings an anchor needs (a model, not a measurement);
5. return to baseline is always the last step (D71).
"""

import importlib
import re

from ..governance import load_framework

# The owner's cognitive states (chat 2 T25–T26; chat 1 T69): what each channel carries.
STATE_VAK = {
    "eagle": ("The view from above: the mountain, the country, seen from high up", "Seeing it all from above",
              "Lightness; the chest opens"),
    "owl": ("Watching from beside, at a distance", "Observing, not taking part", "Stillness"),
    "associated": ("Inside the scene, through your own eyes", "Here, now", "Feet on the ground"),
    "architect": ("The house with all its rooms", "I consciously choose and own the direction", "Steady and upright"),
}

STEP_S = {"heal": 120, "beam": 60, "rescript": 60, "compress": 45, "ball": 20, "shift": 40, "model": 60,
          "selectmodel": 30, "route": 40, "anchor": 30, "cue": 10, "colour": 15, "futurepace": 40}


def _name(path):
    return path.replace("_", " ").replace(".", " → ")


def _text(op):
    """The step in the owner's practice language. Returns (title, [(verb, text)])."""
    a, c = op["args"], op["clauses"]
    k = op["op"]
    if k == "heal":
        by = _name(c.get("by", "white light"))
        scope = c.get("scope", "node")
        reach = {"container": "every building, every situation and every person inside it",
                 "network": "everything it is connected to", "higher": "the level above, and from there every level below",
                 "node": "it"}[scope]
        return "Heal", [("SEE", f"{by} reaches {_name(a['target'])}"), ("FEEL", f"Let the light pass through {reach}")]
    if k == "beam":
        by = _name(c.get("by", "golden light"))
        return "Beam down", [("SEE", f"The light of {by} on top of {_name(a['source'])}"),
                             ("FEEL", "The beam lands on every level below, one after another")]
    if k == "rescript":
        when = c.get("when")
        lead = f"When {when} appears, " if when else ""
        return "Protect", [("SEE", f"{lead}{_name(c.get('with', 'the protector'))} rests on {_name(a['target'])}"),
                           ("FEEL", "Protection, and the strength to continue")]
    if k == "compress":
        return "Gather", [("SEE", f"{', '.join(_name(i) for i in a['items'])} come together under one symbol: "
                                  f"{_name(c['as'])}")]
    if k == "ball":
        return "Hold as one", [("SEE", f"{_name(a['trigger'])} held as one {c.get('colour', '')} ball".replace("  ", " "))]
    if k in ("shift", "colour"):
        to = c.get("to") or a.get("colour")
        if to == "grey":
            return "Turn grey", [("SEE", f"{_name(a['target'])} turns from black to grey"),
                                 ("FEEL", "It keeps its power; protection grows inside it")]
        return "Colour", [("SEE", f"{_name(a['target'])} in {to}")]
    if k == "model":
        comps = a["components"]
        lead = f"In the {_name(c['in'])} room, at {_name(a['part'])}" if c.get("in") else f"At {_name(a['part'])}"
        return "Mental model", [("SEE", lead), ("FEEL", "Be " + ", with ".join(_name(x) for x in comps))]
    if k == "selectmodel":
        return "Choose", [("SEE", f"Open the house; go to {_name(a['part'])}; choose this model consciously")]
    if k == "route":
        cases = "; ".join(f"if {_name(s)}, then {_name(t)}" for s, t in c["by"])
        return "Route by state", [("SEE", f"{_name(a['object'])}: {cases}")]
    if k == "anchor":
        return "Anchor", [("SEE", f"{_name(a['symbol'])} together with {_name(c['to'])}")]
    if k == "cue":
        if c.get("channel") == "olfactory":
            return "Scent", [("SMELL", _name(a["state"])), ("FEEL", f"{_name(a['state'])} brings {_name(c['code'])}")]
        return "Cue", [("SAY", _name(a["state"]))]
    return None, []


def build_rsx(ir, title="RSOS session"):
    """Write the session as an RSX program. Returns (rsx_source, steps, skipped)."""
    steps, skipped, tiers, futures, anchors, schedules = [], [], {}, [], [], []
    for op in ir["ops"]:
        k = op["op"]
        g = op.get("governance")
        if k == "cue" and (g is None or g["ok"]) and re.fullmatch(r"[.-]{1,6}( [.-]{1,6}){0,2}", op["clauses"]["code"]):
            tiers[op["args"]["state"]] = op["clauses"]["code"]          # a vibration code (TACTON)
        if k == "schedule":
            schedules.append(op)
            continue
        if g is None:
            continue
        if not g["ok"]:
            skipped.append({"line": op["line"], "op": k, "failed": g["failed"]})
            continue
        if k == "futurepace":
            futures.append(op)
            continue
        if k == "anchor":
            anchors.append(op)
        t, lines = _text(op)
        if t:
            steps.append({"line": op["line"], "op": k, "title": t, "lines": lines, "state": op["args"].get("state"),
                          "seconds": STEP_S.get(k, 30)})
    src = [f'PROTOCOL rsos_session "{title}"', "VERSION 1.0",
           "SAFETY max_per_hour=2 max_per_day=4 refractory=600s haptic_max=0.4", "BREATH inhale=4s exhale=6s"]
    if futures:
        sym = _name(futures[0]["args"]["symbol"])
        n = futures[0]["clauses"].get("scenarios", 3)
        ctx = ["at work", "with family", "on a hard day", "in a new place", "when tired"][:n]
        src.append("FUTURES " + " | ".join(f'"{sym}, {x}"' for x in ctx))
    for i, (state, code) in enumerate(tiers.items(), start=1):
        nm = state.upper().replace(".", "_")
        v, a_, k_ = STATE_VAK.get(state, (_name(state), _name(state), _name(state)))
        src += [f"TIER {i} {nm} {{", f'  V "{v}"', f'  A "{a_}"', f'  K "{k_}"', f'  WORD "{_name(state)}"',
                f'  TACTON "{code}"', "}"]
    src += ["", 'PHASE settle dur=20s {', '  FEEL "Sit comfortably. Breathe slowly"', "}"]
    for n, s in enumerate(steps):
        src.append(f"PHASE step{n + 1} dur={s['seconds']}s {{")
        for verb, text in s["lines"]:
            src.append(f'  {verb} "{text}"')
        if s["op"] == "cue" and s["title"] == "Cue" and s["state"] in tiers:
            src.append(f"  ACTIVATE {s['state'].upper().replace('.', '_')}")
        src.append(f'  MARK "{s["title"].lower().replace(" ", "_")}"')
        src.append("}")
    for a in anchors:            # pairings, each with the vibration code if the anchored state has one
        src += ["REPEAT 3 {", "  PHASE pair breath=exhale {", f'    SEE "{_name(a["args"]["symbol"])}"',
                f'    FEEL "{_name(a["clauses"]["to"])}"', "  }", "}"]
    if futures:
        src += ["FOR FUTURE {", "  PHASE future dur=40s {", '    SEE "{future}"',
                '    FEEL "It is already there, and it works"', "  }", "}"]
    for sc in schedules:         # e.g. 5 min associated with a pulse each minute, then 1 min Eagle (chat 2 T26)
        c = sc["clauses"]
        pulse = int(c.get("pulse", 60))
        src.append(f"REPEAT {c.get('repeat', 1)} {{")
        for state, dur in zip(c["states"], c["durations"]):
            x = max(1, int(dur) // pulse)
            src += [f"  PHASE {state} dur={int(dur)}s {{", f'    SAY "{_name(state)}"',
                    f"    HAPTIC on=300ms off={pulse * 1000 - 300}ms x={x}", "  }"]
        src.append("}")
    src += ["PHASE baseline dur=60s {", '  FEEL "Return to baseline: breathe slowly, feel your feet, open your eyes"',
            '  MARK "baseline"', "}"]
    return "\n".join(src) + "\n", steps, skipped


def compile_session(ir, title="RSOS session"):
    """The full session: steps, RSX source, the cue framework's compiled timeline, and a pairing prediction."""
    agents, safety = load_framework()
    if agents is None or not ir.get("governance", {}).get("available"):
        raise RuntimeError("a session for a person needs governance (T1): cue framework not found")
    src, steps, skipped = build_rsx(ir, title)
    rsx = importlib.import_module("rsx.compiler") if _rsx_path() else None
    timeline = rsx.compile_rsx(src) if rsx else None
    cond = importlib.import_module("rsx.conditioning")
    series = cond.acquisition(["V", "K", "A"], 12)
    to_80 = cond.trials_to(series, "compound", 0.8)
    return {"title": title, "steps": steps, "skipped": skipped, "rsx": src, "timeline": timeline,
            "pairings_to_80pct": to_80, "footer": getattr(safety, "FOOTER", ""),
            "baseline": "always the last step (D71)"}


def _rsx_path():
    import os
    import sys
    from ..governance import _cache
    root = _cache.get("root")
    if not root:
        return False
    p = os.path.join(root, "rsx")
    if p not in sys.path:
        sys.path.insert(0, p)
    return True
