"""Score REAL1 quick logs with the settled rule (HOST_BRIEF 14:15): priced and fixed-budget rows: seed result > standard;
free-resource rows: Pareto (result >=, resource <=, one strictly)."""
import re, sys, collections
KIND = {"energy": "res", "economics": "res", "quantum": "res", "neuro": "res", "space": "res", "biology": "res",
        "robotics": "pareto", "ai_agents": "pareto", "ai_ai": "pareto", "ai_human": "pareto"}
pat = re.compile(r"(?:standard=(\w+)\s+)?(?:cell\s+)?(\d+)\s+(seed|default)\s+result\s+([-\d.]+)\s+resource\s+([-\d.]+)")
def score(row, path):
    D = collections.defaultdict(dict)
    for line in open(path):
        m = pat.search(line)
        if m: D[(m.group(1) or "", int(m.group(2)))][m.group(3)] = (float(m.group(4)), float(m.group(5)))
    out = collections.defaultdict(list)
    for (std, c), d in sorted(D.items()):
        if "seed" not in d or "default" not in d: continue
        (a, b), (x, y) = d["seed"], d["default"]
        if KIND[row] == "res": v = "WIN" if a > x else ("TIE" if a == x else "loss")
        else: v = "WIN" if (a >= x and b <= y and (a > x or b < y)) else ("TIE" if (a == x and b == y) else "loss")
        out[std].append((c, v, round(a - x, 4), round(b - y, 3)))
    return out
if __name__ == "__main__":
    for row in sys.argv[1:]:
        for std, cells in score(row, f"quick_logs/{row}_v3.txt").items():
            w = sum(v == "WIN" for _, v, _, _ in cells)
            print(f"{row}{'/' + std if std else ''}: {w}/{len(cells)} wins", [(c, v, dr, dres) for c, v, dr, dres in cells])
