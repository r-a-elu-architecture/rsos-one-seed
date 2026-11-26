"""The White Dragon engine: a cross-domain creativity module over spheres.

A sphere is a graph node with spatial extent: a surface, an interior and a core. Landings have a position and a
depth, and spheres can nest. Owner's terms: ball (17 Nov 2026, 09:20), sphere (17 Nov 2026, 11:22).

Owner, 17 Nov 2026 (White Dragon, golden light, green particles, the water drop). Functional reading:
- white light  = heal: keep only children that are measurable, new and of good intention (`heal_filter`);
                 styles per archetype: lion (courage: boldest path) and tiger (precision: closest path);
- golden light = find the best paths between a sphere and the domain library by shared relations (`paths`);
- green particle = lands on the shared relation, becomes part of the sphere, opens that place's library and
                   creates a child sphere (`land`); the effect is bounded by the sphere's lack (deficit);
- green flow   = children are spheres too, so the engine runs again on them (`grow`).
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OBSERVABLE = {
    "drift": "green-dot drift detection (C1)", "recovery": "White Dragon heal rate and cost (C1)",
    "compression": "palace size ratio (C1)", "integrity": "structure-decode accuracy (T7c)",
    "propagation": "runtime propagation (R-003)", "persistence": "glyph lineage continuity (U1)",
    "lineage": "glyph lineage graph (U1)", "containment": "consent and Spine checks (T1/U1)",
    "ethics": "consent and Spine checks (T1/U1)", "coupling": "lens co-lighting (S1)",
    "resonance": "lens co-lighting (S1)", "depth": "operation depth (U1)",
}


def load():
    spheres = json.load(open(os.path.join(HERE, "data", "metric_spheres.json"), encoding="utf-8"))
    books = json.load(open(os.path.join(HERE, "data", "domain_books.json"), encoding="utf-8"))
    entries = [{"domain": d, **e} for d, L in books.items() for e in L]
    return spheres, entries


def observable(rels, obj="system"):
    return [r for r in rels if r in OBSERVABLE] if obj != "model" else []


def deficit(sphere):
    rels = sphere["relations"]
    return 1.0 - len(observable(rels, sphere.get("object", "system"))) / len(rels)


def paths(sphere, entries):
    """Golden light: every measure sharing at least one relation with the sphere."""
    out = []
    for e in entries:
        shared = sorted(set(sphere["relations"]) & set(e["relations"]))
        if shared:
            out.append((e, shared))
    return out


def land(sphere, entry, shared):
    """Green particle: lands on the shared relation and makes the child sphere."""
    rels = sorted(set(sphere["relations"]) | set(entry["relations"]))
    obs_e = observable(entry["relations"])
    obj = sphere.get("object", "system") if sphere.get("object") != "model" or not obs_e else "model_via_" + entry["domain"]
    child = {"code": f"{sphere['code']}×{entry['measure']}", "name": f"{entry['measure']} of {sphere['name']}",
             "relations": rels, "object": obj, "domain": entry["domain"], "parent": sphere["code"],
             "landed_on": shared, "domains": sorted(set(sphere.get("domains", [])) | {entry["domain"]})}
    obs = observable(rels, "system" if obj.startswith("model_via") else obj)
    child["measured_by"] = sorted({OBSERVABLE[r] for r in obs})
    child["deficit"] = 1.0 - len(obs) / len(rels)
    child["definition"] = (f"{entry['measure']} ({entry['domain']}) applied to {sphere['name']}, landing on "
                           f"{', '.join(shared)}; measured by {'; '.join(child['measured_by']) or 'nothing yet'}")
    return child


def good_intention(child):
    r = set(child["relations"])
    return "bias" not in r or bool(r & {"ethics", "containment"})


def heal_filter(children, seen):
    """White light: measurable, new signature, good intention."""
    out = []
    for c in children:
        sig = (tuple(c["relations"]), tuple(c["domains"]))
        if c["measured_by"] and sig not in seen and good_intention(c):
            seen.add(sig); out.append(c)
    return out


def grow(spheres, entries, generations=2, filtered=True):
    sizes, gen, seen, allc = [len(spheres)], spheres, set(), []
    for _ in range(generations):
        kids = [land(b, e, s) for b in gen for e, s in paths(b, entries)]
        if filtered:
            kids = heal_filter(kids, seen)
        sizes.append(len(kids)); allc.append(kids); gen = kids
    return sizes, allc


def style_choice(sphere, entries, style):
    ps = paths(sphere, entries)
    if not ps:
        return None
    if style == "lion":                     # courage: boldest, most new relations
        key = lambda p: (len(set(p[0]["relations"]) - set(sphere["relations"])), -len(p[1]))
    else:                                    # tiger: precision, most shared, fewest new
        key = lambda p: (len(p[1]), -len(set(p[0]["relations"]) - set(sphere["relations"])))
    best = max(key(p) for p in ps)
    return [p for p in ps if key(p) == best]
