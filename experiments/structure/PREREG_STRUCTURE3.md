# PREREG STRUCTURE3 (24 Nov 2026 ~11:15, UTC+02:00). Layer 2, development quick test, no colour. Pushed before the run.
Owner OK 11:09 ("yes") to IDENT_STRUCTURE3.md with the advice: D = the child's own continuation (K.2 applied to the child);
LE = option (b), the check unchanged, its replays on 60-tick worlds.
Cells as STRUCTURE2: D shades 4, 10 x seed 6720; LE shades 4, 10 x seed 6670.
Checks (unchanged from PREREG_STRUCTURE2): D_B1 child > best parent in both cells; LE_relations every (shade, channel) row
within tolerance at windows 2, 4, 8. All other checks carried from STRUCTURE2 (same code and seeds, deterministic).
TABLE_FILLED = all checks pass. Failure -> step 1, no variations.
Note fixed now: in the layer-2 twin the replays share the world's randomness (common randomness), so the child's own
committed continuation is a future it can follow exactly; if a parent's own run is its best option the child equals it,
and B1 needs the child to find a strictly better (option, continuation).
