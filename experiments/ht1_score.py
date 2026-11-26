"""HT1 scoring. Pre-registration: PREREGISTRATION_HT1.md. Decodes by two fresh agents (S arm, P arm), no target access."""
import json
from common import save

S = ["head + inside + associated + relief + confidence + analogical reasoning",
     "robot hand + action model + top viev + dissociated + future + action",
     "couch hypothesis testing forward = hypoth back",
     "eagle calc decision above before moeny decisoin",
     "kitchen microv - the palm = calmness, the top = deep work with tunnel image",
     "heart rocket transplanted into team , deep: structure order 1 efficiency"]
P = ["head = making decision + associated + confidence + analogical reasonin",
     "robots hand - action model up view, diss + future + do",
     "couch hypothesis testing forward hypotheris backward contradiction",
     "eagle room calculator decisionn from the view above beffore any money decision",
     "kitchen microwave: the palm = clamness, the top = deep work with a tunnel image",
     "rocet heart transplanted into a team heat place deeply : strucutre order 1st efficiency gained"]
time_S = [10, 19, 20, 42, 28, None]
time_P = [12, 15, 25, 22, 26, None]
# field-by-field scores against the pre-registered targets (1 = recovered by the decoder, 0 = not)
fields = [["place", "perspective", "state", "components", "function"],
          ["place", "perspective", "components", "function"],
          ["place", "function", "forward=hypothesis", "backward=contradiction"],
          ["place", "perspective", "function", "trigger"],
          ["place", "palm=calmness", "top=deep work+tunnel", "state anchors"],
          ["source", "host", "depth", "order", "gain"]]
score_S = [[1, 1, 1, 1, 0], [1, 1, 1, 1], [1, 1, 1, 0], [1, 1, 1, 1], [1, 1, 1, 0], [1, 1, 1, 1, 1]]
score_P = [[1, 1, 1, 1, 1], [1, 1, 1, 1], [1, 1, 1, 1], [1, 1, 1, 1], [1, 1, 1, 0], [1, 1, 1, 1, 1]]
acc_S = [sum(x) / len(x) for x in score_S]; acc_P = [sum(x) / len(x) for x in score_P]
k1 = [None if (a is None or b is None) else (a < b and s >= p) for a, b, s, p in zip(time_S, time_P, acc_S, acc_P)]
rows = [{"task": i + 1, "S": S[i], "P": P[i], "chars_S": len(S[i]), "chars_P": len(P[i]), "time_S": time_S[i],
         "time_P": time_P[i], "acc_S": acc_S[i], "acc_P": acc_P[i], "fields": fields[i], "K1_task": k1[i]} for i in range(6)]
wins = sum(1 for x in k1 if x); known = sum(1 for x in k1 if x is not None)
summary = {"K1_wins": wins, "K1_tasks_with_times": known, "K1_pass": wins >= 4,
           "K1_can_still_pass": wins + (6 - known) >= 4,
           "acc_mean_S": sum(acc_S) / 6, "acc_mean_P": sum(acc_P) / 6,
           "chars_S": sum(len(x) for x in S), "chars_P": sum(len(x) for x in P),
           "time_S_T1_T5": sum(time_S[:5]), "time_P_T1_T5": sum(time_P[:5]),
           "deviation": "P was written as shorthand, not full sentences, on every task"}
path, d = save("ht1_speed", {"rows": rows, "summary": summary})
print(json.dumps(summary, indent=1)); print(d)
