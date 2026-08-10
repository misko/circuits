subject: programmable-usb2-hub pre-route board c4b42a9f
date: 2026-08-01
reviewer: independent-agent (GPT-5, physical-pin and changed-passive lens)
context-given: full-tree
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
review_stage: pre-route
review_kind: pin
source_commit: e822cf5a23d42b66bd41bae380237f1e121e8448
board_sha256: c4b42a9fe8c78850c720bdd5e9b036805dfe9cf634ab706654004491da97918a
parts_sha256: 10c59b6a9f25a72db20eb258863b209572a3c61ccf0e15fcde4b981541f5d796
design_rules_sha256: 72399b539bd768d1ca45d22fa0402573c75665e57052ab0559de70465a8accb7

# Independent pre-route pin review

This review is bound to the exact track-free placement board above. It does
not approve placement, rendering, routing, sourcing, or ordering.

## Evidence and findings

- `pin_map_check.py` graded 33 multi-pin references and 385 declared physical
  pin identities: 385/385 reached both producer artifacts, with every fused
  identity explicit and evidenced.
- Q3-Q6 preserve eight AON6266E physical identities: sources 1-3, gate 4,
  and drains 5-8. High-side devices bind sources to SW, gate to HO and drains
  to VIN; low-side devices bind sources to CS, gate to LO and drains to SW.
  No pin collapse or source/drain reversal was found.
- Restored R38-R41 each bind the corresponding `P1_PWR_CMD` through
  `P4_PWR_CMD` net on pad 1 to GND on pad 2. This implements deterministic
  reset-state pull-downs without crossing command identities.
- New R111 and R211 preserve channel symmetry: pad 1 is `FBTOP_A/B`, and pad
  2 is `FB_A/B`. Neither channel is swapped.
- J2-J6 signal and shell pads remain explicit. J2's two physical shell lands
  share pad 5 only under the dossier's `fused: true` declaration; no signal
  contact is collapsed into the shell identity.

## Verdict

`design_verdict: SOUND` for physical pin identity on these exact bytes. The
order verdict remains DO-NOT-ORDER because the companion placement and render
reviews found blocking defects on the same board.
