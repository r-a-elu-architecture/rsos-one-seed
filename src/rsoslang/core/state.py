"""RSOS State Runtime: the model decides, the language executes.

A drop-in runtime for multi-agent workflows that edit shared state. Measured in A4 and A5 (RSOS-Language,
experiments/A4_REPORT.md, experiments/A5_REPORT.md): a 14-step task in 2 model calls instead of 42, 2.8-3.7x cheaper
than the best baseline built for the same agents at API prices, 8x faster, 32/32 exact; every injected drift healed with
zero model calls.

How it works:
  1. plan_prompt(requests, state)  -> one prompt in which a model (any model) translates ALL requests into RSOS operations.
  2. parse_plan(text)               -> {step: [operations]}
  3. Ledger.apply(ops)              -> the runtime reads every value from its own state and computes every result;
                                       invalid operations are rejected with a reason (re-ask only those steps).
  4. Ledger.sync(replica)           -> each agent's copy is checked against the green dot (a hash of the agreed state)
                                       and every drifted line is restored from the snapshot, with zero model calls.

Operations (one per line; keys are dotted names such as auth.timeout_ms; values are single words or "quoted text"):
  SET k v                    k = v (v may be another key: copy its value; a missing key is an error)
  SET k "text"               k = the quoted text, never read as a key
  DEL k                      remove k
  INHERIT d s [+n] [CAP m]   d = s (+ n), at most m
  FUSE d a b [CAP m]         d = a + b, at most m
  SCALE k f [CAP m]          k = k x f, at most m
  ROUTE s = x : d v1 | v2    d = v1 if s equals x, else v2
  REHOST field a b           every key ending in .field whose value is a becomes b
"""

from __future__ import annotations

import hashlib
import json
import re
import shlex

OPS = ("SET", "DEL", "INHERIT", "FUSE", "SCALE", "ROUTE", "REHOST", "FLOW")
KEY_RX = re.compile(r"^[A-Za-z_][\w-]*(\.[A-Za-z_][\w-]*)+$")
ROUTE_RX = re.compile(r"^ROUTE\s+(\S+)\s*=\s*(\S+)\s*:\s*(\S+)\s+(\S+)\s*\|\s*(\S+)$")
STEP_RX = re.compile(r"^#\s*(\d+)\s*$")
SET_QUOTED_RX = re.compile(r"""^SET\s+(\S+)\s*=?\s*(["'])(.*)\2$""", re.IGNORECASE)

GRAMMAR = ("RSOS operations, one per line (keys are dotted names): SET k v | DEL k | INHERIT d s [+n] [CAP m] "
           "(d = s+n, max m) | FUSE d a b [CAP m] (d = a+b) | SCALE k f [CAP m] (k = k*f) | "
           "ROUTE s = x : d v1 | v2 (d = v1 if s is x, else v2) | REHOST field a b (every key ending in .field equal "
           "to a becomes b) | FLOW field OVER c x [+n] [CAP m] (for every object whose c equals x, its field = field+n, max m). SET k other.key copies a value; to set text that contains a dot, quote it: SET k \"a.b\". Never compute or look up a value yourself: name the keys, "
           "the runtime reads and computes every value.")


class OpError(ValueError):
    """An operation the runtime cannot execute; the message says why (send it back to the model).
    `code` is a stable Core error code (spec/core/STATE_OPS.md, section 7)."""

    def __init__(self, message: str, code: str = "E_PARSE"):
        super().__init__(message)
        self.code = code


def dot(state: dict) -> str:
    """The green dot: a short hash of the whole state. Equal dots = equal copies.
    Keys and values are compared as text and encoded as sorted JSON, so no value can imitate a key boundary."""
    canon = json.dumps({str(k): str(v) for k, v in state.items()}, sort_keys=True, ensure_ascii=False,
                       separators=(",", ":"))
    return hashlib.sha256(canon.encode()).hexdigest()[:12]


def _int(state, k):
    if k not in state:
        raise OpError(f"{k} does not exist", "E_MISSING_KEY")
    try:
        return int(str(state[k]))
    except ValueError:
        raise OpError(f"{k} is not a whole number ({state[k]!r})", "E_NOT_INTEGER")


def _key(tok):
    if not KEY_RX.match(tok):
        raise OpError(f"{tok!r} is not a key (expected dotted.name)", "E_NOT_KEY")
    return tok


def _opt(words, i):
    """Parse optional '+n' and 'CAP m' starting at words[i]."""
    n, cap = 0, None
    while i < len(words):
        w = words[i]
        if re.fullmatch(r"[+-]\d+", w):
            n = int(w); i += 1
        elif w.upper() == "CAP" and i + 1 < len(words) and re.fullmatch(r"-?\d+", words[i + 1]):
            cap = int(words[i + 1]); i += 2
        else:
            raise OpError(f"unexpected {w!r}", "E_PARSE")
    return n, cap


def parse_ops(text: str) -> list:
    """Parse operations; lines that do not start with an operation are ignored (models add prose)."""
    ops = []
    for raw in text.strip().splitlines():
        line = raw.strip().rstrip(";")
        if not line or line.split()[0].upper() not in OPS:
            continue
        kw = line.split()[0].upper()
        if kw == "SET":
            q = SET_QUOTED_RX.match(line)
            if q:
                ops.append(("SET", _key(q.group(1)), q.group(3), True)); continue
        if kw == "ROUTE":
            m = ROUTE_RX.match(line)
            if not m:
                raise OpError(f"ROUTE needs 's = x : d v1 | v2': {line!r}", "E_PARSE")
            s, x, d, v1, v2 = m.groups()
            ops.append(("ROUTE", _key(s), x, _key(d), v1, v2)); continue
        try:
            w = shlex.split(line)
        except ValueError as e:
            raise OpError(f"cannot read {line!r}: {e}", "E_PARSE")
        w = [w[0].upper()] + [x for x in w[1:] if x != "="]
        if kw == "SET" and len(w) == 3:
            ops.append(("SET", _key(w[1]), w[2]))
        elif kw == "DEL" and len(w) == 2:
            ops.append(("DEL", _key(w[1])))
        elif kw == "INHERIT" and len(w) >= 3:
            ops.append(("INHERIT", _key(w[1]), _key(w[2])) + _opt(w, 3))
        elif kw == "FUSE" and len(w) >= 4:
            ops.append(("FUSE", _key(w[1]), _key(w[2]), _key(w[3]), _opt(w, 4)[1]))
        elif kw == "SCALE" and len(w) >= 3 and re.fullmatch(r"\d+(\.\d+)?", w[2]):
            ops.append(("SCALE", _key(w[1]), float(w[2]), _opt(w, 3)[1]))
        elif kw == "REHOST" and len(w) == 4:
            ops.append(("REHOST", w[1], w[2], w[3]))
        elif kw == "FLOW" and len(w) >= 6 and w[2].upper() == "OVER":
            n, cap = _opt(w, 5)
            ops.append(("FLOW", w[1], w[3], w[4], n, cap))
        else:
            raise OpError(f"malformed operation {line!r}", "E_PARSE")
    if not ops:
        raise OpError("no operations", "E_EMPTY")
    return ops


def _cap(x, cap):
    return min(x, cap) if cap is not None else x


def execute(state: dict, ops: list) -> dict:
    """Apply operations to a copy of state; every value is read and computed by the runtime."""
    st = dict(state)
    for op in ops:
        kw = op[0]
        if kw == "SET":
            k, v, literal = op[1], op[2], len(op) > 3 and op[3]
            if not literal and KEY_RX.match(v):
                if v not in st:
                    raise OpError(f"SET {k}: source key {v} does not exist (quote the value to set it as text)", "E_MISSING_KEY")
                v = st[v]
            st[k] = v
        elif kw == "DEL":
            if op[1] not in st:
                raise OpError(f"DEL {op[1]}: no such key", "E_MISSING_KEY")
            del st[op[1]]
        elif kw == "INHERIT":
            _, d, s, n, cap = op
            if s not in st:
                raise OpError(f"INHERIT: {s} does not exist", "E_MISSING_KEY")
            st[d] = str(_cap(_int(st, s) + n, cap)) if (n or cap is not None) else st[s]
        elif kw == "FUSE":
            _, d, a, b, cap = op
            st[d] = str(_cap(_int(st, a) + _int(st, b), cap))
        elif kw == "SCALE":
            _, k, f, cap = op
            v = _int(st, k) * f
            if not float(v).is_integer():
                raise OpError(f"SCALE {k} {f:g}: result {v:g} is not a whole number", "E_FRACTION")
            st[k] = str(_cap(int(v), cap))
        elif kw == "ROUTE":
            _, s, x, d, v1, v2 = op
            if s not in st:
                raise OpError(f"ROUTE: {s} does not exist", "E_MISSING_KEY")
            st[d] = v1 if str(st[s]) == x else v2
        elif kw == "REHOST":
            _, field, a, b = op
            for k in [k for k, v in st.items() if k.rsplit(".", 1)[-1] == field and str(v) == a]:
                st[k] = b
        elif kw == "FLOW":
            _, field, cond, x, n, cap = op
            objs = [k.rsplit(".", 1)[0] for k, v in st.items() if k.rsplit(".", 1)[-1] == cond and str(v) == x]
            for o in objs:
                k = f"{o}.{field}"
                if k in st:
                    st[k] = str(_cap(_int(st, k) + n, cap))
    return st


def plan_prompt(requests: list, state: dict) -> dict:
    """One prompt for the whole task (the assembly line): the model writes operations for every request at once.
    Works with any chat model; send {'system': ..., 'user': ...} and pass the reply to parse_plan."""
    keys = ", ".join(sorted(state))
    reqs = "\n".join(f"#{i}\n{r}" for i, r in enumerate(requests))
    return {"system": "You translate change requests into RSOS operations. " + GRAMMAR +
                      " For each request write '#<n>' on its own line, then its operations. No prose.",
            "user": f"Keys in the shared state: {keys}\n\nRequests:\n{reqs}"}


def parse_plan(text: str) -> dict:
    """{step number: operations text} from a reply to plan_prompt."""
    out, cur = {}, None
    for line in text.splitlines():
        m = STEP_RX.match(line.strip())
        if m:
            cur = int(m.group(1)); out[cur] = []
        elif cur is not None:
            out[cur].append(line)
    return {k: "\n".join(v) for k, v in out.items()}


class Ledger:
    """The agreed state, its green dot and its history. Agents keep copies; sync() heals them."""

    def __init__(self, state: dict):
        self.state = {k: str(v) for k, v in state.items()}
        self.history = [(dot(self.state), None)]

    @property
    def dot(self) -> str:
        return dot(self.state)

    def apply(self, ops_text: str) -> dict:
        """Execute one step. Returns {'ok', 'dot', 'changed'} or {'ok': False, 'error'} (state unchanged)."""
        try:
            new = execute(self.state, parse_ops(ops_text))
        except OpError as e:
            return {"ok": False, "error": str(e), "code": e.code}
        changed = {k: (self.state.get(k), new.get(k)) for k in set(self.state) | set(new) if self.state.get(k) != new.get(k)}
        self.state = new
        self.history.append((self.dot, ops_text))
        return {"ok": True, "dot": self.dot, "changed": changed}

    def apply_plan(self, plan: dict) -> dict:
        """Execute every step of a parse_plan result in order; failed steps are reported for one re-ask."""
        results = {}
        for step in sorted(plan):
            results[step] = self.apply(plan[step])
        return {"dot": self.dot, "steps": results, "failed": [s for s, r in results.items() if not r["ok"]]}

    def sync(self, replica: dict) -> dict:
        """Check a copy against the green dot and restore every drifted line from the agreed state. 0 model calls."""
        rep = {k: str(v) for k, v in replica.items()}
        if dot(rep) == self.dot:
            return {"healed": [], "state": rep, "dot": self.dot, "model_calls": 0}
        drifted = sorted(k for k in set(rep) | set(self.state) if rep.get(k) != self.state.get(k))
        return {"healed": drifted, "state": dict(self.state), "dot": self.dot, "model_calls": 0}

    def to_json(self) -> str:
        return json.dumps({"state": self.state, "dot": self.dot, "steps": len(self.history) - 1}, sort_keys=True)
