"""The statement table: grammar, register links and host rules for every statement.

Each statement is `KEYWORD positional... [CLAUSE value]...`.
`refs` link a statement to the unified operator register (the unified operator register in the private design record,
mirrored in data/register.json). `family` follows the register's families.

Argument kinds:
  name      a new identifier (no dots)
  path      a reference to a declared entity, dotted for parts (house.door.middle)
  word      any identifier
  num, int  numbers
  nums      comma-separated numbers
  string    quoted text
  value     number, string or identifier
  list      comma-separated identifiers or paths
  comp      composition with + (associated + confidence + analogical_reasoning)
  cases     state -> target ; state -> target
  enum:a|b  one of the listed words (case-insensitive)
"""

from dataclasses import dataclass, field

SIDES = "top|bottom|left|right|front|back|side|surface|edge|interior|inside|outside|centre|center"
DIRECTIONS = "vertical|horizontal|outward|inward|down|up|across"
SHAPES = "triangle|square|circle|point"
SCOPES = "state|host|world|profile"


@dataclass
class Stmt:
    kw: str
    family: str
    refs: list
    pos: list = field(default_factory=list)          # [(name, kind)]
    clauses: dict = field(default_factory=dict)      # CLAUSE -> kind
    required: list = field(default_factory=list)     # clause names that must be present
    declares: str = ""                                # entity class this statement declares
    meaning: str = ""                                 # meaning-key prefix this statement resolves
    host_rule: str = ""                               # name of a host check in semantics.HOST_RULES
    doc: str = ""


S = []


def st(*a, **k):
    S.append(Stmt(*a, **k))


# ---- header, world, hosts, entities ---------------------------------------------------------
st("LANGUAGE", "header", ["U79"], pos=[("name", "word"), ("version", "value")], doc="LANGUAGE RSOS 0.2")
st("WORLD", "declare", [], pos=[("name", "name")], declares="world", doc="WORLD lab")
st("HOST", "declare", ["U18", "U20"], pos=[("name", "name")],
   clauses={"KIND": "word", "CHANNELS": "list", "STATES": "list"}, declares="host",
   doc="HOST person KIND human CHANNELS visual, auditory, kinesthetic STATES eagle, owl")
st("PROFILE", "declare", [], pos=[("name", "name")], declares="profile", doc="PROFILE owner")
st("USE", "context", [], pos=[("scope", "enum:" + SCOPES), ("name", "word")],
   doc="USE HOST person | USE STATE eagle | USE PROFILE owner (sets the context for what follows)")
st("OBJECT", "declare", ["U16", "U70"], pos=[("name", "name")],
   clauses={"KIND": "word", "DOMAIN": "word", "IN": "path", "REPRESENTS": "value"}, declares="object",
   doc="OBJECT couch KIND furniture IN eagle REPRESENTS langgraph")
st("PLACE", "declare", ["U16", "U23"], pos=[("object", "path")],
   clauses={"X": "num", "Y": "num", "ROT": "num", "SIZE": "num", "NEAR": "path"},
   doc="PLACE painting_b X 1.5 Y 0 ROT 0 | PLACE spell_corrector NEAR classify")
st("PART", "declare", ["U45"], pos=[("path", "word")], clauses={"KIND": "word"}, declares="part",
   doc="PART car.seat KIND module")
st("PROPERTY", "declare", ["U17"], pos=[("path", "path"), ("_eq", "="), ("value", "value")],
   doc="PROPERTY sol.frequency = 392")
st("RELATION", "declare", ["U60"], pos=[("a", "path"), ("verb", "word"), ("b", "path")],
   doc="RELATION brain regulates heart")

# ---- mental-model construction (pillar 2) ---------------------------------------------------
st("HOUSE", "mental", ["U63"], pos=[("name", "name")], clauses={"FOR": "path"}, declares="house",
   doc="HOUSE mind FOR person")
st("ROOM", "mental", ["U64"], pos=[("name", "name")],
   clauses={"PERSPECTIVE": "word", "IN": "path"}, declares="room",
   doc="ROOM eagle PERSPECTIVE above IN mind")
st("MODEL", "mental", ["U63", "U72"], pos=[("part", "path"), ("_eq", "="), ("components", "comp")],
   clauses={"IN": "path", "FOR": "word"}, host_rule="mental_host",
   doc="MODEL robot.head = associated + confidence + analogical_reasoning IN eagle FOR decision")
st("DEDICATE", "mental", ["U65"], pos=[("object", "path")], clauses={"TO": "word"}, required=["TO"],
   doc="DEDICATE couch TO hypothesis_testing")
st("FORM", "mental", ["U66"], pos=[("object", "path")], clauses={"DIRECTIONS": "cases"}, required=["DIRECTIONS"],
   doc="FORM couch DIRECTIONS forward -> hypothesis ; backward -> contradiction ; up -> framing ; down -> operational_test")
st("MATERIAL", "mental", ["U67"], pos=[("object", "path"), ("_eq", "="), ("level", "value")],
   doc="MATERIAL couch = user_interface")
st("ANCHOR", "mental", ["U14", "U68"], pos=[("symbol", "path")], clauses={"TO": "path", "CHANNEL": "word"},
   required=["TO"], host_rule="channel", doc="ANCHOR eagle_calculator TO robot.head CHANNEL kinesthetic")
st("FUTUREPACE", "mental", ["U68"], pos=[("symbol", "path")], clauses={"SCENARIOS": "int"},
   doc="FUTUREPACE eagle_calculator SCENARIOS 3")
st("SCHEDULE", "mental", ["U68", "U83"], pos=[("name", "name")],
   clauses={"STATES": "list", "DURATIONS": "nums", "PULSE": "num", "REPEAT": "int", "CHANNEL": "word"},
   required=["STATES", "DURATIONS"], declares="schedule", host_rule="channel",
   doc="SCHEDULE eagle_drill STATES associated, eagle DURATIONS 300, 60 PULSE 60 REPEAT 3 CHANNEL kinesthetic")
st("IDENTITY", "mental", ["U63"], pos=[("host", "path"),
   ("level", "enum:mission|identity|values|beliefs|skills|behaviour|environment"), ("_eq", "="), ("value", "value")],
   doc='IDENTITY person mission = "healing and helping people grow" (the seven levels)')
st("ARCHETYPE", "mental", ["U75"], pos=[("name", "name")], clauses={"TACTON": "string", "LANGUAGE": "string", "SHADOW": "list"},
   declares="archetype", doc="ARCHETYPE lion (profile from the cue framework: virtues, language, shadow, tacton)")
st("PERSONA", "declare", ["U20"], pos=[("name", "name")],
   clauses={"AGE": "int", "ORGANS": "list", "GOAL": "word", "SOURCE": "enum:synthetic|consented"},
   declares="host", doc="PERSONA anna AGE 70 ORGANS heart_attack GOAL calm SOURCE synthetic (a built person, no real human)")
st("SELECTMODEL", "mental", ["U69"], pos=[("part", "path")], clauses={"BY": "enum:trigger|choice"},
   doc="SELECTMODEL robot.head BY choice (the control panel)")

# ---- scenes, colour, state, flows (chat 1 family I) -----------------------------------------
st("SCENE", "scene", ["U48", "U23"], pos=[("name", "name")], clauses={"ORDER": "list", "IN": "path", "LIGHT": "word"},
   declares="scene", meaning="scene", doc="SCENE painting ORDER mountains, sky, house, grass, car, road LIGHT engineering")
st("COLOUR", "state", ["U4", "U55"], pos=[("target", "path"), ("colour", "word")], clauses={"STATE": "word"},
   meaning="colour", doc="COLOUR sol red STATE drive")
st("SHIFT", "state", ["U4"], pos=[("target", "path")], clauses={"FROM": "word", "TO": "word"}, required=["TO"],
   meaning="colour", doc="SHIFT planet.surface FROM black TO grey (a state transition that changes the repertoire)")
st("HEAL", "state", ["U1", "U8"], pos=[("target", "path")], clauses={"BY": "path", "SCOPE": "enum:node|network|container|higher"},
   doc="HEAL country BY white_dragon.light SCOPE container")
st("BEAM", "state", ["U2"], pos=[("source", "path")], clauses={"DIRECTION": "enum:" + DIRECTIONS, "TO": "path", "BY": "path"},
   meaning="flow", doc="BEAM identity DIRECTION down (lands on all lower layers)")
st("FLOW", "state", ["U3", "U22"], pos=[("source", "path")], clauses={"DIRECTION": "enum:" + DIRECTIONS, "TO": "path"},
   required=["DIRECTION"], meaning="flow", doc="FLOW heart DIRECTION horizontal TO body")
st("ROUTE", "state", ["U5"], pos=[("object", "path")], clauses={"BY": "cases"}, required=["BY"],
   doc="ROUTE tv BY slumped -> problems ; agency -> communication_strategy")
st("RESONATE", "state", ["U6"], pos=[("a", "path")], clauses={"WITH": "path"}, required=["WITH"],
   doc="RESONATE bones WITH rocket_heart")
st("BALL", "state", ["U7"], pos=[("trigger", "word")], clauses={"AS": "name", "COLOUR": "word"}, declares="object",
   doc="BALL family_sounds AS ball1 COLOUR orange")
st("COMPRESS", "state", ["U8"], pos=[("items", "list")], clauses={"AS": "name"}, required=["AS"], declares="object",
   doc="COMPRESS s1, s2, s3 AS lion_symbol")
st("WEIGHT", "state", ["U9"], pos=[("target", "path"), ("w", "num")], doc="WEIGHT pinky 0.9")
st("RESCRIPT", "state", ["U11", "U12", "U13"], pos=[("target", "path")], clauses={"WITH": "path", "WHEN": "word"},
   doc="RESCRIPT earlier_self WITH lion.paw WHEN tension")

# ---- contact (family III) --------------------------------------------------------------------
CONTACT = {"AT": "enum:" + SIDES, "FROM": "enum:" + SIDES, "DEPTH": "int", "AS": "name", "INTO": "path",
           "MODE": "enum:view|system"}
st("TOUCH", "contact", ["U26"], pos=[("source", "path")], clauses={**CONTACT, "ON": "path"}, required=["ON"],
   meaning="contact", doc="TOUCH sol ON remote AT top")
st("ATTACH", "contact", ["U27"], pos=[("source", "path")], clauses={**CONTACT, "TO": "path"}, required=["TO"],
   meaning="contact", doc="ATTACH sensor TO robot AT edge AS robot2")
st("PIERCE", "contact", ["U28", "U29", "U30", "U31"], pos=[("source", "path")], clauses={**CONTACT, "THROUGH": "path"},
   required=["THROUGH"], meaning="contact", doc="PIERCE sol THROUGH remote FROM top DEPTH 3 AS remote_sol")
st("PASS", "contact", ["U32"], pos=[("source", "path")], clauses={**CONTACT, "THROUGH": "path"}, required=["THROUGH"],
   meaning="contact", doc="PASS virus.particles THROUGH wall INTO langgraph.node2")
st("WRAP", "contact", ["U33"], pos=[("source", "path")], clauses={**CONTACT, "AROUND": "path"}, required=["AROUND"],
   meaning="contact", doc="WRAP shell AROUND agent AS guarded_agent")
st("MERGE", "contact", ["U35"], pos=[("source", "path")], clauses={**CONTACT, "WITH": "path"}, required=["WITH"],
   meaning="contact", doc="MERGE regulator WITH agent.controller AS controller2")
st("SPLIT", "contact", ["U34"], pos=[("target", "path")], clauses={"INTO": "list"}, required=["INTO"],
   doc="SPLIT remote INTO a, b")
st("DOT", "contact", ["U36"], pos=[("function", "path")], clauses={"INTO": "path", "AS": "name"}, required=["INTO"],
   doc="DOT immune_memory INTO langgraph.router AS dot1 (adds; does not replace)")
st("MOVE", "contact", ["U42", "U37"], pos=[("source", "path")], clauses={"ONTO": "path", "AT": "enum:" + SIDES, "AS": "name"},
   required=["ONTO"], meaning="contact", doc="MOVE painting_b ONTO painting_a")
st("ROTATE", "contact", ["U38"], pos=[("target", "path")], clauses={"BY": "num", "RELATIVE": "path", "AS": "name"},
   doc="ROTATE painting_b BY 90 RELATIVE painting_a")
st("FLIP", "contact", ["U39"], pos=[("target", "path")], clauses={"AS": "name"}, doc="FLIP painting_b")
st("OVERLAY", "contact", ["U40"], pos=[("source", "path")], clauses={"ON": "path", "SHOW": "enum:half|full|part", "AS": "name"},
   required=["ON"], doc="OVERLAY painting_b ON painting_a SHOW half")
st("PROTRUDE", "contact", ["U41"], pos=[("target", "path")], clauses={"INTO": "path"}, required=["INTO"],
   doc="PROTRUDE painting_ab.middle INTO room")
st("FUSE", "contact", ["U60"], pos=[("a", "path")], clauses={"WITH": "path", "AS": "name"}, required=["WITH", "AS"],
   doc="FUSE bacterium WITH liver AS guardian")

# ---- selection and navigation (family IV) ---------------------------------------------------
st("SELECT", "select", ["U43"], pos=[("target", "path"), ("extent", "enum:whole|part")], clauses={"AS": "name"},
   meaning="select", doc="SELECT house.door WHOLE | SELECT house.door.middle PART")
st("REGION", "select", ["U44"], pos=[("name", "name")],
   clauses={"SHAPE": "enum:" + SHAPES, "CENTER": "path", "SIZE": "num", "INCLUDES": "list"}, required=["SHAPE", "CENTER"],
   declares="region", doc="REGION r1 SHAPE triangle CENTER car SIZE 0.4 INCLUDES engine, seat, window")
st("ENTER", "select", ["U45", "U58"], pos=[("target", "path")], clauses={"DEPTH": "int", "MODE": "enum:view|system"},
   doc="ENTER car.seat DEPTH 2 (goes 3D: inside and hidden parts)")
st("ZOOM", "select", ["U46"], pos=[("direction", "enum:in|out"), ("target", "path")], clauses={"MODE": "enum:view|system"},
   doc="ZOOM in couch.spring")
st("LINE", "select", ["U47", "U53"], pos=[("name", "name")],
   clauses={"THROUGH": "list", "FROM": "enum:" + SIDES, "PACE": "list", "PAUSE": "list", "IN": "path"},
   required=["THROUGH"], declares="line", doc="LINE l1 THROUGH mountain.top, house.door.middle, car.seat PAUSE car.seat")
st("WIDEN", "select", ["U54"], pos=[("line", "path")], clauses={"TO": "enum:tube|volume", "RADIUS": "num"},
   required=["TO"], doc="WIDEN l1 TO tube RADIUS 0.2")
st("TIME", "select", ["U50", "U52", "U56"], pos=[("target", "path"), ("action", "enum:play|pause|slow|fast|rewind|tempo|cut|branch")],
   clauses={"AT": "value", "RATE": "num", "AS": "name", "MODE": "enum:view|system"},
   doc="TIME workflow_video slow RATE 0.25 MODE system")

# ---- host and transfer (family II) ----------------------------------------------------------
st("TRANSPLANT", "host", ["U17", "U107"], pos=[("bundle", "path")],
   clauses={"TO": "path", "AS": "name", "FROM": "word", "DEPTH": "enum:surface|inside|structure", "ORDER": "int", "GAIN": "word"},
   required=["TO"],
   doc="TRANSPLANT rocket TO body.heart AS rocket_heart (the whole property bundle travels); knowing form (D84): "
       "TRANSPLANT turbopump TO engine.heart FROM rocketry DEPTH structure ORDER 1 GAIN efficiency")
st("REHOST", "host", ["U18"], pos=[("bundle", "path")], clauses={"IN": "path", "AS": "name"}, required=["IN"],
   doc="REHOST rocket_heart IN planet AS planet_core")
st("EXTERNALISE", "host", ["U19"], pos=[("bundle", "path")], clauses={"TO": "path"}, doc="EXTERNALISE rocket_heart TO society")
st("TRANSFER", "host", ["U85"], pos=[("source", "path")], clauses={"TO": "path", "AS": "name"}, required=["TO"],
   doc="TRANSFER bacterium.mobility TO guardian.mobility")

# ---- communication and compile targets ------------------------------------------------------
st("CUE", "compile", ["U82", "U83", "U15"], pos=[("state", "word")], clauses={"CODE": "string", "CHANNEL": "word", "LAYER": "word"},
   required=["CODE", "CHANNEL"], host_rule="channel", doc='CUE eagle CODE "-.." CHANNEL kinesthetic')
st("MESSAGE", "compile", ["U82"], pos=[("sender", "word")], clauses={"TO": "word", "STATE": "word", "CHANNEL": "word"},
   required=["TO", "STATE"], host_rule="channel", doc="MESSAGE owl TO architect STATE needs_input CHANNEL kinesthetic")
st("PERSPECTIVE", "compile", ["U51", "U64"], pos=[("target", "path"), ("view", "word")], doc="PERSPECTIVE guardian eagle")

# ---- meanings: core, bindings, search (D80, T12) ---------------------------------------------
st("MEANING", "meaning", [], pos=[("key", "word"), ("_eq", "="), ("value", "value")],
   clauses={"IN": "word", "SCOPE": "enum:" + SCOPES}, required=["SCOPE", "IN"],
   doc="MEANING contact.top = local_contact SCOPE state IN eagle")
st("SEARCH", "meaning", ["U62"], pos=[("key", "word")], clauses={"OVER": "list", "METRIC": "word"}, required=["OVER"],
   doc="SEARCH contact.bottom OVER lateral, local_contact, multi_layer METRIC task_success")

# ---- testing (family X) ----------------------------------------------------------------------
st("SNAPSHOT", "test", ["U68"], pos=[("target", "path")], clauses={"BEFORE": "int", "DURING": "int", "AFTER": "int"},
   doc="SNAPSHOT guardian BEFORE 100 DURING 100 AFTER 100")
st("COMPARE", "test", ["U87"], pos=[("target", "path")], clauses={"AGAINST": "list", "METRIC": "word"}, required=["AGAINST"],
   doc="COMPARE guardian AGAINST bacterium, liver METRIC safety")
st("TEST", "test", [], pos=[("target", "path")], clauses={"METRIC": "word", "IN": "path", "SEEDS": "int"},
   doc="TEST guardian METRIC hazard_avoidance IN street SEEDS 20")
st("REVERSE", "test", ["U87"], pos=[("relation", "word")], clauses={"IN": "path"},
   doc="REVERSE distress_raises_spending IN economy")
st("ABLATE", "test", ["U87"], pos=[("target", "path")], clauses={"REMOVE": "list"}, required=["REMOVE"],
   doc="ABLATE guardian REMOVE legs")
st("BASELINE", "test", ["U76"], pos=[("target", "path")], doc="BASELINE person (return to baseline, always available)")


# ---- painting composition and the representation cipher (family VI) -----------------------------
st("LAYER", "paint", ["U59"], pos=[("painting", "path"), ("action", "enum:add|reveal|foreground|background|repaint")],
   clauses={"NAME": "word", "AS": "name"}, doc="LAYER painting reveal NAME sketch")
st("CUTPLACE", "paint", ["U59", "U60"], pos=[("element", "path")], clauses={"TO": "path", "AS": "name"}, required=["TO"],
   doc="CUTPLACE painting_a.engine TO painting_b AS painting_b2 (cut out and place in another painting)")
st("ENCODE", "paint", ["U61"], pos=[("system", "path")], clauses={"AS": "name", "MODE": "enum:exact|controlled|generative"},
   required=["AS"], doc="ENCODE car AS car_painting MODE controlled")
st("DECODE", "paint", ["U61"], pos=[("painting", "path")], clauses={"DOMAIN": "word", "AS": "name"}, required=["DOMAIN"],
   doc="DECODE car_painting DOMAIN thermal_engineering AS new_design")
st("EXTRACT", "paint", ["U57"], pos=[("source", "path")], clauses={"AS": "name"}, required=["AS"],
   doc="EXTRACT workflow_video AS recovery_rule (a function inferred from observed transitions)")

# ---- cognition relations and mechanism -------------------------------------------------------------
st("RELATE", "mental", ["U71"], pos=[("a", "path")],
   clauses={"TO": "path", "AS": "enum:coordination|distinction|comparison|hierarchy|temporal|perspective|analogy"},
   required=["TO", "AS"], doc="RELATE kidney TO agent_filter AS analogy")
st("LOCATE", "state", ["U10"], pos=[("output", "path")], clauses={"MECHANISM": "path"},
   doc="LOCATE clock.hands MECHANISM clock.gears (fix the mechanism and the output follows)")
st("UPGRADE", "host", ["U25"], pos=[("target", "path")], clauses={"WITH": "path", "AS": "name"},
   doc="UPGRADE body WITH rocket_heart AS superhero_body")
st("INPUT", "host", ["U24"], pos=[("target", "path")], clauses={"FROM": "enum:movement|position|gaze|touch", "VIEW": "enum:front|side|back"},
   doc="INPUT painting_ab FROM movement VIEW front (human movement as input; view-dependent reading)")
st("HOSTLOOP", "host", ["U21"], pos=[("host", "path")], clauses={"OBSERVE": "list", "INTERVENE": "list", "MEASURE": "list"},
   doc="HOSTLOOP bacteria OBSERVE light, nutrients INTERVENE light MEASURE movement, contraction")

# ---- governance (chat 3; the public repo's hierarchy) -----------------------------------------------
st("SPINE", "govern", ["U73"], pos=[("action", "path")], clauses={"CHECK": "list"},
   doc="SPINE pierce_remote CHECK gi, jin, rei (every agent acts through the Spine)")
st("WATCHDOG", "govern", ["U74"], pos=[("host", "path")], clauses={"SWITCH": "word", "WHEN": "word"}, required=["SWITCH"],
   doc="WATCHDOG person SWITCH bear WHEN overload")
st("ARCHITECT", "govern", ["U75"], pos=[("action", "enum:strategy|lock|hybrid|retire|reset")], clauses={"TARGET": "list", "AS": "name"},
   doc="ARCHITECT hybrid TARGET lion, eagle AS lion_eagle")
st("OVERRIDE", "govern", ["U77"], pos=[("host", "path")], clauses={"TYPE": "enum:drive|calmness|regulation"}, required=["TYPE"],
   doc="OVERRIDE person TYPE calmness")
st("CONSENT", "govern", ["U73", "U78", "U105"], pos=[("host", "path")],
   clauses={"FOR": "list", "BY": "word", "SCOPE": "enum:per_action|standing", "IN": "word"},
   doc="CONSENT others FOR practice, cues BY others SCOPE standing IN circle (Rei; standing consent, D82)")
st("NETWORK", "govern", ["U105"], pos=[("name", "name")], clauses={"MEMBERS": "list", "LAWS": "list"},
   required=["MEMBERS", "LAWS"], declares="object",
   doc="NETWORK circle MEMBERS practitioner, others LAWS gi, jin, rei (visible participants and the Spine laws, D82)")
st("SAFETY", "govern", ["U73"], pos=[("host", "path")], clauses={"MODE": "enum:normal|stabilise|practical_crisis|crisis"},
   required=["MODE"], doc="SAFETY person MODE stabilise (the cue framework's safety modes)")
st("GATE", "govern", ["U78"], pos=[("operator", "word")], clauses={"REQUIRES": "list"}, required=["REQUIRES"],
   doc="GATE autonomous_cue REQUIRES evidence, consent")

# ---- language growth (operator induction and re-entry) ------------------------------------------------
st("INDUCE", "meta", ["U81", "U62"], pos=[("name", "name")], clauses={"FROM": "path"}, required=["FROM"], declares="operator",
   doc="INDUCE aperture_rule FROM gate_trials")
st("REENTER", "meta", ["U86"], pos=[("node", "path")], clauses={"WITH": "word"}, required=["WITH"],
   doc="REENTER ai_room WITH aperture_rule")

# ---- communication speed: node palace, signal, light, carriers (mission re-scan, C1) -----------------
st("BOOK", "meta", ["U88"], pos=[("name", "name")], clauses={"SYMBOL": "word", "AT": "path"}, required=["SYMBOL"],
   declares="object", doc="BOOK robot_head SYMBOL eagle_calculator AT eagle (a node's palace holds the book)")
st("SIGNAL", "meta", ["U89"], pos=[("target", "path")], clauses={"CHECK": "enum:hash|none", "COLOR": "word"},
   doc="SIGNAL robot_head CHECK hash COLOR green (the green dot travels with the symbol)")
st("LIGHT", "state", ["U90", "U104"], pos=[("source", "word")], clauses={"OVER": "list", "ACTS": "list", "STYLE": "word"},
   required=["ACTS"], doc="LIGHT white_dragon OVER all ACTS find, show, heal, hear STYLE tiger (archetype style of healing)")
st("SENSE", "state", ["U91"], pos=[("seed", "path")], clauses={"RADIUS": "int", "CHANNELS": "list"}, required=["RADIUS"],
   doc="SENSE engine RADIUS 5 CHANNELS smell, visual, memory (the seed grows and senses more)")
st("FOUNDATION", "host", ["U92"], pos=[("name", "name")], clauses={"DOMAINS": "list"}, required=["DOMAINS"],
   declares="object", doc="FOUNDATION figure DOMAINS economy, aerodynamics, physics, chemistry, biology, neuroscience")
st("LEVEL", "meta", ["U93"], pos=[("name", "name")], clauses={"ABOVE": "word"}, required=["ABOVE"],
   doc="LEVEL symbolic ABOVE text (language levels: today's language is the C level)")
st("CARRIER", "compile", ["U94"], pos=[("name", "name")], clauses={"MAIN": "word", "LAYERS": "list"}, required=["MAIN"],
   doc="CARRIER universe MAIN structure LAYERS accent_a, accent_b")
st("GLYPHS", "compile", ["U95"], pos=[("target", "path")], clauses={"CHANNEL": "word", "RATE": "num"},
   required=["CHANNEL"], doc="GLYPHS robot_head CHANNEL haptic RATE 10 (Morse per glyph; rate in words per minute)")
st("ENVELOPE", "compile", ["U96"], pos=[("name", "name")], clauses={"FIELDS": "list"}, required=["FIELDS"],
   doc="ENVELOPE msg FIELDS version, sender, recipient, preconditions, effects, invariants, lineage")
st("CONTRACT", "test", ["U97"], pos=[("target", "path")], clauses={"KEEP": "list"}, required=["KEEP"],
   doc="CONTRACT robot_head KEEP behaviour, safety (compression must keep these)")
st("STANDARD", "paint", ["U98"], pos=[("name", "name")], clauses={"CODEBOOK": "word"}, required=["CODEBOOK"],
   doc="STANDARD rsos_visual CODEBOOK default (image quality = language quality)")
st("OBSERVE", "context", ["U99"], pos=[("target", "path")], clauses={"BY": "list", "CHANNELS": "list"}, required=["BY"],
   doc="OBSERVE rocket_heart BY others CHANNELS visual, smell, kinesthetic")
st("ASSOCIATE", "state", ["U100"], pos=[("target", "path")], clauses={"IN": "word", "LEADS": "word"},
   required=["IN", "LEADS"], doc="ASSOCIATE tv IN shoulders_dropped LEADS worry (the chain depends on the state)")

st("PATH", "meta", ["U101"], pos=[("source", "path")], clauses={"TO": "list", "BEST": "int", "BY": "word"}, required=["TO"],
   doc="PATH RIF TO neuroscience, economics BEST 3 BY shared_relations (golden light)")
st("PARTICLE", "contact", ["U102"], pos=[("name", "name")], clauses={"LAND": "path", "ON": "word", "OPENS": "word"},
   required=["LAND"], declares="object", doc="PARTICLE g1 LAND RIF ON anticipation OPENS prediction_error (green particle)")
st("DEFICIT", "state", ["U103"], pos=[("target", "path"), ("value", "num")],
   doc="DEFICIT RIF 1.0 (the lack; a particle's effect is bounded by it)")

st("REACH", "test", ["U108"], pos=[("name", "name")],
   clauses={"ON": "path", "TARGET": "num", "AGAINST": "word", "MEASURE": "word", "RESULT": "num", "LIMIT": "word",
            "BLOCKERS": "list", "FROM": "word"},
   required=["ON", "TARGET", "AGAINST", "MEASURE"], declares="reach",
   doc="REACH cost10 ON cost.task TARGET 10 AGAINST market_best MEASURE cost_per_task RESULT 3.7 LIMIT thinking "
       "BLOCKERS thinking, audit_calls (a stretch target as an instrument: each blocker opens a planet; the verdict "
       "is what was reached, against what, and what stopped it; FROM starts the next target from an earlier REACH)")

st("OPEN", "mental", ["U106"], pos=[("target", "path")], clauses={"FROM": "list", "SCOPE": "enum:whole|part|network"},
   required=["FROM"], doc="OPEN eagle_calculator FROM olfactory SCOPE whole (one VAKOG channel opens the anchored state)")

# ---- signatures and axes (U80, U49) ------------------------------------------------------------------
# The ten-axis transformation space (chat 2 T49.12, ChatGPT's proposal) as a typing of statement families.
AXES = {
    "declare": ["representation"], "mental": ["perspective", "function"], "scene": ["representation", "position"],
    "state": ["function", "causality"], "contact": ["position", "depth", "function"], "select": ["depth", "abstraction"],
    "host": ["domain", "function"], "compile": ["representation"], "meaning": ["abstraction"], "test": ["causality", "time"],
    "paint": ["representation", "generation"], "govern": ["perspective"], "meta": ["generation", "abstraction"],
    "context": ["perspective"], "header": [],
}


def signature(stmt):
    """Input → output signature of a statement (U80)."""
    ins = [f"{n}:{k}" for n, k in stmt.pos if not n.startswith("_")]
    ins += [f"{c}?:{k}" if c not in stmt.required else f"{c}:{k}" for c, k in stmt.clauses.items() if c != "AS"]
    out = stmt.declares or ("descendant" if "AS" in stmt.clauses else "effect")
    return {"in": ins, "out": out, "axes": AXES.get(stmt.family, [])}


for _s in S:
    if _s.kw in ("TRANSFER", "TRANSPLANT", "DOT", "PIERCE", "PASS"):
        _s.refs = sorted(set(_s.refs) | {"U84"})
for _s in S:
    _s.refs = sorted(set(_s.refs) | {"U80", "U49"}) if _s.kw == "LANGUAGE" else _s.refs

STATEMENTS = {s.kw: s for s in S}
