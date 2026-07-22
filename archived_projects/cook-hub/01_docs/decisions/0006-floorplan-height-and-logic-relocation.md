# ADR-0006 — Holistic floorplan: +8 mm height + coil-driver logic to the east strip

Context: the promoted schematic (176 cells, ERC 0) is SEALED and unchanged. The
first board generation ran clean but the pre-route placement audit failed 8 ways
(I1 J1 barrel pads past the south edge; I8 six unsanctioned refdes waivers; IP
four decouplers stranded from their ICs; plus ~11 real anchor-on-anchor courtyard
collisions — U11↔D2, U12↔J9, CE1↔U11, U10↔U3, U15↔U3, J5↔J3, J13↔J12, J10↔J6,
SW1↔J2, …). Root cause was a SELV floorplan squeeze: the Pico 2 socket is a
24×52 mm block mid-west (x30–54, y58–110), seven connectors stack the west edge
(y36–110), and the original 112 mm-tall board left only a ~25 mm south strip that
had to hold power entry + safety/watchdog + E-stop schmitt + Pico bottom + two
shift registers + opto + ESD + six south-edge connectors. The incremental
legalizer cannot untangle that — it needs a deliberate floorplan.

## Decision

Do BOTH modest moves the brief authorised (§8.2 requires only an
"enclosure-compatible outline" + mounting holes; no fixed enclosure exists):

1. **Grow board height Y 132 → 140 mm (112 → 120 mm tall, board now 185 × 120).**
   Cheap because the outline is discretionary. Buys a genuine third south row.
   South mounting holes track to y = 136; the isolation geometry (bank y44–97,
   inter-column + west-guard slots, NOGO y ≤ 106.8) is entirely north of the
   growth and is UNCHANGED.

2. **Relocate the SELV coil-driver logic chain into the empty east-south strip
   (x 100–205, south of the relay bank):**
   - U3 (74HC595 #1) → (112, 120), south-east of its ULN U5 (K1–K8).
   - U4 (74HC595 #2) → (170, 120), south-east of its ULN U6 (K9–K16).
   - U10 (LTV-817S contactor opto) + U15 (USBLC6 ESD) → (99/110, 127), directly
     above the contactor connector J10 (99, 136).
   - E-stop/door schmitt U11 (74HC14) → (90, 120), with its RC filters moved to
     the receiver side (R31/R32/C31 estop below, R33/R34/C33 door above); the
     ESD parts D3/D4 stay at their west entry connectors J8/J7.

3. **Dedicate the freed west-south corner (x 24–66) to power entry + safety.**
   Power column F1→Q3→D2→D1→CE1→U12 at x 28–53, y 117–124; watchdog/gate chain
   U7→U8→U9 with Q1/Q2 around x 55–90, y 108–118. Decouplers seed/pin at their
   ICs (C12@U3, C13@U4, R11@U7, C21@U14 pinned as anchors where the dense
   clusters otherwise pushed them off-limit).

South-edge connectors respaced along the wider edge: J1(37) J9(55) J6(76)
J10(99) J12(122) J13(143), each ~20 mm apart (was 14–16 mm and colliding). J1
barrel pulled to y = 129 so all copper pads sit inside y = 140 while the jack
body still overhangs the south edge for plug access (I1).

Analog corner (MAX31856/thermistor/K-type/HX711-digital entry, U1 + dividers)
stays NW, away from the coils (§8.3) — unchanged.

## Isolation zone (unchanged, re-verified after the move)

- Creepage/clearance floor ISO_MIN = 6.0 mm. Audit I-ISO min keypad-SELV copper
  distance = **6.12 mm** (binding case: relay K8 pin-8 contact pad ↔ pin-7 coil
  pad — the package's own 7.62 mm row spacing minus two 0.75 mm pad radii).
- Super-column pitch 17.78 mm; **8 milled slots** (2.0 mm wide, y 44–97: seven
  between-column + one west-guard) present in Edge.Cuts.
- No SELV pour/track/KRT copper inside NOGO; silk boundary story intact.

## Consequences

- Pre-route audit **fully green (0 failures)**: I1, I8 (5 waivers, all sanctioned
  tiny 0402/0603 passives + J2 Pico socket, each with an F.Fab copy), I9, I-ISO,
  I-NG, IP, IS, IZ, IW all pass; no unintentional courtyard overlaps.
- U3→U5 / U4→U6 shift-register-to-driver runs are short and stay within the
  south SELV band; the 595→ULN→coil path heads toward the bank.
- The east-far strip (x 120–200) is now the main routing headroom; the west-south
  power/analog return paths are decongested.
- Height +8 mm is an enclosure input recorded here and in the release ORDER_README
  (open §17 item #6: board/enclosure mounting location still TBD).
