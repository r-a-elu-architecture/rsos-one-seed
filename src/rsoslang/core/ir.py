"""RSOS Core v1: the intermediate representation (IR) and the Core syntax.

Specification: spec/core/STATE_OPS.md. Schema: spec/core/ir.schema.json. Registry: registry/operators.json.

Two surface syntaxes compile to one IR:
  * RSOS syntax (the symbolic layer):  REHOST owner bruno chen
  * Core syntax (the technical layer): reassign_where(field=owner, from=bruno, to=chen)
The IR is a JSON list of operation objects. `ir_digest` hashes its canonical encoding, so "the same program written
both ways" is a checkable claim: equal digests. The runtime (rsoslang.core.state.execute) executes the IR.
Standard library only.
"""
from __future__ import annotations

import hashlib
import json
import re

from rsoslang.core.state import KEY_RX, OpError, execute, parse_ops

CORE_VERSION = "1.0.0"

# Core operation name -> (RSOS keyword, ordered fields). The registry (registry/operators.json) must agree; a test
# fails if it does not.
CORE_OPS = {
    "set": ("SET", ("key", "value")),
    "copy": ("SET", ("key", "from")),
    "delete": ("DEL", ("key",)),
    "derive": ("INHERIT", ("dst", "src", "add", "max")),
    "sum_into": ("FUSE", ("dst", "a", "b", "max")),
    "multiply": ("SCALE", ("key", "factor", "max")),
    "select_if": ("ROUTE", ("cond_key", "equals", "dst", "then", "else")),
    "reassign_where": ("REHOST", ("field", "from", "to")),
    "derive_where": ("FLOW", ("field", "cond_field", "equals", "add", "max")),
}
KEY_FIELDS = {"set": {"key"}, "copy": {"key", "from"}, "delete": {"key"}, "derive": {"dst", "src"},
              "sum_into": {"dst", "a", "b"}, "multiply": {"key"}, "select_if": {"cond_key", "dst"},
              "reassign_where": set(), "derive_where": set()}
INT_FIELDS = {"add", "max"}


def to_ir(ops: list) -> list:
    """Runtime operation tuples (from parse_ops) -> IR objects."""
    out = []
    for op in ops:
        kw = op[0]
        if kw == "SET":
            k, v, literal = op[1], op[2], len(op) > 3 and op[3]
            if not literal and KEY_RX.match(v):
                out.append({"op": "copy", "key": k, "from": v})
            else:
                out.append({"op": "set", "key": k, "value": v})
        elif kw == "DEL":
            out.append({"op": "delete", "key": op[1]})
        elif kw == "INHERIT":
            out.append({"op": "derive", "dst": op[1], "src": op[2], "add": op[3], "max": op[4]})
        elif kw == "FUSE":
            out.append({"op": "sum_into", "dst": op[1], "a": op[2], "b": op[3], "max": op[4]})
        elif kw == "SCALE":
            f = op[2]
            out.append({"op": "multiply", "key": op[1], "factor": int(f) if float(f).is_integer() else f, "max": op[3]})
        elif kw == "ROUTE":
            out.append({"op": "select_if", "cond_key": op[1], "equals": op[2], "dst": op[3], "then": op[4], "else": op[5]})
        elif kw == "REHOST":
            out.append({"op": "reassign_where", "field": op[1], "from": op[2], "to": op[3]})
        elif kw == "FLOW":
            out.append({"op": "derive_where", "field": op[1], "cond_field": op[2], "equals": op[3], "add": op[4],
                        "max": op[5]})
        else:
            raise OpError(f"unknown operation {kw!r}", "E_PARSE")
    return out


def from_ir(ir: list) -> list:
    """IR objects -> runtime operation tuples. Validates names, fields and types (E_PARSE, E_NOT_KEY)."""
    ops = []
    for i, o in enumerate(ir):
        if not isinstance(o, dict) or o.get("op") not in CORE_OPS:
            raise OpError(f"IR[{i}]: unknown operation {o!r}", "E_PARSE")
        name = o["op"]
        fields = CORE_OPS[name][1]
        extra = set(o) - set(fields) - {"op"}
        if extra:
            raise OpError(f"IR[{i}] {name}: unexpected fields {sorted(extra)}", "E_PARSE")
        for f in fields:
            if f not in o and f not in INT_FIELDS:
                raise OpError(f"IR[{i}] {name}: missing field {f!r}", "E_PARSE")
        for f in KEY_FIELDS[name]:
            if not (isinstance(o[f], str) and KEY_RX.match(o[f])):
                raise OpError(f"IR[{i}] {name}.{f}: {o[f]!r} is not a key (expected dotted.name)", "E_NOT_KEY")
        g = {f: o.get(f) for f in fields}
        for f in INT_FIELDS & set(fields):
            if g[f] is not None and not isinstance(g[f], int):
                raise OpError(f"IR[{i}] {name}.{f}: expected an integer", "E_PARSE")
        if name == "set":
            ops.append(("SET", g["key"], str(g["value"]), True))
        elif name == "copy":
            ops.append(("SET", g["key"], g["from"]))
        elif name == "delete":
            ops.append(("DEL", g["key"]))
        elif name == "derive":
            ops.append(("INHERIT", g["dst"], g["src"], g["add"] or 0, g["max"]))
        elif name == "sum_into":
            ops.append(("FUSE", g["dst"], g["a"], g["b"], g["max"]))
        elif name == "multiply":
            if not isinstance(g["factor"], (int, float)) or g["factor"] < 0:
                raise OpError(f"IR[{i}] multiply.factor: expected a non-negative number", "E_PARSE")
            ops.append(("SCALE", g["key"], float(g["factor"]), g["max"]))
        elif name == "select_if":
            ops.append(("ROUTE", g["cond_key"], str(g["equals"]), g["dst"], str(g["then"]), str(g["else"])))
        elif name == "reassign_where":
            ops.append(("REHOST", str(g["field"]), str(g["from"]), str(g["to"])))
        elif name == "derive_where":
            ops.append(("FLOW", str(g["field"]), str(g["cond_field"]), str(g["equals"]), g["add"] or 0, g["max"]))
    if not ops:
        raise OpError("no operations", "E_EMPTY")
    return ops


def ir_digest(ir: list) -> str:
    """SHA-256 of the IR's canonical JSON encoding (sorted keys, no spaces, UTF-8)."""
    canon = json.dumps(ir, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canon.encode()).hexdigest()


CALL_RX = re.compile(r"^([a-z_]+)\s*\((.*)\)\s*;?$")
ARG_RX = re.compile(r'\s*([a-z_]+)\s*=\s*("(?:[^"\\]|\\.)*"|[^,]+?)\s*(?:,|$)')


def _value(field, raw):
    raw = raw.strip()
    if raw.startswith('"'):
        return json.loads(raw)
    if field in INT_FIELDS:
        if raw.lower() in ("none", "null"):
            return None
        if not re.fullmatch(r"[+-]?\d+", raw):
            raise OpError(f"{field}: expected an integer, got {raw!r}", "E_PARSE")
        return int(raw)
    if field == "factor":
        if not re.fullmatch(r"\d+(\.\d+)?", raw):
            raise OpError(f"factor: expected a number, got {raw!r}", "E_PARSE")
        return int(raw) if "." not in raw else float(raw)
    return raw


def parse_core(text: str) -> list:
    """Core syntax -> IR. One call per line: name(field=value, ...). Values are bare words or "JSON strings".
    Lines that are blank or start with '#' are ignored."""
    ir = []
    for raw in text.strip().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = CALL_RX.match(line)
        if not m or m.group(1) not in CORE_OPS:
            raise OpError(f"malformed Core operation {line!r}", "E_PARSE")
        name, body = m.groups()
        args, pos = {}, 0
        while pos < len(body):
            a = ARG_RX.match(body, pos)
            if not a or a.end() == pos:
                raise OpError(f"cannot read arguments of {line!r}", "E_PARSE")
            args[a.group(1)] = a.group(2)
            pos = a.end()
        fields = CORE_OPS[name][1]
        unknown = set(args) - set(fields)
        if unknown:
            raise OpError(f"{name}: unknown fields {sorted(unknown)}", "E_PARSE")
        obj = {"op": name}
        for f in fields:
            if f in args:
                obj[f] = _value(f, args[f])
            elif f in INT_FIELDS:
                obj[f] = 0 if f == "add" else None
            else:
                raise OpError(f"{name}: missing field {f!r}", "E_PARSE")
        ir.append(obj)
    from_ir(ir)  # validate
    return ir


def compile_rsos(text: str) -> list:
    """RSOS syntax -> IR."""
    return to_ir(parse_ops(text))


def execute_ir(state: dict, ir: list) -> dict:
    """Execute an IR program on a copy of state (the same runtime as RSOS syntax)."""
    return execute(state, from_ir(ir))


def to_core_text(ir: list) -> str:
    """IR -> Core syntax (one call per line)."""
    lines = []
    for o in ir:
        parts = []
        for f in CORE_OPS[o["op"]][1]:
            v = o.get(f)
            if v is None:
                continue
            if f == "add" and v == 0:
                continue
            parts.append(f"{f}={json.dumps(v) if isinstance(v, str) and not re.fullmatch(r'[A-Za-z0-9_.-]+', v) else v}")
        lines.append(f"{o['op']}({', '.join(parts)})")
    return "\n".join(lines)
