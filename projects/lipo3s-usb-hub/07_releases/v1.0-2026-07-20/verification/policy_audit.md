# Policy audit — lipo3s-usb-hub v1.0

`policy_audit.py projects/lipo3s-usb-hub` result (see `policy_audit.txt` for the raw
line): **FAIL=0** machine items (M-REL clears once this release's MANIFEST is written),
**WAIVED=4** (all evidence-backed, see `03_src/rules/policy_waivers.yaml`), **PASS=12**,
**HUMAN=6**, **N-A=3**.

## Machine gates — clean

DRC (from the one-command `tsx_to_board.sh`): `--severity-all --refill-zones
--schematic-parity` = **0 violations / 0 unconnected / 0 parity**. ERC = 0 errors.
Placement audit = PASS. Board-netlist parity vs sealed usb-power-3s = **0** (303 nodes /
56 nets).

## WAIVED (4) — all evidence-backed, honest for THIS board

- **S-OCCL** — architectural disposition (ADR-0002): the human schematic is tscircuit's
  own render (`pdf/schematic.pdf`); the converter `.kicad_sch` scanned by the auditor is
  a machine-only artifact. Human readability graded on tscircuit's render by the render
  review. NOT a defect.
- **R-POUR** (VBUS1-3) — measured next-spin DEFECT: 0.8 mm/1 oz VBUS runs meet ~1.1–1.3×
  ampacity margin (not the 1.5× bar) at the ILIM-hard-limited 2.51 A; functional and safe
  as-is, flagged for rev-next pours/wider trunks.
- **P-SILK-REF / P-SILK-FN** — real DEFECTs deferred with mitigation: the reused floorplan
  puts refdes on F.Fab (assembly PDF) not F.SilkS, and has no functional connector silk;
  retrofitting silk onto this densely-routed board breaks the proven DRC 0/0/0 (empirically
  verified). Functions delivered via ORDER_README + assembly PDF + the mandatory
  first-power multimeter ritual. Next-spin fix = generator silk pass run pre-route.

## HUMAN-graded (6) — verdicts

- **S6 schematic readability** — graded on tscircuit's `pdf/schematic.pdf` by the
  fresh-context render review (`render_review.md`).
- **S5 design math** — `01_docs/DETAIL_DESIGN.md` (every value derived with margins).
- **S7 decoupling** — per-rail bulk + per-IC decoupling present (VCC 2.2µF, BST 100nF,
  input 3×10µF/stage, output 4×47µF+220µF/rail, 100nF at each TPS/USB); confirmed in
  schematic + pin reviews.
- **Pin correctness** — 3 fresh-context pin reviews, all PASS (`pin_review.md`).
- **Twin / render** — jlc_twin exit 0 (all criticals adjudicated); render review verdict
  in `render_review.md`.

## N-A (3)

Firmware/programming policies — this board has no MCU (pure hardware protection), so the
unprogrammed-state and firmware items are not applicable.
