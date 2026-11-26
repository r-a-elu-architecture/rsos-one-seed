"""Build the public copy of the site from site/seed/index.html (the private review draft): links point to the public
repository, contact goes through GitHub issues, and the draft banner and draft footer are removed. Writes $1/index.html."""
import os, sys
OWNER = "r-a-elu-architecture"; RESEARCH = "rsos-one-seed"; PROTOCOL = "srcx5"
src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "site", "seed", "index.html")
s = open(src, encoding="utf-8").read()
def rep(a, b):
    global s
    assert s.count(a) == 1, a[:60]; s = s.replace(a, b)
i = s.find('<div class="draft">'); j = s.find('</div>', i) + len('</div>'); assert i > 0; s = s[:i] + s[j:]
rep('<p class="small">Contact details will be added before publication.</p>',
    f'<p class="small">Open an issue titled "Pilot: &lt;your domain&gt;" at <a href="https://github.com/{OWNER}/{RESEARCH}/issues">github.com/{OWNER}/{RESEARCH}/issues</a>.</p>')
k = s.find('<footer class="band"><div class="in small">'); e = s.find('</footer>', k); assert k > 0
s = s[:k] + (f'<footer class="band"><div class="in small">Every number on this page comes from the sealed result files in '
             f'<a href="https://github.com/{OWNER}/{RESEARCH}">{OWNER}/{RESEARCH}</a>. The open record: '
             f'<a href="https://github.com/{OWNER}/{PROTOCOL}">SRC-X.5</a>. Code: Apache 2.0.</div>') + s[e:]
rep('const REPO = "https://github.com/r-a-elu-architecture/RSOS-Multimodal-World/blob/core-v1/";',
    f'const REPO = "https://github.com/{OWNER}/{RESEARCH}/blob/main/";')
assert "RSOS-Multimodal-World" not in s and "core-v1" not in s and "Private draft" not in s
os.makedirs(sys.argv[1], exist_ok=True); open(os.path.join(sys.argv[1], "index.html"), "w", encoding="utf-8").write(s)
print("public site:", os.path.join(sys.argv[1], "index.html"))
