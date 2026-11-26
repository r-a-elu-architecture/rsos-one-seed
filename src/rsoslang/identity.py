"""Identity and profiles (T4).

- The seven levels (mission, identity, values, beliefs, skills, behaviour, environment), as in the cue framework's
  IDENTITY (rsso/identity.py).
- Archetype profiles (Lion, Eagle, Bear, Leopard, Raven, Tiger; Dragon, Observer) from the cue framework
  (rsxv/archetypes.py): virtues, language, shadow, vibration code.
- Built persons (chat 3 T4): synthetic people with an age, organ history and goal. No real human.
- Host-specific protocol choice (chat 3 T4): "a person who is 70 and had a heart attack: calmness rather than override
  or drive"; an athlete gets different conditioning. The choice feeds the Spine as predicted harm (Jin).
"""

import importlib
import random

from .governance import load_framework

LEVELS = ("mission", "identity", "values", "beliefs", "skills", "behaviour", "environment")
CARDIAC = {"heart_attack", "cardiac", "arrhythmia", "heart_failure", "hypertension"}


def archetypes():
    if load_framework()[0] is None:
        return {}
    return importlib.import_module("rsxv.archetypes").PROFILES


def override_type(persona):
    """Calmness for a cardiac history at 60+; drive for athletes; regulation otherwise (chat 3 T4)."""
    organs = set(persona.get("organs") or [])
    age = persona.get("age") or 0
    if organs & CARDIAC and age >= 60:
        return "calmness"
    if persona.get("goal") in ("sport", "athlete", "performance"):
        return "drive"
    return "regulation"


def predicted_harm(persona, override):
    """A stated rule, not a clinical model: drive on a cardiac history at 60+ is above the Spine's threshold."""
    if not persona:
        return 0.0
    if override == "drive" and set(persona.get("organs") or []) & CARDIAC and (persona.get("age") or 0) >= 60:
        return 0.6
    if override == "drive" and set(persona.get("organs") or []) & CARDIAC:
        return 0.35
    return 0.0


GOALS = ["calm", "focus", "sport", "confidence", "sleep", "learning"]
ORGANS = ["heart_attack", "hypertension", "asthma", "knee_injury", "none", "none", "none", "none"]


def population(n, seed=0):
    """Built persons for simulation (chat 3 T4): synthetic, seeded, with the seven levels filled from templates."""
    rng = random.Random(seed)
    out = []
    for i in range(n):
        age = rng.randint(18, 85)
        organs = [o for o in {rng.choice(ORGANS) for _ in range(rng.randint(0, 2))} if o != "none"]
        goal = rng.choice(GOALS)
        p = {"name": f"p{i:04d}", "age": age, "organs": organs, "goal": goal, "source": "synthetic",
             "levels": {"mission": f"live toward {goal}", "identity": rng.choice(["builder", "carer", "learner", "athlete"]),
                        "values": rng.sample(["honesty", "family", "freedom", "growth", "calm", "courage"], 2),
                        "beliefs": [rng.choice(["I can change", "change is slow", "I need help", "I manage alone"])],
                        "skills": rng.sample(["breathing", "focus", "planning", "movement"], 2),
                        "behaviour": rng.choice(["routine", "avoidance", "overwork", "balanced"]),
                        "environment": rng.choice(["city", "village", "shared home", "alone"])},
             "archetype": rng.choice(["LION", "EAGLE", "BEAR", "LEOPARD", "RAVEN", "TIGER"])}
        p["override"] = override_type(p)
        out.append(p)
    return out
