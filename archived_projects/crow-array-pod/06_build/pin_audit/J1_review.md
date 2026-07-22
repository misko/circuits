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
