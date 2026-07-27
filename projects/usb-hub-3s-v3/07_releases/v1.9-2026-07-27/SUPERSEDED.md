# SUPERSEDED — v1.9-2026-07-27

**Superseded by `07_releases/v1.10-2026-07-27/` on 2026-07-27.**

**Reason: BOM LEGIBILITY ONLY. NO COPPER CHANGE.**

Read this before assuming the board was wrong: **it was not.** v1.9's
`.kicad_pcb` is md5-identical (`83af8e5a5596a51cf139dd06e8903d47`) to v1.10's and
to `04_kicad/`'s; v1.10's gerbers and drills re-plot from that same board
**15/15 byte-identical** after stripping the plot timestamp comments, the
restored copper pour included (36 zones / 106 filled outlines); `fab/cpl.csv` is
byte-identical. 21 of 22 payload files are sha256-identical. **The one file that
differs is `fab/bom.csv`, and only in its `Comment` and `MPN` columns.**

Every gate, review verdict, bench threshold and measurement v1.9 carries stands
unaltered in v1.10. v1.9 is **not** DO-NOT-ORDER; ordering its bare PCB gives the
same board.

## What v1.10 fixes

Canon **F-LEGIBLE** (ADR-0006) — a fab artifact is graded as its RECIPIENT will
parse it. `bom_legibility_check.py` reports **26 findings** on this release's
`fab/bom.csv`:

* **21 F-WORDS** — the `Comment` column is an LCSC code on 21 of 46 rows, so
  those rows cannot be reviewed by a human on either side of the upload.
* **4 F-MPN** — `C25757` (R42), `C2296` (D8) and `C2297` (D9–D12) ship a **blank
  MPN** although all three have `02_parts` dossiers, so JLC's matcher leaves a
  code-only line at *No Part Selected*; and **SW1 ships `SS12D07VG6 087` with a
  SPACE** where `02_parts/SS12D07VG6-087` declares a **HYPHEN** — the two match
  paths disagree, which is precisely what that redundancy exists to catch. This
  is the only board in the fleet that ever maintained the retired
  `lcsc_mpn_map.csv` side-file, and therefore the only one where a second home
  for the MPN could drift from the first.
* **1 F-ENCODE** — `Ω` with no UTF-8 byte-order-mark, so a reader defaulting to
  cp936 renders `CE A9` as `惟`.

v1.10 ships **0 findings**.

## This directory is unchanged

Per the `07_releases/` contract, adding this file is the ONE mutation a sealed
release permits, and only because a successor now exists to name. Nothing else
here has been touched. The sha256 table in `MANIFEST.txt` still verifies against
every file it lists.
