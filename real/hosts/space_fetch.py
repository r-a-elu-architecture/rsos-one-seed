"""REAL1 row 5: fetch current orbital elements from CelesTrak (run on the laptop; CelesTrak is not reachable from the
build machine). Writes real/hosts/data/space_tle.txt (3-line TLE format) and space_tle.meta.json (source URL, UTC fetch
time, sha256). space.py then uses the first satellite in the file (or the one named in env REAL1_SPACE_SAT) instead of
the stand-in, and computes the contact windows from these elements starting at their epoch.
Default: CelesTrak GP group "planet" (Planet Labs EO satellites: real downlink-limited imagers), first active entry.
Usage: python space_fetch.py [--group planet | --catnr 25544]
"""
import sys, os, json, hashlib, datetime, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "data")

def main():
    args = sys.argv[1:]
    if "--catnr" in args: q = "CATNR=" + args[args.index("--catnr") + 1]
    else: q = "GROUP=" + (args[args.index("--group") + 1] if "--group" in args else "planet")
    url = f"https://celestrak.org/NORAD/elements/gp.php?{q}&FORMAT=tle"
    req = urllib.request.Request(url, headers={"User-Agent": "real1-space-fetch"})
    txt = urllib.request.urlopen(req, timeout=60).read().decode("ascii", "replace")
    lines = [l.rstrip() for l in txt.splitlines() if l.strip()]
    if len(lines) < 3 or not lines[1].startswith("1 "):
        sys.exit(f"unexpected answer from {url}:\n{txt[:300]}")
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "space_tle.txt"), "w", newline="\n") as f: f.write("\n".join(lines) + "\n")
    meta = {"url": url, "fetched_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            "satellites": len(lines) // 3, "first": lines[0].strip(),
            "sha256": hashlib.sha256(("\n".join(lines) + "\n").encode()).hexdigest()}
    with open(os.path.join(OUT, "space_tle.meta.json"), "w") as f: json.dump(meta, f, indent=1)
    print(json.dumps(meta, indent=1))

if __name__ == "__main__":
    main()
