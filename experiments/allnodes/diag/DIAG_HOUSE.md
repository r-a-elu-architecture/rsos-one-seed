# The house as the architect: quick test (23 Nov 2026 ~04:45, UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius)
house.py; development seeds: growth 7300-7301, evaluation 7310-7312; 11 odd shades; 33 paired runs. Descriptive.
| House vs | wins / losses / ties | p (one-sided) | mean gain |
|---|---|---|---|
| flat (all roles of the same 4 objects at once: same content, no routing) | 24 / 5 / 4 | 0.0003 | +0.0095 |
| shuffled (same objects, rooms permuted: switching without reading the state) | 18 / 9 / 6 | 0.061 | +0.0014 |
| fixed (best single object of the same 4, chosen on the same growth seeds) | 13 / 10 / 10 | 0.34 | +0.0002 |
| best native | 33 / 0 / 0 | <0.0001 | +0.0287 |
Channels house <= fixed on both: 25/33. The house used more than one object in 9/11 shades.
Reading: the same content organised by state (rooms) beats the same content as one list, and routing by the read state
beats routing without it; but the house does not beat the best single model of its four (ceiling: all arms ~0.97-0.99).
Caveat for a critic: 'flat' in the twin is the union of roles, itself one (often weaker) structure; the agent host's
flat-list control (identical instruction text) is the cleaner form of problem M.
