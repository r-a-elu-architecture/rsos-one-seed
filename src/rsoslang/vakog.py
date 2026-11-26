"""The VAKOG key: a name is a five-channel anchor; any presented channels can open the whole book.

Owner, 17 Nov 2026: the name itself is visual, auditory, kinesthetic, olfactory, gustatory; anchored in a state,
one or two channels open the whole structure, and the opened node stimulates its subnode network.
"""

import hashlib

import numpy as np

CHANNELS = ("V", "A", "K", "O", "G")


class VakogPalace:
    def __init__(self, anchors, contents):
        self.anchors = np.asarray(anchors)            # N × 5 symbols
        self.contents = list(contents)

    def signal(self, i):
        return hashlib.sha256(str(self.contents[i]).encode()).hexdigest()[:8]

    def open_by_name(self, cue, rng, channel=0):
        """A: exact lookup on one fixed channel (the seen name)."""
        if channel not in cue:
            return None
        hits = np.where(self.anchors[:, channel] == cue[channel])[0]
        return int(rng.choice(hits)) if len(hits) else None

    def complete(self, cue, rng):
        """C: the book that matches the most presented channels opens (pattern completion)."""
        if not cue:
            return None
        score = np.zeros(len(self.anchors), int)
        for ch, sym in cue.items():
            score += self.anchors[:, ch] == sym
        best = score.max()
        if best == 0:
            return None
        return int(rng.choice(np.where(score == best)[0]))

    def complete_checked(self, cue, signal, rng):
        """E: completion, then the green dot: open only if the book is the sender's book."""
        i = self.complete(cue, rng)
        if i is None:
            return None, False
        return (i, False) if self.signal(i) == signal else (None, True)


def spread(links, deficit, budget, to_lack=True):
    """Green flow after an open: a fixed budget goes to the linked subnodes; effect bounded by each lack."""
    d = np.array([deficit[j] for j in links], float)
    if to_lack:
        w = d / d.sum() if d.sum() else np.ones(len(d)) / len(d)
    else:
        w = np.ones(len(d)) / len(d)
    return float(np.minimum(w * budget, d).sum())
