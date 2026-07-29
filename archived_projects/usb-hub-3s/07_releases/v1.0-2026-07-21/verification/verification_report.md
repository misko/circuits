# usb-hub-3s — verification report (2026-07-21)

## Gate scoreboard (all measured, all green)

| Gate | Result |
|---|---|
| ERC (severity-all, errors gate) | Errors 0 (208 warnings, baselined env classes) |
| count/netlist parity | 112/112 components |
| audit_board.py | PASS: 13 polarity / 22 proximity / 4 edge / 116 silk |
| KRT route acceptance | NON-J5 failures: NONE (J5 row closed by taps by design) |
| taps | 44/44 routed (incl. 7 thermal via-pair drops) |
| stitch | gate: clean |
| DRC (`--severity-all --refill-zones --schematic-parity`) | **0 / 0 / 0** |
| rebuild_all.sh end-to-end (M3 regenerability) | exit 0, DRC 0/0/0 |
| bom_seed | 48/48 lines coded, 110 assembled; R25 DNP; F1 hand-solder |
| jlc_stock_check (min 5x) | 48/48 OK |
| jlc_twin | exit 0 — 82 OK / 237 checked, every finding adjudicated with evidence |
| policy_audit | FAIL=0 (PASS=20, HUMAN=6 graded below, N-A=4) |

## Fresh-context pin review (3 independent agents, no design context)

Verdicts: **U1 PASS** (48+EP pins independently derived from IP6559 DS
Fig 2/Fig 8-9; winding CCW, no mirror). **U2/Q1-Q8 PASS** (LM5116 map from
SNVS499I; all half-bridges coherent; source-shunt CS/CSG matches).
**U3-U5, U6-U7, U8-U10, J5, F1 PASS** — J5's custom EdgeTrim footprint
matched the mirror-sensitive A/B row signature exactly. **J2-J4 FAIL →
FIXED** (see below).

### Review catches (both fixed before release)
1. **J2-J4: the sourced part was a USB-A MALE PLUG rated 1.5A** (its own
   drawing title "USB 4P AM SMT"). Machine gates passed because footprint,
   netlist and silk were consistently wrong together. Replaced with
   Kinghelm KH-AF90DIP-112 female THT receptacle (C503996); vendored
   footprint from the vendor drawing; jlc_twin re-fit = 0.00 mm against
   JLC's own model. ADR 0006.
2. **U6/U7: TPS2513 (non-A) claimed the A-only 2.7/2.7 V Apple-2.4A
   divider.** Promoted the recorded alternate TPS2513ADBVR (C473910).

### Question dispositions (designer answers, board-verified)
- U1 PATH_G fanout → exactly one gate: Q8.4 (path NFET). CLOSED.
- EMK/Vconn mapping → EMK1(GPIO22/47)→Q10→VCONN_G1→Q9→**CC1**;
  EMK2(GPIO21/46)→Q12→VCONN_G2→Q11→**CC2** — matches DS Fig 9. CLOSED.
- Kelvin polarity → P-taps sit on the current-entry ends on both shunts:
  RS2.1(VIN)→R14→SNS_IN_P; RS3.1(VOUT_PDS = H-bridge output side)→R18→
  SNS_OUT_P; N-taps mirror on the far ends. CLOSED.
- PCON/PCIN networks → 10 Ω + filter caps per DS Fig 8 (DETAIL_DESIGN
  value table). CLOSED.
- PDO_CFG → single 1%-class 0603 slot to GND, DNP by ADR 0004. CLOSED.
- U2 VCCX=GND → documented "unused" strapping; VCCX←5VA efficiency option
  deliberately not taken v1 (SS ramp interaction untested). ACCEPTED.
- U2 DEMB=GND → diode-emulation mode intended (pre-biased-start safe).
  ACCEPTED.
- Q8 single path FET cannot block VBUS back-drive when off → this is the
  IP6559 DS Fig 8 reference topology (chip senses VOUTI/VOUT2 across the
  FET and owns its gate); source-only port. ACCEPTED per reference.

## Fresh-context render review (1 agent, no design context)

- Polarity: C1/C2/C26 and D1-D7 all AGREE (model band vs silk).
  D8/D9 (SOD-523, featureless model) CANNOT be visually adjudicated →
  electrically verified (pad1=K on the data line per part.yaml + audit
  I-POL) and added to the ORDER_README JLC-preview ritual.
- XT60 "+" assignment rests on our footprint (pad1='−' was verified from
  the XT60PW-M drawing at parts stage, audit I-POL asserts J1.2=VBAT at
  the "+" silk) → first-power continuity check in ORDER_README.
- Connector orientation/overhang: all correct (XT60 west, USB-C south,
  USB-A east) — re-verified after the receptacle swap.
- PAD-GEOM dispositions: all recorded in 03_src/rules/twin_adjudications.yaml
  (the reviewer saw a pre-adjudication report).
- Cosmetic notes accepted for v1.0, recorded for a future spin: no silk
  cathode bar on D1/D8/D9 (fab layer carries it); assembly-PDF refdes
  collisions on D8/D9; pcb_layers.pdf trailing page; tscircuit schematic
  render is machine-placed (ADR-0002 ships it as-is).

## HUMAN-graded policy items

- S5 design math: DETAIL_DESIGN.md derives every value (UVLO 9.65/8.84 V,
  RILIM 36.5 k → 2.72-3.29 A, CRAMP 330 pF, L1 12.7 A peak, Fig 8/9 set).
- S6 schematic readability: tscircuit render shipped per ADR-0002; graded
  weak-but-contractual by the render review.
- S7 decoupling: per-pin 100 nF + bulk per rail verified in the pin review
  net tables (U2.16 VCC, U1.29/32, TPS2557 IN pins).
