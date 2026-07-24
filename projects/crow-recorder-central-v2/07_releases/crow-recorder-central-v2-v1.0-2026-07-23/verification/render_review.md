# Render review — v1.0-2026-07-23 (fix-pass scoping)

Integrated into the zero-context lens (fresh_lens.md) per canon
"Verification scoping". Board-lead render observations recorded for the
lens to challenge:
- Bare renders (render_{top,bottom}_bare.png): 8x "NOT ETH 5V!" per-port
  silk + banner + pinout legend verified present at the port bank; refdes
  silk de-collided; DRC silkscreen classes clean (0 violations).
- Twin renders (twin_*.png): modeled bodies land on our courtyards;
  missing_models.txt = 0 missing for all 172 CPL refs. U1 (XU316) is a
  consignment line — its JLC WRL renders low-contrast; pads verified by
  the adjudicated name-fit evidence instead (twin_adjudications.yaml).
- J1 barrel + J2 USB-C MODEL-REG dispositions in twin_adjudications.yaml
  (JLC .kicad_mod rotation authoritative; order-preview confirm).
