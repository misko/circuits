# ADR-0003 — board outline (1551WY maximum PCB) + cable termination choice

Status: accepted 2026-07-18; **termination section (D6) SUPERSEDED
2026-07-19 by decisions/0004-rj45-termination.md** (A4: RJ45 jack,
field-crimped plug inside the gland — drives v1.1). The outline section
(D4) remains in force.

## Outline (D4)

The commission targets the Hammond 1551WYBK (IP68, 100x50x24 mm). Its
drawing (01_docs/hammond_1551wy_rev2023-08-31.pdf, "MAXIMUM P.C. BOARD")
specifies: 94.50 x 44.50 mm, corners notched to 82.00/32.00 mm straight
spans (R4.42 boss clearance), four Ø2.60 holes on a 75.00 x 35.00 pattern
inset 9.75/4.75 from the corner (hole centers pixel-verified against the
drawing: (9.78, 4.84) / (84.89, 39.89) on the max outline — nominal
9.75/4.75 + 75.00 x 35.00 adopted).

Decision: use the full maximum outline with concave-arc corner cutouts of
R6.25 centered at each rectangle corner (removes at least the drawing's
notch, clearing the #4 bosses with margin), Ø2.7 mm NPTH holes for the #2
self-tapping post screws. A "~50x35" board was considered and REJECTED:
it cannot reach the 75x35 boss pattern (holes would sit 2.5 mm from its
edge), and §3A wants mic and transducer at opposite ends — the full-length
board gives 85 mm of acoustic separation and room for the gland service
loop above the terminal.

## Termination (D6): 8-pos 3.5 mm screw terminal, hand-solder

Commission §4 allows "PCB terminal block or solder pads". Chosen: KF128L-
3.5-8P-class 3.5 mm screw terminal (KiCad Phoenix PT 1,5/8-3.5-H land
pattern), terminal n = T568B pin n.

- Screw terminals take 24 AWG solid Cat5e directly (no ferrules needed for
  solid core), are field-serviceable through the gland, and re-terminate
  after cable trims — solder pads are not.
- JLC assembles no such THT part from stock (consign-only), so the line
  ships UNCODED as a hand-solder item with a Digi-Key equivalents list
  (On Shore OSTVN08A150 / TE 282834-8 / LCSC C474936 consign) in
  ORDER_README. 8 joints/board by hand is trivial.
- Mic attach (also §3A-driven): 2.54 mm 1x2 pads (J2) for short twisted
  leads to the capsule in its acoustic cavity — the capsule tolerates only
  2 s of soldering per terminal and must not be reflowed.
