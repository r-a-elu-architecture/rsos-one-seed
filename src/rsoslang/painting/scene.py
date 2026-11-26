"""Program ⇄ painting for agent workflows.

encode(workflow, metrics) → scene         the program as a painting (default codebook, spec/PAINTING_INTERFACE.md)
apply(workflow, rsos_source) → workflow   gestures written in the RSOS Language become exact program changes
render_svg(scene) → SVG                   what a person sees
"""

from ..compiler import compile_source
from ..agents.library import LIBRARY

# Default codebook: node role → scene object (people can bind their own symbols later).
OBJECT_FOR_ROLE = {"input": "door", "transform": "path", "reason": "bird", "memory": "lake", "policy": "sky",
                   "tool": "engine", "check": "owl", "output": "bridge"}
PLACES = ("head", "heart", "brain")


def header(workflow):
    """The RSOS declarations of a workflow: every node is an object with head, heart and brain; every guest is too."""
    lines = ["LANGUAGE RSOS 0.2", "WORLD workflow"]
    for name, n in workflow.nodes.items():
        lines.append(f"OBJECT {name} KIND {OBJECT_FOR_ROLE.get(n.role, 'object')} DOMAIN ai")
        for p in PLACES:
            lines.append(f"PART {name}.{p}")
    for g in LIBRARY:
        lines.append(f"OBJECT {g} KIND guest DOMAIN ai")
    return "\n".join(lines) + "\n"


def apply(workflow, gestures: str):
    """Compile gestures (RSOS statements) and apply them to a copy of the workflow. Returns (workflow, changes)."""
    res = compile_source(header(workflow) + gestures)
    if not res.ok:
        raise ValueError("\n".join(str(d) for d in res.errors))
    wf = workflow.copy()
    changes = []
    n_head = header(workflow).count("\n")
    for op in res.ir["ops"]:
        if op["line"] <= n_head:
            continue
        kind, a, c = op["op"], op["args"], op["clauses"]
        if kind == "pierce":
            guest, target = a["source"], c["through"]
            node, _, place = target.partition(".")
            g = LIBRARY.get(guest)
            if g is None or node not in wf.nodes or place not in PLACES:
                raise ValueError(f"line {op['line']}: PIERCE <guest> THROUGH <node>.head|heart|brain")
            n = wf.nodes[node]
            if place == "head":
                n.head.append(g)
            elif place == "heart":
                n.heart.append(g)
            elif place == "brain":
                if not g.at_brain(n):
                    changes.append(f"{guest} has no meaning in the brain of {node}: nothing changed")
                    continue
                n.brain.append(g)
            changes.append(f"{guest} pierced into the {place} of {node}")
        elif kind == "place" and "near" in c:
            g, node = LIBRARY[a["object"]], c["near"]
            wf.nodes[node].near.append(g)
            changes.append(f"{a['object']} placed near {node}")
        elif kind == "dot":
            g, node = LIBRARY[a["function"]], c["into"].split(".")[0]
            wf.nodes[node].near.append(g)
            changes.append(f"{a['function']} dotted into {node} (adds a check after it; replaces nothing)")
        elif kind == "shift":
            node = a["target"]
            if c["to"] == "grey":
                wf.nodes[node].sandboxed = True
                changes.append(f"{node} turned grey: its power is kept, its crashes are contained")
        elif kind == "heal":
            node = a["target"]
            wf.nodes[node].retries += 1
            changes.append(f"{node} healed: one more recovery attempt")
        elif kind == "move":
            src, dst = a["source"], c["onto"]
            order = [x for x in wf.order if x != src]
            order.insert(order.index(dst), src)
            wf.order = order
            changes.append(f"{src} moved in front of {dst}")
    return wf, changes


def encode(workflow, metrics):
    """The workflow as a scene: x = order in the flow, y = layer (top = supervisory), size = cost share,
    colour = state (healthy / errors / contained / crashing)."""
    visits = metrics.get("visits", {})
    errors = metrics.get("errors", {})
    total_cost = sum(n.cost * visits.get(k, 0) for k, n in workflow.nodes.items()) or 1.0
    objs = []
    for i, name in enumerate(workflow.order):
        n = workflow.nodes[name]
        v = max(visits.get(name, 1), 1)
        err = errors.get(name, 0) / v
        state = "black" if (name == "act" and metrics.get("crashed", 0) > 0) else \
                "grey" if n.sandboxed else ("red" if err > 0.2 else "white")
        objs.append({"name": name, "kind": OBJECT_FOR_ROLE.get(n.role, "object"), "x": i, "y": n.layer,
                     "size": 0.5 + 3 * n.cost * visits.get(name, 0) / total_cost, "state": state,
                     "error_rate": round(err, 3),
                     "guests": {"head": [g.name for g in n.head], "heart": [g.name for g in n.heart],
                                "brain": [g.name for g in n.brain],
                                "near": [g.name for g in n.near]}})
    links = [{"from": a, "to": b} for a, b in zip(workflow.order, workflow.order[1:])]
    return {"objects": objs, "links": links,
            "metrics": {k: metrics[k] for k in ("accuracy", "crashed", "cost_per_ticket", "score")}}


COLOURS = {"white": "#f4f1e8", "red": "#d9534f", "grey": "#9a9a9a", "black": "#222"}
GLYPH = {"door": "▯", "path": "≈", "bird": "⋎", "lake": "◡", "sky": "☁", "engine": "⚙", "owl": "◉", "bridge": "⌒"}


def render_svg(scene, title=""):
    W, H, dx, dy = 1100, 430, 85, 85
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="sans-serif">',
           f'<rect width="{W}" height="{H}" fill="#eaf2f8"/>',
           f'<rect y="{H - 90}" width="{W}" height="90" fill="#dfe8d0"/>',
           f'<text x="16" y="24" font-size="15" font-weight="bold">{title}</text>']
    pos = {o["name"]: (60 + o["x"] * dx, 70 + o["y"] * dy) for o in scene["objects"]}
    for l in scene["links"]:
        (x1, y1), (x2, y2) = pos[l["from"]], pos[l["to"]]
        out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#4a7ba6" stroke-width="2" opacity="0.6"/>')
    for o in scene["objects"]:
        x, y = pos[o["name"]]
        r = 12 + 6 * o["size"]
        out.append(f'<circle cx="{x}" cy="{y}" r="{r:.1f}" fill="{COLOURS[o["state"]]}" stroke="#333"/>')
        out.append(f'<text x="{x}" y="{y + 5}" font-size="16" text-anchor="middle"'
                   f' fill="{"#fff" if o["state"] == "black" else "#222"}">{GLYPH.get(o["kind"], "•")}</text>')
        out.append(f'<text x="{x}" y="{y + r + 14}" font-size="11" text-anchor="middle">{o["name"]}</text>')
        for k, (ox, oy) in {"head": (0, -r - 8), "heart": (0, 0), "brain": (0, -r / 2), "near": (r + 14, 0)}.items():
            for j, g in enumerate(o["guests"][k]):
                fill = "#7b5ea7" if k == "brain" else "#f0ad4e"
                out.append(f'<rect x="{x + ox - 5 + 11 * j}" y="{y + oy - 5}" width="10" height="10" fill="{fill}"'
                           f' stroke="#333"><title>{g} at {k}</title></rect>')
    m = scene["metrics"]
    out.append(f'<text x="16" y="{H - 16}" font-size="13">accuracy {m["accuracy"]:.3f} · crashed {m["crashed"]:.3f} · '
               f'cost per ticket {m["cost_per_ticket"]:.2f} · score {m["score"]:.3f}</text>')
    out.append("</svg>")
    return "\n".join(out)
