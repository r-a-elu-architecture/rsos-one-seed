"""ENCODE / DECODE: a world as a painting record and back (the representation cipher, U61).

A painting record lists one glyph per module: its label (from a codebook), colour, position, depth and properties.
The codebook maps labels to module identities. Relabelling every glyph consistently (a new codebook) must not change
what runs.
"""

import numpy as np

from .model import World, Module


def encode(world: World, codebook=None):
    codebook = dict(codebook or {})
    record = {"objects": []}
    for o in world.objs.values():
        glyphs = []
        for m in o.modules.values():
            label = codebook.setdefault(m.key, f"g{len(codebook)}")
            colour = int(np.argmax(m.props))
            glyphs.append({"glyph": label, "colour": colour, "rel": list(m.rel), "depth": m.depth,
                           "props": [float(v) for v in m.props], "health": m.health})
        record["objects"].append({"name": o.name, "pos": list(o.pos), "rot": o.rot, "glyphs": glyphs,
                                  "hidden": sorted(codebook[k] for k in o.hidden)})
    record["links"] = [[codebook[l.src], codebook[l.dst], l.kind, l.w, l.state] for l in world.links]
    return record, codebook


def decode(record, codebook):
    inv = {v: k for k, v in codebook.items()}
    w = World()
    for ob in record["objects"]:
        mods = []
        for g in ob["glyphs"]:
            key = inv[g["glyph"]]
            name = key[len(ob["name"]) + 1:] if key != ob["name"] else ""
            mods.append(Module(name, ob["name"], g["depth"], tuple(g["rel"]), np.array(g["props"]), g["health"]))
        o = w.add_object(ob["name"], mods, tuple(ob["pos"]), ob["rot"])
        o.hidden = {inv[h] for h in ob["hidden"]}
    from .model import Link
    for s, d, kind, wt, state in record["links"]:
        w.links.append(Link(inv[s], inv[d], kind, wt, state))
    return w


def relabel(record, codebook, rng):
    """Give every glyph a new label; return the new record and the matching codebook."""
    labels = list(codebook.values())
    new = [f"h{i}" for i in rng.permutation(len(labels))]
    m = dict(zip(labels, new))
    rec = {"objects": [], "links": [[m[s], m[d], k, w, st] for s, d, k, w, st in record["links"]]}
    for ob in record["objects"]:
        rec["objects"].append({**ob, "glyphs": [{**g, "glyph": m[g["glyph"]]} for g in ob["glyphs"]],
                               "hidden": [m[h] for h in ob["hidden"]]})
    return rec, {k: m[v] for k, v in codebook.items()}
