"""The communication protocol (T7): a constant structural carrier plus one accent layer per participant.

Chat 2 S58–S61: the main channel is the visual structure (objects and their relations), the same for everyone;
each participant adds an accent layer (its own names, styles); a third participant adds a layer while the main channel
stays constant. Decoding by structure finds where a message's relational pattern sits in the receiver's own world.
"""

import networkx as nx
from networkx.algorithms import isomorphism as iso

RELATIONS = ("above", "inside", "pierces", "flows_to", "same_colour")


def world(rng, n=30, p=0.12):
    g = nx.DiGraph()
    g.add_nodes_from(range(n))
    for a in range(n):
        for b in range(n):
            if a != b and rng.random() < p:
                g.add_edge(a, b, rel=RELATIONS[rng.integers(len(RELATIONS))])
    return g


def vocabulary(rng, n, shared, share=0.2):
    """A participant's private names; a share of them coincide with the shared pool by chance."""
    return {c: (shared[c] if rng.random() < share else f"w{rng.integers(10**9)}") for c in range(n)}


def message(g, concepts, vocab):
    """The carrier (relations between the message's objects) and the sender's accent layer (its names)."""
    sub = g.subgraph(concepts)
    return {"carrier": [(vocab[a], vocab[b], d["rel"]) for a, b, d in sub.edges(data=True)],
            "accents": [{"participant": "sender", "names": [vocab[c] for c in concepts]}]}


def add_accent(msg, participant, rename):
    """A further participant adds its own layer; the carrier is not touched."""
    msg = {"carrier": list(msg["carrier"]), "accents": msg["accents"] + [{"participant": participant,
                                                                          "names": [rename(x) for x in msg["accents"][0]["names"]]}]}
    return msg


def decode_by_names(msg, vocab):
    inv = {v: k for k, v in vocab.items()}
    return {name: inv.get(name) for name in msg["accents"][0]["names"]}


def decode_by_structure(msg, g):
    """Find the message's relational pattern inside the receiver's world (typed subgraph match)."""
    m = nx.DiGraph()
    for a, b, rel in msg["carrier"]:
        m.add_edge(a, b, rel=rel)
    for nme in msg["accents"][0]["names"]:
        m.add_node(nme)
    gm = iso.DiGraphMatcher(g, m, edge_match=lambda x, y: x["rel"] == y["rel"])
    for mapping in gm.subgraph_monomorphisms_iter():
        return {v: k for k, v in mapping.items()}
    return {}


def decode_tolerant(msg, g, return_score=False):
    """Near-match decoding: anchor, extend along the message's relations, keep the mapping that agrees most.

    A relation of the same type counts 1; a relation of another type still lets the mapping extend (counts 0.25);
    no relation at all counts 0. Ties are broken by world-node order, so the result is deterministic.
    """
    m = nx.DiGraph()
    for a, b, rel in msg["carrier"]:
        m.add_edge(a, b, rel=rel)
    for nme in msg["accents"][0]["names"]:
        m.add_node(nme)
    if m.number_of_nodes() == 0:
        return ({}, 0.0) if return_score else {}
    order = sorted(m.nodes, key=lambda x: -m.degree(x))
    mu = m.to_undirected()

    def edge_score(mapping, u, w):
        s = 0.0
        for a, b, d in m.edges(data=True):
            if a == u and b in mapping:
                x, y = w, mapping[b]
            elif b == u and a in mapping:
                x, y = mapping[a], w
            else:
                continue
            if g.has_edge(x, y):
                s += 1.0 if g[x][y]["rel"] == d["rel"] else 0.25
        return s

    best, best_s = {}, -1.0
    anchor = order[0]
    for start in g.nodes:
        mapping, used = {anchor: start}, {start}
        frontier = [anchor]
        total = 0.0
        while frontier:
            u = frontier.pop(0)
            for v in sorted(mu.neighbors(u), key=lambda x: -m.degree(x)):
                if v in mapping:
                    continue
                cands = set(g.successors(mapping[u])) | set(g.predecessors(mapping[u]))
                cands -= used
                if not cands:
                    continue
                w = max(sorted(cands), key=lambda c: edge_score(mapping, v, c))
                total += edge_score(mapping, v, w)
                mapping[v], used = w, used | {w}
                frontier.append(v)
        if total > best_s:
            best, best_s = dict(mapping), total
    if return_score:
        return best, (best_s / len(msg["carrier"]) if msg["carrier"] else 0.0)
    return best


def decode(msg, g):
    """The protocol's decoder: an exact structural match when there is one, otherwise the tolerant near-match."""
    exact = decode_by_structure(msg, g)
    return exact if exact else decode_tolerant(msg, g)
