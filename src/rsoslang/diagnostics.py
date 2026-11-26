"""Diagnostics: errors stop compilation, warnings do not.

Codes E001-E015 follow the VSFL v0.1 manual (section 12) where they overlap; E016-E020 and the
warnings are new in 0.2 (host, open meanings, implicit parts).
"""

from dataclasses import dataclass, asdict

CODES = {
    "E001_HEADER": "Language header missing or wrong version",
    "E002_WORLD": "Missing or duplicate world declaration",
    "E003_UNKNOWN_ENTITY": "Object, part, host, room or line not declared",
    "E004_PATH": "Path absent, empty or malformed",
    "E005_SYNTAX": "Statement does not match its grammar",
    "E006_CONTRACT": "A required property is absent",
    "E007_VALUE": "Value out of range or of the wrong kind",
    "E008_OPERATOR": "Unknown statement or operator",
    "E009_DUPLICATE": "Name declared twice",
    "E010_AMBIGUITY": "Two bindings give different meanings in the same scope",
    "E016_HOST": "Operator not defined for this host (kind or channel)",
    "E017_MEANING": "Meaning key unknown to the core and not bound or searched",
    "E018_CONSENT": "Person-facing operation without consent for that host (Spine: Rei)",
    "E019_SPINE": "Wording the Spine forbids (Jin: extreme cold/heat, pain, breath-holding, sleep loss; Makoto: ranks)",
    "E020_GOVERNANCE": "Blocked by the Spine or by the active safety mode",
    "E021_STANDING": "Standing consent needs a declared NETWORK listing the host as a member and the Spine laws (D82)",
    "E022_REACH": "REACH target or chain malformed (TARGET is an improvement factor above 1; FROM names an earlier REACH)",
    "W007_REACH_LIMIT": "A measured REACH below its target does not name what stopped it (LIMIT)",
    "W005_NO_GOVERNANCE": "Cue framework not found: governance could not run",
    "W006_BASELINE_ADDED": "Return to baseline added for a person host (D71)",
    "W001_OPEN_MEANING": "Meaning left open: resolved by search, not by the core",
    "W002_IMPLICIT_PART": "Sub-part used without a PART declaration (accepted, created implicitly)",
    "W003_NO_HOST": "Operator runs without a declared host; the core meaning is used",
}


@dataclass
class Diagnostic:
    code: str
    line: int
    message: str

    @property
    def is_error(self) -> bool:
        return self.code.startswith("E")

    def to_dict(self):
        d = asdict(self)
        d["severity"] = "error" if self.is_error else "warning"
        return d

    def __str__(self):
        sev = "error" if self.is_error else "warning"
        return f"line {self.line}: {sev} {self.code}: {self.message}"


class CompileError(Exception):
    def __init__(self, diagnostics):
        self.diagnostics = diagnostics
        super().__init__("\n".join(str(d) for d in diagnostics if d.is_error))
