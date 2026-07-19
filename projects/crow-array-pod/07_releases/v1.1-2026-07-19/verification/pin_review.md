# Fresh-context pin review: J1 (Amphenol RJHSE-5384) — crow-array-pod v1.1

Reviewer: fresh-context agent, 2026-07-19. Inputs: dossier `06_build/pin_audit/J1.md`,
catalogue PDF (p.4/PDF-5 RJHSE-548X figures re-rendered at 300 dpi), part.yaml treated
as claims, central `generate_schematic.py` + `BRIEF.md` D28 read directly. Board pad
positions ground-truthed with pcbnew (not the dossier's math).

## VERDICT: PASS

- J1 winding/numbering: datasheet RECOMMENDED PCB LAYOUT (548X, catalogue p.4) read
  independently — contacts staggered **8..1 left-to-right** (8 upper row at cluster
  left, 1 lower row at right), LED groups **"12 11" left / "10 9" right**, shield
  o1.57 holes **16.26 mm** apart, NPTH posts o3.25 **12.70 mm** apart, LED row
  **9.14 mm** behind the post row — vs dossier/KiCad table (1@0,0..8@7.112,+1.78;
  9/10@-3.30/-1.01,+6.6; 11/12@+8.13/+10.42,+6.6; SH@-4.57/+11.69,+0.89; NPTH
  @-2.79/+9.91,-2.54): **exact match as a 180 deg ROTATION, no mirror**. Every pitch
  re-derived and matched: 2.032 in-row / 1.016 stagger / 1.78 row offset / 2.29 LED
  pair / 13.72 LED 9-to-12 span / 16.26 shield / 12.70 post / 4.83 LED-to-near-row /
  2.54 far-row-to-post / 3.43 shield-to-post. PASS.
- Chirality cross-check (independent of the layout figure's view convention): front
  view p.4 puts LED1 on the RIGHT looking into the face; with the face on the
  post side, the footprint puts pins 9/10 (LED1) and contact 1 on the observer's
  right looking into the opening — consistent. Not mirrored. PASS.
- Mating-face side: side view p.4 dim chain: face->snap-post centerline .215
  [5.46]; post row sits at local y=-2.54 (from the layout figure's 9.14 LED-to-post
  chain), so the FACE PLANE is at local y=-8.00; shield tails 8.89 from face
  (pad y=+0.89), contact rows 8.00/9.78, LED tails 14.60 from face = **1.15 mm from
  the rear** of the 15.75 body. Face is on the SNAP-POST side (local -y), NOT the
  LED side — confirms part.yaml's corrected gotcha; the original "LED tails mark
  the face" claim is indeed inverted. PASS.
- Board orientation (pcbnew absolute, board +x=east +y=south): J1 at (78,71) rot 90
  places NPTH posts at **(75.46, 73.79)/(75.46, 61.09)**, contact rows at
  **x=78.00 (1,3,5,7) / x=79.78 (2,4,6,8)** running north-south, shield tails at
  **(78.89, 75.57)/(78.89, 59.31)**, LED tails at **x=84.60**, face plane at
  **x≈70.0**. Posts and face are WEST of the contacts, LED tails EAST →
  **opening faces WEST**, toward the cable-gland end (board west edge x=51.5).
  Matches design intent. PASS.
- J1 pins 1-8 (contacts): AUDIO_P / AUDIO_N / BEEP_5V / 5V / GND / BEEP_RET / 5V /
  GND — expected a custom non-Ethernet map with pair-balanced DC; board matches
  part.yaml claim and, pin-for-pin over straight-through T568B, matches central
  `rj_nets` (generate_schematic.py:486-489) and BRIEF D28 (BRIEF.md:160-170).
  Pair discipline verified: 1/2 orange = differential audio; 3/6 green = beep feed +
  beep return (central low-side FET Qn drain, lines 497-498); 4/5 blue and 7/8 brown
  each carry 5V feed + GND return, out+back on one twisted pair, two pairs in
  parallel. No split-pair DC. 1.5 A/contact rating, two feed contacts. PASS.
- J1 pins 9-12 (LED tails): datasheet gives no LED polarity; both boards leave all
  four unconnected (central rj_nets 9..12 = None; pod nets `unconnected-(J1-LED*)`).
  Correct given -5384 HAS LEDs (part-number decode) — the holes must exist and do
  (footprint RJHSE538X, not RJHSE5380). PASS.
- J1 SH x2 (shield): pod SH = SHIELD net whose only other members are TP6 and DNP
  R15 (SHIELD->GND) — verified on the board netlist; R15 is absent from
  fab/bom_jlc.csv and listed as an empty reserve pad in ORDER_README_v1.1.md.
  Central SH = GND (rj_nets line 489; BRIEF D28 "single-point star bond ...
  deliberate"). Topology judgment: **sound** — cable shield grounded at exactly one
  end (central) prevents shield ground loops between pods; pod end floats with a
  test point + bondable DNP resistor if EMC testing demands a hybrid bond. PASS.
- Observation (not a fail): R15's DNP is enforced only by BOM exclusion (value
  string "shield bond DNP"); the footprint's DNP attribute and exclude-from-BOM
  flags are NOT set in the .kicad_pcb. If a future BOM regen keys off attributes
  instead of the value, R15 could get populated and double-bond the shield.
  Recommend setting the DNP attribute on R15 (also D3/L1 if same pattern).

## Interop truth table (pod J1 <-> central J1..J8, straight-through T568B)

Central nets cited from `crow-array-central/03_src/generate_schematic.py:486-489`
(n = port number 1..8; J7/J8 DNP).

| pod pin | pod net | T568B pair (conductor) | central pin | central net | role |
|---|---|---|---|---|---|
| 1 | AUDIO_P | orange (wht/org) | 1 | AUD_Pn | mic audio + (diff pair, ESD D2n at central) |
| 2 | AUDIO_N | orange (org) | 2 | AUD_Nn | mic audio - |
| 3 | BEEP_5V | green (wht/grn) | 3 | BEEP_5Vn | beeper feed (central 5V via PTC F2n) |
| 4 | 5V | blue (blu) | 4 | 5V_AUDn | pod power feed A (central 5V via PTC F1n) |
| 5 | GND | blue (wht/blu) | 5 | GND | power return A (same pair as 4) |
| 6 | BEEP_RET | green (grn) | 6 | BEEP_RETn | beeper return -> central Qn drain (low-side switch) |
| 7 | 5V | brown (wht/brn) | 7 | 5V_AUDn | pod power feed B (parallels pair 4/5) |
| 8 | GND | brown (brn) | 8 | GND | power return B (same pair as 7) |
| SH | SHIELD (float; TP6 + DNP R15 bond) | cable shield | SH | GND | single-point shield ground at central |

Every DC loop closes within one twisted pair: (3,6) beep, (4,5) power A, (7,8)
power B; (1,2) is the balanced audio pair. Confirmed against BRIEF D28
(BRIEF.md:160-170), which also documents that the part.yaml 4/5-7/8 reading was
the artifact previously in error, not the boards.
# Fresh-context pin review: D1 (TI TPD2E2U06DRLR, DRL/SOT-553) — v1.1 spot re-review

Reviewer: fresh-context agent, 2026-07-19. No design-session context (by protocol).
Datasheet: `02_parts/TPD2E2U06DRLR/tpd2e2u06_sllseg9c_2019-12.pdf` (SLLSEG9C), page 3
rendered at 300 dpi and read directly. Package pinout derived independently from the
"DRL Package, 5-Pin SOT, Top View" figure — not from the dossier or part.yaml.

## Independent derivation (datasheet figure, top view)

- Pin 1 = NC, top-LEFT corner. Pins 1-2-3 run DOWN the left side (3 pins west).
- Pin 3 = IO1, bottom-left. Pin 4 = GND, bottom-RIGHT. Pin 5 = IO2, top-right (2 pins east).
- Winding 1..5: down the left, up the right = **CCW (top view)**. No exposed pad; 5 pads total.
- Pin Functions table (DRL column): IO1=3, IO2=5, NC=1,2, GND=4. IO pins: "Connect these
  pins to the data line **as close to the connector as possible**."

## Verdict table

| pad | dossier local (x,y), +y down | side | expected (datasheet) | board net | verdict |
|---|---|---|---|---|---|
| 1 | (-0.71, -0.50) top-left | W | NC (float/GND/VCC ok) | unconnected | PASS |
| 2 | (-0.71, +0.00) mid-left | W | NC | unconnected | PASS |
| 3 | (-0.71, +0.50) bottom-left | W | IO1 — protected data line | AUDIO_P | PASS |
| 4 | (+0.71, +0.50) bottom-right | E | GND | GND | PASS |
| 5 | (+0.71, -0.50) top-right | E | IO2 — protected data line | AUDIO_N | PASS |

- **Winding/mirror:** dossier's computed CCW (top view), 3 pads W / 2 pads E, pin 1 at
  top-left matches the datasheet figure pad-for-pad under zero rotation. NOT mirrored. PASS.
- **Pin count / EP:** 5 pads, no EP — matches DRL package. PASS.
- **Electrical sanity:** two I/O clamp channels on the balanced audio pair, GND on ground,
  NCs floating (datasheet permits). Matches ADR-0001 intent (clamp AUDIO_P/N to GND). PASS.

## Placement (the reason for this spot re-review)

D1 pin 3 (IO1): expected AT the cable entry per datasheet ("as close to the connector as
possible") and ADR-0001 §1 ("strike energy dumps at the entry", 68R resistors between amp
and clamp) vs dossier shows D1 at **(88.5, 59.0)** while J1 is at (78, 64) with the
AUDIO_P/N tails at ~(76-78, 64-65.1) — **~11.6 mm from the nearest tail**. The v1.1
re-route moved the jack (screw terminal -> RJ45) but the clamp did not follow it; ~12 mm of
trace between the connector and the clamp carries the raw strike, and the clamp no longer
sits upstream at the entry as ADR-0001 requires. **FAIL.**

## Overall

**VERDICT: FAIL** (placement). Pin mapping, winding, and net assignment are all correct —
the v1.0 net contract is intact — but the moved part no longer performs entry clamping.
Block release until D1 is repositioned adjacent to the J1 AUDIO_P/N tails (~(76-78,
64-65.1)), with the clamp in the path before any downstream routing, or the ~11.6 mm
deviation is explicitly accepted in writing against ADR-0001.

---

# Orchestrator disposition of the D1 FAIL (release gate record)

The D1 review's verdict offered two exits: reposition D1, or "the ~11.6 mm
deviation is explicitly accepted in writing against ADR-0001". The second
exit was taken: ADR-0004 section (b2) (01_docs/decisions/0004-rj45-termination.md,
accepted 2026-07-19) records the written acceptance with reasons:
(1) the RJHSE-5384's 15.75mm-deep THT body makes the courtyard's east edge
the closest physically legal position and D1 sits directly against it;
(2) routed topology is clamp-FIRST (J1 tail -> D1 IO -> R13/R14/L1), so the
full strike current reaches the clamp before any protected element;
(3) sealed v1.0 shipped the same ~12mm figure. Pin mapping, winding, and
nets: PASS per the review itself. DISPOSITION: ACCEPTED — does not block v1.1.
