---
id: 0009
date: 2026-07-21
status: accepted
---
# 0009 — USB-C port robustness: D3 is surge-grade only; Q8 single-FET backfeed accepted

## Context
v1.1 respin, reviews X8 (external), X30 + P2-1 (red-team A). Two claims on
the C-port power path were verified against the netlist and datasheets:

1. **D3 (SMAJ24A, VBUSC→GND)** has Vbr 26.7–29.5 V and Vc(max) ≈ 38.9 V.
   Devices behind it: IP6559 VOUT1/VOUT2/VOUTI abs max 25 V (IP6559_V1.4 §6
   — VOUT2 reaches VBUSC through R20 10 Ω; VOUTI/VIO sit on VOUT_PD behind
   Q8's body diode), C26/C28/C29 rated 25 V. Any event that makes D3 conduct
   has ALREADY exceeded the 25 V abs-max of the protected parts.
2. **Q8 (path NFET, D=VOUT_PD, S=VBUSC)** cannot block backfeed: an
   externally driven VBUS forward-biases its body diode into VOUT_PD.

## Options
- **Replace D3 with a lower clamp** — REJECTED: no SMA TVS fits a
  21 V-working / 25 V-abs window (a 22 V-standoff part still breaks down
  ≥ 24.2 V and clamps in the mid-30s). The window is physically unservable
  by a single discrete clamp.
- **Back-to-back path FETs (Q8 + mirror)** — REJECTED for v1.1: the IP6559
  drives VOUT2G for its DS-reference single-FET path; a second FET's gate
  drive is not provided by the chip (charge-pump headroom unverified), and
  red-team A's consequence trace shows the backfeed path is BENIGN: 20 V
  back-drive charges VOUT_PD to ~19.3 V, below the 25 V abs-max of
  everything on that net (X30, verified).
- **Document both as characterized limitations** — CHOSEN.

## Decision
Keep the DS-reference topology. Document, in this ADR and ORDER_README:
- D3 is SURGE-GRADE protection (tames cable/ESD surges) — it is NOT
  abs-max-grade protection for the IP6559; real OVP is the chip's internal
  loop + its 4 kV pin ESD. Nobody may later "rely" on D3 for chip survival.
- Q8 backfeed is accepted: worst back-drive (20 V, e-marked charger) lands
  VOUT_PD at ~19.3 V < 25 V abs-max of U1.VOUTI/VIO/C26/C28/C29 (X30).
- CC1/CC2 short-to-VBUS survival is UNVERIFIABLE from records (no CC
  abs-max row in IP6559_V1.4 — X16); DS-reference wiring accepted.

## Bench-validation plan (ORDER_README first-power ritual additions)
1. VBUS abuse: with the port unpowered, back-drive VBUSC at 5 V then 20 V
   from a current-limited source; verify no damage, VOUT_PD tracks minus a
   diode, and normal operation after removal.
2. CC abuse (destructive-risk, LAST, optional): short CC1 to VBUS at 5 V
   via 1 kΩ, then direct; verify the port re-enumerates afterwards.
3. Surge sanity: scope VBUSC during rapid e-marked-cable plug/unplug cycles
   at 20 V/5 A contract; confirm no D3 conduction in normal service
   (VBUSC stays < 24 V).
