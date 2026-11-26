"""C1: communication speed of one meaning across carriers; node palace; green-dot drift signal; heal.
Pre-registration: experiments/PREREGISTRATION_C1.md."""

import difflib
import glob
import gzip
import json
import os
import re

import numpy as np

from common import ROOT, save
from rsoslang import compile_source
from rsoslang import palace as P

SEED = 20261117
NVAR = 40
BOOKS = {"body_society.rsl", "car_seat.rsl", "healing.rsl", "paintings.rsl", "robot_head.rsl", "rocket_heart.rsl",
         "sol_remote.rsl"}                  # the 7 pre-registered books
TOK = re.compile(r"\w+|[^\w\s]")
MORSE = {**dict(zip("abcdefghijklmnopqrstuvwxyz", ".- -... -.-. -.. . ..-. --. .... .. .--- -.- .-.. -- -. --- "
                    ".--. --.- .-. ... - ..- ...- .-- -..- -.-- --..".split())),
         **dict(zip("0123456789", "----- .---- ..--- ...-- ....- ..... -.... --... ---.. ----.".split())),
         ".": ".-.-.-", ",": "--..--", "?": "..--..", "'": ".----.", "!": "-.-.--", "/": "-..-.", "(": "-.--.",
         ")": "-.--.-", "&": ".-...", ":": "---...", ";": "-.-.-.", "=": "-...-", "+": ".-.-.", "-": "-....-",
         "_": "..--.-", '"': ".-..-.", "$": "...-..-", "@": ".--.-.", "#": "...-.-", "|": "-.-.-", ">": "--.-.",
         "*": "-..-"}


def morse_seconds(text, wpm=10):
    unit = 1.2 / wpm
    total = 0
    for word in text.lower().split():
        for k, ch in enumerate(word):
            code = MORSE.get(ch, "........")          # unknown glyph: error prosign length
            total += sum(1 if c == "." else 3 for c in code) + (len(code) - 1)
            if k < len(word) - 1:
                total += 3
        total += 7
    return total * unit


def ir_of(src):
    r = compile_source(src)
    ir = dict(r.ir); ir.pop("diagnostics", None)
    return r, ir


def canon(ir, pretty=False):
    return json.dumps(ir, sort_keys=True, ensure_ascii=False,
                      indent=1 if pretty else None, separators=None if pretty else (",", ":"))


def mutate(src, rng, k):
    lines = src.split("\n")
    for _ in range(k):
        kind = rng.integers(3)
        idx = [i for i, l in enumerate(lines) if i > 1 and l and not l.startswith("#")]
        if kind == 0:
            c = [i for i in idx if re.search(r"\b\d+\b", lines[i])]
            if c:
                i = int(rng.choice(c)); lines[i] = re.sub(r"\b\d+\b", str(int(rng.integers(1, 10))), lines[i], count=1)
                continue
        if kind <= 1:
            c = [i for i in idx if re.search(r'CODE "[.-]+"', lines[i])]
            if c:
                i = int(rng.choice(c))
                code = "".join(rng.choice([".", "-"], int(rng.integers(1, 5))))
                lines[i] = re.sub(r'CODE "[.-]+"', f'CODE "{code}"', lines[i], count=1)
                continue
        c = [i for i in idx if lines[i].split()[0] in ("CUE", "FUTUREPACE")]
        if c:
            del lines[int(rng.choice(c))]
    return "\n".join(lines)


def variants(src, rng, n):
    out, tries = [], 0
    while len(out) < n and tries < n * 20:
        tries += 1
        v = mutate(src, rng, int(rng.integers(1, 4)))
        if v != src and compile_source(v).ok:
            out.append(v)
    return out


def main():
    rng = np.random.default_rng(SEED)
    books = {os.path.basename(f)[:-4]: open(f).read().rstrip("\n") for f in sorted(glob.glob(f"{ROOT}/examples/*.rsl"))
             if os.path.basename(f) in BOOKS}
    pal = P.Palace(books)
    lib_ir = {s: ir_of(b)[1] for s, b in books.items()}
    rows, drift_rows = [], []
    for sym, book in books.items():
        for v in variants(book, rng, NVAR):
            r, ir = ir_of(v)
            dig = r.digest()
            js = canon(ir)
            msg = P.encode(pal, sym, v)
            back = P.decode(pal, msg)
            jdiff = "\n".join(l for l in difflib.unified_diff(canon(lib_ir[sym], True).split("\n"),
                                                               canon(ir, True).split("\n"), n=0, lineterm="")
                              if not l.startswith(("---", "+++")))
            b = lambda s: len(s.encode("utf-8"))
            rows.append({"book": sym, "json": b(js), "json_gz": len(gzip.compress(js.encode(), 9)),
                         "rsos": b(v), "rsos_gz": len(gzip.compress(v.encode(), 9)), "json_diff": b(jdiff),
                         "palace": b(msg), "tok_json": len(TOK.findall(js)), "tok_rsos": len(TOK.findall(v)),
                         "tok_palace": len(TOK.findall(msg)),
                         "exact": compile_source(back).digest() == dig,
                         "haptic_rsos_s": morse_seconds(v), "haptic_palace_s": morse_seconds(msg),
                         "haptic_json_s": morse_seconds(js)})
            for k in (1, 3):                                 # receiver's book drifted
                drifted = variants(book, rng, 1)
                if not drifted:
                    continue
                rb = mutate(book, rng, k)
                if rb == book:
                    continue
                rp = P.Palace({**books, sym: rb})
                blind = P.decode(rp, msg, check=False)
                try:
                    P.decode(rp, msg); detected = False
                except P.Drift:
                    detected = True
                healed, cost = P.heal(book, rb)
                after = P.decode(P.Palace({**books, sym: healed}), msg)
                drift_rows.append({"book": sym, "k": k,
                                   "blind_exact": compile_source(blind).digest() == dig,
                                   "detected": detected,
                                   "healed_exact": compile_source(after).digest() == dig,
                                   "heal_bytes": cost + b(msg), "full_bytes": b(v)})
    med = lambda key: float(np.median([r[key] for r in rows]))
    ratio = lambda a, c: float(np.median([r[a] / r[c] for r in rows]))
    n = len(rows)
    sync_exact = sum(r["exact"] for r in rows) / n
    blind = sum(d["blind_exact"] for d in drift_rows) / len(drift_rows)
    detected = sum(d["detected"] for d in drift_rows) / len(drift_rows)
    silent_wrong = sum((not d["detected"]) and (not d["blind_exact"]) for d in drift_rows)
    healed = sum(d["healed_exact"] for d in drift_rows) / len(drift_rows)
    heal_ratio = float(np.median([d["heal_bytes"] / d["full_bytes"] for d in drift_rows]))
    summary = {
        "n_messages": n, "n_drift": len(drift_rows),
        "median_bytes": {k: med(k) for k in ("json", "json_gz", "rsos", "rsos_gz", "json_diff", "palace")},
        "median_tokens": {k: med(k) for k in ("tok_json", "tok_rsos", "tok_palace")},
        "median_haptic_s_10wpm": {k: med(k) for k in ("haptic_json_s", "haptic_rsos_s", "haptic_palace_s")},
        "rsos_over_json": ratio("rsos", "json"), "palace_over_rsos": ratio("palace", "rsos"),
        "palace_over_json": ratio("palace", "json"),
        "sync_exact": sync_exact, "drift_blind_exact": blind, "drift_detected": detected,
        "drift_silent_wrong": silent_wrong, "healed_exact": healed, "heal_over_full": heal_ratio,
        "heal_over_full_by_k": {k: float(np.median([d["heal_bytes"] / d["full_bytes"] for d in drift_rows
                                                    if d["k"] == k])) for k in (1, 3)},
    }
    mb = summary["median_bytes"]; hs = summary["median_haptic_s_10wpm"]
    checks = {
        "P1_rsos_le_half_json": summary["rsos_over_json"] <= 0.50,
        "P2_sync_exact_and_palace_le_10pct": sync_exact == 1.0 and summary["palace_over_rsos"] <= 0.10,
        "P3_palace_lt_rsos_gz": mb["palace"] < mb["rsos_gz"],
        "P4_palace_lt_json_diff": mb["palace"] < mb["json_diff"],
        "P5_blind_lt_50_detect_100_no_silent": blind < 0.5 and detected == 1.0 and silent_wrong == 0,
        "P6_heal_exact_and_le_half": healed == 1.0 and heal_ratio <= 0.5,
        "P7_haptic_rsos_gt120_palace_lt15": hs["haptic_rsos_s"] > 120 and hs["haptic_palace_s"] < 15,
    }
    path, digest = save("c1_communication", {"seed": SEED, "summary": summary, "checks": checks,
                                              "rows": rows, "drift_rows": drift_rows})
    print(json.dumps({"summary": summary, "checks": checks}, indent=1)); print(path, digest)


if __name__ == "__main__":
    main()
