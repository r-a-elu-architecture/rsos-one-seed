"""Parser: tokens → statements, checked against the statement table (grammar.py).

The parser checks form only. Names, hosts and meanings are checked in semantics.py.
"""

from dataclasses import dataclass, field

from .lexer import tokenize, LexError
from .grammar import STATEMENTS
from .diagnostics import Diagnostic


@dataclass
class Statement:
    kw: str
    line: int
    args: dict = field(default_factory=dict)
    clauses: dict = field(default_factory=dict)

    def get(self, key, default=None):
        if key in self.args:
            return self.args[key]
        return self.clauses.get(key, default)


@dataclass
class Program:
    statements: list
    diagnostics: list


class _Fail(Exception):
    def __init__(self, msg, code="E005_SYNTAX"):
        self.msg, self.code = msg, code


class _Cursor:
    def __init__(self, toks, clause_words):
        self.t, self.i, self.clause_words = toks, 0, clause_words

    def done(self):
        return self.i >= len(self.t)

    def peek(self):
        return None if self.done() else self.t[self.i]

    def next(self):
        if self.done():
            raise _Fail("statement ends too early")
        tok = self.t[self.i]
        self.i += 1
        return tok

    def at_clause(self):
        tok = self.peek()
        return tok is not None and tok.kind == "WORD" and tok.value in self.clause_words

    def at_sym(self, sym):
        tok = self.peek()
        return tok is not None and tok.kind in ("SYM", "ARROW") and tok.value == sym


def _word(c, allow_dots=True, what="identifier"):
    tok = c.next()
    if tok.kind != "WORD":
        raise _Fail(f"expected {what}, found {tok.value!r}")
    if not allow_dots and "." in tok.value:
        raise _Fail(f"a new name cannot contain dots: {tok.value!r}", "E004_PATH")
    return tok.value


def _value(c):
    tok = c.next()
    if tok.kind == "NUMBER":
        return float(tok.value) if "." in tok.value else int(tok.value)
    if tok.kind in ("STRING", "WORD"):
        return tok.value
    raise _Fail(f"expected a value, found {tok.value!r}")


def _list(c):
    items = [_word(c)]
    while c.at_sym(","):
        c.next()
        items.append(_word(c))
    return items


def _nums(c):
    items = [_read(c, "num")]
    while c.at_sym(","):
        c.next()
        items.append(_read(c, "num"))
    return items


def _comp(c):
    items = [_word(c)]
    while c.at_sym("+"):
        c.next()
        items.append(_word(c))
    return items


def _cases(c):
    cases = []
    while True:
        key = _word(c)
        if not c.at_sym("->"):
            raise _Fail("expected '->' in a case list")
        c.next()
        cases.append([key, _word(c)])
        if c.at_sym(";"):
            c.next()
            continue
        break
    return cases


def _read(c, kind):
    if kind == "name":
        return _word(c, allow_dots=False, what="a new name")
    if kind in ("path", "word"):
        return _word(c)
    if kind in ("num", "int"):
        tok = c.next()
        if tok.kind != "NUMBER":
            raise _Fail(f"expected a number, found {tok.value!r}", "E007_VALUE")
        if kind == "int":
            if "." in tok.value:
                raise _Fail(f"expected a whole number, found {tok.value}", "E007_VALUE")
            return int(tok.value)
        return float(tok.value)
    if kind == "string":
        tok = c.next()
        if tok.kind != "STRING":
            raise _Fail(f"expected quoted text, found {tok.value!r}")
        return tok.value
    if kind == "value":
        return _value(c)
    if kind == "list":
        return _list(c)
    if kind == "comp":
        return _comp(c)
    if kind == "nums":
        return _nums(c)
    if kind == "cases":
        return _cases(c)
    if kind.startswith("enum:"):
        options = kind[5:].split("|")
        w = _word(c).lower()
        if w not in options:
            raise _Fail(f"expected one of {', '.join(options)}; found {w!r}", "E007_VALUE")
        return w
    if kind == "=":
        if not c.at_sym("="):
            raise _Fail("expected '='")
        c.next()
        return "="
    raise AssertionError(kind)


def parse_statement(lineno, toks):
    head = toks[0]
    if head.kind != "WORD":
        raise _Fail(f"a statement starts with a keyword, found {head.value!r}")
    kw = head.value.upper()
    spec = STATEMENTS.get(kw)
    if spec is None:
        raise _Fail(f"unknown statement {head.value!r}", "E008_OPERATOR")
    c = _Cursor(toks[1:], set(spec.clauses))
    stmt = Statement(kw, lineno)
    for name, kind in spec.pos:
        if c.at_clause() and kind not in ("=",):
            raise _Fail(f"{kw} needs <{name}> before {c.peek().value}")
        val = _read(c, kind)
        if not name.startswith("_"):
            stmt.args[name] = val
    while not c.done():
        tok = c.next()
        if tok.kind != "WORD" or tok.value not in spec.clauses:
            allowed = ", ".join(spec.clauses) or "none"
            raise _Fail(f"unexpected {tok.value!r} in {kw} (clauses allowed: {allowed})")
        if tok.value in stmt.clauses:
            raise _Fail(f"clause {tok.value} given twice")
        stmt.clauses[tok.value] = _read(c, spec.clauses[tok.value])
    for req in spec.required:
        if req not in stmt.clauses:
            raise _Fail(f"{kw} requires the clause {req}")
    return stmt


def parse(source: str) -> Program:
    statements, diags = [], []
    try:
        lines = tokenize(source)
    except LexError as e:
        return Program([], [Diagnostic("E005_SYNTAX", e.line, str(e))])
    for lineno, toks in lines:
        try:
            statements.append(parse_statement(lineno, toks))
        except _Fail as f:
            diags.append(Diagnostic(f.code, lineno, f.msg))
    return Program(statements, diags)
