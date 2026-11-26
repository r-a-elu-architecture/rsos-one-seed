"""Program ⇄ painting: gestures compile to exact, place-dependent program changes."""

from rsoslang.agents.workflow import build
from rsoslang.agents.tickets import make_tickets
from rsoslang.painting.scene import apply, encode, render_svg, header

DATA = make_tickets(120, 5, typo_rate=0.3, unseen_rate=0.3)


def test_header_compiles_and_declares_places():
    from rsoslang import compile_source
    res = compile_source(header(build()))
    assert res.ok
    assert "classify.brain" in res.ir["parts"]


def test_pierce_places_go_to_the_right_place():
    wf, _ = apply(build(), "PIERCE spell_corrector THROUGH classify.head\nPIERCE cache THROUGH memory.heart\n")
    assert [g.name for g in wf.nodes["classify"].head] == ["spell_corrector"]
    assert [g.name for g in wf.nodes["memory"].heart] == ["cache"]


def test_the_original_workflow_is_untouched():
    base = build()
    apply(base, "PIERCE spell_corrector THROUGH classify.brain\nSHIFT act TO grey\n")
    assert not base.nodes["act"].sandboxed and len(base.nodes["classify"].knowledge["lexicon"]["billing"]) == 5


def test_place_decides_and_near_does_not_touch_the_node():
    base = build()
    r0 = base.evaluate(DATA)
    head = apply(base, "PIERCE spell_corrector THROUGH classify.head\n")[0].evaluate(DATA)
    near = apply(base, "PLACE spell_corrector NEAR classify\n")[0].evaluate(DATA)
    assert head["accuracy"] > r0["accuracy"]
    assert near["errors"].get("classify") == r0["errors"].get("classify")


def test_grey_contains_crashes():
    r = apply(build(), "SHIFT act TO grey\n")[0].evaluate(DATA)
    assert r["crashed"] == 0


def test_meaningless_place_is_reported():
    _, changes = apply(build(), "PIERCE fast_retry THROUGH classify.brain\n")
    assert "no meaning" in changes[0]


def test_painting_renders():
    wf = build()
    svg = render_svg(encode(wf, wf.evaluate(DATA)), "t")
    assert svg.startswith("<svg") and "classify" in svg
