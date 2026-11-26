"""Compile RSOS Language source to the JSON intermediate representation."""

import hashlib
import json
from dataclasses import dataclass

from .parser import parse
from .semantics import analyze


@dataclass
class Result:
    ir: dict
    diagnostics: list

    @property
    def ok(self):
        return not any(d.is_error for d in self.diagnostics)

    @property
    def errors(self):
        return [d for d in self.diagnostics if d.is_error]

    @property
    def warnings(self):
        return [d for d in self.diagnostics if not d.is_error]

    def to_json(self, indent=2):
        return json.dumps(self.ir, indent=indent, ensure_ascii=False, sort_keys=True)

    def digest(self):
        """SHA-256 of the canonical IR: the same source always gives the same digest."""
        canon = json.dumps(self.ir, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        return hashlib.sha256(canon.encode("utf-8")).hexdigest()


def compile_source(source: str, govern: bool = True) -> Result:
    prog = parse(source)
    ir, sem = analyze(prog.statements)
    gov = []
    if govern and ir.get("hosts"):
        from .governance import govern as _govern
        _, gov = _govern(ir)
    diags = sorted(prog.diagnostics + sem + gov, key=lambda d: (d.line, d.code))
    ir["diagnostics"] = [d.to_dict() for d in diags]
    return Result(ir, diags)


def compile_file(path) -> Result:
    with open(path, encoding="utf-8") as f:
        return compile_source(f.read())
