"""RSOS protocol v0: one message format between any two hosts (layer 2). Private.

An envelope carries operators that name keys and relations, never state values (a SET literal is the only value,
and it is the instruction itself), plus the Merkle root of the receiver's book before and after the change. The
receiver applies the operators deterministically and opens the result only if both roots verify (READY) and every
written value is in its safe range (Law 0). Nothing is pushed into a receiver that is not prepared.
"""
import hashlib
import json

VERSION = "rsos-protocol/0"
OPS = ("SET", "COPY", "REHOST", "DERIVE")          # the minimal set used between hosts in SPHERE1


def _h(b):
    return hashlib.sha256(b).digest()


def merkle_root(book):
    leaves = [_h(json.dumps([k, book[k]], separators=(",", ":")).encode()) for k in sorted(book)]
    if not leaves:
        return _h(b"").hex()
    while len(leaves) > 1:
        if len(leaves) % 2:
            leaves.append(leaves[-1])
        leaves = [_h(leaves[i] + leaves[i + 1]) for i in range(0, len(leaves), 2)]
    return leaves[0].hex()


def apply(book, ops, safe):
    """Deterministic runtime. Returns (new_book, ok). ok is False if any value leaves its safe range."""
    b = dict(book)
    for op in ops:
        kind = op["op"]
        if kind == "SET":
            b[op["key"]] = op["value"]
        elif kind == "COPY":
            b[op["dst"]] = b[op["src"]]
        elif kind == "REHOST":                         # everything with field == old becomes new
            for k in b:
                if k.endswith("." + op["field"]) and b[k] == op["old"]:
                    b[k] = op["new"]
        elif kind == "DERIVE":                         # dst := min(int(src) + add, cap)
            b[op["dst"]] = str(min(int(b[op["src"]]) + int(op["add"]), int(op["cap"])))
        else:
            return b, False
    ok = all(safe(k, v) for k, v in b.items())
    return b, ok


def envelope(sender, receiver, host, book_before, ops, seq, safe, author="R.A. Elu"):
    after, _ = apply(book_before, ops, safe)
    env = {"v": VERSION, "author": author, "from": sender, "to": receiver, "host": host, "seq": seq, "ops": ops,
           "root_before": merkle_root(book_before), "root_after": merkle_root(after)}
    env["id"] = hashlib.sha256(json.dumps(env, sort_keys=True).encode()).hexdigest()
    return env


def receive(book, env, safe, seen):
    """READY + Law 0 at the receiver. Returns (book, verdict)."""
    if env.get("v") != VERSION:
        return book, "refused:version"
    body = {k: v for k, v in env.items() if k != "id"}
    if hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest() != env.get("id"):
        return book, "refused:tampered"
    if env["id"] in seen:
        return book, "refused:replay"
    if any(op.get("op") not in OPS for op in env["ops"]):
        return book, "refused:operator"
    if merkle_root(book) != env["root_before"]:
        return book, "refused:not_ready"              # the receiver's book is not the one the sender planned on
    new, ok = apply(book, env["ops"], safe)
    if not ok:
        return book, "refused:law0"
    if merkle_root(new) != env["root_after"]:
        return book, "refused:root"
    seen.add(env["id"])
    return new, "accepted"
