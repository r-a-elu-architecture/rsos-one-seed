"""Tokenizer for the RSOS Language text form.

One statement per line. `#` starts a comment. Tokens: words and dotted paths, numbers,
quoted strings, and the symbols , + = -> ; ( ).
"""

import re
from dataclasses import dataclass

TOKEN_RE = re.compile(r'''
    (?P<STRING>"(?:[^"\\]|\\.)*")
  | (?P<ARROW>->)
  | (?P<NUMBER>[-+]?\d+(?:\.\d+)?(?![\w.]))
  | (?P<WORD>[A-Za-z_][\w]*(?:\.[A-Za-z_\d][\w]*)*)
  | (?P<SYM>[,+=;()])
  | (?P<WS>\s+)
''', re.VERBOSE)


@dataclass
class Token:
    kind: str   # STRING, ARROW, NUMBER, WORD, SYM
    value: str
    col: int

    def __repr__(self):
        return f"{self.kind}:{self.value}"


class LexError(Exception):
    def __init__(self, line, col, text):
        self.line, self.col, self.text = line, col, text
        super().__init__(f"line {line}, col {col}: cannot read {text!r}")


def strip_comment(line: str) -> str:
    out, in_str = [], False
    for ch in line:
        if ch == '"':
            in_str = not in_str
        if ch == "#" and not in_str:
            break
        out.append(ch)
    return "".join(out)


def tokenize_line(text: str, lineno: int = 0):
    text = strip_comment(text)
    pos, toks = 0, []
    while pos < len(text):
        m = TOKEN_RE.match(text, pos)
        if not m:
            raise LexError(lineno, pos + 1, text[pos:pos + 10])
        kind = m.lastgroup
        if kind != "WS":
            val = m.group(kind)
            if kind == "STRING":
                val = bytes(val[1:-1], "utf-8").decode("unicode_escape")
            toks.append(Token(kind, val, pos + 1))
        pos = m.end()
    return toks


def tokenize(source: str):
    """Return a list of (line number, tokens) for every non-empty line."""
    lines = []
    for i, raw in enumerate(source.splitlines(), start=1):
        toks = tokenize_line(raw, i)
        if toks:
            lines.append((i, toks))
    return lines
