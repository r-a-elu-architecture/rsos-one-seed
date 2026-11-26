# T9 pre-registration: the discovery engine (written before running)

Owner, chat 2 T35: "it can be preprogrammed how many spatial connections might be and which ones … the agent might
compute those differences and find the best". Chat 2 T47–T48: a discovered function becomes an operator.

**Engine (`src/rsoslang/discovery.py`).**
1. **Search:** every placement of every guest (the 800 programs of the editor), scored on a **search set** (seed 11,
   500 tickets, same mix), not on the held-out sets.
2. **Removal test:** the best program minus each gesture in turn; what each gesture carries.
3. **Induction:** for each guest, the place that scores best becomes a rule (a new operator: `PLACE_BEST guest`).
4. **Transfer:** the induced rule applied to a **different host**: the same workflow with a different ticket mix
   (seed 21: 50% typos, 10% unseen phrasing).

| # | Hypothesis | Pass rule |
|---|---|---|
| H1 | The program found on the search set holds on held-out A and B | Its held-out score is within 0.02 of the best held-out score among the 800 |
| H2 | The removal test locates what carries the function: removing at least one gesture costs ≥ 0.05 score, and removing at least one costs < 0.01 | Both hold |
| H3 | The induced rule transfers to the different host | Rule-built program beats the baseline there by ≥ 0.05 score |
