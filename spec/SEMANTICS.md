# RSOS Language 0.2: execution semantics of the simulation runtime (day 2)

Fixed in code (`src/rsoslang/runtime/`) and tested (`tests/test_runtime.py`) **before** the day 2 experiments were
run. Parameters: K = 7 functional properties per module; contact radius RHO = 0.35; proximity weight 0.2; cost 0.002
per link; 3 propagation steps.

## World

- **Object.** Modules at depth 0 (surface), 1 (body), 2 (sub-code). Each module has a position in the object's frame
  and a property vector of length K. The object has a position and a rotation.
- **Placement.** Surface modules of different objects within RHO of each other get a weak proximity link (0.2). This
  is what moving an object onto another does by itself.
- **Execution.** Each module starts at tanh(props · drive) × health. For 3 steps, each link adds
  w × cos(props_src, props_dst) × activation_src / √indegree, then tanh is applied. Compatible functions reinforce;
  incompatible ones interfere.
- **Utility.** tanh of (active modules' properties · environment target), minus 0.002 per link. With `sinks_only`,
  only modules at the end of directed paths count, so direction matters.

## Operators

| Operator | Effect |
|---|---|
| TOUCH, ATTACH | One contact, shaped by the entry meaning: `interface_only` = one link to the nearest surface module; `dependency` = one link (1.0) to the outermost module; `supervisory_entry` = links (0.25) to every surface module; `lateral` = two-way links (0.5) to the two modules facing that side; `local_contact` = one link (0.6) at the contact point; `nested_state` = a link (0.7) into depth 1 |
| PIERCE | If the objects overlap: every co-located pair of surface modules gets two-way links (1.0), plus links down through the layers (0.7, 0.5) on **both** sides (each side sees the other), plus links (0.3) to neighbouring modules (1–1.6 RHO). If they don't overlap: a spear from the source along the line to the target, linking the target's modules within RHO of the line at every depth up to DEPTH. Then the entry-side meaning is applied (FROM) |
| PASS | Links (0.8) from the source into every module of the arrival point (whole sub-part or sub-sub-part). Nothing is replaced |
| DOT | A new module (the function's properties) inside the target, one level deeper, linked both ways (1.0). The target's own properties are unchanged |
| MOVE | Source placed at the target's position |
| ROTATE, FLIP | Rotation of the object frame; mirror of module positions |
| OVERLAY … SHOW half | Source placed on target; the source's left half and the target's right half are hidden |
| PROTRUDE | Links (0.2) from the part to every module of other objects within 2 RHO |
| FUSE | A new object holding both parents' modules, with two-way links (0.5) across surface pairs |
| ENTER | Selections in that object may reach this depth |
| REGION | Modules inside the shape (point, circle, square, triangle) around the centre, up to the entered depth |
| LINE | Directed links (w1 × w2) from each selection to the next. A whole object = its surface modules, each weighted 1/n (spread); a part = that module at full weight (plus deeper ones if entered) |
| WIDEN | Links (0.3) from the line's modules to surface modules within RHO + radius (× 2 for volume) |
| TRANSPLANT | The target modules take the mean properties of the whole bundle |
| REHOST | The bundle's modules are copied into the host at depth 1 and linked (0.5) to the host's surface modules |
| HEAL | Health set to 1; negative properties halved; incompatible incoming links damped × 0.3. Scope `container` = all modules; `network` = plus linked modules; `higher` = plus BEAM down |
| BEAM | Properties of all lower layers (and other objects' modules at the same or lower layer) move 30% towards the source |
| FLOW | vertical / down / up: links (0.6) to other depths of the same object; horizontal: links (0.4) to same-depth modules everywhere; outward: links (0.3) to other objects' surfaces; inward: links (0.6) to deeper modules |
| SHIFT, COLOUR | black: properties become −|base| (destructive only); grey: negatives halved, +0.1 protection |
| ROUTE | One link per state; active only while the host is in that state (USE STATE) |
| RESONATE | Properties move 30% towards the other; a link (0.5) back |
| COMPRESS | A new symbol module with the mean properties of the items, linked (0.5) to each |

Mental-model, cue and governance statements compile to the cue framework (day 5); the simulation does not run them.
