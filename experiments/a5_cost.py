"""A5 cost model: token counts x price table (experiments/a5_prices.json). PREREGISTRATION_A5.md section 4.

Bases:
  billed  the call as the CLI billed it: input, 5-minute and 1-hour cache writes, cache reads, output.
  api     API-optimal accounting: the CLI scaffold (measured null-call tokens) removed, every remaining input token
          at base input price (no static prefix in any A5 arm reaches the 512-token cacheable minimum, so no cache
          read is available to any arm), output as measured.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def prices():
    return json.load(open(os.path.join(HERE, "a5_prices.json")))


def price_tokens(t, P):
    return (t.get("in", 0) * P["input"] + t.get("cache_w5m", 0) * P["cache_write_5m"] +
            t.get("cache_w1h", 0) * P["cache_write_1h"] + t.get("cache_r", 0) * P["cache_read"] +
            t.get("out", 0) * P["output"]) / 1e6


def call_cost(r, P, basis, scaffold=0.0):
    if basis == "billed":
        w5, w1 = r.get("cache_w5m", 0), r.get("cache_w1h", 0)
        if w5 + w1 != r.get("cache_w", 0):               # older records without the TTL split: 5-minute
            w5 = r.get("cache_w", 0) - w1
        return price_tokens({"in": r["in"], "cache_w5m": w5, "cache_w1h": w1, "cache_r": r["cache_r"],
                             "out": r["out"]}, P)
    content = r["in"] + r["cache_w"] + r["cache_r"] - scaffold
    return price_tokens({"in": max(content, 0), "out": r["out"]}, P)
