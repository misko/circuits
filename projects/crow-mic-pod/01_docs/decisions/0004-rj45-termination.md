> Adopted 2026-07-21 into crow-mic-pod from archived_projects/crow-array-pod (ADR-0005 provenance; re-verified by this project's own gates). Original text follows.

# ADR-0004 — RJ45 jack termination (supersedes ADR-0003's terminal section / D6)

Status: accepted 2026-07-19 (drives release v1.1)

## Context

A4 (BRIEF, 2026-07-19): user utterance "i would rather have a ethernet
terminal on the pod". The pod cable termination changes from the 8-pos
3.5mm screw terminal (D6, ADR-0003) to an RJ45 jack — the SAME part the
central board uses on all its pod ports: **Amphenol RJHSE-5384**
(right-angle, shielded w/ top EMI tabs, built-in green/yellow LEDs left
unconnected). The Cat5e still passes through the M12 gland; the cable is
FIELD-CRIMPED to an RJ45 plug inside the enclosure and plugged into the
board jack. ADR-0003's outline section (D4) is unchanged.

## (a) Net mapping — old terminal n = T568B pin n = RJ45 contact n, 1:1

The jack's contact n takes exactly the net the screw terminal's position n
carried in v1.0. Verified against BOTH interop authorities:

| RJ45 pin | pod net (v1.0 = v1.1) | central v1.0 sealed map (D28) | Rev-A doc §4 table |
|---|---|---|---|
| 1 | AUDIO_P | AUD_Pn | orange: AUDIO+ |
| 2 | AUDIO_N | AUD_Nn | orange: AUDIO- |
| 3 | BEEP_5V | BEEP_5Vn | green: +5V_BEEP |
| 4 | 5V | 5V_AUDn | blue: +5V_AUDIO |
| 5 | GND | GND | blue: GND_AUDIO |
| 6 | BEEP_RET | BEEP_RETn | green: BEEP_SWITCHED_RETURN |
| 7 | 5V | 5V_AUDn | brown: +5V_AUDIO |
| 8 | GND | GND | brown: GND_AUDIO |
| 9-12 | no_connect (LED tails) | no_connect | — |
| SH | SHIELD (see b) | GND (star bond) | — |

Each of the blue/brown pairs carries feed+return (4=5V/5=GND, 7=5V/8=GND)
per the central's D28 — the central v1.0 sealed release is the interop
authority and the pod matches it contact-for-contact. A straight-through
T568B-crimped cable is therefore correct end-to-end. Contact current
rating 1.5A/contact >> 150mA beeper peak and ~6mA pod draw.

## (b) RJ45 shield -> the existing D7 bond provision

The jack's two SH tails land on the pod's existing **SHIELD** net: TP6
(bond pad) + R15 (DNP 0805) to GND — the D7 shield-bond reserve, unchanged.
Pod-side shield stays FLOATING by default; the central end carries the
single-point star bond to GND (central D28). This preserves the source
doc's "start unshielded; reserve shield-bonding pads" posture AND avoids a
ground loop through the (currently unshielded) cable if shielded cable is
ever fitted. To bond at the pod for EMI testing: populate R15 (0R).

## (c) Mechanical clearance inside the Hammond 1551WY

All numbers from 01_docs/hammond_1551wy_rev2023-08-31.pdf and the Amphenol
catalogue p.4 (RJHSE-548X drawings; 300dpi renders re-measured 2026-07-19):

```
Enclosure interior height   24.00 − 2.50 (base wall) − 2.20 (lid wall) = 19.30
Board stack                 4.00 (posts, section B-B) + 1.60 (PCB)     =  5.60
Headroom over board, INSIDE the lid's 81 x 31 mm recess: 19.30 − 5.60  = 13.70
Headroom over board, under the ~6.4mm perimeter band where the lid
  underside descends to the parting line (16.00 − 2.50 = 13.50):
  13.50 − 5.60                                                         =  7.90
Jack body height            13.46 ± 0.38  ->  nominal margin +0.24 mm
                                              worst-case body  −0.14 mm
Top EMI spring tabs         ~1.5-2 mm proud of the body (undimensioned)
                            -> compress against the polycarbonate lid
Exposed plug top            ~10-11.5 mm above board  (< 13.70, > 7.90)
```

**Verdict: CONDITIONAL FIT.** Nominal body clears the lid recess by
0.24 mm; the sprung top tabs will touch and flatten against the (insulating)
lid — mechanically and electrically harmless, slight preload. At the
+0.38 mm body tolerance extreme there is 0.14 mm of nominal interference —
within polycarbonate lid flex/gasket compliance, but **FIRST-ARTICLE GATE:
close the lid on an assembled pod before building the fleet**; if it
binds, flatten/trim the two top EMI tabs (shield is DNP-bonded anyway);
documented fallback part: RJHSE-L384 low profile, 12.70 mm (verify hole
pattern before substituting).

Placement constraints derived from the same math (encoded in
generate_board.py + audit I2):

- The full-height lid recess is the central **81 x 31 mm** (board coords
  x 56.75-137.75, y 56.75-87.75). The jack BODY (13.46 tall) and the
  EXPOSED PLUG (~10-11.5 tall, protruding ~12 mm west of the jack face)
  must BOTH sit inside it: jack mating face at board x ≈ 70.0 ≥ 56.75+12.
- **FACE-SIDE CORRECTION (2026-07-19, the v1.1 fresh pin review's catch):
  the mating face is on the SNAP-POST side of the hole pattern (footprint
  local -y; catalogue side view: face->post .215 [5.46]), and the LED
  tails sit 1.15 mm from the REAR.** The first v1.1 layout used the
  inherited (inverted) "LED tails mark the face" doctrine and mounted the
  jack 180 deg backwards — opening EAST into the board. Corrected to
  rot 90 (posts west of contacts, LED tails east); generator + audit
  asserts now key on the NPTH posts, and the part.yaml doctrine is fixed.
  The central board's jacks are placed correctly (rot 0, openings north).
- **Orientation: side-entry, opening WEST toward the gland wall** (the
  M12 gland sits on the west end per ARCHITECTURE) — the crimped plug
  points east into the jack, the cable exits west toward the gland with a
  near-straight run at gland height; the service loop lives between plug
  and gland. Under the perimeter band only the CABLE passes (≤ ~7 mm
  above board < 7.90 headroom) — use bootless or slim-boot plugs.
- LATENT v1.0 FINDING (superseded anyway): the v1.0 screw terminal
  (KF128L class, ~10.4 mm tall) had its body within ~4 mm of the west
  board edge — i.e. under the perimeter band with only 7.90 mm headroom.
  The lid would likely not have closed. v1.0 never ran this height math
  (twin edge renders had no model for the uncoded terminal); v1.1 adds it
  here and moves ALL tall bodies inside the recess.

## (b2) Entry ESD clamp position (D1) — accepted deviation note

The v1.1 fresh-context pin review flagged D1 (TPD2E2U06) at ~11.6 mm from
the J1 audio tails vs the datasheet's "as close to the connector as
possible". ACCEPTED, with reasons: (1) the RJHSE-5384 is a THT jack whose
contact tails sit under a 15.75 mm-deep body — the courtyard's east edge
(x 86.6) is the physically closest legal component position, and D1 sits
directly against it; (2) topology is clamp-FIRST: the routed AUDIO_P/N
tracks run J1 tail -> D1 IO pin -> onward to R13/R14/L1 (verified from
the routed board's net order), so the full strike current reaches the
clamp before any protected element; (3) v1.0 (sealed) shipped the same
~12 mm figure with the screw terminal. The extra ~9 nH of pre-clamp trace
slightly ADDS series impedance ahead of the clamp — not a protection
regression.

## (d) Silkscreen safety policy (P5 / P-SILK-FN)

- "NOT ETHERNET - CUSTOM 5V PINOUT" stays prominent DIRECTLY next to the
  jack (west, above the plug zone — permanently visible with plug in),
  in addition to the north-center banner.
- The per-contact function map moves from the old terminal-side words to a
  compact legend printed in the plug zone west of the jack: readable
  during field crimping/bring-up (no plug inserted), covered only when a
  plug occupies the jack — at which point the wiring is already committed.
- The jack's own contact numbering follows the 8P8C standard (part.yaml
  pin-1 convention note), so the legend + T568B is sufficient to crimp.

## Assembly consequence (ORDER_README)

JLC does not stock the jack (consign-only, stock 0) — it stays a
hand-solder line (Digi-Key RJHSE-5384-ND), 16 joints + 2 board locks per
pod, replacing the terminal's 8 screw joints. Field side: crimp a
**solid-core-rated** RJ45 plug (24AWG solid Cat5e) inside the enclosure
after passing the cable through the gland; T568B order; bootless/slim
plugs only.
