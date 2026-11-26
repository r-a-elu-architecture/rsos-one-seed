"""Build docs/editor.html: the editor template with the measured table embedded (one self-contained page)."""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data = json.load(open(os.path.join(ROOT, "results", "editor_table.json")))
tpl = open(os.path.join(ROOT, "tools", "editor_template.html"), encoding="utf-8").read()
html = tpl.replace("/*DATA*/null", json.dumps(data, separators=(",", ":")))
os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True)
open(os.path.join(ROOT, "docs", "editor.html"), "w", encoding="utf-8").write(html)
print("docs/editor.html", len(html))
