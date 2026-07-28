# SUPERSEDED — by `interposer-v1.1-2026-07-27`

**DO NOT ORDER THIS RELEASE.** It was never fabbed, and it must not be.

## The P0 that superseded it

`fab/cpl.csv` ships `J_KEY_MATRIX` (C2683602, JST GH SM10B-GHS-TB) at
**Rotation 90.0**. The measured authority says **270.0** — the board places the
part at orientation −90 ⇒ board_rot 270, and the MEASURED per-LCSC offset for
C2683602 is 0 (`jlc_lcsc_rotations.csv:17`: pad-by-number fit against JLC's own
cached model, **rms 0.0049 mm vs 5.0792 mm for the next-best angle = 1037×
separation**). This release's own `verification/twin_report.csv` already said
`jlc_offset=0`.

The 90.0 came from the footprint-**NAME** rule `^JST_GH_SM,180`, which was
**REFUTED on 2026-07-25 — the day after this release sealed** — after putting
EIGHT connectors 180° out across two sealed releases. A name is not a part.

**It fails silently, which is why it is a P0 rather than a nuisance.** The GH
pad array is symmetric about its own centre, so at 180° every pad still lands on
a pad: the connector solders perfectly, passes every visual and electrical
check, and **pin 1 ↔ pin 10 swaps — reversing the entire ten-line keypad
ribbon** (KP_U1 ↔ KP_D4). That is verbatim the failure this release's own
`ORDER_README.md` §3 exists to prevent; §3's claim that "both boards carry the
SAME part at the SAME rotation" was true of the two BOARDS and FALSE of the two
CPLs.

## The second defect, and the reason neither was caught

`J_MEMBRANE` and `J_CN1_JUMPER` — blank-LCSC through-hole 10FDZ-BT ZIFs, 10
plated drilled pads each with **F.Paste on none** — ship **ON the CPL**, with no
`exclude_from_pos_files`, no `assembly.yaml`, and no `not_assembled:` MANIFEST
line. JLC is told to machine-place two parts it cannot source and no reflow
process can solder. The only defence was prose in `ORDER_README.md` §1 telling a
human to delete the rows before uploading.

**ROOT CAUSE OF BOTH: the entire assembly gate family never ran on this
release.** `verification/policy_audit.md` has no A-POP / A-POS / A-ROT / A-POL /
A-BODY / A-STOCK row at all — the family was landing on the same days this
sealed, and the release was never re-graded. **An absent verdict is not a pass.**

## What else v1.1 fixes

- `fab/bom.csv` is now legible to its recipient (canon F-LEGIBLE, ADR-0006).
  This release's BOM: `J_KEY_MATRIX`'s Comment is the LCSC code `C2683602`, its
  MPN cell is blank, and there is no UTF-8 byte-order-mark. `bom_legibility_check.py`
  returns **FAIL, 2 findings** on it and **OK, 3 checks** on v1.1's.
- `source/` did not stand alone. `source/fp-lib-table` points the `cooksense`
  library at `${KIPRJMOD}/../03_src/lib/cooksense.pretty` — OUTSIDE the archive —
  while `source/cooksense.pretty/` ships INSIDE it, and no `.kicad_pro` /
  `.kicad_dru` ship at all. **`kicad-cli pcb drc --severity-all --refill-zones
  --schematic-parity` on this archive alone returns 29 violations**; the two
  footprints that fail to load are the two 10FDZ-BT ZIFs, the entire point of
  the board. The same command on v1.1's archive returns **0 / 0 / 0**.
- The CPL datum. All three of this release's CPL rows are emitted on the KiCad
  footprint ANCHOR, not on JLC's pad-array-centre datum (`J_KEY_MATRIX` 0.25 mm
  off; the two ZIF rows 10.16 mm off).
- `pourless:` is now declared, so F-POUR can tell a deliberately pourless board
  from one that lost its zones.

## What was NOT wrong, and is carried forward unchanged

**The copper.** Measured with an aperture-resolved, order-independent
gerber/Excellon comparator that shares no method with the plotter: both copper
layers, both masks, both pastes and both drill files are **geometrically
identical** between this release and v1.1 (F_Cu 450 atoms, B_Cu 180, masks
84/52, pastes 12/0, 55 PTH holes, 6 NPTH). The profile is identical as an
undirected segment set; F.Silkscreen differs by 50 of 5368 atoms, all inside one
0.514 × 0.900 mm character cell — the version digit. Full working:
`../interposer-v1.1-2026-07-27/verification/copper_identity.txt`.

This release remains a valid historical record of what was designed on
2026-07-24, and its DRC/ERC/routing/isolation evidence stands. It is superseded
for its ASSEMBLY payload, not its board.

    superseded: 2026-07-27
    successor:  07_releases/interposer-v1.1-2026-07-27/
