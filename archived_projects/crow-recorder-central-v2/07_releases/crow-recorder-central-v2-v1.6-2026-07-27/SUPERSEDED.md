# SUPERSEDED — crow-recorder-central-v2-v1.6-2026-07-27

**Superseded by `07_releases/crow-recorder-central-v2-v1.7-2026-07-27/` on
2026-07-27.**

**Reason: ONE SOURCING SUBSTITUTION. NO COPPER CHANGE.**

## v1.6 is not wrong. It is UNORDERABLE, and only for sourcing

v1.6's board **is** v1.7's board, and every gate verdict and review verdict it
carries stands unaltered. What it cannot do is get all 47 of its coded BOM lines
supplied, because one of them went to stock 0 after it sealed.

> **`C25767` (UNI-ROYAL `0402WGF2203TCE`, 220 kΩ 0402) is `R_vb1`**, the top leg
> of the VBUS→VBUS_SENSE divider into the XU316. JLC's parts API reports
> `stockCount: 0`. It is ON the CPL — 1 placement × 5 boards = 5 needed — and
> unlike this release's other two stock-0 lines it carries **no `sourcing_plan:`
> entry** and appears on **no order-day watch-list**.

**The part worth recording is that this release's own gate PASSED that line.**
v1.6's sealed `verification/stock_check.json` records `C25767` at **stock 16,
status OK** — 16 ≥ 5 × 1, so the rule was satisfied. Sixteen units is inside a
single day's churn of zero, and nothing in the pipeline distinguishes "clears 5×
need" from "clears 5× need by eleven units". The watch-list this release's
ORDER_README *did* publish named `C5224055` (383) and `C882626` (496) — the two
lines a human had noticed — and missed the one actually at risk. The same shape
cost usb-hub-3s-v3 a release the same day: it recorded `"status": "OK",
"stock": 291` hours before JLC refused the line.

## The board did not move, and that claim carries numbers

| measured | result |
|---|---|
| `source/crow_recorder_central_v2.kicad_pcb` md5 | **`de39e145e856cb14d491770c77d1ec0a`** — identical across this release, v1.7, v1.5 and the working `04_kicad/` |
| gerbers + drills RE-PLOTTED from that board | **17/17 byte-identical** to this release's sealed payload after stripping only the plot's own timestamps (15 zip members + 2 loose drills) |
| `fab/cpl.csv` | **byte-identical** (174 rows) — a substitution to the same 0402 land moves no placement, rotation or datum |
| `fab/bom.csv`, parsed as CSV | 49 → 49 rows, designator list identical **in order**, **exactly 2 cells changed**, both on `R_vb1` (`MPN`, `LCSC`), 0 Footprint changes, 0 Comment changes, 0 rows added or removed |

The replacement is `C138030` / YAGEO `RC0402FR-07220KL`, stock **736 704**, same
0402 land, catalog `describe` string **character-identical** compared as strings,
same RC0402FR series as this board's existing `C60490` (10 kΩ) and `C105871`
(4.7 kΩ) swaps. Changed at SOURCE (`supplierPartNumbers` in the `.tsx`), never in
the CSV — canon M3.

**v1.7 is gated by an ASSERTION, not by waivers.** It is the first release graded
by `release_freshness_check.py --sourcing-supersede`, a mode promoted under canon
M8 the same day because usb-hub-3s-v3 v1.11 had to state seven of these same
claims as prose file waivers. v1.7 ships **zero** freshness exceptions.

## Three other things v1.7 corrects that are about THIS directory

1. **Two ORDER_README sentences here are STALE and a human will act on them.**
   Line 213 says `fab/bom.csv` is *"byte-identical to v1.3 and v1.2"* — it is the
   one file this release changed (`c6a8ff14c563bd0b8913a5259bfff72d` vs
   `b9e4486adb2813a7fe577638597a6f23`). Lines 383–385 tell the §3a operator that
   *"`fab/bom.csv`'s MPN column is blank on all 49 rows"* — **the exact defect
   this release exists to fix.** Both were true at v1.4 and inherited unchecked.
   Harmless in outcome, corrosive in trust: a docs fix not re-read at the next
   release becomes the next release's defect.
2. **`verification/twin_top.png` here is STALE.** It is byte-identical to v1.5's
   (`c48a2bd3e70d270c3b768069e2529567`) and predates the `jlc_twin` J2 mount fix,
   so canon A-RENDER **FAILs on the shipped picture** (J2 centre 1.44 mm) while a
   render regenerated from **this same sealed board** passes all 22 measurable
   bodies within 1.00 mm. **The board is right; the picture is stale.** Anyone
   re-reviewing this release from that PNG will conclude the v1.5 J2 fix did not
   take. It did — corroborated by a different method (canon M1): A-POS grades the
   CPL *coordinate* at a worst datum residual of 0.00050 mm over all 174 rows.
   v1.7 ships a regenerated render (`0d8cf827e3e2da2aba998a86fcb8f2cc`).
3. **F-PAYLOAD and A-RENDER had never graded any release of this board.** Both
   now ship in v1.7's `verification/`; an absent verdict is not a pass.

## What is NOT changed by this supersede

* **v1.4 remains DO-NOT-ORDER FOR PCBA** — its CPL places J2, the board's only
  USB-C connector, 1.3025 mm off its own pads. **v1.3 remains DO-NOT-ORDER** for
  its separate rotation defect.
* Every pre-order condition of this release carries into v1.7 unchanged: the
  A-POL JLC order-preview human gate, the **U1 270° rotation gate**, the MSL-3
  handling for the consigned XU316, the order-day stock recheck, and the
  **blocking 33 pF feedforward rework** on `R_fb1a` / `R_fb2a`.
* **F-ECHO still applies and is still not waivable.** v1.7 additionally records
  the adjudication for the one finding to expect: our `C82317` for `U5` resolves
  to JLC's `C131025`, which is the SAME part (`W25Q16JVSSIQ`, Winbond,
  SOIC-8-208mil, character-identical spec string) at 7.5× the stock — a duplicate
  catalog entry consolidated upward. **ACCEPT.**

Evidence for every number above: `../crow-recorder-central-v2-v1.7-2026-07-27/`
— `verification/replot_identity.txt`, `verification/stock_check.json`,
`verification/twin_overlay_top.md`, `verification/fab_payload_census.txt`,
`verification/release_freshness.txt`.
