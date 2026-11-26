"""Guest modules: what each one does at each place in a host node (head, heart, brain, near).

The place decides the result (owner, round 3). A guest that has no meaning at a place does nothing there, and that
is reported, not hidden.
"""

import re

from .tickets import CATEGORIES

VOCAB = sorted({w for spec in CATEGORIES.values() for p in spec["words"] for w in p.split()})


def _swap_variants(word):
    return {word[:i] + word[i + 1] + word[i] + word[i + 2:] for i in range(1, len(word) - 2)} if len(word) >= 4 else set()


def _correct_tokens(text):
    fixed = []
    for tok in text.split():
        bare = tok.strip(".,!?")
        hit = next((v for v in VOCAB if bare != v and bare in _swap_variants(v)), None)
        fixed.append(tok.replace(bare, hit) if hit else tok)
    return " ".join(fixed)


# A thesaurus that knows most, not all, of the unseen phrasings (2 of 3 per category).
THESAURUS = {cat: spec["unseen"][:2] for cat, spec in CATEGORIES.items()}


class Guest:
    name = "guest"
    cost = {"head": 0.0, "heart": 0.0, "brain": 0.0, "near": 0.0}

    def at_head(self, node, state, ctx):
        pass

    def at_heart(self, node, fn):
        return fn

    def at_brain(self, node):
        return False

    def at_near(self, node, state, ctx):
        pass


class SpellCorrector(Guest):
    """Fixes swapped letters."""
    name = "spell_corrector"
    cost = {"head": 1.5, "heart": 2.5, "brain": 0.0, "near": 1.5}

    def at_head(self, node, state, ctx):          # corrects the text before the node reads it
        if "text" in state:
            state["text"] = _correct_tokens(state["text"])
        ctx["cost"] += self.cost["head"]

    def at_heart(self, node, fn):                 # the node's own matching becomes tolerant of swaps
        def wrapped(n, s, c, fn=fn):
            if n.role != "reason" or "lexicon" not in n.knowledge:
                return fn(n, s, c)
            original = n.knowledge["lexicon"]
            n.knowledge["lexicon"] = {k: list(v) + [x for w in v for x in _swap_variants(w)] for k, v in original.items()}
            c["cost"] += self.cost["heart"]
            try:
                return fn(n, s, c)
            finally:
                n.knowledge["lexicon"] = original
        return wrapped

    def at_brain(self, node):                     # the swapped forms are learned once into the node's knowledge
        if "lexicon" not in node.knowledge:
            return False
        node.knowledge["lexicon"] = {k: list(v) + [x for w in v for x in _swap_variants(w)]
                                     for k, v in node.knowledge["lexicon"].items()}
        return True

    def at_near(self, node, state, ctx):          # corrects the text for the neighbours after the node has run
        if "text" in state:
            state["text"] = _correct_tokens(state["text"])
        ctx["cost"] += self.cost["near"]


class SynonymExpander(Guest):
    """Knows other ways of saying the same thing (most, not all)."""
    name = "synonym_expander"
    cost = {"head": 1.0, "heart": 2.0, "brain": 0.0, "near": 1.0}

    def _rewrite(self, text):
        for cat, phrases in THESAURUS.items():
            for p in phrases:
                text = text.replace(p, CATEGORIES[cat]["words"][0])
        return text

    def at_head(self, node, state, ctx):
        if "text" in state:
            state["text"] = self._rewrite(state["text"])
        ctx["cost"] += self.cost["head"]

    def at_heart(self, node, fn):
        def wrapped(n, s, c, fn=fn):
            if "lexicon" not in n.knowledge:
                return fn(n, s, c)
            original = n.knowledge["lexicon"]
            n.knowledge["lexicon"] = {k: list(v) + THESAURUS.get(k, []) for k, v in original.items()}
            c["cost"] += self.cost["heart"]
            try:
                return fn(n, s, c)
            finally:
                n.knowledge["lexicon"] = original
        return wrapped

    def at_brain(self, node):
        if "lexicon" not in node.knowledge:
            return False
        node.knowledge["lexicon"] = {k: list(v) + THESAURUS.get(k, []) for k, v in node.knowledge["lexicon"].items()}
        return True

    def at_near(self, node, state, ctx):
        if "text" in state:
            state["text"] = self._rewrite(state["text"])
        ctx["cost"] += self.cost["near"]


class Cache(Guest):
    """Remembers answers it has already fetched."""
    name = "cache"
    cost = {"head": 0.2, "heart": 0.2, "brain": 0.0, "near": 0.2}

    def at_heart(self, node, fn):                 # inside the memory node: a hit skips the expensive lookup
        def wrapped(n, s, c, fn=fn):
            if n.role != "memory":
                return fn(n, s, c)
            key = s.get("customer")
            c["cost"] += self.cost["heart"]
            if key in c["cache"]:
                s["tier"] = c["cache"][key]
                return s
            s = fn(n, s, c)
            c["cache"][key] = s["tier"]
            return s
        return wrapped

    def at_head(self, node, state, ctx):          # before the node: it can only note the request; the lookup still runs
        ctx["cost"] += self.cost["head"]

    def at_brain(self, node):                     # in the knowledge: lookups become cheaper for everyone
        if "lookup_cost" not in node.knowledge:
            return False
        node.knowledge["lookup_cost"] = 1.5
        return True


class FastRetry(Guest):
    """Retries a failed tool call at once."""
    name = "fast_retry"
    cost = {"head": 0.0, "heart": 0.5, "brain": 0.0, "near": 0.0}

    def at_heart(self, node, fn):
        def wrapped(n, s, c, fn=fn):
            s = fn(n, s, c)
            if n.role == "tool" and not s.get("tool_ok"):
                c["cost"] += self.cost["heart"] + n.cost
                c["visits"]["act"] = c["visits"].get("act", 0) + 1
                s = fn(n, s, c)
            return s
        return wrapped


class AmountValidator(Guest):
    """Checks that an amount was read; reads it in another way if not."""
    name = "amount_validator"
    cost = {"head": 0.3, "heart": 0.3, "brain": 0.0, "near": 0.3}

    def at_near(self, node, state, ctx):
        if state.get("amount", 0) == 0 and "amount" in state.get("text", ""):
            m = re.search(r"(\d+(?:\.\d+)?)\s*eur", state["text"])
            if m:
                state["amount"] = float(m.group(1))
        ctx["cost"] += self.cost["near"]


LIBRARY = {g.name: g for g in (SpellCorrector(), SynonymExpander(), Cache(), FastRetry(), AmountValidator())}
