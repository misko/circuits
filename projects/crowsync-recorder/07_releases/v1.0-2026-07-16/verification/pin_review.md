# Fresh-context pin review — crowsync-recorder v1.0 (2026-07-16)

Protocol: kicad-pcb/references/pin-review-protocol.md. Three independent
fresh-context agents, one per part group; dossiers from pin_audit.py
(06_build/pin_audit/), datasheets from 02_parts/. Reviewers had no design
context beyond the stated topology facts.

## Group 1 — codec + crystal (agent 1)

- **U1 PCM2900CDBR — VERDICT: PASS.** Winding CCW / pin-1 top-left matches
  SBFS039 p6 figure (not mirrored); 28/28 pins; all functions match
  Table 1; straps verified (SEL0/1 = VDDI high, TEST0 = GND, TEST1 open,
  HID NC on internal pulldowns); internal-regulator pins on dedicated
  decoupling nets, not rails; VBUS pin on the filtered VBUS_PCM net.
- **Y1 X322512MSB4SI — VERDICT: PASS.** Electrodes 1/3 on XTI/XTO, corners
  2/4 on GND per the YSX321SL connection figure; winding matches, not
  mirrored.

## Group 2 — analog (agent 2)

- **U2 TLV9062IDR — VERDICT: PASS.** CCW winding matches SBOS839N fig 5-6;
  all 8 functions match table 5-3; ch A = preamp (OUT1/AMP_OUT,
  IN1-/AMP_FB, IN1+/AMP_INP), ch B = unity VCOM buffer (IN2+=VCOM,
  IN2-=OUT2=VCOM_BUF); V+ = 3V3A, V- = GND.
- **U3 TPS7A2033PDBVR — VERDICT: PASS.** Matches SBVS338H fig 4-4
  (IN/GND/EN west, OUT/NC east); EN tied to IN (valid, V_EN <= V_IN);
  NC floating per datasheet; OUT = 3V3A.

## Group 3 — protection + connectors (agent 3)

- **D1 USBLC6-2SC6 — VERDICT: PASS.** CCW, not mirrored; pass-through
  pairs 1/6 = DP_C, 3/4 = DM_C; 2 = GND; 5 = VBUS_5V.
- **D2 USBLC6-2SC6 — VERDICT: PASS.** Same geometry; 1/6 = MIC, 3/4 = PPS,
  5 = 3V3A clamp rail; symmetric with D1 (same pin -> same KIND of net).
- **J1 USB4105-GF-A — VERDICT: QUESTION -> RESOLVED PASS.** All pads match
  the GCT pin table (4x VBUS, 4x GND, DP/DM pairs, SBU NC, shield GND);
  CC1/CC2 correctly separate. The QUESTION — whether each CC terminates in
  its own 5.1k Rd — is outside the connector dossier; resolved by board
  fact: R4 = {1: CC1, 2: GND}, R5 = {1: CC2, 2: GND}, both 0603WAF5101T5E
  (C23186, live-verified 5.1kOhm +-1%). Two separate pulldowns present.
- **J2 SM03B-GHS-TB — VERDICT: PASS.** Pin 1 = MIC (matches D2 I/O1 pair),
  2 = GND, 3 = GND shield, MP = GND; pattern matches the eGH drawing.
- **J3 SM02B-GHS-TB — VERDICT: PASS.** 1 = PPS (matches D2 I/O2 pair),
  2 = GND, MP = GND.
- Reviewer note: the LCSC-hosted "UMW" PDF carries ST-branded content;
  pinning identical either way (recorded in 02_parts/USBLC6-2SC6).

## Result

**Zero FAIL verdicts.** One QUESTION resolved with board evidence above.
Order may proceed.
