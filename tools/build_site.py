#!/usr/bin/env python3
"""Build the RSOS Language site: tools/site/<page>.html bodies -> docs/<page>.html with shared chrome.

Run from the repo root: python3 tools/build_site.py
docs/editor.html and docs/keyboard.html are standalone tools and are not touched.
"""
import html
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "tools" / "site"
OUT = ROOT / "docs"
REPO = "https://github.com/r-a-elu-architecture/RSOS-Language"
CUE = "https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/"
SITE = "https://r-a-elu-architecture.github.io/RSOS-Language/"

PAGES = [  # file, nav label (None = not in the main nav), <title>, description
    ("index", None, "RSOS: exact shared state for AI agents, and the language it grew from",
     "RSOS Core keeps every AI agent's copy of shared state exact: the model names the change, a deterministic "
     "runtime computes it and repairs drift with no model call. Predicted in public, measured on six models."),
    ("core", "Core", "RSOS Core v1: specification, operations and guarantees | RSOS",
     "Eight state operations, a JSON IR with a schema, stable error codes, a state digest and conformance tests."),
    ("adopt", "For organisations", "For organisations: guarantees, fit, pilot path and limits | RSOS",
     "What RSOS Core guarantees, where it fits in an agent platform, how to run a pilot and what is not yet shown."),
    ("results", "Results", "Results: every pre-registered test, failures included | RSOS",
     "Pre-registered tests on real LLM agents across four model families, every prediction and the failure map."),
    ("try", None, "The RSOS language: editor and keyboard | RSOS",
     "Compose RSOS programs as paintings in the editor, or key them in with the RSOS keyboard layer."),
    ("paper", "Research", "Research: whitepaper, citation and reproduction | RSOS",
     "Whitepaper, software DOIs, how to cite and how to reproduce every result with zero model calls."),
    ("origins", None, "Origins: the seed, three layers and responsible use | RSOS",
     "How RSOS grew from a symbolic language into Core, how symbols become operations, and the safeguards."),
    ("programme", None, "Research programme and responsible use | RSOS",
     "Twenty-four domains, each with a first measurable test and its safeguards."),
    ("404", None, "Page not found | RSOS", "This page does not exist."),
    ("family", None, "The RSOS family: language and cue framework | RSOS",
     "How the RSOS Language and the RSOS Multimodal Cue Framework relate."),
]

JSONLD = """
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"SoftwareSourceCode","name":"RSOS Core and RSOS Language",
"description":"Exact shared state for AI agents: a specification, JSON IR, deterministic runtime and MCP server.",
"codeRepository":"https://github.com/r-a-elu-architecture/RSOS-Language","programmingLanguage":"Python",
"license":"https://www.apache.org/licenses/LICENSE-2.0","version":"0.4.0","identifier":"https://doi.org/10.5281/zenodo.24359268",
"author":{"@type":"Person","name":"R. A. Elu","identifier":"https://orcid.org/0009-0000-1456-2467"}}
</script>"""

HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:url" content="{url}">
<meta property="og:site_name" content="RSOS">
<meta property="og:image" content="{site}og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="RSOS Core: shared state for AI agents, exact by construction. 318 of 320 tasks exact across six models.">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{site}og.png">
<meta name="theme-color" content="#0e2233">
<link rel="icon" href="favicon.svg" type="image/svg+xml">{jsonld}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible+Next:wght@400;600;700&family=Atkinson+Hyperlegible+Mono:wght@400;600&display=swap">
<link rel="stylesheet" href="site.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<div class="family" role="navigation" aria-label="RSOS family"><div class="wrap">
<b>RSOS</b>
<a class="here" href="index.html">Core and Language</a>
<a href="{cue}">Multimodal Cue Framework</a>
</div></div>
<div class="wrap">
<header class="top">
<a class="mark" href="index.html"><span class="dot" aria-hidden="true"></span>RSOS</a>
<nav class="main" aria-label="Site">{nav}</nav>
</header>
</div>
<main id="main">
"""

FOOT = """</main>
<footer><div class="wrap">
<div><p>RSOS by R. A. Elu, <a href="https://orcid.org/0009-0000-1456-2467">ORCID 0009-0000-1456-2467</a>.
Code under Apache 2.0, text under CC BY 4.0.</p>
<p>Research and development software. Not a medical device.</p></div>
<div><p><a href="{repo}">Source on GitHub</a></p><p><a href="{repo}/blob/main/spec/core/STATE_OPS.md">Core specification</a></p>
<p><a href="https://doi.org/10.5281/zenodo.24359268">Software DOI</a></p><p><a href="{repo}/blob/main/RESPONSIBLE_USE.md">Responsible use</a></p>
<p><a href="{repo}/blob/main/SECURITY.md">Security</a></p></div>
<div><p><a href="try.html">The RSOS language: editor and keyboard</a></p><p><a href="origins.html">Origins of the operations</a></p>
<p><a href="programme.html">Research programme</a></p><p><a href="family.html">The RSOS family</a></p></div>
</div></footer>
</body>
</html>
"""


def nav_for(current: str) -> str:
    out = []
    for f, label, _, _ in PAGES:
        if label is None:
            continue
        cur = ' aria-current="page"' if f == current else ""
        out.append(f'<a href="{f}.html"{cur}>{label}</a>')
    out.append(f'<a class="gh" href="{REPO}">GitHub</a>')
    return "".join(out)


def ops_table() -> str:
    """The Core operations table, generated from registry/operators.json (the single source of truth)."""
    reg = json.loads((ROOT / "registry" / "operators.json").read_text(encoding="utf-8"))
    rows = []
    for e in reg["entries"]:
        core = e["status"] in ("tested", "executed") and bool(e.get("evidence"))
        uses = e.get("measured_uses_a7_a8")
        rows.append(
            "<tr{cls}><td><code class=\"op\">{name}</code><span class=\"sig\">{sig}</span></td><td>{sem}</td><td>{fam}</td><td>{sym}</td><td class=\"n\">{uses}</td>"
            "<td><span class=\"tag {tag}\">{status}</span></td></tr>".format(
                cls="" if core else ' class="outside"', name=html.escape(e["tech_name"]), sig=html.escape(e["signature"]), sem=html.escape(e["semantics"]),
                fam=html.escape(e["familiar_equivalent"]), sym=html.escape(e["symbolic_name"]),
                uses="" if uses is None else f"{uses:,}", tag="pass" if core else "pred",
                status=html.escape(e["status"] + ("" if core else ", no experiment yet"))))
    return ('<div class="tw"><table class="ops"><caption>Generated from <code>registry/operators.json</code>, '
            f'registry {html.escape(str(reg["registry_version"]))}, Core {html.escape(reg["core_version"])}. Uses: operations written by blind planners across experiments A7 and A8.</caption>'
            '<thead><tr><th scope="col">Operation</th><th scope="col">Meaning</th><th scope="col">Familiar as</th>'
            '<th scope="col">RSOS name</th><th scope="col" class="n">Uses in A7, A8</th>'
            '<th scope="col">Status</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table></div>")


def main() -> None:
    for f, _, title, desc in PAGES:
        body = (SRC / f"{f}.html").read_text(encoding="utf-8")
        body = body.replace("{REPO}", REPO).replace("{CUE}", CUE).replace("{OPS}", ops_table() if "{OPS}" in body else "")
        url = SITE + ("" if f == "index" else f + ".html")
        html = HEAD.format(title=title, desc=desc, url=url, cue=CUE, nav=nav_for(f), site=SITE, jsonld=JSONLD if f == "index" else "") + body + FOOT.format(repo=REPO)
        assert not re.search(r"\{[A-Z]+\}", html), f"unfilled placeholder in {f}"
        (OUT / f"{f}.html").write_text(html, encoding="utf-8")
        print(f"docs/{f}.html  {len(html):>6} bytes")
    urls = "".join(f"<url><loc>{SITE}{'' if f == 'index' else f + '.html'}</loc></url>"
                   for f, *_ in PAGES if f != "404") + f"<url><loc>{SITE}editor.html</loc></url><url><loc>{SITE}keyboard.html</loc></url>"
    (OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                                     + urls + "</urlset>\n", encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}sitemap.xml\n", encoding="utf-8")


if __name__ == "__main__":
    main()
