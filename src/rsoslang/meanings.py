"""Meanings in three tiers (D80, T12).

1. core      fixed default meanings, shared by every program, human and AI
2. binding   declared in the program for a scope: state > host > world > profile
3. search    a meaning left open on purpose; the runtime tries the candidates

Resolution order: binding (most specific scope first) > search > core.
Two bindings with different values in the same scope and name are an ambiguity (E010).
A key with no core meaning, no binding and no search is an error (E017): nothing is guessed.
"""

from dataclasses import dataclass, field

# Each core entry: value, provenance.
CORE = {
    # Contact: the chat 2 T35 table is the fixed default (D80).
    "contact.surface":  ("interface_only",   "c2 T35.3 touch the surface; D80"),
    "contact.edge":     ("dependency",       "c2 T35.3 attach to an edge; D80"),
    "contact.top":      ("supervisory_entry","c2 T35.3 enter through the top; D80"),
    "contact.side":     ("lateral",          "c2 T35.3 enter through the side; D80"),
    "contact.left":     ("lateral",          "alias of contact.side (c2 T35.3); D80"),
    "contact.right":    ("lateral",          "alias of contact.side (c2 T35.3); D80"),
    "contact.front":    ("lateral",          "alias of contact.side (c2 T35.3); D80"),
    "contact.back":     ("lateral",          "alias of contact.side (c2 T35.3); D80"),
    "contact.interior": ("nested_state",     "c2 T35.3 penetrate into the interior; owner c2 T35 surface→body→sub-code"),
    "contact.inside":   ("nested_state",     "alias of contact.interior"),
    "contact.through":  ("multi_layer",      "c2 T35.3 pass completely through; owner c2 T33 through the wall"),
    # contact.bottom, contact.centre, contact.outside: no fixed meaning in the chats (Q71) → bind or search.

    # Flows: the owner's own grammar (the owner's spatial-grammar design notes, private record).
    "flow.vertical":    ("hierarchy",            "owner c1 T44, T88"),
    "flow.down":        ("lands_on_all_lower",   "owner c1 T47 beams land on the lower layers"),
    "flow.up":          ("towards_higher_order", "owner c1 T44, T55"),
    "flow.horizontal":  ("spread_across",        "owner c1 T95 pulse moves horizontally to others"),
    "flow.across":      ("spread_across",        "alias of flow.horizontal"),
    "flow.outward":     ("to_environment",       "owner c1 T66, T95 outside the body, others perceive"),
    "flow.inward":      ("into_host_subsystems", "owner c1 T66 extension inside affects the brain"),

    # Selection: the owner's line-and-dot grammar (c1 T108).
    "select.whole":     ("full_module",       "owner c1 T108 the whole door"),
    "select.part":      ("partial_function",  "owner c1 T108 the middle of the door"),

    # Colour = state that changes function (c1 T95; c2 T35; c2 T53).
    "colour.black":     ("destructive_only",              "owner c1 T95"),
    "colour.grey":      ("good_and_bad_with_protection",  "owner c1 T95 black → grey, evolution"),
    "colour.white":     ("soothing_healing",              "owner c1 T14 White Dragon light"),
    "colour.gold":      ("strength_agency",               "owner c1 T14 Golden Lion light"),
    "colour.red":       ("drive",                         "owner c2 T35"),
    "colour.black_and_white": ("state_change_of_selection", "owner c2 T53"),
}

KNOWN_PREFIXES = ("contact.", "flow.", "select.", "colour.", "scene.", "model.")
SCOPE_ORDER = ("state", "host", "world", "profile")


@dataclass
class Resolution:
    key: str
    value: object
    source: str              # "core" | "binding" | "search"
    detail: str = ""
    candidates: list = field(default_factory=list)

    def to_dict(self):
        d = {"key": self.key, "value": self.value, "source": self.source}
        if self.detail:
            d["detail"] = self.detail
        if self.candidates:
            d["candidates"] = self.candidates
        return d


class MeaningTable:
    def __init__(self):
        self.bindings = {}   # (key, scope, name) -> (value, line)
        self.searches = {}   # key -> (candidates, metric, line)

    @staticmethod
    def known_key(key):
        return key in CORE or key.startswith(KNOWN_PREFIXES)

    def bind(self, key, value, scope, name, line):
        """Returns None, or the line of a conflicting binding."""
        k = (key, scope, name)
        if k in self.bindings and self.bindings[k][0] != value:
            return self.bindings[k][1]
        self.bindings[k] = (value, line)
        return None

    def search(self, key, candidates, metric, line):
        self.searches[key] = (list(candidates), metric, line)

    def resolve(self, key, context):
        """context: dict scope -> active name (state, host, world, profile). Returns Resolution or None."""
        for scope in SCOPE_ORDER:
            name = context.get(scope)
            if name is not None and (key, scope, name) in self.bindings:
                value, line = self.bindings[(key, scope, name)]
                return Resolution(key, value, "binding", f"{scope} {name} (line {line})")
        if key in self.searches:
            cands, metric, line = self.searches[key]
            return Resolution(key, None, "search", f"metric {metric} (line {line})", cands)
        if key in CORE:
            value, prov = CORE[key]
            return Resolution(key, value, "core", prov)
        return None
