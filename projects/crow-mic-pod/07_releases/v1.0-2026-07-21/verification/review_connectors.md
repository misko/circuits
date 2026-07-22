# Fresh-context pin review — connector group (J1, J2, L1, BZ1)

Reviewer: fresh-context agent, no design-session context. Expectations derived
independently from the datasheet PDFs (figures re-rendered at 300 dpi and read
directly), then compared against the dossiers and the live board netlist.
Date: 2026-07-21.

## J1 — Amphenol RJHSE-5384 RJ45 jack (Connector_RJ:RJ45_Amphenol_RJHSE538X)

Datasheet derivation (independent): Amphenol Modular Jacks Catalogue 2015-04,
printed p.4, "Shielded - With Top & Side Ground Tabs" RJHSE-548X RECOMMENDED
PCB LAYOUT (single-port figure; per-port hole labels cross-checked against the
multiport RJHSE-538X04 figure, printed p.6 — identical labeling). In the
datasheet's view: contacts run 8 (left) to 1 (right) in two staggered rows,
hole 8 in the row nearer the LED row and leftmost overall, hole 1 in the far
row and rightmost overall; LED holes "12 11" left group, "10 9" right group,
LED row on the far side of the contacts; two shield holes o1.57 at 16.26 mm
span at mid-row height; two NPTH o3.25 at 12.70 mm.

KiCad footprint comparison: the pad table is the datasheet figure rotated
180 deg — pad 1 leftmost in the near row (y=0), pad 8 rightmost in the far row
(y=1.78), LEDs 9,10 left / 11,12 right at y=6.6. Dimensional cross-checks all
match the drawing: contact stagger 1.02 (.040 TYP), in-row pitch 2.03 (.080
TYP), row separation 1.78 (.070), LED pitch within a pair 2.29 (.090 TYP),
LED-row to nearest contact row 4.82 (.190 [4.83]), LED 9-to-12 span 13.72
(.540), shield-leg span 16.26 (.640), NPTH span 12.70 (.500). This is a
ROTATION, not a mirror — pad numbers correspond to true jack contacts 1-8.

Net map vs the system interop contract (1=AUDIO_P, 2=AUDIO_N, 3=BEEP_5V, 4=5V,
5=GND, 6=BEEP_RET, 7=5V, 8=GND, LEDs NC, shield=SHIELD):

| pad | contact function | expected net | board net | verdict |
|---|---|---|---|---|
| 1 | jack contact 1 | AUDIO_P | AUDIO_P | PASS |
| 2 | jack contact 2 | AUDIO_N | AUDIO_N | PASS |
| 3 | jack contact 3 | BEEP_5V | BEEP_5V | PASS |
| 4 | jack contact 4 | 5V | 5V | PASS |
| 5 | jack contact 5 | GND | GND | PASS |
| 6 | jack contact 6 | BEEP_RET | BEEP_RET | PASS |
| 7 | jack contact 7 | 5V | 5V | PASS |
| 8 | jack contact 8 | GND | GND | PASS |
| 9 | LED1 anode | no-connect | unconnected-(J1-LED1A-Pad9) | PASS |
| 10 | LED1 cathode | no-connect | unconnected-(J1-LED1B-Pad10) | PASS |
| 11 | LED2 anode | no-connect | unconnected-(J1-LED2A-Pad11) | PASS |
| 12 | LED2 cathode | no-connect | unconnected-(J1-LED2B-Pad12) | PASS |
| SH (left) | shield leg | SHIELD | SHIELD | PASS |
| SH (right) | shield leg | SHIELD | SHIELD | PASS |

Electrical judgement: the map puts each signal with its return inside one
T568 twisted pair — audio differential on pair 1/2, beeper feed/return on
pair 3/6, 5V/GND on pair 4/5 and again on pair 7/8 (doubled feed and return
conductors). Sound for a non-Ethernet audio-over-Cat5 link. Shield tabs on a
dedicated SHIELD net (terminated via R15, TP6 present) — sane.

J1 VERDICT: PASS

## J2 — 2-pin header pads for mic capsule (PinHeader_1x02_P2.54mm)

Generic 2.54 mm THT pads; no polarity is defined by the header drawing itself,
so the check is function-vs-net sanity:

| pad | function (part.yaml) | board net | verdict |
|---|---|---|---|
| 1 | MIC+ (capsule signal) | MIC | PASS — MIC net carries R2.2 (bias pull-up) and C3.1 (AC coupling to amp): the classic electret bias/couple topology, so pad 1 is genuinely the signal/bias node |
| 2 | MIC- (capsule ground) | GND | PASS — capsule return on ground |

Note (informational, not a board defect): correct capsule orientation is an
assembly-time act — the capsule's case/ground lead must go to pad 2. The
standard KiCad 1x02 footprint carries a pin-1 silk marker; assembly docs
should state "capsule GND lead to pad 2".

J2 VERDICT: PASS

## L1 — Wuerth WE-SL2 common-mode choke provision (744227S, DNP)

Datasheet derivation (independent): WE 744227S rev 009.003 (2023-04-12),
page 1. Recommended Land Pattern (board top view): pad 1 upper-left, 2
lower-left, 3 lower-right, 4 upper-right; 9.5 mm outer span, 2.0 mm pad width,
2.54 mm row spacing, 2.0 x 1.2 pads. Schematic figure: winding A = pins 1-4,
winding B = pins 2-3, dots on the pin-1/pin-2 side (same-side dots).

KiCad footprint comparison: pads at (+-3.75, +-1.27), 2.0x1.2 — outer span
9.5, row spacing 2.54, numbering 1 UL / 2 LL / 3 LR / 4 UR. Exact match to the
land pattern (rotation-consistent, not mirrored; dossier winding CCW agrees).

| pad | winding role | board net | verdict |
|---|---|---|---|
| 1 | winding A in (dot) | AUD_P_I | PASS |
| 2 | winding B in (dot) | AUD_N_I | PASS |
| 3 | winding B out | AUDIO_N | PASS |
| 4 | winding A out | AUDIO_P | PASS |

Judgement: winding A carries P (AUD_P_I -> AUDIO_P), winding B carries N
(AUD_N_I -> AUDIO_N) — a true series common-mode element, no P/N swap, no
short. Same-side dots with both inputs on the W side gives correct
common-mode-blocking / differential-passing sense. The 0R bridges verified
from the board netlist: R13 = AUD_P_I <-> AUDIO_P, R14 = AUD_N_I <-> AUDIO_N —
each bridge parallels exactly one winding, a clean pass-through when the choke
is DNP. Note: if L1 is ever populated, R13/R14 must be removed or the choke is
bypassed (provision logic, not a defect).

L1 VERDICT: PASS

## BZ1 — CMT-8504-100-SMT-TR magnetic transducer (pod:CMT-8504)

Datasheet derivation (independent): Same Sky CMT-8504-100-SMT-TR datasheet
2024-09-11, page 2 Mechanical Drawing, "Recommended PCB Layout Top View":
POLARITY PAD(+) = upper-left, POLARITY PAD(-) = lower-left, 2x DUMMY PAD on
the right; 9.5 mm outer span, 4.5 mm inner gap -> 2.5 mm pads centered at
+-3.5 mm both axes.

KiCad footprint comparison: pad 1 (+) at (-3.5,-3.5) upper-left, pad 2 (-) at
(-3.5,+3.5) lower-left, pads 3/4 dummy on the right, 2.5x2.5 — exact match,
not mirrored.

| pad | function | board net | verdict |
|---|---|---|---|
| 1 | + | BZ_P | PASS — fed from cable BEEP_5V (J1.3) via R12 0R; D2/D3 clamp pair across the coil present |
| 2 | - | BEEP_RET | PASS — returns to cable contact 6 (J1.6) |
| 3 | DUMMY | unconnected-(BZ1-DMY-Pad3) | PASS — mechanical only per datasheet |
| 4 | DUMMY | unconnected-(BZ1-DMY-Pad4) | PASS — mechanical only per datasheet |

Judgement: transducer + on the fed side, - on the return, drive pair on jack
contacts 3/6 (one twisted pair). Correct polarity convention; magnetic
transducer tolerates reversal, so no damage mode even if the far end inverts.

BZ1 VERDICT: PASS

---

Findings summary: 0 FAIL, 0 QUESTION. Two informational notes (J2 capsule
orientation is assembly-dependent; L1 population requires removing R13/R14).

GROUP VERDICT: PASS
