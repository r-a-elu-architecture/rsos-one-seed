"""A deterministic benchmark for the agent workflow: customer-support tickets with known answers.

Each ticket has a category, the right action and (for refunds) an amount. Held-out sets add typos and phrasing the
workflow has never seen, so improvements can be measured on tickets not used while building.
"""

import random

CATEGORIES = {
    "billing":   {"words": ["invoice", "charged", "payment", "bill", "refund"], "action": "refund",
                  "unseen": ["debited", "overbilled", "money back"]},
    "technical": {"words": ["error", "crash", "bug", "broken", "freezes"], "action": "troubleshoot",
                  "unseen": ["glitch", "stops working", "keeps closing"]},
    "account":   {"words": ["password", "login", "locked", "account", "sign in"], "action": "reset",
                  "unseen": ["cannot get in", "credentials", "two factor"]},
    "shipping":  {"words": ["delivery", "package", "shipping", "parcel", "tracking"], "action": "track",
                  "unseen": ["courier", "never arrived", "order is late"]},
}
TEMPLATES = [
    "Hello, {w} problem with my order {cid}. {extra}",
    "I have an issue: {w}. Customer {cid}. {extra}",
    "{extra} My {w} is not right, id {cid}.",
    "Please help, {w} again for {cid}! {extra}",
]
EXTRAS = ["Thanks.", "This is urgent.", "Second time writing.", "", "Kind regards."]


def typo(word, rng):
    if len(word) < 4:
        return word
    i = rng.randrange(1, len(word) - 2)
    return word[:i] + word[i + 1] + word[i] + word[i + 2:]


def make_tickets(n, seed, typo_rate=0.0, unseen_rate=0.0):
    rng = random.Random(seed)
    out = []
    for k in range(n):
        cat = rng.choice(list(CATEGORIES))
        spec = CATEGORIES[cat]
        w = rng.choice(spec["unseen"]) if rng.random() < unseen_rate else rng.choice(spec["words"])
        if rng.random() < typo_rate:
            w = " ".join(typo(x, rng) for x in w.split())
        cid = f"C{rng.randrange(1000, 1200)}" if rng.random() < 0.5 else f"C{rng.randrange(1000, 9999)}"  # regulars
        amount = round(rng.uniform(5, 400), 2) if cat == "billing" else 0.0
        extra = rng.choice(EXTRAS)
        text = rng.choice(TEMPLATES).format(w=w, cid=cid, extra=extra)
        if amount:
            text += f" Amount {amount} EUR."
        out.append({"id": k, "text": text, "category": cat, "action": spec["action"], "customer": cid,
                    "amount": amount})
    return out


def knowledge_base(seed=7):
    rng = random.Random(seed)
    return {f"C{i}": rng.choice(["gold", "silver", "bronze"]) for i in range(1000, 10000)}


REFUND_LIMIT = {"gold": 300.0, "silver": 150.0, "bronze": 50.0}
