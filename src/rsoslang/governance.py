"""Governance (T1): the Spine, the Watchdog, the Meta-Architect, consent and return to baseline.

One rule set, not a copy: the checks are the public cue framework's own (rsxv/agents.py spine_check and AuditLog;
rsso/safety.py wording flags and safety modes), loaded read-only (D78). The framework is found through the
environment variable RSOS_CUE_FRAMEWORK or next to this repository.

What governance adds to a compiled program:
- every person-facing operation becomes a proposal, checked by the Spine and written to a hash-chained audit log;
- a person-facing operation without CONSENT for that host fails Rei (E018);
- wording in a program that the Spine forbids (extreme cold or heat, pain, extreme breath-holding, sleep deprivation,
  population ranks about a person) fails Jin or Makoto (E019);
- the active safety mode limits what may run;
- every person host gets a return to baseline (added and reported if the program forgot it).
"""

import importlib
import os
import sys

from .diagnostics import Diagnostic

HUMAN_KINDS = {"human", "person", "team", "organisation", "organization", "company"}
PERSON_OPS = {"heal", "beam", "rescript", "anchor", "futurepace", "cue", "override", "model", "selectmodel",
              "ball", "shift", "colour", "route", "compress", "watchdog", "architect", "schedule", "session"}
REGULATING = {"futurepace", "anchor", "cue", "schedule"}
_CANDIDATES = ["RSOS_CUE_FRAMEWORK", "../wt-dev", "../RSOS-Multimodal-Cue-Framework"]
_cache = {}


def load_framework():
    """Import the cue framework's governance modules. Returns (agents, safety) or (None, None)."""
    if "mods" in _cache:
        return _cache["mods"]
    here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    roots = [os.environ.get("RSOS_CUE_FRAMEWORK")] + [os.path.join(here, c) for c in _CANDIDATES[1:]]
    for root in roots:
        if root and os.path.isfile(os.path.join(root, "rsxv", "rsxv", "agents.py")):
            for sub in ("rsxv", "rsso"):
                p = os.path.join(root, sub)
                if p not in sys.path:
                    sys.path.insert(0, p)
            try:
                agents = importlib.import_module("rsxv.agents")
                safety = importlib.import_module("rsso.safety")
                _cache["mods"] = (agents, safety)
                _cache["root"] = root
                return _cache["mods"]
            except Exception:  # noqa: BLE001
                continue
    _cache["mods"] = (None, None)
    return _cache["mods"]


def _strings(x):
    if isinstance(x, str):
        yield x.replace("_", " ")
    elif isinstance(x, dict):
        for v in x.values():
            yield from _strings(v)
    elif isinstance(x, (list, tuple)):
        for v in x:
            yield from _strings(v)


def govern(ir):
    """Check a compiled program. Returns (report, diagnostics). The IR gains 'governance'."""
    agents, safety = load_framework()
    diags = []
    if agents is None:
        diags.append(Diagnostic("W005_NO_GOVERNANCE", 1,
                                "cue framework not found (set RSOS_CUE_FRAMEWORK): person-facing output must not be used"))
        ir["governance"] = {"available": False}
        return ir["governance"], diags
    hosts = ir.get("hosts", {})
    persons = {h for h, v in hosts.items() if (v.get("kind") or "").lower() in HUMAN_KINDS}
    consent, mode, baseline = {}, {h: "NORMAL" for h in persons}, set()
    log = agents.AuditLog()
    blocked, passed = [], 0
    networks = {op["args"]["name"]: op["clauses"] for op in ir["ops"] if op["op"] == "network"}
    standing = {}
    for op in ir["ops"]:
        kind, line = op["op"], op["line"]
        host = op["context"].get("host")
        if kind == "consent":
            h = op["args"]["host"]
            if op["clauses"].get("scope") == "standing":
                net = networks.get(op["clauses"].get("in"))
                if not net or h not in net.get("members", []) or not net.get("laws"):
                    diags.append(Diagnostic("E021_STANDING", line,
                                            f"standing consent for {h} without a visible NETWORK and Spine laws"))
                    continue
                standing[h] = op["clauses"].get("in")
            consent[h] = op["clauses"].get("for", ["all"])
            continue
        if kind == "safety":
            mode[op["args"]["host"]] = op["clauses"]["mode"].upper()
            continue
        if kind == "baseline":
            baseline.add(op["args"]["target"])
            continue
        flags = [f for t in _strings(op["args"]) for f in safety.spine_flags(t)] + \
                [f for t in _strings(op["clauses"]) for f in safety.spine_flags(t)]
        for f in flags:
            diags.append(Diagnostic("E019_SPINE", line, f"{f['virtue']}: {f['text']}"))
        if host not in persons or kind not in PERSON_OPS:
            continue
        category = "regulating_cue" if kind in REGULATING else ("deep_processing" if kind in ("heal", "rescript", "beam")
                                                                else "module_work")
        harm = 0.0
        if kind == "override":
            from .identity import predicted_harm, override_type
            persona = hosts.get(host, {}) if hosts.get(host, {}).get("persona") else None
            harm = predicted_harm(persona, op["clauses"].get("type"))
            if persona:
                op["recommended_override"] = override_type(persona)
        p = {"actor": "PROGRAM", "action": kind, "target": "person", "disclosed": True, "logged": True,
             "consent": bool(consent.get(host)), "predicted_harm": harm, "measured": True, "serves_mission": True,
             "mode": mode.get(host, "NORMAL"), "category": category,
             "intensity_mechanism": next((f["flag"] for f in flags if f["virtue"] == "jin"), None),
             "rank_claim_about_person": any(f["flag"] == "rank_claim" for f in flags)}
        chk = agents.submit(p, log)
        op["governance"] = {"ok": chk["ok"], "failed": chk["failed"], "category": category, "mode": p["mode"]}
        if chk["ok"]:
            passed += 1
            continue
        blocked.append({"line": line, "op": kind, "failed": chk["failed"]})
        if "rei" in chk["failed"]:
            diags.append(Diagnostic("E018_CONSENT", line, f"{kind} on {host} without CONSENT (Rei)"))
        other = [f for f in chk["failed"] if f not in ("rei", "jin", "makoto")] + \
                (["jin (predicted harm %.2f)" % harm] if "jin" in chk["failed"] and not flags else [])
        for f in other:
            diags.append(Diagnostic("E020_GOVERNANCE", line, f"{kind} blocked by the Spine: {f} (mode {p['mode']})"))
    for h in sorted(persons - baseline):
        diags.append(Diagnostic("W006_BASELINE_ADDED", 1, f"return to baseline added for {h} (always available, D71)"))
    ir["governance"] = {"available": True, "framework": _cache.get("root"), "persons": sorted(persons),
                        "consent": consent, "standing": standing, "networks": sorted(networks), "modes": mode, "baseline": sorted(persons), "passed": passed,
                        "blocked": blocked, "audit_head": getattr(log, "head", None) or _audit_head(log)}
    return ir["governance"], diags


def _audit_head(log):
    recs = getattr(log, "records", None) or getattr(log, "entries", None) or []
    return recs[-1].get("hash") if recs and isinstance(recs[-1], dict) else None
