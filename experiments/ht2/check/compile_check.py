"""Compile each page output with src/rsoslang and summarise the HT2 functional check. Usage: python compile_check.py <page_out.json>"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "src"))
from rsoslang import compile_source
# entities the messages refer to but do not declare themselves (rooms and the calculator are declared by the page)
PRE = ("LANGUAGE RSOS 0.2\nWORLD w\nHOST team KIND organisation\nOBJECT robot\nOBJECT couch\nOBJECT microwave\n"
       "OBJECT white_dragon\nOBJECT rocket_heart\nOBJECT sphere\n")
d = json.load(open(sys.argv[1]))
rows = {}
for k, r in d["results"].items():
    res = compile_source(PRE + r["rsos"])
    rows[k] = {"compiles": res.ok, "errors": [str(e) for e in res.errors], "rsos_match": r["rsos_match"],
               "plain_complete": not r["plain_missing"], "plain_missing": r["plain_missing"]}
    rows[k]["correct"] = rows[k]["compiles"] and rows[k]["rsos_match"] and rows[k]["plain_complete"]
n = sum(r["correct"] for r in rows.values())
summary = {"correct": n, "of": len(rows), "page_errors": d["errors"]}
json.dump({"summary": summary, "rows": rows}, open(sys.argv[1].replace(".json", "_compiled.json"), "w"), indent=1)
print(json.dumps(summary)); [print(k, v) for k, v in rows.items() if not v["correct"]]
