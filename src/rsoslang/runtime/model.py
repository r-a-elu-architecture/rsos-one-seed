"""The simulation runtime: objects made of functional modules, placed in a plane, linked by operators.

Every rule here is written down in spec/SEMANTICS.md and was fixed before any experiment was run.

- An object has modules (its parts) at depth 0 (surface), 1 (body), 2 (sub-code), ...; each module has a position
  relative to the object's centre and a vector of functional properties.
- Operators add, remove or re-weight directed links between modules, or change module state (health, colour).
- Execution passes activation along the links for a few steps. A link carries the source's activation times the
  functional compatibility (cosine) of the two modules: compatible functions reinforce, incompatible ones interfere.
- Utility in an environment = how well the system's active functions match the environment's demands, minus a small
  cost per link.
"""

from dataclasses import dataclass, field
import math

import numpy as np

K = 7                      # functional properties per module (EXP-004: 7 links x 7 properties = 49)
RHO = 0.35                 # contact radius in the plane
PROX_W = 0.2               # weight of a proximity link (placement alone)
LINK_COST = 0.002          # utility cost per link


@dataclass
class Module:
    name: str
    obj: str
    depth: int
    rel: tuple
    props: np.ndarray
    health: float = 1.0
    colour: str = ""

    @property
    def key(self):
        return f"{self.obj}.{self.name}" if self.name else self.obj


@dataclass
class Obj:
    name: str
    pos: tuple = (0.0, 0.0)
    rot: float = 0.0
    host: str = ""
    modules: dict = field(default_factory=dict)
    hidden: set = field(default_factory=set)     # module keys not exposed (overlay half, flip)

    def world(self, m: Module):
        c, s = math.cos(math.radians(self.rot)), math.sin(math.radians(self.rot))
        x, y = m.rel
        return (self.pos[0] + c * x - s * y, self.pos[1] + s * x + c * y)


@dataclass
class Link:
    src: str
    dst: str
    kind: str
    w: float
    state: str = None          # a ROUTE link is active only in its state

    def tup(self):
        return (self.src, self.dst, self.kind)


@dataclass
class Env:
    """An environment: what it demands from functions (target) and what drives modules (drive)."""
    name: str
    target: np.ndarray
    drive: np.ndarray


def random_env(rng, name="env"):
    return Env(name, rng.normal(size=K), rng.normal(size=K))


def shifted_env(env, rng, shift=0.6, name="unseen"):
    """An unseen environment: the objectives are altered (EXP-003 used a held-out world with altered objectives)."""
    return Env(name, env.target + shift * rng.normal(size=K), env.drive + shift * rng.normal(size=K))


class World:
    def __init__(self):
        self.objs = {}
        self.links = []        # explicit links from operators
        self.proximity = True  # placement creates weak links between nearby modules of different objects
        self.cross = True      # False = the ablation: objects cannot exchange functional effects
        self.state = None

    # ---- construction -------------------------------------------------------------------------
    def add_object(self, name, modules, pos=(0.0, 0.0), rot=0.0, host=""):
        o = Obj(name, pos, rot, host)
        for m in modules:
            m.obj = name
            o.modules[m.key] = m
        self.objs[name] = o
        return o

    def module(self, key):
        obj = key.split(".")[0]
        return self.objs[obj].modules[key]

    def modules(self):
        for o in self.objs.values():
            yield from o.modules.values()

    def pos(self, m):
        return self.objs[m.obj].world(m)

    def exposed(self, m):
        return m.key not in self.objs[m.obj].hidden

    # ---- links ----------------------------------------------------------------------------------
    def proximity_links(self):
        out = []
        if not self.proximity:
            return out
        mods = [m for m in self.modules() if m.depth == 0 and self.exposed(m)]
        for a in mods:
            for b in mods:
                if a.obj != b.obj and _dist(self.pos(a), self.pos(b)) <= RHO:
                    out.append(Link(a.key, b.key, "proximity", PROX_W))
        return out

    def all_links(self):
        links = [l for l in self.links if l.state is None or l.state == self.state] + self.proximity_links()
        if not self.cross:
            links = [l for l in links if l.src.split(".")[0] == l.dst.split(".")[0]]
        return links

    def link_set(self):
        return {l.tup() for l in self.all_links()}

    # ---- execution ----------------------------------------------------------------------------
    def execute(self, env: Env, steps=3, sinks_only=False, link_cost=None):
        mods = list(self.modules())
        idx = {m.key: i for i, m in enumerate(mods)}
        P = np.array([m.props for m in mods])
        norms = np.linalg.norm(P, axis=1) + 1e-9
        base = np.tanh(P @ env.drive / math.sqrt(K)) * np.array([m.health for m in mods])
        x = base.copy()
        links = [l for l in self.all_links() if l.src in idx and l.dst in idx]
        for _ in range(steps):
            nxt = base.copy()
            indeg = {}
            for l in links:
                indeg[l.dst] = indeg.get(l.dst, 0) + 1
            for l in links:
                i, j = idx[l.src], idx[l.dst]
                compat = float(P[i] @ P[j] / (norms[i] * norms[j]))
                nxt[j] += l.w * compat * x[i] / math.sqrt(indeg[l.dst])
            x = np.tanh(nxt)
        active = np.maximum(x, 0)
        if sinks_only:
            has_out = {l.src for l in links}
            mask = np.array([0.0 if m.key in has_out else 1.0 for m in mods])
            linked = {l.src for l in links} | {l.dst for l in links}
            mask *= np.array([1.0 if m.key in linked else 0.0 for m in mods])
            active = active * mask
        output = active @ P
        u = math.tanh(float(output @ env.target) / (math.sqrt(K) * max(1.0, len(mods) ** 0.5)))
        return u - (LINK_COST if link_cost is None else link_cost) * len(links)


def _dist(p, q):
    return math.hypot(p[0] - q[0], p[1] - q[1])


def grid_modules(rng, names=None, rows=2, cols=4, depth_layers=(0, 1, 2), spacing=0.5):
    """A painting-like object: a grid of surface modules, each with a body and sub-code module beneath it."""
    mods = []
    k = 0
    for r in range(rows):
        for c in range(cols):
            x = (c - (cols - 1) / 2) * spacing
            y = ((rows - 1) / 2 - r) * spacing
            base = names[k] if names and k < len(names) else f"m{k}"
            for d in depth_layers:
                nm = base if d == 0 else f"{base}.{['surface', 'body', 'subcode'][d] if d < 3 else 'd' + str(d)}"
                mods.append(Module(nm, "", d, (x, y), rng.normal(size=K)))
            k += 1
    return mods
