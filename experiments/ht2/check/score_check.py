"""Score the HT2 functional check (amendment 1). Field lists: HT1 (T1-T6) and the amendment rule (P1-P6).
1 = recovered by the code-only decoder (decodes_code_only.md), 0 = not. Ambiguous calls are listed in NOTES."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
F = {
 "T1": {"place": 1, "perspective": 1, "state": 1, "components": 1, "function": 1},
 "T2": {"place": 1, "perspective": 1, "components": 1, "function": 1},
 "T3": {"place": 1, "function": 1, "forward=hypothesis": 1, "backward=contradiction": 1},
 "T4": {"place": 1, "perspective": 1, "function": 1, "trigger": 1},
 "T5": {"place": 1, "palm=calmness": 1, "top=deep work+tunnel": 1, "state anchors": 1},
 "T6": {"source": 1, "host": 1, "depth": 1, "order": 1, "gain": 1},
 "P1": {"dragon": 1, "pierce": 1, "sphere": 1, "golden light": 1, "lion style": 1, "structure": 1, "order 2": 1,
        "rocket heart": 1, "heal": 1, "robot leg": 1},
 "P2": {"robot head": 1, "dissociated": 1, "determination": 1, "contradiction": 1, "action": 1,
        "rocket heart": 1, "flow": 1, "team": 1, "backward": 0, "inside": 1, "efficiency": 1},
 "P3": {"couch": 1, "forward=analogical": 1, "down=future pacing": 1, "decision-making": 1,
        "sphere": 1, "transplant": 1, "team": 1, "order 3": 1},
 "P4": {"owl room": 1, "calculator": 1, "associated": 1, "relief": 1, "hypothesis": 1, "state anchor": 1, "trigger": 1},
 "P5": {"palm": 1, "confidence": 1, "hologram": 1, "hypothesis testing": 1, "top": 1, "calmness": 1, "state anchor": 1,
        "dragon": 1, "beam": 1, "team": 1, "up": 1, "green particles": 1, "tiger style": 1, "surface": 1},
 "P6": {"eagle room": 1, "robot leg": 1, "top view": 1, "deep work": 1, "tunnel image": 1, "action": 1, "order 4": 1,
        "team": 1, "contain": 1, "rocket heart": 1, "robot hand": 1, "compress": 1, "couch": 1},
}
NOTES = {
 "P2.backward": "0: the page compiles 'backward' to FLOW DIRECTION inward (the grammar's direction enum has no "
                "forward/backward); the decoder read 'inward'. Information lost in the code, not by the decoder.",
 "P6.contain": "1 (lenient): decoded operator 'wrap' (team wrapped around rocket heart); the page compiles contain to "
               "WRAP. Same meaning; strict scoring counts it 0.",
}
acc = {k: sum(v.values()) / len(v) for k, v in F.items()}
fields = sum(len(v) for v in F.values()); hit = sum(sum(v.values()) for v in F.values())
compiled = json.load(open(os.path.join(HERE, "run2_fixed_compiled.json")))["summary"]
summary = {"compile_correct": f'{compiled["correct"]}/{compiled["of"]}', "fields": fields, "recovered": hit,
           "accuracy_fields": round(hit / fields, 4), "accuracy_strict": round((hit - 1) / fields, 4),
           "accuracy_task_mean": round(sum(acc.values()) / len(acc), 4),
           "pass": compiled["correct"] == 12 and (hit - 1) / fields >= 0.90}
json.dump({"summary": summary, "per_task": acc, "fields": F, "notes": NOTES}, open(os.path.join(HERE, "score.json"), "w"), indent=1)
print(json.dumps(summary, indent=1))
