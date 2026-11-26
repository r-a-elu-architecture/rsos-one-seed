"""The node palace: every node keeps its books; a message is a symbol that opens one, plus the change.

Owner, 17 Nov 2026: green dots signal through all foundations and leave at each node "the palace in which all
books of universe are there for that specific node"; the White Dragon light "heals and finds and shows and hears".
Chat 2 T28: a compact symbolic cue retrieves a larger structure.

Functional reading built here:
- Palace  = a per-node library of books (programs), each opened by a symbol.
- Message = `@symbol#hash` + line edits. The receiver opens its own book and applies the edits.
- Green dot = the hash signal: before opening, the receiver checks its book is the same book.
- White Dragon = find / show / heal: chunk hashes find where two books differ, show the place, and heal only it.
"""

import hashlib

CHUNK = 4


def h(text, n=8):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:n]


class Palace:
    def __init__(self, books=None):
        self.books = dict(books or {})

    def add(self, symbol, source):
        self.books[symbol] = source

    def signal(self, symbol):
        """Green dot: the short hash that says which book this is."""
        return h(self.books[symbol])


def _edits(old, new):
    """Minimal line edits old -> new as ops (difflib opcodes, replace/insert/delete only)."""
    import difflib
    a, b = old.split("\n"), new.split("\n")
    ops = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        if tag != "equal":
            ops.append((i1, i2, b[j1:j2]))
    return ops


def encode(palace, symbol, source):
    """Message text: header line, then per op `i1,i2` and the new lines."""
    out = [f"@{symbol}#{palace.signal(symbol)}"]
    for i1, i2, lines in _edits(palace.books[symbol], source):
        out.append(f"{i1},{i2}" if i2 != i1 + 1 or not lines else f"{i1}")
        out.extend("|" + ln for ln in lines)
    return "\n".join(out)


class Drift(Exception):
    def __init__(self, symbol, mine, theirs):
        super().__init__(f"book {symbol}: receiver {mine} != sender {theirs}")
        self.symbol, self.mine, self.theirs = symbol, mine, theirs


def decode(palace, message, check=True):
    rows = message.split("\n")
    sym, sig = rows[0][1:].split("#")
    if check and palace.signal(sym) != sig:
        raise Drift(sym, palace.signal(sym), sig)
    base = palace.books[sym].split("\n")
    ops, cur = [], None
    for r in rows[1:]:
        if r.startswith("|"):
            cur[2].append(r[1:])
        else:
            if "," in r:
                i1, i2 = map(int, r.split(","))
            else:
                i1 = int(r); i2 = i1 + 1
            cur = [i1, i2, []]; ops.append(cur)
    for i1, i2, lines in reversed(ops):
        base[i1:i2] = lines
    return "\n".join(base)


def chunk_signals(source, size=CHUNK):
    lines = source.split("\n")
    return [h("\n".join(lines[i:i + size]), 6) for i in range(0, len(lines), size)]


def find(mine, theirs_signals, size=CHUNK):
    """White Dragon find/show: indices of chunks whose signal differs (the places that need light)."""
    m = chunk_signals(mine, size)
    n = max(len(m), len(theirs_signals))
    return [i for i in range(n) if i >= len(m) or i >= len(theirs_signals) or m[i] != theirs_signals[i]]


def heal(sender_book, receiver_book, size=CHUNK):
    """Receiver sends its chunk signals; sender returns only the differing chunks. Returns healed book, bytes."""
    req = ",".join(chunk_signals(receiver_book, size))
    bad = find(sender_book, chunk_signals(receiver_book, size), size)
    s = sender_book.split("\n")
    nchunks = (len(s) + size - 1) // size
    reply = []
    for i in bad:
        if i < nchunks:
            reply.append(f"#{i}\n" + "\n".join(s[i * size:(i + 1) * size]))
    reply.append(f"N{nchunks}")
    reply = "\n".join(reply)
    r = receiver_book.split("\n")
    out = []
    for i in range(nchunks):
        out.extend(s[i * size:(i + 1) * size] if i in bad else r[i * size:(i + 1) * size])
    return "\n".join(out), len(req.encode()) + len(reply.encode())
