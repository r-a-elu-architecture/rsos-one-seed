"""Command line: python -m rsoslang check|ir|statements|register FILE

  check FILE        report errors and warnings; exit 1 on errors
  ir FILE           print the JSON IR (and its SHA-256 on stderr)
  statements        list every statement with its register links and an example
  register          show which register rows (U1–U87) the language covers
  session FILE      a person's practice session: RSX program and the cue framework's timeline
  mcp               run the MCP server (stdio): the State Runtime and the language as tools
"""

import json
import sys
from importlib import resources

from .compiler import compile_file
from .grammar import STATEMENTS


def _register():
    with resources.files("rsoslang").joinpath("data/register.json").open(encoding="utf-8") as f:
        return json.load(f)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd = argv[0]
    if cmd == "mcp":
        from .mcp_server import main as serve
        serve()
        return 0
    if cmd == "statements":
        if "--json" in argv:
            from .grammar import signature
            print(json.dumps({s.kw: {"family": s.family, "refs": s.refs, "signature": signature(s), "example": s.doc}
                              for s in STATEMENTS.values()}, indent=1, ensure_ascii=False))
            return 0
        for s in STATEMENTS.values():
            print(f"{s.kw:<12} {s.family:<8} {','.join(s.refs):<22} {s.doc}")
        return 0
    if cmd == "register":
        reg = _register()
        covered = {r for s in STATEMENTS.values() for r in s.refs}
        for row in reg:
            mark = "x" if row["id"] in covered else " "
            print(f"[{mark}] {row['id']:<4} {row['name'][:70]}")
        print(f"\ncovered {sum(r['id'] in covered for r in reg)} / {len(reg)} register rows")
        return 0
    if cmd == "session" and len(argv) >= 2:
        from .mind.session import compile_session
        res = compile_file(argv[1])
        for d in res.diagnostics:
            print(d, file=sys.stderr)
        s = compile_session(res.ir, argv[1])
        print(s["rsx"])
        print(f"# {len(s['steps'])} steps, {len(s['timeline']['events'])} timeline events, "
              f"{s['timeline'].get('duration_ms', 0) / 1000:.0f} s; skipped {s['skipped']}; {s['footer']}", file=sys.stderr)
        return 0
    if cmd in ("check", "ir") and len(argv) >= 2:
        res = compile_file(argv[1])
        for d in res.diagnostics:
            print(d, file=sys.stderr)
        if cmd == "ir":
            print(res.to_json())
            print(f"sha256 {res.digest()}", file=sys.stderr)
        else:
            print(f"{argv[1]}: {len(res.errors)} errors, {len(res.warnings)} warnings, {len(res.ir['ops'])} operations")
        return 0 if res.ok else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())


def cli():
    sys.exit(main())
