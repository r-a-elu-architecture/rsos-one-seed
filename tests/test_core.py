"""Day 1 gate: parser, types, meanings, hosts and diagnostics."""

import glob
import json
import os

import pytest

from rsoslang import compile_source, tokenize
from rsoslang.grammar import STATEMENTS
from rsoslang.meanings import CORE

ROOT = os.path.dirname(os.path.dirname(__file__))
HEAD = "LANGUAGE RSOS 0.2\nWORLD w\n"


def codes(src):
    return [d.code for d in compile_source(src).diagnostics]


def ops(src):
    return compile_source(src).ir["ops"]


def meaning(src, op_index=-1, k=-1):
    return ops(src)[op_index]["meanings"][k]


# ---- lexer and parser ---------------------------------------------------------------------------
def test_tokenizer_symbols_strings_comments():
    toks = tokenize('CUE eagle CODE "-.." CHANNEL kinesthetic  # comment\nROUTE tv BY a -> b ; c -> d')
    assert [t.value for t in toks[0][1]] == ["CUE", "eagle", "CODE", "-..", "CHANNEL", "kinesthetic"]
    assert [t.kind for t in toks[1][1]][4:8] == ["ARROW", "WORD", "SYM", "WORD"]


@pytest.mark.parametrize("path", sorted(glob.glob(os.path.join(ROOT, "examples", "*.rsl"))))
def test_examples_compile_without_errors(path):
    res = compile_source(open(path, encoding="utf-8").read())
    assert res.ok, [str(d) for d in res.errors]
    assert res.ir["ops"]


def test_every_statement_example_parses():
    """The doc line of every statement is a valid statement (checked for form only)."""
    from rsoslang.parser import parse
    for s in STATEMENTS.values():
        example = s.doc.split(" (")[0].split(" | ")[0]
        prog = parse(example)
        assert not [d for d in prog.diagnostics if d.is_error], (s.kw, example, [str(d) for d in prog.diagnostics])


def test_header_and_world_required():
    assert "E001_HEADER" in codes("WORLD w\n")
    assert "E001_HEADER" in codes("LANGUAGE RSOS 0.1\nWORLD w\n")
    assert "E002_WORLD" in codes("LANGUAGE RSOS 0.2\nOBJECT a\n")
    assert "E002_WORLD" in codes(HEAD + "WORLD v\n")


def test_syntax_errors():
    assert "E008_OPERATOR" in codes(HEAD + "TELEPORT a\n")
    assert "E005_SYNTAX" in codes(HEAD + "OBJECT a\nPIERCE a\n")                 # THROUGH required
    assert "E007_VALUE" in codes(HEAD + "OBJECT a\nOBJECT b\nPIERCE a THROUGH b FROM sideways\n")
    assert "E007_VALUE" in codes(HEAD + "OBJECT a\nOBJECT b\nPIERCE a THROUGH b DEPTH 2.5\n")
    assert "E004_PATH" in codes(HEAD + "OBJECT a.b\n")
    assert "E005_SYNTAX" in codes(HEAD + "OBJECT a KIND x KIND y\n")


def test_names_declared_before_use_and_no_duplicates():
    assert "E003_UNKNOWN_ENTITY" in codes(HEAD + "OBJECT a\nPIERCE a THROUGH ghost\n")
    assert "E009_DUPLICATE" in codes(HEAD + "OBJECT a\nOBJECT a\n")
    assert "W002_IMPLICIT_PART" in codes(HEAD + "OBJECT car\nENTER car.seat\n")
    assert "W002_IMPLICIT_PART" not in codes(HEAD + "OBJECT car\nPART car.seat\nENTER car.seat\n")


def test_descendants_carry_lineage():
    res = compile_source(HEAD + "OBJECT a\nOBJECT b\nPIERCE a THROUGH b AS ab\nPIERCE ab THROUGH b AS abb\n")
    assert res.ok
    assert res.ir["lineage"][0] == {"child": "ab", "op": "PIERCE", "parents": ["a", "b"], "line": 5}
    assert res.ir["entities"]["abb"]["parents"] == ["ab", "b"]


# ---- meanings: core, binding, search --------------------------------------------------------------
def test_core_contact_table_is_the_d80_default():
    assert CORE["contact.top"][0] == "supervisory_entry"
    assert CORE["contact.side"][0] == "lateral"
    assert CORE["contact.through"][0] == "multi_layer"
    m = ops(HEAD + "OBJECT a\nOBJECT b\nTOUCH a ON b AT top\n")[-1]["meanings"][0]
    assert (m["key"], m["value"], m["source"]) == ("contact.top", "supervisory_entry", "core")


def test_pierce_resolves_method_and_side():
    ms = ops(HEAD + "OBJECT a\nOBJECT b\nPIERCE a THROUGH b FROM left\n")[-1]["meanings"]
    assert [(m["key"], m["value"]) for m in ms] == [("contact.through", "multi_layer"), ("contact.left", "lateral")]


def test_binding_overrides_core_only_in_its_scope():
    src = HEAD + ("HOST p KIND human STATES eagle, owl\nUSE HOST p\nOBJECT a\nOBJECT b\n"
                  "MEANING contact.top = local_contact SCOPE state IN eagle\n"
                  "TOUCH a ON b AT top\nUSE STATE eagle\nTOUCH a ON b AT top\nUSE STATE owl\nTOUCH a ON b AT top\n")
    vals = [(o["meanings"][0]["value"], o["meanings"][0]["source"]) for o in ops(src) if o["op"] == "touch"]
    assert vals == [("supervisory_entry", "core"), ("local_contact", "binding"), ("supervisory_entry", "core")]


def test_most_specific_scope_wins():
    src = HEAD + ("PROFILE owner\nHOST p KIND human STATES eagle\nUSE HOST p\nUSE PROFILE owner\nOBJECT a\nOBJECT b\n"
                  "MEANING contact.top = profile_meaning SCOPE profile IN owner\n"
                  "MEANING contact.top = host_meaning SCOPE host IN p\n"
                  "MEANING contact.top = state_meaning SCOPE state IN eagle\n"
                  "TOUCH a ON b AT top\nUSE STATE eagle\nTOUCH a ON b AT top\n")
    vals = [o["meanings"][0]["value"] for o in ops(src) if o["op"] == "touch"]
    assert vals == ["host_meaning", "state_meaning"]


def test_ambiguous_binding_is_an_error():
    src = HEAD + ("MEANING contact.top = x SCOPE world IN w\nMEANING contact.top = y SCOPE world IN w\n")
    assert "E010_AMBIGUITY" in codes(src)
    src_same = HEAD + ("MEANING contact.top = x SCOPE world IN w\nMEANING contact.top = x SCOPE world IN w\n")
    assert "E010_AMBIGUITY" not in codes(src_same)


def test_open_meaning_needs_binding_or_search():
    base = HEAD + "OBJECT a\nOBJECT b\n"
    assert "E017_MEANING" in codes(base + "PIERCE a THROUGH b FROM bottom\n")
    c = codes(base + "SEARCH contact.bottom OVER lateral, local_contact\nPIERCE a THROUGH b FROM bottom\n")
    assert "E017_MEANING" not in c and "W001_OPEN_MEANING" in c
    m = meaning(base + "SEARCH contact.bottom OVER lateral, local_contact\nPIERCE a THROUGH b FROM bottom\n")
    assert m["source"] == "search" and m["candidates"] == ["lateral", "local_contact"]


def test_binding_beats_search_beats_core():
    base = HEAD + "OBJECT a\nOBJECT b\nSEARCH contact.top OVER u, v\n"
    assert meaning(base + "TOUCH a ON b AT top\n")["source"] == "search"
    m = meaning(base + "MEANING contact.top = z SCOPE world IN w\nTOUCH a ON b AT top\n")
    assert (m["value"], m["source"]) == ("z", "binding")


def test_unknown_meaning_key_rejected():
    assert "E017_MEANING" in codes(HEAD + "MEANING weather.top = x SCOPE world IN w\n")


def test_flow_selection_and_colour_meanings():
    m = meaning(HEAD + "OBJECT identity\nBEAM identity\n")
    assert (m["key"], m["value"]) == ("flow.down", "lands_on_all_lower")
    m = meaning(HEAD + "OBJECT heart\nFLOW heart DIRECTION horizontal\n")
    assert m["value"] == "spread_across"
    m = meaning(HEAD + "OBJECT door\nSELECT door WHOLE\n")
    assert m["value"] == "full_module"
    m = meaning(HEAD + "OBJECT p\nSHIFT p FROM black TO grey\n")
    assert m["value"] == "good_and_bad_with_protection"
    m = meaning(HEAD + "OBJECT sol\nCOLOUR sol red STATE drive\n")
    assert (m["value"], m["source"]) == ("drive", "declared")


# ---- hosts -----------------------------------------------------------------------------------------
def test_cue_channel_must_exist_on_host():
    src = HEAD + "HOST b KIND bacterium CHANNELS light, chemical\nUSE HOST b\n"
    assert "E016_HOST" in codes(src + 'CUE calm CODE "-" CHANNEL kinesthetic\n')
    assert "E016_HOST" not in codes(src + 'CUE seek CODE "-" CHANNEL light\n')
    assert "W003_NO_HOST" in codes(HEAD + 'CUE calm CODE "-" CHANNEL kinesthetic\n')


def test_mental_model_needs_a_reasoning_host():
    body = "OBJECT robot\nPART robot.head\nMODEL robot.head = associated + confidence\n"
    assert "E016_HOST" in codes(HEAD + "HOST pl KIND planet\nUSE HOST pl\n" + body)
    assert "E016_HOST" not in codes(HEAD + "HOST p KIND human\nUSE HOST p\n" + body)
    assert "E016_HOST" not in codes(HEAD + "HOST g KIND agent\nUSE HOST g\n" + body)


def test_state_must_belong_to_host():
    assert "E016_HOST" in codes(HEAD + "HOST p KIND human STATES eagle\nUSE HOST p\nUSE STATE tiger\n")


def test_model_components_are_kept_in_order():
    o = ops(HEAD + "HOST p KIND human\nUSE HOST p\nOBJECT robot\nPART robot.head\n"
                   "MODEL robot.head = associated + confidence + analogical_reasoning FOR decision\n")[-1]
    assert o["args"]["components"] == ["associated", "confidence", "analogical_reasoning"]
    assert o["clauses"]["for"] == "decision" and "U63" in o["refs"]


# ---- reproducibility and register coverage -------------------------------------------------------
def test_ir_digest_is_deterministic():
    src = open(os.path.join(ROOT, "examples", "sol_remote.rsl"), encoding="utf-8").read()
    assert compile_source(src).digest() == compile_source(src).digest()


def test_register_coverage_of_owner_operators():
    reg = json.load(open(os.path.join(ROOT, "src", "rsoslang", "data", "register.json"), encoding="utf-8"))
    ids = {r["id"] for r in reg}
    covered = {r for s in STATEMENTS.values() for r in s.refs}
    assert covered <= ids, covered - ids
    # Every operator executed with its own result in chats 1-3 has a statement (TABLES_COMPARISON §1).
    for must in ["U17", "U18", "U28", "U36", "U38", "U42", "U43", "U44", "U46", "U47"]:
        assert must in covered, must
    # The healing and state family is in the language (U1-U15).
    for must in ["U1", "U2", "U3", "U4", "U5", "U6", "U7", "U8", "U9", "U11", "U14"]:
        assert must in covered, must


def test_unit_fields_on_transfer_and_contact_ops():
    o = ops(HEAD + "HOST p KIND human\nUSE HOST p\nOBJECT a\nOBJECT b\nPIERCE a THROUGH b.core FROM top DEPTH 3 AS ab\n")[-1]
    u = o["unit"]
    assert (u["source"], u["target"], u["path"], u["method"], u["host"]) == ("a", "b.core", ["core"], "pierce", "p")
    assert u["geometry"] == {"from": "top", "depth": 3}
    assert u["relation"][0]["child"] == "ab"


def test_all_register_rows_are_linked():
    reg = json.load(open(os.path.join(ROOT, "src", "rsoslang", "data", "register.json"), encoding="utf-8"))
    covered = {r for s in STATEMENTS.values() for r in s.refs}
    assert {r["id"] for r in reg} == covered
