"""REAL1 row 3 "ai_human": THE REAL TREE (owner 24 Nov: the own future is read from the real tree, not a single sample).

What a human's next turn needs is not invented by the host: it is counted on real human-human records.
Source: Topical-Chat conversations/train.json (the TRAINING split, 8628 conversations, sha256 in ai_human_fetch.py),
never test_freq.json (the conversations used in cells). Every triple (h_t, r_t, h_t+1) where one person speaks, the
other replies and the first speaks again (both roles: all speakers are human) gives, for each content word w of h_t:
  carried  = w in content(h_t+1)           (the human's next turn needed / took up w: the row's "needs" rule)
  echoed   = w in content(r_t)             (a real human partner's reply covered w: prior for the reply's free echo)
counted per feature bucket  key = q last prev nb
  q    : w is in a sentence of h_t that ends with "?"
  last : w is in the last sentence of h_t
  prev : w was already said earlier in the conversation (any speaker, before h_t)
  nb   : size of h_t (content words <= 5 / <= 12 / more)
and per word (lexical rate, words seen >= 10 times). Also:
  carried point: words of h_t-1 (same speaker) not taken up by r_t-1 or h_t -> P(in h_t+1), P(in r_t)
  unknown needs: |content(h_t+1) & content(r_t) - content(h_t)| (words the real partner brought in), mean
The statistics are cached in data/topical_chat/tree_stats.json (git-ignored, rebuilt if the train sha or VERSION
changes; ~20 s once).
p(w) = logistic( logit p_bucket + logit p_word - logit p_all ), p_word shrunk to p_all with weight 20."""
import os, json, math

VERSION = 1
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "data", "topical_chat", "tree_stats.json")
SHRINK = 20.0


def word_feats(conv, i, content, sentences):
    """Bucket key of every content word of h_t = conv[i] (data up to h_t only)."""
    h = conv[i][1]; cw = content(h)
    sents = [x for x in sentences(h) if content(x)]
    qw = set().union(*[content(x) for x in sents if x.rstrip().endswith("?")]) if sents else set()
    lw = content(sents[-1]) if sents else set()
    prev = set().union(*[content(m) for _, m in conv[:i]]) if i else set()
    nb = 0 if len(cw) <= 5 else (1 if len(cw) <= 12 else 2)
    return {w: f"{int(w in qw)}{int(w in lw)}{int(w in prev)}{nb}" for w in cw}


def build(train_path, sha, content, sentences):
    d = json.load(open(train_path)); B = {}; W = {}; car = [0, 0, 0]; unk = [0, 0]; tot = [0, 0, 0]
    for k in sorted(d):
        conv = [(m["agent"], m["message"]) for m in d[k]["content"]]
        C = [content(m) for _, m in conv]
        prev = set(); prevs = []
        for c in C: prevs.append(set(prev)); prev |= c
        for i in range(len(conv) - 2):
            if not (conv[i][0] == conv[i + 2][0] != conv[i + 1][0]): continue
            h, r, h2 = C[i], C[i + 1], C[i + 2]
            sents = [x for x in sentences(conv[i][1]) if content(x)]
            qw = set().union(*[content(x) for x in sents if x.rstrip().endswith("?")]) if sents else set()
            lw = content(sents[-1]) if sents else set()
            nb = 0 if len(h) <= 5 else (1 if len(h) <= 12 else 2)
            for w in h:
                key = f"{int(w in qw)}{int(w in lw)}{int(w in prevs[i])}{nb}"
                b = B.setdefault(key, [0, 0, 0]); c1, e1 = int(w in h2), int(w in r)
                b[0] += 1; b[1] += c1; b[2] += e1; tot[0] += 1; tot[1] += c1; tot[2] += e1
                x = W.setdefault(w, [0, 0]); x[0] += 1; x[1] += c1
            if i >= 2 and conv[i - 2][0] == conv[i][0]:
                for w in C[i - 2] - (C[i - 1] | h):
                    car[0] += 1; car[1] += int(w in h2); car[2] += int(w in r)
            unk[0] += 1; unk[1] += len((h2 & r) - h)
    return {"version": VERSION, "train_sha256": sha, "triples": unk[0], "words": tot[0],
            "p_all": tot[1] / tot[0], "echo_all": tot[2] / tot[0], "bucket": B,
            "lex": {w: v for w, v in W.items() if v[0] >= 10},
            "carried": car[1] / max(1, car[0]), "carried_echo": car[2] / max(1, car[0]), "carried_n": car[0], "unknown_mean": unk[1] / max(1, unk[0])}


def load(content, sentences):
    from ai_human_fetch import fetch_train, TRAIN_SHA256
    if os.path.exists(CACHE):
        t = json.load(open(CACHE))
        if t.get("version") == VERSION and t.get("train_sha256") == TRAIN_SHA256: return Tree(t)
    t = build(fetch_train(quiet=True), TRAIN_SHA256, content, sentences)
    json.dump(t, open(CACHE, "w")); return Tree(t)


def _logit(p): p = min(max(p, 1e-4), 1 - 1e-4); return math.log(p / (1 - p))


class Tree:
    def __init__(s, t):
        s.t = t; s.p_all = t["p_all"]; s.l_all = _logit(t["p_all"])

    def p_need(s, w, key):
        """key = a bucket key, or "carried" for a word of the carried point."""
        if key == "carried": pb = s.t["carried"]
        else: b = s.t["bucket"].get(key); pb = (b[1] + 2 * s.p_all) / (b[0] + 2) if b else s.p_all
        n, c = s.t["lex"].get(w, (0, 0)); pw = (c + SHRINK * s.p_all) / (n + SHRINK)
        return 1 / (1 + math.exp(-(_logit(pb) + _logit(pw) - s.l_all)))

    def p_echo(s, key):
        if key == "carried": return s.t["carried_echo"]
        b = s.t["bucket"].get(key); e = s.t["echo_all"]
        return (b[2] + 2 * e) / (b[0] + 2) if b else e

    @property
    def unknown_mean(s): return s.t["unknown_mean"]
