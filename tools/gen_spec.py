"""Generate the reference sections of spec/LANGUAGE.md from the code (statements, meanings, diagnostics).
Usage: PYTHONPATH=src python3 tools/gen_spec.py > spec/REFERENCE.md"""
from rsoslang.grammar import STATEMENTS, signature
from rsoslang.meanings import CORE
from rsoslang.diagnostics import CODES

print("# RSOS Language 0.2: reference (generated from the code; do not edit by hand)\n")
print("## Statements\n")
fam = None
for s in STATEMENTS.values():
    if s.family != fam:
        fam = s.family
        print(f"\n### {fam}\n\n| Statement | Register | Signature | Example |\n|---|---|---|---|")
    sig = signature(s)
    ins = ", ".join(sig["in"]).replace("|", "/")
    print(f"| `{s.kw}` | {', '.join(s.refs) or '—'} | {ins} → {sig['out']} | `{s.doc.replace('|', '/')}` |")
print("\n## Core meanings (tier 1, fixed; D80)\n\n| Key | Meaning | Source |\n|---|---|---|")
for k, (v, p) in CORE.items():
    print(f"| `{k}` | `{v}` | {p} |")
print("\nKeys with no core meaning (for example `contact.bottom`, `contact.centre`, `contact.outside`) must be bound with "
      "`MEANING` or left open with `SEARCH`; otherwise the compiler stops with E017.\n")
print("## Diagnostics\n\n| Code | Meaning |\n|---|---|")
for k, v in CODES.items():
    print(f"| `{k}` | {v} |")
