"""The same program written in RSOS syntax and in Core syntax compiles to an identical IR (equal digests) and
executes to the same state. This is what makes the symbolic layer a surface over Core rather than a second language."""
import json

import pytest

from rsoslang.core import compile_rsos, execute, execute_ir, ir_digest, parse_core, parse_ops, to_core_text

S = {"auth.timeout_ms": "700", "auth.retries": "3", "search.retries": "6", "auth.owner": "chen",
     "auth.region": "eu-west"}

PAIRS = [
    ('SET auth.mode strict', 'set(key=auth.mode, value=strict)'),
    ('SET auth.note "a.b"', 'set(key=auth.note, value="a.b")'),
    ('SET billing.owner auth.owner', 'copy(key=billing.owner, from=auth.owner)'),
    ('DEL auth.region', 'delete(key=auth.region)'),
    ('INHERIT gateway.region auth.region', 'derive(dst=gateway.region, src=auth.region)'),
    ('INHERIT auth.timeout_ms auth.timeout_ms +100 CAP 900', 'derive(dst=auth.timeout_ms, src=auth.timeout_ms, add=100, max=900)'),
    ('FUSE total.retries auth.retries search.retries CAP 8', 'sum_into(dst=total.retries, a=auth.retries, b=search.retries, max=8)'),
    ('SCALE search.retries 0.5', 'multiply(key=search.retries, factor=0.5)'),
    ('SCALE search.retries 2 CAP 9', 'multiply(key=search.retries, factor=2, max=9)'),
    ('ROUTE auth.region = eu-west : auth.log debug | info', 'select_if(cond_key=auth.region, equals=eu-west, dst=auth.log, then=debug, else=info)'),
    ('REHOST owner chen bruno', 'reassign_where(field=owner, from=chen, to=bruno)'),
    ('FLOW retries OVER owner chen +1 CAP 9', 'derive_where(field=retries, cond_field=owner, equals=chen, add=1, max=9)'),
]


@pytest.mark.parametrize("rsos,core", PAIRS)
def test_same_ir_both_syntaxes(rsos, core):
    a, b = compile_rsos(rsos), parse_core(core)
    assert ir_digest(a) == ir_digest(b), (a, b)
    assert execute(S, parse_ops(rsos)) == execute_ir(S, b)


def test_whole_program_round_trip():
    rsos = "\n".join(r for r, _ in PAIRS[2:] if not r.startswith("DEL"))  # a whole program must be executable
    ir = compile_rsos(rsos)
    assert ir_digest(parse_core(to_core_text(ir))) == ir_digest(ir)
    assert execute(S, parse_ops(rsos)) == execute_ir(S, ir)


def test_ir_is_plain_json():
    ir = compile_rsos("\n".join(r for r, _ in PAIRS))
    assert json.loads(json.dumps(ir)) == ir


def test_ir_matches_schema():
    jsonschema = pytest.importorskip("jsonschema")
    import pathlib
    schema = json.loads((pathlib.Path(__file__).parents[2] / "spec/core/ir.schema.json").read_text())
    jsonschema.validate(compile_rsos("\n".join(r for r, _ in PAIRS)), schema)
