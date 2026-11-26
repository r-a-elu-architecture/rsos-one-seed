"""Execute compiled RSOS programs (the IR) in the simulation runtime.

Each operator has its own effect; the effect of the contact operators depends on the resolved meaning
(core, binding or search), so a declared variation changes what runs.
"""

import hashlib
import math

import numpy as np

from .model import World, Module, Link, K, RHO, _dist

STEER = 0.3   # how far BEAM / RESONATE move properties


def _seed_for(name, seed):
    h = hashlib.sha256(f"{seed}:{name}".encode()).digest()
    return int.from_bytes(h[:4], "little")


def default_modules(name, seed):
    rng = np.random.default_rng(_seed_for(name, seed))
    return [Module("", name, 0, (0.0, 0.0), rng.normal(size=K))]


class Executor:
    def __init__(self, ir, layouts=None, seed=0, search_choice=None):
        """layouts: obj name -> list of Module (from model.grid_modules) or None for one default module.
        search_choice: meaning key -> chosen candidate, for keys left open with SEARCH."""
        self.ir = ir
        self.layouts = layouts or {}
        self.seed = seed
        self.search_choice = search_choice or {}
        self.w = World()
        self.depth_allowed = {}     # obj -> max depth reachable after ENTER
        self.lines = {}
        self.regions = {}
        self.trace = []
        self.base_props = {}

    # ---- helpers ------------------------------------------------------------------------------
    def ensure(self, name):
        root = name.split(".")[0]
        if root not in self.w.objs:
            mods = self.layouts.get(root)
            mods = [Module(m.name, root, m.depth, m.rel, m.props.copy()) for m in mods] if mods else default_modules(root, self.seed)
            self.w.add_object(root, mods)
            for m in self.w.objs[root].modules.values():
                self.base_props[m.key] = m.props.copy()
        return self.w.objs[root]

    def mods_of(self, path, depth=None):
        """Modules addressed by a path: the object (all modules) or a part and everything beneath it."""
        o = self.ensure(path)
        if path == o.name:
            mods = list(o.modules.values())
        else:
            mods = [m for m in o.modules.values() if m.key == path or m.key.startswith(path + ".")]
            if not mods:   # implicit part: create a module at the object's centre
                rng = np.random.default_rng(_seed_for(path, self.seed))
                m = Module(path[len(o.name) + 1:], o.name, path.count("."), (0.0, 0.0), rng.normal(size=K))
                o.modules[m.key] = m
                self.base_props[m.key] = m.props.copy()
                mods = [m]
        if depth is not None:
            mods = [m for m in mods if m.depth <= depth]
        return mods

    def surface(self, path):
        return [m for m in self.mods_of(path) if m.depth == min(x.depth for x in self.mods_of(path))]

    def link(self, a, b, kind, w, both=False):
        self.w.links.append(Link(a.key, b.key, kind, w))
        if both:
            self.w.links.append(Link(b.key, a.key, kind, w))

    def meaning(self, op, prefix):
        for m in op["meanings"]:
            if m["key"].startswith(prefix):
                if m["source"] == "search":
                    return self.search_choice.get(m["key"], m["candidates"][0])
                return m["value"]
        return None

    def side_point(self, obj, side):
        mods = [m for m in obj.modules.values() if m.depth == 0]
        pts = [obj.world(m) for m in mods]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
        return {"top": (cx, max(ys)), "bottom": (cx, min(ys)), "left": (min(xs), cy), "right": (max(xs), cy),
                "front": (cx, cy), "back": (cx, cy)}.get(side, (cx, cy))

    def nearest(self, mods, point):
        return min(mods, key=lambda m: _dist(self.w.pos(m), point))

    # ---- the contact meanings -------------------------------------------------------------------
    def apply_entry(self, src_mod, tgt, meaning, side):
        """The effect of the entry-side meaning on the target object."""
        o = self.w.objs[tgt.split(".")[0]]
        surf = [m for m in self.mods_of(tgt) if m.depth == 0] or self.mods_of(tgt)
        if meaning == "supervisory_entry":          # the entry layer supervises every surface module
            for m in surf:
                self.link(src_mod, m, "supervise", 0.25)
        elif meaning == "lateral":                  # the facing side and its same-level neighbours
            p = self.side_point(o, side)
            for m in sorted(surf, key=lambda m: _dist(self.w.pos(m), p))[:2]:
                self.link(src_mod, m, "lateral", 0.5, both=True)
        elif meaning == "local_contact":            # one place
            self.link(src_mod, self.nearest(surf, self.side_point(o, side)), "local", 0.6)
        elif meaning == "interface_only":
            self.link(src_mod, self.nearest(surf, self.side_point(o, side)), "interface", 0.5)
        elif meaning == "dependency":
            edge = max(surf, key=lambda m: _dist(o.world(m), o.pos))
            self.link(src_mod, edge, "dependency", 1.0)
        elif meaning == "nested_state":
            inner = [m for m in self.mods_of(tgt) if m.depth == 1] or surf
            self.link(src_mod, self.nearest(inner, self.side_point(o, side)), "nested", 0.7)
        elif meaning == "multi_layer":
            pass                                    # handled by the pierce body
        else:
            raise ValueError(f"no effect defined for meaning {meaning!r}")

    def pierce(self, op):
        a, b = op["args"]["source"], op["clauses"]["through"]
        depth = op["clauses"].get("depth", 2)
        side = op["clauses"].get("from")
        A, B = self.mods_of(a), self.mods_of(b)
        sa = [m for m in A if m.depth == 0 and self.w.exposed(m)]
        sb = [m for m in B if m.depth == 0 and self.w.exposed(m)]
        pairs = [(x, y) for x in sa for y in sb if _dist(self.w.pos(x), self.w.pos(y)) <= RHO]
        if pairs:
            # Through each other: each side sees the other, down through the layers (surface → body → sub-code).
            for x, y in pairs:
                self.link(x, y, "pierce", 1.0, both=True)
                for d, w in ((1, 0.7), (2, 0.5)):
                    if d <= depth:
                        for yy in B:
                            if yy.depth == d and yy.rel == y.rel:
                                self.link(x, yy, "pierce", w)
                        for xx in A:
                            if xx.depth == d and xx.rel == x.rel:
                                self.link(y, xx, "pierce", w)
                # neighbouring processes are touched too (owner c2 T35)
                for yy in sb:
                    if yy is not y and RHO < _dist(self.w.pos(x), self.w.pos(yy)) <= 1.6 * RHO:
                        self.link(x, yy, "pierce_neighbour", 0.3)
        else:
            # Not overlapping: a spear along the line from the source to the target, through the layers it hits.
            pa = np.mean([self.w.pos(m) for m in sa], axis=0)
            pb = np.mean([self.w.pos(m) for m in sb], axis=0)
            start = self.nearest(sa, tuple(pb))
            for y in B:
                if y.depth <= depth and _dist_to_line(self.w.pos(y), pa, pb) <= RHO:
                    self.link(start, y, "pierce", 1.0 if y.depth == 0 else 0.6)
        if side:
            meaning = self.meaning(op, f"contact.{side}")
            if meaning and meaning != "multi_layer":
                self.apply_entry(sa[0] if sa else A[0], b, meaning, side)

    # ---- dispatch -------------------------------------------------------------------------------
    def run(self):
        for op in self.ir["ops"]:
            fn = getattr(self, "op_" + op["op"], None)
            if fn:
                fn(op)
                self.trace.append(op["op"])
        return self.w

    def op_object(self, op):
        self.ensure(op["args"]["name"])

    def op_scene(self, op):
        for it in op["clauses"].get("order", []):
            self.ensure(it)
        # left-to-right order: lay the scene out along x
        for i, it in enumerate(op["clauses"].get("order", [])):
            self.w.objs[it].pos = (i * 1.0, 0.0)

    def op_place(self, op):
        o = self.ensure(op["args"]["object"])
        if "near" in op["clauses"]:
            t = self.ensure(op["clauses"]["near"])
            o.pos = (t.pos[0] + 0.6, t.pos[1])
            return
        o.pos = (op["clauses"]["x"], op["clauses"]["y"])
        o.rot = op["clauses"].get("rot", o.rot)

    def op_property(self, op):
        path = op["args"]["path"]
        val = op["args"]["value"]
        if isinstance(val, (int, float)):
            obj = path.rsplit(".", 1)[0]
            for m in self.mods_of(obj):
                m.props = m.props * (1 + 0.1 * float(val))

    def op_touch(self, op):
        a, b = op["args"]["source"], op["clauses"]["on"]
        side = op["clauses"].get("at", "surface")
        src = self.nearest(self.surface(a), self.side_point(self.ensure(b), side))
        self.apply_entry(src, b, self.meaning(op, "contact."), side)

    def op_attach(self, op):
        a, b = op["args"]["source"], op["clauses"]["to"]
        side = op["clauses"].get("at", "edge")
        src = self.surface(a)[0]
        self.apply_entry(src, b, self.meaning(op, "contact."), side)

    def op_pierce(self, op):
        self.pierce(op)

    def op_pass(self, op):
        a, wall = op["args"]["source"], op["clauses"]["through"]
        into = op["clauses"].get("into") or wall
        src = self.surface(a)[0]
        for m in self.mods_of(into):
            self.link(src, m, "pass", 0.8)       # adds; nothing is replaced (owner c2 T33)

    def op_dot(self, op):
        f, into = op["args"]["function"], op["clauses"]["into"]
        fm = self.surface(f)[0]
        tgt = self.mods_of(into)[0]
        o = self.w.objs[tgt.obj]
        name = op["clauses"].get("as") or f"dot_{len(o.modules)}"
        dm = Module(f"{tgt.name + '.' if tgt.name else ''}{name}", o.name, tgt.depth + 1, tgt.rel, fm.props.copy())
        o.modules[dm.key] = dm
        self.link(dm, tgt, "dot", 1.0, both=True)

    def op_move(self, op):
        a, b = self.ensure(op["args"]["source"]), self.ensure(op["clauses"]["onto"])
        a.pos = b.pos

    def op_rotate(self, op):
        o = self.ensure(op["args"]["target"])
        o.rot = (o.rot + op["clauses"].get("by", 90.0)) % 360

    def op_flip(self, op):
        o = self.ensure(op["args"]["target"])
        for m in o.modules.values():
            m.rel = (-m.rel[0], m.rel[1])

    def op_overlay(self, op):
        a, b = self.ensure(op["args"]["source"]), self.ensure(op["clauses"]["on"])
        a.pos = b.pos
        if op["clauses"].get("show", "half") == "half":     # half of each is seen from each side
            a.hidden |= {m.key for m in a.modules.values() if m.rel[0] < 0}
            b.hidden |= {m.key for m in b.modules.values() if m.rel[0] > 0}

    def op_protrude(self, op):
        for p in self.mods_of(op["args"]["target"]):
            for m in self.w.modules():
                if m.obj != p.obj and _dist(self.w.pos(m), self.w.pos(p)) <= 2 * RHO:
                    self.link(p, m, "protrude", 0.2)

    def op_fuse(self, op):
        a, b, c = op["args"]["a"], op["clauses"]["with"], op["clauses"]["as"]
        A, B = self.mods_of(a), self.mods_of(b)
        mods = [Module(f"{x.obj}_{x.name}".strip("_"), c, x.depth, x.rel, x.props.copy()) for x in A + B]
        self.w.add_object(c, mods, pos=self.w.objs[a.split('.')[0]].pos)
        o = self.w.objs[c]
        ka = [m for m in o.modules.values() if m.name.startswith(a.split(".")[0])]
        kb = [m for m in o.modules.values() if not m.name.startswith(a.split(".")[0])]
        for x in ka:
            for y in kb:
                if x.depth == y.depth == 0:
                    self.link(x, y, "fuse", 0.5, both=True)

    def op_enter(self, op):
        t = op["args"]["target"]
        self.depth_allowed[t.split(".")[0]] = op["clauses"].get("depth", 1)
        self.depth_allowed[t] = op["clauses"].get("depth", 1)

    def op_region(self, op):
        c = op["clauses"]
        center, size, shape = c["center"], c.get("size", 0.5), c["shape"]
        o = self.ensure(center)
        cx, cy = self.w.pos(self.surface(center)[0]) if "." in center else o.pos
        max_d = self.depth_allowed.get(center.split(".")[0], 1)
        sel = []
        for m in o.modules.values():
            if m.depth > max_d:
                continue
            x, y = self.w.pos(m)
            if _inside(shape, (x - cx, y - cy), size):
                sel.append(m)
        inc = c.get("includes")
        if inc:
            sel = [m for m in sel if any(m.key == f"{o.name}.{i}" or m.key.startswith(f"{o.name}.{i}.") or m.key == i
                                         for i in inc)] or sel
        self.regions[op["args"]["name"]] = sel

    def selection(self, item):
        """Resolve one point of a line: a region, a part (partial function), or an object (the whole module)."""
        if item in self.regions:
            return [(m, 1.0) for m in self.regions[item]]
        mods = self.mods_of(item)
        root = item.split(".")[0]
        if item == root:                  # whole module: its surface modules together, spread
            surf = [m for m in mods if m.depth == 0]
            return [(m, 1.0 / len(surf)) for m in surf]
        allowed = self.depth_allowed.get(item, self.depth_allowed.get(root, 0))
        top = min(m.depth for m in mods)
        chosen = [m for m in mods if m.depth == top] + [m for m in mods if top < m.depth <= allowed]
        return [(m, 1.0) for m in chosen]

    def op_line(self, op):
        pts = op["clauses"]["through"]
        sels = [self.selection(p) for p in pts]
        if op["clauses"].get("from") in ("right",):
            sels = sels[::-1]
        for s1, s2 in zip(sels, sels[1:]):
            for m1, w1 in s1:
                for m2, w2 in s2:
                    self.link(m1, m2, "line", w1 * w2)
        self.lines[op["args"]["name"]] = [m.key for s in sels for m, _ in s]

    def op_select(self, op):
        pass  # selections take effect through LINE and REGION

    def op_widen(self, op):
        keys = self.lines.get(op["args"]["line"], [])
        r = op["clauses"].get("radius", 0.2) * (2 if op["clauses"]["to"] == "volume" else 1)
        for k in keys:
            a = self.w.module(k)
            for m in self.w.modules():
                if m.key not in keys and m.depth == 0 and _dist(self.w.pos(m), self.w.pos(a)) <= RHO + r:
                    self.link(a, m, "widen", 0.3)

    # ---- host and transfer ------------------------------------------------------------------------
    def op_transplant(self, op):
        bundle, to = op["args"]["bundle"], op["clauses"]["to"]
        B = self.mods_of(bundle)
        tgt = self.mods_of(to)
        mean = np.mean([m.props for m in B], axis=0)
        for m in tgt:
            m.props = mean.copy()            # the whole bundle travels, not one function
        name = op["clauses"].get("as")
        if name:
            o = self.w.objs[tgt[0].obj]
            self.w.objs[name] = o            # the descendant refers to the host object now carrying the bundle

    def op_rehost(self, op):
        bundle, host = op["args"]["bundle"], op["clauses"]["in"]
        src = self.mods_of(bundle)
        h = self.ensure(host)
        name = op["clauses"].get("as") or f"{bundle}_in_{host}"
        mods = [Module(f"{name}_{i}", h.name, 1, (0.0, 0.0), m.props.copy()) for i, m in enumerate(src)]
        for m in mods:
            h.modules[m.key] = m
            for hm in [x for x in h.modules.values() if x.depth == 0]:
                self.link(m, hm, "rehost", 0.5)

    # ---- state and flow ------------------------------------------------------------------------------
    def op_heal(self, op):
        scope = op["clauses"].get("scope", "node")
        tgt = op["args"]["target"]
        mods = self.mods_of(tgt) if scope in ("container", "network", "higher") else self.surface(tgt)
        if scope == "network":
            linked = {l.dst for l in self.w.links if l.src in {m.key for m in mods}}
            mods += [self.w.module(k) for k in linked]
        keys = {m.key for m in mods}
        for m in mods:
            m.health = 1.0
            m.props = np.where(m.props < 0, m.props * 0.5, m.props)     # harmful functions reduced
        for l in self.w.links:                                            # interference into healed modules damped
            if l.dst in keys:
                a, b = self.w.module(l.src).props, self.w.module(l.dst).props
                if float(a @ b) < 0:
                    l.w *= 0.3
        if scope == "higher":
            self.op_beam({"args": {"source": tgt}, "clauses": {"direction": "down"}, "meanings": []})

    def op_beam(self, op):
        src = self.surface(op["args"]["source"])
        sp = np.mean([m.props for m in src], axis=0)
        d0 = min(m.depth for m in src)
        for m in self.w.modules():                    # lands on all lower layers
            if m.depth > d0 or (m.obj != src[0].obj and m.depth >= d0):
                m.props = (1 - STEER) * m.props + STEER * sp

    def op_flow(self, op):
        src = self.surface(op["args"]["source"])[0]
        d = op["clauses"]["direction"]
        o = self.w.objs[src.obj]
        if d in ("vertical", "down", "up"):
            for m in o.modules.values():
                if m.depth != src.depth and (d == "vertical" or (d == "down") == (m.depth > src.depth)):
                    self.link(src, m, "flow_vertical", 0.6)
        elif d in ("horizontal", "across"):
            for m in self.w.modules():
                if m.key != src.key and m.depth == src.depth:
                    self.link(src, m, "flow_horizontal", 0.4)
        elif d == "outward":
            for m in self.w.modules():
                if m.obj != src.obj and m.depth == 0:
                    self.link(src, m, "flow_outward", 0.3)
        elif d == "inward":
            for m in o.modules.values():
                if m.depth > src.depth:
                    self.link(src, m, "flow_inward", 0.6)

    def op_shift(self, op):
        to = op["clauses"]["to"]
        for m in self.mods_of(op["args"]["target"]):
            base = self.base_props.get(m.key, m.props)
            if to == "black":
                m.props = -np.abs(base)                        # destructive only
            elif to == "grey":
                m.props = np.where(base < 0, base * 0.5, base) + 0.1   # good and bad held; protection added
            m.colour = to

    def op_colour(self, op):
        if op["args"]["colour"] in ("black", "grey"):
            self.op_shift({"args": op["args"], "clauses": {"to": op["args"]["colour"]}})
        for m in self.mods_of(op["args"]["target"]):
            m.colour = op["args"]["colour"]

    def op_route(self, op):
        obj = op["args"]["object"]
        for state, target in op["clauses"]["by"]:      # the link exists only while the host is in that state
            l = Link(self.surface(obj)[0].key, self.surface(target)[0].key, "route", 1.0)
            l.state = state
            self.w.links.append(l)

    def op_use(self, op):
        if op["args"]["scope"] == "state":
            self.w.state = op["args"]["name"]

    def op_resonate(self, op):
        A, B = self.mods_of(op["args"]["a"]), self.mods_of(op["clauses"]["with"])
        bp = np.mean([m.props for m in B], axis=0)
        for m in A:
            m.props = (1 - STEER) * m.props + STEER * bp
        self.link(B[0], A[0], "resonate", 0.5)

    def op_compress(self, op):
        items = [x for x in op["args"]["items"]]
        name = op["clauses"]["as"]
        props = [self.surface(i)[0].props for i in items]
        self.w.add_object(name, [Module("", name, 0, (0.0, 0.0), np.mean(props, axis=0))])
        for i in items:
            self.link(self.surface(name)[0], self.surface(i)[0], "compress", 0.5)


def _dist_to_line(p, a, b):
    a, b, p = np.asarray(a, float), np.asarray(b, float), np.asarray(p, float)
    ab = b - a
    if not ab.any():
        return float(np.linalg.norm(p - a))
    t = np.clip(np.dot(p - a, ab) / np.dot(ab, ab), -0.5, 1.5)
    return float(np.linalg.norm(p - (a + t * ab)))


def _inside(shape, d, size):
    x, y = d
    if shape == "point":
        return math.hypot(x, y) <= 0.05
    if shape == "circle":
        return math.hypot(x, y) <= size
    if shape == "square":
        return abs(x) <= size and abs(y) <= size
    if shape == "triangle":           # apex up, centred: |x| <= size * (1 - (y + size/2) / (1.5 size))
        if y < -size / 2 or y > size:
            return False
        return abs(x) <= size * (size - y) / (1.5 * size) * 1.15
    return False


def run(ir, layouts=None, seed=0, search_choice=None):
    ex = Executor(ir, layouts, seed, search_choice)
    ex.run()
    return ex
