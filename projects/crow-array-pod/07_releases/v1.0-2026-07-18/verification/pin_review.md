# Fresh-context pin review — crow-array-pod v1.0 (2026-07-18)

Protocol: kicad-pcb/references/pin-review-protocol.md. Two independent
fresh-context agents, dossiers from pin_audit.py (06_build/pin_audit/),
expectations derived from the datasheets, not the design.

## Group 1 (U1, D1) — reviewer A

- U1 OPA1678IDR (SOIC-8): **VERDICT: PASS.** Winding CCW / pin-1 NW
  matches SBOS855E fig 5-3 (no mirror). All 8 pins function<->net sane:
  1 OUT_A=A_OUT, 2 -IN_A=FB_A (gain re-derived 1+10k/20k=x1.5),
  3 +IN_A=AIN, 4 V-=GND, 5 +IN_B=VMID, 6 -IN_B=FB_B (20k/20k unity
  inverter), 7 OUT_B=B_OUT, 8 V+=5V.
- D1 TPD2E2U06DRLR (DRL/SOT-553): **VERDICT: PASS.** The DRL trap (right
  side = pin 4 BOTTOM, pin 5 TOP) independently derived from SLLSEG9C p.3
  and matched: 3 IO1=AUDIO_P, 5 IO2=AUDIO_N, 4 GND=GND, 1/2 NC unnetted.

## Group 2 (J1, BZ1, D2, C1) — reviewer B

- J1 8-pos terminal: **VERDICT: PASS.** Straight 3.5mm row (drawing
  hole Ø1.3 vs 2.4mm pads = ~0.55 annulus), nets 1..8 = AUDIO_P, AUDIO_N,
  BEEP_5V, 5V, GND, BEEP_RET, 5V, GND exactly.
- BZ1 CMT-8504: **VERDICT: PASS.** +/- derived from datasheet p.2
  (both electrical pads on the west column, + top-left): pad1(+)=BZ_P,
  pad2(-)=BEEP_RET, dummies unnetted; the bottom-view mirror was checked.
- D2 SS14 flyback: **VERDICT: PASS.** Independently derived clamp
  orientation (remote low-side switch -> BEEP_RET flies positive ->
  anode=BEEP_RET, cathode=BZ_P) matches pad1(K)=BZ_P.
- C1 100u electro: **VERDICT: PASS.** pad1(+)=5VF, pad2(-)=GND.

## Result

6/6 PASS, 0 FAIL, 0 QUESTION. No order blockers from pin review.
