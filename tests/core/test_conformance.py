"""RSOS Core v1 conformance: one test per operation and function (spec/core/STATE_OPS.md, registry/operators.json).
An implementation of Core v1 conforms if it passes these tests through execute_ir with the same results."""
import hashlib
import json

import pytest

from rsoslang.core import Ledger, OpError, execute_ir, parse_core, state_digest

S = {"auth.timeout_ms": "700", "auth.retries": "3", "search.retries": "6", "auth.owner": "chen",
     "search.owner": "chen", "cache.owner": "dara", "auth.region": "eu-west", "auth.note": "text"}


def run(core_text, state=S):
    return execute_ir(state, parse_core(core_text))


def code_of(core_text, state=S):
    with pytest.raises(OpError) as e:
        run(core_text, state)
    return e.value.code


def test_set():
    assert run('set(key=auth.mode, value=strict)')["auth.mode"] == "strict"
    assert run('set(key=auth.note, value="a.b")')["auth.note"] == "a.b"  # set is always literal
    assert run('set(key=auth.note, value="two words")')["auth.note"] == "two words"
    assert code_of("set(key=notakey, value=x)") == "E_NOT_KEY"


def test_copy():
    assert run("copy(key=billing.owner, from=auth.owner)")["billing.owner"] == "chen"
    assert code_of("copy(key=billing.owner, from=nobody.owner)") == "E_MISSING_KEY"


def test_delete():
    assert "auth.note" not in run("delete(key=auth.note)")
    assert code_of("delete(key=auth.nothing)") == "E_MISSING_KEY"


def test_derive():
    assert run("derive(dst=gateway.region, src=auth.region)")["gateway.region"] == "eu-west"  # plain copy of text
    assert run("derive(dst=auth.timeout_ms, src=auth.timeout_ms, add=100)")["auth.timeout_ms"] == "800"
    assert run("derive(dst=auth.retries, src=auth.retries, add=9, max=9)")["auth.retries"] == "9"
    assert run("derive(dst=auth.retries, src=auth.retries, add=-1)")["auth.retries"] == "2"
    assert code_of("derive(dst=a.b, src=auth.missing, add=1)") == "E_MISSING_KEY"
    assert code_of("derive(dst=a.b, src=auth.region, add=1)") == "E_NOT_INTEGER"


def test_sum_into():
    assert run("sum_into(dst=total.retries, a=auth.retries, b=search.retries)")["total.retries"] == "9"
    assert run("sum_into(dst=total.retries, a=auth.retries, b=search.retries, max=8)")["total.retries"] == "8"
    assert code_of("sum_into(dst=t.x, a=auth.retries, b=auth.region)") == "E_NOT_INTEGER"


def test_multiply():
    assert run("multiply(key=search.retries, factor=2)")["search.retries"] == "12"
    assert run("multiply(key=search.retries, factor=2, max=9)")["search.retries"] == "9"
    assert run("multiply(key=search.retries, factor=0.5)")["search.retries"] == "3"
    assert code_of("multiply(key=auth.retries, factor=0.5)") == "E_FRACTION"
    assert code_of("multiply(key=auth.region, factor=2)") == "E_NOT_INTEGER"


def test_select_if():
    assert run("select_if(cond_key=auth.region, equals=eu-west, dst=auth.log, then=debug, else=info)")["auth.log"] == "debug"
    assert run("select_if(cond_key=auth.region, equals=us-east, dst=auth.log, then=debug, else=info)")["auth.log"] == "info"
    assert code_of("select_if(cond_key=auth.none, equals=x, dst=auth.log, then=a, else=b)") == "E_MISSING_KEY"


def test_reassign_where():
    out = run("reassign_where(field=owner, from=chen, to=bruno)")
    assert out["auth.owner"] == out["search.owner"] == "bruno" and out["cache.owner"] == "dara"
    assert run("reassign_where(field=owner, from=nobody, to=bruno)") == S  # no match is not an error


def test_derive_where():
    """FLOW (C-009, specified 19 Nov in experiments/PREREGISTRATION_SC2.md before it was built)."""
    st = {"cup.x": "3", "cup.owner": "rover", "box.x": "8", "box.owner": "rover", "pan.x": "1", "pan.owner": "drone",
          "tag.owner": "rover"}
    out = run("derive_where(field=x, cond_field=owner, equals=rover, add=2, max=9)", st)
    assert out == {**st, "cup.x": "5", "box.x": "9"}       # every match moves, capped; pan untouched; tag has no x
    assert run("derive_where(field=x, cond_field=owner, equals=nobody, add=1)", st) == st  # no match is not an error
    assert code_of("derive_where(field=owner, cond_field=owner, equals=rover, add=1)", st) == "E_NOT_INTEGER"


def test_parse_errors():
    assert code_of("rename(key=a.b)") == "E_PARSE"
    assert code_of("set(key=a.b)") == "E_PARSE"
    assert code_of("set(key=a.b, value=x, extra=1)") == "E_PARSE"
    assert code_of("derive(dst=a.b, src=auth.retries, add=one)") == "E_PARSE"
    with pytest.raises(OpError) as e:
        execute_ir(S, [])
    assert e.value.code == "E_EMPTY"


def test_steps_are_atomic():
    led = Ledger(S)
    before = led.dot
    r = led.apply("SET auth.mode strict\nDEL auth.nothing")
    assert not r["ok"] and r["code"] == "E_MISSING_KEY" and led.dot == before and "auth.mode" not in led.state


def test_state_digest_vectors():
    assert state_digest({}) == "44136fa355b3"
    assert state_digest({"a.b": "1"}) == "737a6b803cf8"
    assert state_digest({"a.b": "1", "c.d": "two words"}) == "daae52c2238c"
    assert state_digest({"k.x": "é"}) == "04d8868891da"
    canon = json.dumps({"a.b": "1"}, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    assert state_digest({"a.b": 1}) == hashlib.sha256(canon.encode()).hexdigest()[:12]


def test_reconcile():
    led = Ledger(S)
    same = led.sync(dict(S))
    assert same["healed"] == [] and same["model_calls"] == 0
    drifted = dict(S, **{"auth.retries": "4"}); drifted.pop("auth.note")
    r = led.sync(drifted)
    assert r["healed"] == ["auth.note", "auth.retries"] and r["state"] == led.state and r["model_calls"] == 0
