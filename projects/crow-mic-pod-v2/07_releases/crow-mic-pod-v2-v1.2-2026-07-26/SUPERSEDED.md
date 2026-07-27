# SUPERSEDED — crow-mic-pod-v2-v1.2-2026-07-26

**Superseded by `07_releases/crow-mic-pod-v2-v1.3-2026-07-27/` on 2026-07-27.**

**Reason: BOM LEGIBILITY ONLY. NO COPPER CHANGE.**

Read this before assuming the board was wrong: **it was not.** v1.2's
`.kicad_pcb` is md5-identical (`c7b8512ccf0810997116c8c2e59dcad9`) to v1.3's and
to `04_kicad/`'s; v1.3's gerbers and drills re-plot from that same board **13/13
byte-identical** after stripping the plot timestamp comments; `fab/cpl.csv` is
byte-identical. 17 of 18 payload files are sha256-identical. **The one file that
differs is `fab/bom.csv`, and only in its `Comment` and `MPN` columns.**

Every gate and review verdict v1.2 carries stands unaltered in v1.3. v1.2 is
**not** DO-NOT-ORDER; ordering its bare PCB gives the same board.

## What v1.3 fixes

Canon **F-LEGIBLE** (ADR-0006) — a fab artifact is graded as its RECIPIENT will
parse it. `bom_legibility_check.py` reports **21 findings** on this release's
`fab/bom.csv`:

* **15 F-MPN** — *every* coded row ships a blank MPN, so JLC's matcher leaves a
  code-only line at *No Part Selected*. This board has 6 dossiers and the rest
  of its codes are vetted-ledger passives; the MPN was available for all 15.
* **5 F-WORDS** — the `Comment` column is an LCSC code on U1 (`C192421`), D1
  (`C1972959`), LS1 (`C22359707`), D2 (`C2480`) and D3 (`C559105`), so those
  rows cannot be reviewed by a human on either side of the upload.
* **1 F-ENCODE** — `Ω` with no UTF-8 byte-order-mark, so a reader defaulting to
  cp936 renders `CE A9` as `惟`.

v1.3 ships **0 findings**.

## One thing v1.3 also fixed that is worth knowing about this directory

v1.1 (whose `fab/` this release carries unchanged) removed the MK1 and J1 rows
from `bom.csv` by **editing the file**. That decision was correct — both rows are
unmatchable by JLC and neither designator is on the CPL — but it was recorded
nowhere in `03_src/`, so re-exporting this same sealed board produces **17 rows,
not 15**. The BOM in this directory is therefore NOT reproducible from source
(canon M3). v1.3 declares the decision in `03_src/rules/assembly.yaml` as
`on_bom: false` and generates the 15 rows instead of trimming them. The decision
itself is identical.

## This directory is unchanged

Per the `07_releases/` contract, adding this file is the ONE mutation a sealed
release permits, and only because a successor now exists to name. Nothing else
here has been touched.
