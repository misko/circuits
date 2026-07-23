# Fresh-context PIN REVIEW — usb-hub-3s-v3

- Board: `projects/usb-hub-3s-v3/04_kicad/usb_hub_3s_v2.kicad_pcb` (DRC-clean routed)
- Reviewer: fresh-context agent, no design-session history
- Protocol: `skills/kicad-pcb/references/pin-review-protocol.md`
- Method: `pin_audit.py` dossiers (pad→net straight from the board) adversarially
  compared against each part's datasheet pinout figure rendered independently
  (`pdftoppm`), NOT against the authors' `part.yaml` conclusions.
- Date: 2026-07-22
- **VERDICT: PASS** (0 FAIL, 0 QUESTION-blocking; 3 non-blocking notes)

The v3 change dropped the USB-C PD controller in favor of a plain 5V rail +
CC Rp resistors (ADR-0001). Focus parts: **J5** (USB-C), **R28/R29** (CC Rp),
**U2/U11** (LM5116, EP footprint swapped to non-thermal-via), **U3/U4/U5**
(TPS2557, EP footprint swapped to non-thermal-via). All other multi-pin parts
reviewed for completeness and pairwise symmetry.

Dossiers + rendered datasheet figures archived in the session scratchpad; the
BOM ref→MPN map was rebuilt from footprint LCSC values cross-referenced to
`02_parts/*/part.yaml` `sourcing.lcsc`.

---

## v3-touched parts

### J5 — TYPE-C-31-M-12A (16-pin USB-C receptacle, power+USB2)  — PASS
Datasheet HRO TYPE-C-31-M-12A pin table verified against footprint pads:

| pad | datasheet | net on board | verdict |
|---|---|---|---|
| A1/B12/A12/B1 | GND | GND | ok |
| A4/A9/B4/B9 | VBUS | 5VC | ok |
| A5 | CC1 | CC1 | ok |
| B5 | CC2 | CC2 | ok |
| A6/B6 | DP1/DP2 | DPC | ok (both D+ tied — correct USB2 Type-C) |
| A7/B7 | DN1/DN2 | DMC | ok (both D− tied) |
| A8/B8 | SBU1/SBU2 | unconnected | ok (SBU unused in USB2 power) |
| SH ×4 | SHIELD | GND | ok |

**Mirror check (the failure this protocol exists for):** the footprint's
physical left-to-right pad order is
`A1 B12 · A4 B9 · B8 · A5 · B7 · A6 · A7 · B6 · A8 · B5 · B4 A9 · B1 A12`,
which matches the datasheet's edge-contact sequence exactly. Not mirrored —
CC1 (A5) sits left-of-center and CC2 (B5) right-of-center as drawn, DP/DM sides
correct. (`winding` reads "n/a" because all signal pads are a single row; the
left-to-right order check substitutes.)

### R28 / R29 — CC Rp resistors (10 kΩ, 0402)  — PASS
- R28: CC1 → 5VC.  R29: CC2 → 5VC.
- Each CC pin drives exactly one Rp pull-up to the 5 V rail; no Rd pulldown,
  no PD controller. This is the correct **DFP/source** advertisement config for
  a hub output port after dropping PD. CC1 net = {R28.1, J5.A5}, CC2 = {R29.1,
  J5.B5} — no cross-short, no CC1↔CC2 tie.

### U2 / U11 — LM5116MHX (HTSSOP-20 + EP, buck controllers A & C)  — PASS
Datasheet SNVS499I Figure 4-1 (PWP top view) verified pin-for-pin. Standard
DIP-style numbering: pin-1 dot top-left, down the W side (1–10), up the E side
(11–20); dossier computed **CCW**, pin-1 at (−2.86,−2.92) top-left — matches.

Electrical sanity (U2 = rail A / U11 = rail C, structurally identical):
VIN(1)=VIN · VOUT(10)=5VA/5VC · SW(20)=SW_A/SW_C · HO(19)/LO(15)=gate nets ·
HB(18)=BOOT · CS(12)/CSG(13)=sense pair · FB(8)=divider · VCC(16) · UVLO/RT/EN/
RAMP/SS/COMP = instance-local. AGND(6)/PGND(14)/DEMB(11)/VCCX(17)/EP(21)=GND.
DEMB→GND = diode-emulation (pre-bias safe) per datasheet; VCCX→GND = external
bias unused, both valid. EP correctly on GND (the non-thermal-via footprint
swap changes only via count, not the pad's net).

### U3 / U4 / U5 — TPS2557DRBR (VSON-8 + EP, USB-A load switches)  — PASS
Datasheet SLVS931B DRB top view verified: pin-1 dot top-left, GND(1) IN(2)
IN(3) EN(4) down W side, ILIM(5) OUT(6) OUT(7) FAULT(8) up E side; dossier
**CCW**, matches. Per-instance nets are cleanly symmetric:

| ref | IN(2,3) | EN(4) | OUT(6,7) | ILIM(5) | GND(1)/EP |
|---|---|---|---|---|---|
| U3 | 5VA | 5VA | VBUSA1 | ILIM1 | GND |
| U4 | 5VA | 5VA | VBUSA2 | ILIM2 | GND |
| U5 | 5VA | 5VA | VBUSA3 | ILIM3 | GND |

EN tied to IN (5VA) = always-enabled (TPS2557 is active-high EN) — correct.
FAULT(8) unconnected — see Note 1. EP on GND; non-thermal-via swap is
connectivity-neutral.

---

## Other multi-pin parts (completeness + symmetry)

### Q1 — AON6403 (P-ch, DFN5x6, reverse-battery protection)  — PASS
Datasheet AOS AON6403: pins 1–3 = S, pin 4 = G, pin 5 (+ perimeter) = D.
Board: S=VIN, G=RPP_G, D=VBAT_F. P-channel body diode (anode=D=VBAT_F,
cathode=S=VIN) conducts battery→load and blocks a reversed battery — correct
RPP orientation. CCW, pin-1 top-left.

### Q2–Q5 — AON6354 (N-ch, DFN5x6, synchronous buck FETs)  — PASS
Same DFN5x6 map (1–3 S, 4 G, 5 D). Buck FET pairs are symmetric A vs C:

| ref | role | D | S | G |
|---|---|---|---|---|
| Q2 | HS buck A | VIN | SW_A | HO_A |
| Q3 | LS buck A | SW_A | CS_A | LO_A |
| Q4 | HS buck C | VIN | SW_C | HO_C |
| Q5 | LS buck C | SW_C | CS_C | LO_C |

High-side drain=VIN, source=switch node, gate=HO; low-side drain=switch node,
source=current-sense shunt node (CS_x), gate=LO. Textbook synchronous buck.

### U6 / U7 — TPS2513A (SOT-23-6, USB charging-port controllers)  — PASS
Datasheet SLVSBY8D DBV: DP1(1) GND(2) DP2(3) DM2(4) IN(5) DM1(6). CCW.
- U6 serves ports A1 (DP1/DM1) + A2 (DP2/DM2), IN=5VA.
- U7 serves port A3 (DP1/DM1); DP2(3)/DM2(4) unconnected (unused 2nd channel —
  valid, D± detect pins may float).

### U8 / U9 / U10 / U12 — USBLC6-2SC6 (SOT-23-6, ESD)  — PASS
Datasheet ST Figure 1: I/O1(1) GND(2) I/O2(3) I/O2(4) VBUS(5) I/O1(6). Both
I/O1 pins on the port's D+ net, both I/O2 on D−, VBUS on the port rail. CCW.

| ref | I/O1 (1,6) | I/O2 (3,4) | VBUS(5) |
|---|---|---|---|
| U8 | DP_A1 | DM_A1 | VBUSA1 |
| U9 | DP_A2 | DM_A2 | VBUSA2 |
| U10 | DP_A3 | DM_A3 | VBUSA3 |
| U12 | DPC | DMC | 5VC (USB-C) |

### J2 / J3 / J4 — KH-AF90DIP-112 (THT USB-A receptacles)  — PASS
Pads monotonic left→right: 1=VBUS, 2=D−, 3=D+, 4=GND, shells=GND — the
industry-fixed USB-A receptacle contact order. Ports A1/A2/A3 map to
VBUSA1/2/3 + DP/DM_A1/2/3. Verified against the USB mechanical standard and
the `part.yaml` note documenting this part's prior fresh-context review (it
replaced a mis-identified USB-A *plug*); not re-rendered from the vendor
figure as it is not a v3-touched part.

### F1 (fuse) + J1 (XT60 battery inlet)  — PASS
Battery path is coherent: J1.2=VBAT / J1.1=GND → F1.1(VBAT) → F1.2(VBAT_F) →
Q1 RPP → VIN → LM5116 bucks + HS-FET drains. No net breaks.

---

## Non-blocking notes (not FAILs)

1. **FAULT / unused-channel pins float.** U3/U4/U5 FAULT (open-drain) and U7's
   second channel (DP2/DM2) carry no net. Autonomous current-limit still works;
   the FAULT flag is simply unreadable (no pull-up). Design choice, connectivity
   valid. P2.
2. **USB-C advertises 3.0 A, not 5 A.** R28/R29 = 10 kΩ Rp to 5 V advertises the
   Type-C legal maximum of 3.0 A on J5; 5 A would require an e-marked cable + PD,
   which v3 deliberately dropped. The "5 V/5 A" figure is the aggregate rail, not
   the single USB-C port. Self-consistent, spec-legal. S5 design-math, P2.
3. **J2/J3/J4 accepted on USB-standard + prior-review evidence** rather than a
   fresh vendor-figure render (THT USB-A contact order is mechanically fixed by
   the USB spec, and the part carries a documented earlier pin review). P2.

No winding, power, gate, or sense pin is mis-mapped. No mirrored footprint.
The board is clear to order on pin-mapping grounds.
