"""Semantic pass: names, hosts, meanings → the intermediate representation (IR).

Single pass in program order: a name must be declared before it is used.
"""

from .grammar import STATEMENTS
from .meanings import MeaningTable, KNOWN_PREFIXES
from .diagnostics import Diagnostic

MENTAL_KINDS = {"human", "person", "agent", "ai", "team", "organisation", "organization", "company"}

# List clauses whose items are references, declarations, or parts relative to another argument.
LIST_ROLES = {
    ("LINE", "THROUGH"): "ref",
    ("COMPARE", "AGAINST"): "ref",
    ("REGION", "INCLUDES"): "rel:CENTER",
    ("ABLATE", "REMOVE"): "rel:target",
    ("SCENE", "ORDER"): "declare",
    ("SPLIT", "INTO"): "declare",
}

# Default meaning keys per statement (D80 contact table; owner flows and selection).
CONTACT_DEFAULT_SIDE = {"TOUCH": "surface", "ATTACH": "edge"}
CONTACT_METHOD_KEY = {"PIERCE": "contact.through", "PASS": "contact.through"}


class Analyzer:
    def __init__(self):
        self.diags = []
        self.world = None
        self.header = None
        self.entities = {}          # name -> {"class": ..., "line": ...}
        self.parts = set()
        self.hosts = {}
        self.context = {"state": None, "host": None, "world": None, "profile": None}
        self.meanings = MeaningTable()
        self.ops = []
        self.lineage = []

    # ---- helpers ------------------------------------------------------------------------------
    def err(self, code, line, msg):
        self.diags.append(Diagnostic(code, line, msg))

    def declare(self, name, cls, line, **info):
        if name in self.entities:
            self.err("E009_DUPLICATE", line, f"{name!r} already declared on line {self.entities[name]['line']}")
            return
        self.entities[name] = {"class": cls, "line": line, **info}

    def ref(self, path, line):
        if not isinstance(path, str) or not path:
            self.err("E004_PATH", line, f"bad path {path!r}")
            return False
        root = path.split(".")[0]
        if root not in self.entities:
            self.err("E003_UNKNOWN_ENTITY", line, f"{root!r} is not declared")
            return False
        if "." in path and path not in self.parts:
            # declare every prefix, so car.seat.foam implies car.seat
            bits = path.split(".")
            for i in range(2, len(bits) + 1):
                p = ".".join(bits[:i])
                if p not in self.parts:
                    self.parts.add(p)
            self.diags.append(Diagnostic("W002_IMPLICIT_PART", line, f"{path!r} used without PART"))
        return True

    def resolve(self, key, line, meanings):
        if not key.startswith(KNOWN_PREFIXES):
            self.err("E017_MEANING", line, f"unknown meaning key {key!r}")
            return
        r = self.meanings.resolve(key, self.context)
        if r is None:
            self.err("E017_MEANING", line,
                     f"{key!r} has no core meaning; declare it with MEANING or leave it open with SEARCH")
            return
        if r.source == "search":
            self.diags.append(Diagnostic("W001_OPEN_MEANING", line, f"{key!r} resolved by search over {r.candidates}"))
        meanings.append(r.to_dict())

    # ---- main ---------------------------------------------------------------------------------
    def run(self, statements):
        if not statements or statements[0].kw != "LANGUAGE":
            self.err("E001_HEADER", statements[0].line if statements else 1, "first statement must be LANGUAGE RSOS 0.2")
        for s in statements:
            self.statement(s)
        if self.world is None:
            self.err("E002_WORLD", 1, "no WORLD declared")
        return self.ir()

    def statement(self, s):
        spec = STATEMENTS[s.kw]
        line = s.line
        meanings = []

        if s.kw == "LANGUAGE":
            name, ver = s.args["name"], str(s.args["version"])
            if name.upper() != "RSOS" or ver not in ("0.2",):
                self.err("E001_HEADER", line, f"expected LANGUAGE RSOS 0.2, found {name} {ver}")
            self.header = {"language": "RSOS", "version": ver}
            return
        if s.kw == "WORLD":
            if self.world is not None:
                self.err("E002_WORLD", line, "a program has one WORLD")
                return
            self.world = s.args["name"]
            self.context["world"] = self.world
            self.declare(self.world, "world", line)
            return
        if self.world is None and s.kw not in ("PROFILE", "MEANING", "SEARCH"):
            self.err("E002_WORLD", line, f"{s.kw} before WORLD")

        # references in positional arguments and clauses
        for name, kind in spec.pos:
            if kind == "path":
                target = s.args[name]
                if s.kw == "PROPERTY" and "." in target:
                    target = target.rsplit(".", 1)[0]     # entity.property: only the entity must exist
                self.ref(target, line)
        for cl, kind in spec.clauses.items():
            if cl in s.clauses and kind == "path":
                self.ref(s.clauses[cl], line)
        for (kw, cl), role in LIST_ROLES.items():
            if kw == s.kw and cl in s.clauses:
                items = s.clauses[cl]
                if role == "ref":
                    for it in items:
                        self.ref(it, line)
                elif role.startswith("rel:"):
                    base = s.clauses.get(role[4:]) or s.args.get(role[4:])
                    for it in items:
                        self.ref(it if it.split(".")[0] in self.entities else f"{base}.{it}", line)
                elif role == "declare":
                    for it in items:
                        if it not in self.entities:
                            self.declare(it, "object", line, implicit=True, parent=s.args.get("name") or s.args.get("target"))

        # declarations
        kw = s.kw
        if kw == "PERSONA":
            nm = s.args["name"]
            if nm in self.entities:
                self.err("E009_DUPLICATE", line, f"{nm!r} already declared")
            else:
                self.entities[nm] = {"class": "host", "line": line, "kind": "human", "persona": True,
                                     "age": s.clauses.get("AGE"), "organs": s.clauses.get("ORGANS", []),
                                     "goal": s.clauses.get("GOAL"), "source": s.clauses.get("SOURCE", "synthetic"),
                                     "channels": ["visual", "auditory", "kinesthetic", "olfactory"], "states": None}
                self.hosts[nm] = self.entities[nm]
        if kw == "HOST":
            nm = s.args["name"]
            self.declare(nm, "host", line, kind=s.clauses.get("KIND"),
                         channels=s.clauses.get("CHANNELS"), states=s.clauses.get("STATES"))
            self.hosts[nm] = self.entities.get(nm, {})
        elif kw == "PROFILE":
            self.declare(s.args["name"], "profile", line)
        elif kw == "PART":
            p = s.args["path"]
            if "." not in p:
                self.err("E004_PATH", line, f"a PART path has a parent: parent.part, found {p!r}")
            elif self.ref(p.split(".")[0], line):
                bits = p.split(".")
                for i in range(2, len(bits) + 1):
                    self.parts.add(".".join(bits[:i]))
        elif spec.declares and kw not in ("WORLD", "PERSONA"):
            nm = s.args.get("name") or s.clauses.get("AS")
            if nm:
                self.declare(nm, spec.declares, line, **{k.lower(): v for k, v in s.clauses.items() if k != "AS"})

        reach = None
        if kw == "REACH":
            reach = self.reach(s, line)

        # descendants (AS) create new objects with lineage
        if "AS" in s.clauses and not spec.declares:
            child = s.clauses["AS"]
            parents = [v for k, v in list(s.args.items()) + list(s.clauses.items())
                       if isinstance(v, str) and v.split(".")[0] in self.entities and k not in ("AS",)]
            self.declare(child, "descendant", line, op=kw, parents=parents)
            self.lineage.append({"child": child, "op": kw, "parents": parents, "line": line})

        if kw == "PLACE" and not ("NEAR" in s.clauses or ("X" in s.clauses and "Y" in s.clauses)):
            self.err("E005_SYNTAX", line, "PLACE needs X and Y, or NEAR")

        # context
        if kw == "USE":
            scope, nm = s.args["scope"], s.args["name"]
            if scope == "host":
                if nm not in self.hosts:
                    self.err("E003_UNKNOWN_ENTITY", line, f"host {nm!r} is not declared")
                self.context["host"] = nm
            elif scope == "profile":
                if nm not in self.entities or self.entities[nm]["class"] != "profile":
                    self.err("E003_UNKNOWN_ENTITY", line, f"profile {nm!r} is not declared")
                self.context["profile"] = nm
            elif scope == "state":
                h = self.hosts.get(self.context["host"] or "", {})
                if h.get("states") and nm not in h["states"]:
                    self.err("E016_HOST", line, f"host {self.context['host']!r} has no state {nm!r} (has {h['states']})")
                self.context["state"] = nm
            elif scope == "world":
                if nm != self.world:
                    self.err("E003_UNKNOWN_ENTITY", line, f"world {nm!r} is not this program's world")

        # meanings: bindings and searches
        if kw == "MEANING":
            key = s.args["key"]
            if not key.startswith(KNOWN_PREFIXES):
                self.err("E017_MEANING", line, f"unknown meaning key {key!r} (known prefixes: {', '.join(KNOWN_PREFIXES)})")
            clash = self.meanings.bind(key, s.args["value"], s.clauses["SCOPE"], s.clauses["IN"], line)
            if clash:
                self.err("E010_AMBIGUITY", line,
                         f"{key!r} in {s.clauses['SCOPE']} {s.clauses['IN']} already bound differently on line {clash}")
        elif kw == "SEARCH":
            key = s.args["key"]
            if not key.startswith(KNOWN_PREFIXES):
                self.err("E017_MEANING", line, f"unknown meaning key {key!r}")
            self.meanings.search(key, s.clauses["OVER"], s.clauses.get("METRIC", "unspecified"), line)

        # meaning resolution for operators
        if spec.meaning == "contact":
            if kw in CONTACT_METHOD_KEY:
                self.resolve(CONTACT_METHOD_KEY[kw], line, meanings)
            side = s.clauses.get("FROM") or s.clauses.get("AT") or CONTACT_DEFAULT_SIDE.get(kw)
            if side:
                side = "centre" if side == "center" else side
                self.resolve(f"contact.{side}", line, meanings)
        elif spec.meaning == "flow":
            direction = s.clauses.get("DIRECTION") or ("down" if kw == "BEAM" else None)
            if direction:
                self.resolve(f"flow.{direction}", line, meanings)
        elif spec.meaning == "select":
            self.resolve(f"select.{s.args['extent']}", line, meanings)
        elif spec.meaning == "colour":
            if kw == "COLOUR" and "STATE" in s.clauses:
                meanings.append({"key": f"colour.{s.args['colour']}", "value": s.clauses["STATE"],
                                 "source": "declared", "detail": f"line {line}"})
            else:
                colour = s.args.get("colour") if kw == "COLOUR" else s.clauses["TO"]
                self.resolve(f"colour.{colour}", line, meanings)

        # host rules
        if spec.host_rule:
            self.host_rule(spec.host_rule, s)

        unit = None
        if spec.family in ("contact", "host", "state", "select"):
            unit = self.unit(s, spec, meanings)
        if spec.family not in ("header",):
            self.ops.append({
                "unit": unit,
                "op": kw.lower(), "family": spec.family, "line": line, "refs": spec.refs,
                "args": s.args, "clauses": {k.lower(): v for k, v in s.clauses.items()},
                "context": {k: v for k, v in self.context.items() if v is not None},
                "meanings": meanings,
            })
            if reach is not None:
                self.ops[-1]["verdict"] = reach

    def reach(self, s, line):
        """REACH: a stretch target used as an instrument (owner, 18 Nov 2026). The target forces the search past small
        gains; the result is the measured distance and the named limit, never a bare pass or fail."""
        name, on, target = s.args["name"], s.clauses["ON"], s.clauses["TARGET"]
        if target <= 1:
            self.err("E022_REACH", line, f"TARGET is an improvement factor above 1, found {target:g}")
        for b in s.clauses.get("BLOCKERS", []):          # each blocker opens a planet: a part of the target
            bits = f"{on}.{b}".split(".")
            for i in range(2, len(bits) + 1):
                self.parts.add(".".join(bits[:i]))
        prev = None
        if "FROM" in s.clauses:
            ent = self.entities.get(s.clauses["FROM"])
            if ent is None or ent.get("class") != "reach" or s.clauses["FROM"] == name:
                self.err("E022_REACH", line, f"FROM names an earlier REACH, found {s.clauses['FROM']!r}")
            else:
                prev = {"name": s.clauses["FROM"], "result": ent.get("result"), "limit": ent.get("limit")}
        verdict = {"name": name, "on": on, "target": target, "against": s.clauses["AGAINST"],
                   "measure": s.clauses["MEASURE"], "blockers": [f"{on}.{b}" for b in s.clauses.get("BLOCKERS", [])],
                   "from": prev}
        if "RESULT" in s.clauses:
            res = s.clauses["RESULT"]
            verdict.update(result=res, reached_share=round(res / target, 3), limit=s.clauses.get("LIMIT"),
                           text=(f"reached {res:g}x of {target:g}x against {s.clauses['AGAINST']} on "
                                 f"{s.clauses['MEASURE']}" + (f"; limit: {s.clauses['LIMIT']}" if "LIMIT" in s.clauses else "")))
            if res < target and "LIMIT" not in s.clauses:
                self.diags.append(Diagnostic("W007_REACH_LIMIT", line,
                                             f"{name}: reached {res:g}x of {target:g}x; name what stopped it (LIMIT)"))
        else:
            verdict["text"] = f"open: {target:g}x against {s.clauses['AGAINST']} on {s.clauses['MEASURE']}, not yet measured"
        return verdict

    def unit(self, s, spec, meanings):
        """The language-core unit (build inputs §1, A6, private design record): one visual phrase as explicit fields."""
        src = s.args.get("source") or s.args.get("bundle") or s.args.get("function") or s.args.get("a")
        tgt = (s.clauses.get("THROUGH") or s.clauses.get("ON") or s.clauses.get("TO") or s.clauses.get("INTO")
               or s.clauses.get("AROUND") or s.clauses.get("WITH") or s.clauses.get("ONTO") or s.clauses.get("IN")
               or s.args.get("target") or s.args.get("object"))
        colour = next((m["value"] for m in meanings if m["key"].startswith("colour.")), None)
        return {
            "source": src,
            "target": tgt,
            "path": tgt.split(".")[1:] if isinstance(tgt, str) and "." in tgt else [],
            "method": s.kw.lower(),
            "geometry": {k.lower(): s.clauses[k] for k in ("FROM", "AT", "DEPTH", "DIRECTION", "SHAPE", "SIZE", "BY")
                         if k in s.clauses},
            "relation": [l for l in self.lineage if l["line"] == s.line],
            "host": self.context.get("host"),
            "colour_state": colour,
            "contract": None,
            "environment": self.world,
            "time": None,
            "evidence": None,
            "meanings": [m["key"] for m in meanings],
        }

    def host_rule(self, rule, s):
        host_name = self.context["host"]
        host = self.hosts.get(host_name) if host_name else None
        if host is None:
            self.diags.append(Diagnostic("W003_NO_HOST", s.line, f"{s.kw} without a host (USE HOST …)"))
            return
        if rule == "channel":
            ch = s.clauses.get("CHANNEL")
            if ch and host.get("channels") and ch not in host["channels"]:
                self.err("E016_HOST", s.line, f"host {host_name!r} has no channel {ch!r} (has {host['channels']})")
        elif rule == "mental_host":
            kind = (host.get("kind") or "").lower()
            if kind and kind not in MENTAL_KINDS:
                self.err("E016_HOST", s.line, f"a mental model needs a host that reasons; {host_name!r} is {kind!r}")

    def ir(self):
        return {
            "rsos_ir": "0.2",
            "header": self.header,
            "world": self.world,
            "hosts": {k: {kk: vv for kk, vv in v.items() if kk not in ("class",)} for k, v in self.hosts.items()},
            "entities": {k: v for k, v in self.entities.items()},
            "parts": sorted(self.parts),
            "bindings": [{"key": k[0], "scope": k[1], "in": k[2], "value": v[0], "line": v[1]}
                         for k, v in self.meanings.bindings.items()],
            "searches": [{"key": k, "over": v[0], "metric": v[1], "line": v[2]} for k, v in self.meanings.searches.items()],
            "lineage": self.lineage,
            "ops": self.ops,
        }


def analyze(statements):
    a = Analyzer()
    ir = a.run(statements)
    return ir, a.diags
