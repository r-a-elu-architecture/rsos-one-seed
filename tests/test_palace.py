import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import pytest
from rsoslang import compile_source
from rsoslang import palace as P

BOOK = open(os.path.join(ROOT, "examples", "robot_head.rsl"), encoding="utf-8").read().rstrip("\n")


def test_symbol_opens_book_exactly():
    pal = P.Palace({"robot_head": BOOK})
    v = BOOK.replace('CUE eagle CODE "-.."', 'CUE eagle CODE "--"')
    msg = P.encode(pal, "robot_head", v)
    assert len(msg) < len(v) / 5
    assert compile_source(P.decode(pal, msg)).digest() == compile_source(v).digest()


def test_green_dot_detects_drift_and_light_heals():
    pal = P.Palace({"robot_head": BOOK})
    v = BOOK.replace("SCENARIOS 3", "SCENARIOS 4")
    msg = P.encode(pal, "robot_head", v)
    drifted = BOOK.replace("USE STATE eagle", "USE STATE owl")
    with pytest.raises(P.Drift):
        P.decode(P.Palace({"robot_head": drifted}), msg)
    healed, cost = P.heal(BOOK, drifted)
    assert healed == BOOK and cost < len(BOOK)
    assert P.decode(P.Palace({"robot_head": healed}), msg) == v


def test_palace_example_compiles():
    r = compile_source(open(os.path.join(ROOT, "examples", "palace.rsl"), encoding="utf-8").read())
    assert r.ok
