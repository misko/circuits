# journal: placement

## 2026-07-23 — start
- did: authored 03_src/floorplan.yaml from the analog-audio-pod archetype +
  audit_board.py (P-POL/P-KEEP polarity + mate/keepout gate). RJ45 west (mouth
  off the edge), ESD near the audio tails, analog cell + mic east, beep block
  SW, TPs south, GND both-layer pours.
- result: generate_board placed 35 + 4 holes, 10 pad_net asserts pass.
- next: clear the placement gates.

## 2026-07-23 — iterate (placement grind, ~8 cycles)
- did/result (each measured):
  - J1 rot: 270 put the mouth INWARD + LED pads off the west edge (audit_board
    caught x=9.4 < 10). Fixed to rot 90 (mouth west, pads on-board).
  - Courtyards: D_SMA courtyard is 7mm wide -> D2/D3 spaced to 43/51; RC filter
    (R1/C1) moved SE out of the crowded beep zone; rail bulk (C9/C10) moved east
    of the RJ45 courtyard; J1 shifted south (16.6->18.6 top) to clear H1.
  - D1 SOT-553 inter-net AUDIO-vs-GND pad gap ~0.15mm tripped the 0.2 default
    clearance -> local pad clearance 0.13 (pad_override; still >= tier floor
    0.127). D-TIER honoured.
  - Silk: captions must be >= 0.6mm (at 0.45 the min 0.15 stroke gives ratio
    0.33 -> text_thickness DRC). CMT-8504 vendored footprint body rect crossed
    its own pads -> removed (kept courtyard + polarity mark). J1 connector body
    silk overhung the west edge (x7.9 < 10) -> J1 set back east to x19.5
    (enclosure-recessed mouth; horizontal plug still clears the edge).
    P-SILK-FN: per-TP net labels + a short "J1 NOT ETHERNET" at the connector.
- MEASURED: pre-route DRC **0 violations / 0 courtyard / 0 silk** (61 unconnected
  = unrouted, expected). audit_board OK. policy_audit: only R-DRC (unconnected)
  outstanding; S-VER/P-LAYOUT/P-ADJ/P-CRT/P-POL/P-KEEP/P-SILK-FN all PASS (17).
- next: KRT routing -> DRC 0/0/0.
