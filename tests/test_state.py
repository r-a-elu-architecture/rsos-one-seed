"""RSOS State Runtime: operations, the green dot, heal, and the whole-task plan."""
from rsoslang.state import Ledger, OpError, dot, execute, parse_ops, parse_plan, plan_prompt

BASE = {"auth.timeout_ms": "700", "auth.retries": "3", "search.retries": "6", "auth.owner": "chen",
        "auth.region": "eu-west", "gateway.region": "eu-west", "billing.log_level": "warn"}


def test_operations_are_computed_by_the_runtime():
    st = execute(BASE, parse_ops("FUSE auth.retries auth.retries search.retries CAP 8\n"
                                 "INHERIT auth.timeout_ms auth.timeout_ms +100\nSCALE search.retries 2 CAP 10\n"
                                 "ROUTE auth.owner = chen : billing.log_level error | info\nREHOST region eu-west us-east\n"
                                 "SET gateway.owner auth.owner\nDEL auth.retries"))
    assert st["auth.timeout_ms"] == "800" and st["search.retries"] == "10" and st["billing.log_level"] == "error"
    assert st["auth.region"] == "us-east" and st["gateway.region"] == "us-east" and st["gateway.owner"] == "chen"
    assert "auth.retries" not in st


def test_prose_is_ignored_and_bad_operations_are_rejected_with_a_reason():
    assert parse_ops("Here you go:\nSET auth.owner kim\nThanks") == [("SET", "auth.owner", "kim")]
    for bad, why in [("DEL nope.key", "no such key"), ("FUSE a.x auth.owner auth.retries", "whole number")]:
        try:
            execute(BASE, parse_ops(bad)); assert False
        except OpError as e:
            assert why in str(e)


def test_failed_step_leaves_state_unchanged():
    led = Ledger(BASE); before = led.dot
    r = led.apply("DEL nope.key")
    assert not r["ok"] and led.dot == before


def test_sync_heals_drift_with_zero_model_calls():
    led = Ledger(BASE); led.apply("SET auth.owner kim")
    worker = dict(led.state); worker["auth.timeout_ms"] = "999"; del worker["auth.region"]
    r = led.sync(worker)
    assert r["healed"] == ["auth.region", "auth.timeout_ms"] and r["state"] == led.state and r["model_calls"] == 0
    assert led.sync(led.state)["healed"] == []


def test_whole_task_plan_round_trip():
    p = plan_prompt(["Raise auth timeout by 100", "Remove auth retries"], BASE)
    assert "#0" in p["user"] and "auth.timeout_ms" in p["user"] and "RSOS operations" in p["system"]
    plan = parse_plan("#0\nINHERIT auth.timeout_ms auth.timeout_ms +100\n#1\nDEL auth.retries\n")
    led = Ledger(BASE); out = led.apply_plan(plan)
    assert out["failed"] == [] and led.state["auth.timeout_ms"] == "800" and "auth.retries" not in led.state


def test_dot_is_order_independent():
    assert dot({"a.b": "1", "c.d": "2"}) == dot({"c.d": "2", "a.b": "1"})


def test_set_from_a_missing_key_is_an_error_not_literal_text():
    try:
        execute(BASE, parse_ops("SET auth.copy search.timeout_ms")); assert False
    except OpError as e:
        assert "does not exist" in str(e)
    led = Ledger(BASE); before = led.dot
    assert not led.apply("SET auth.copy search.timeout_ms")["ok"] and led.dot == before


def test_quoted_set_value_is_literal_text():
    assert execute(BASE, parse_ops('SET auth.note "auth.owner"'))["auth.note"] == "auth.owner"
    assert execute(BASE, parse_ops("SET auth.note 'see search.retries'"))["auth.note"] == "see search.retries"
    assert execute(BASE, parse_ops("SET auth.note auth.owner"))["auth.note"] == "chen"


def test_scale_to_a_fraction_is_rejected():
    try:
        execute(BASE, parse_ops("SCALE auth.retries 1.5")); assert False
    except OpError as e:
        assert "not a whole number" in str(e)
    assert execute(BASE, parse_ops("SCALE search.retries 1.5"))["search.retries"] == "9"


def test_dot_cannot_be_forged_by_a_value_with_a_line_break():
    assert dot({"a.b": "1\nc.d=2"}) != dot({"a.b": "1", "c.d": "2"})
    assert dot({"a.b": 1}) == dot({"a.b": "1"})


def test_numbers_and_versions_stay_literal_values():
    st = execute(BASE, parse_ops("SET auth.ratio 4.5\nSET auth.version v1.2"))
    assert st["auth.ratio"] == "4.5" and st["auth.version"] == "v1.2"


def test_unquoted_dotted_text_must_be_quoted():
    try:
        execute(BASE, parse_ops("SET auth.host api.example")); assert False
    except OpError as e:
        assert "quote the value" in str(e)
    assert execute(BASE, parse_ops('SET auth.host "api.example"'))["auth.host"] == "api.example"
    assert execute(BASE, parse_ops('SET auth.note "two words here"'))["auth.note"] == "two words here"


def test_scale_by_a_half_is_exact_or_rejected():
    assert execute(BASE, parse_ops("SCALE search.retries 0.5"))["search.retries"] == "3"
    try:
        execute(BASE, parse_ops("SCALE auth.retries 0.5")); assert False
    except OpError as e:
        assert "not a whole number" in str(e)


def test_grammar_tells_the_planner_to_quote_dotted_text():
    from rsoslang.state import GRAMMAR
    assert 'SET k "a.b"' in GRAMMAR
