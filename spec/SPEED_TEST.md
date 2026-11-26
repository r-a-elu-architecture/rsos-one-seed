# Speed test protocol (roadmap step 7): painting vs code, the owner as the first user

**Question:** is improving a program faster and better through the painting than through its code?

**Tasks (fixed before the test):** five improvement tasks on the 12-module support agent, each with a target on the
search set:
1. fix typos;
2. understand unseen phrasing;
3. cut the cost of memory lookups;
4. stop the crashes;
5. all four together.

**Arms:**
- **painting:** `docs/editor.html`;
- **code:** edit `src/rsoslang/agents/workflow.py` with the guest library available.

Same tasks, alternating order, a fresh task variant per arm.

**Measured:**
- time to the first program that meets the target;
- held-out score of the final program (sets A and B);
- number of attempts;
- errors (programs that fail or score below baseline).

**Pass:** the painting arm is faster on at least 4 of 5 tasks, with held-out score at least as good. One person is a
first measurement, not proof; the protocol is written so others can repeat it.
