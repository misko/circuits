# Fresh-context pin review protocol

Why this exists: a mirror-numbered footprint (pins wound CW where the part
winds CCW) shipped on one board and nearly shipped on a second. DRC, parity,
and polarity checks all passed, because the footprint, netlist, and pin map
were **consistently wrong together**. Automated gates compare the project's
artifacts against each other; this review compares them against the world.

## The setup — independence is the whole point

- The reviewer is a NEW agent with no context from the design session, no
  access to the authors' reasoning, and no stake in the answer.
- Input per part: the `pin_audit.py` dossier (pad positions, sides, computed
  winding, part.yaml functions, actual board nets) + the datasheet PDF path.
- The reviewer's job is to independently derive what SHOULD be true from the
  datasheet, then compare. Never start from the dossier's data and
  rationalize it.

## Checks, per part

1. **Package winding + pin-1 corner.** Render the datasheet's pin
   configuration figure (`pdftoppm -png -r 80 -f <page> -l <page>`), and
   read off: which corner is pin 1, which way do the numbers wind (top
   view), how many pins per side. Compare against the dossier's computed
   winding and the pad table's sides. The dossier's frame may be any
   ROTATION of the figure — rotation is fine, MIRROR is a dead board.
2. **Pin count and exposed pad.** Every datasheet pin exists as a pad; the
   EP is present and on the net the datasheet demands (usually GND or a
   specific plane).
3. **Function ↔ net electrical sanity.** For each pin, ask: given this
   function, what kind of net must be here? Power-in pins see a rail net;
   switch nodes see the inductor net; FB sees a divider net, not a rail;
   gate-drive outputs (HO/LO/DRV) go to exactly one FET gate net; NC pins
   carry no net; grounds (AGND/PGND/EP) are on ground. Flag anything that
   needs design context you don't have as a QUESTION, not a pass.
4. **Pairwise symmetry traps.** For multi-instance parts (two controllers,
   FET pairs), the same pin must map to the same KIND of net on every
   instance (U2 pin 19 = SW_A, U3 pin 19 = SW_B — flag if one instance
   diverges structurally).

## Output format (the orchestrator collects these)

Per part: `VERDICT: PASS | FAIL | QUESTION` plus one line per finding:
`<ref> pin <n> (<function>): <what you expected from the datasheet> vs
<what the dossier shows>`. A FAIL on winding or any power/gate pin blocks
the order. Do not soften: "probably fine" is a QUESTION.

## Orchestration (the main agent's side)

- Generate dossiers: `pin_audit.py BOARD bom.csv 02_parts 06_build/pin_audit`
- Spawn one fresh agent per PART GROUP (controllers; power switches;
  connectors) so no single review exceeds a few parts — attention dilutes.
- Give each agent ONLY: the protocol, its dossier paths, the datasheet
  paths. Not the schematic, not the session history.
- Record verdicts + findings in the release's `verification/pin_review.md`;
  any FAIL reopens the design before ordering.

## Render-review additions (canon S5/S6/S7 — human-graded policy items)

When the fresh-context reviewer examines the schematic PDF, three graded
verdicts are MANDATORY (recorded in the release's render_review.md):

1. **S6 readability**: can you trace power entry -> protection ->
   regulation and the primary signal chain as DRAWN circuits, or must you
   mentally re-net label-blobs? Grade READABLE / EFFORTFUL / OPAQUE, with
   one concrete example. (The fleet audited at 0 drawn wires, 2026-07-17 —
   until generators emit wires, expect EFFORTFUL and say so; the grade
   keeps the debt visible.)
2. **S7 decoupling adjacency**: are decouplers shown at the IC they serve
   (schematic teaches the layout), or farmed in a corner?
3. **S5 design math spot-check**: pick TWO derived values (a divider, a
   current limit) and re-derive them from DETAIL_DESIGN.md. Flag any value
   whose derivation you cannot find.
