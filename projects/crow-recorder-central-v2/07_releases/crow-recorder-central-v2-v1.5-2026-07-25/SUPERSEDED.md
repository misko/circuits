# SUPERSEDED — crow-recorder-central-v2-v1.5-2026-07-25

**Superseded by `07_releases/crow-recorder-central-v2-v1.6-2026-07-27/` on
2026-07-27.**

**Reason: BOM LEGIBILITY (plus the E-TOPO rail declaration). NO COPPER CHANGE.**

## Read this before assuming the board was wrong — it was not

v1.5's board **is** v1.6's board. Measured, three independent ways:

* the `.kicad_pcb` is **md5-identical** — `de39e145e856cb14d491770c77d1ec0a` —
  across v1.5's `source/`, v1.6's `source/`, and the working `04_kicad/`;
* v1.6's gerbers and drills were **RE-PLOTTED** from that same board and came out
  **17/17 byte-identical** to v1.5's sealed archive (15 zip members + 2 loose
  drills) after stripping only KiCad's own wall-clock stamps;
* `fab/cpl.csv` is **byte-identical**, so every A-ROT rotation and A-POS
  coordinate carries forward untouched. 20 of 21 payload files are
  sha256-identical.

**Exactly one payload file differs: `fab/bom.csv`, and only in its `Comment` and
`MPN` columns** — 24 Comment rewrites and 47 MPN fills over 49 rows, with **0
rows added, 0 removed, and 0 changes to any Footprint or LCSC code.** That shape
is asserted mechanically by
`release_freshness_check.py <v1.6> --legible-bom-supersede <v1.5>`, which FAILs
on a changed LCSC (that would be a *substitution*), on a blanked MPN, and on a
BOM that does not itself pass F-LEGIBLE.

Every gate, review verdict and measurement v1.5 carries stands unaltered in
v1.6. **v1.5 is NOT DO-NOT-ORDER.** Ordering its bare PCB gives the same board;
what it cannot do is get its BOM through JLC's matcher.

## What v1.6 fixes

### 1. The BOM was right and unreadable (canon F-LEGIBLE, ADR-0006)

v1.5's `fab/bom.csv` was uploaded to JLCPCB and the parts "were not being picked
up by their web processing". `bom_legibility_check.py` reports **72 findings**
on this release:

| check | findings | what JLC saw |
|---|---|---|
| **F-MPN** | 47 | **every** coded row ships a blank MPN, so JLC's matcher leaves a code-only line at *No Part Selected* |
| **F-WORDS** | 24 | the `Comment` is an LCSC code, or the tscircuit generator stand-in `simple_chip` / `simple_inductor` — a row nobody can review on either side of the upload |
| **F-ENCODE** | 1 | the ohm sign ships with **no UTF-8 byte-order-mark**, so a reader defaulting to cp936 renders `CE A9` as the mojibake the user reported |

v1.6 has **0**. Nothing was invented to get there: five dossiers
(`1277AS-H-1R0M`, `1277AS-H-2R2M`, `BLM21PG600SN1D`, `BLM21SP601SN1D`,
`TLV70018DDCR`) had declared their code as a bare top-level `lcsc:` instead of
the `sourcing:` block the 02_parts contract mandates — the repo already knew the
answer and could not see it — and Y1's NDK crystal, which genuinely has no
dossier, gained a catalog-verified ledger row.

### 2. Two of this board's three regulators had never been graded

Canon **E-TOPO** gained LINEAR-regulator support on 2026-07-27, *hours after
this release sealed*, and immediately reported:

```
UNGRADED CONVERTERS: 2 of 3 converter part(s) in 02_parts are named by no rail:
  TCR2LF18 (type: 'ldo' -> LINEAR), XC6227C331PR-G (type: 'ldo' -> LINEAR)
```

The `1V8` (U9) and `3V3A` (U10) rails were real, and were declared in a
**comment** in `03_src/rules/power_tree.yaml` — which no gate reads. v1.6
declares them properly, so both are now graded on the two failure modes the
Vin-vs-Vout topology derivation cannot see:

| rail | headroom vs dropout | PD vs package rating |
|---|---|---|
| `1V8` (3V3→1.8 V @ 50 mA, TCR2LF18) | 1382 mV vs **620 mV** | 81 mW vs **200 mW** (40%) |
| `3V3A` (5V→3.3 V @ 80 mA, XC6227C331PR-G) | 1567 mV vs **200 mV** | 147 mW vs **500 mW** (29%) |

**Both rails PASS, and they would have passed in v1.5 too** — nothing about this
board's power tree was found to be wrong. What changed is that a gate can now
see it. E-TOPO on this board: **FAIL (2 of 3 ungraded) → OK, 4/4 rails covering
3/3 converters.**

That declaration reaches no gerber, no drill, no placement and no BOM row. It is
recorded here only so a reader six months out is not left wondering what else
moved between v1.5 and v1.6. **Nothing else did.**

## What is NOT changed by this supersede

* **v1.4 remains DO-NOT-ORDER FOR PCBA** — its CPL places J2, the board's only
  USB-C connector, 1.3025 mm off its own pads.
* **v1.3 remains DO-NOT-ORDER** for its separate rotation defect.
* The v1.5 pre-order conditions carry into v1.6 unchanged: the A-POL JLC
  order-preview human gate, the order-day stock recheck on the Extended-tier
  parts, and the **blocking 33 pF feedforward rework** on `R_fb1a` / `R_fb2a`.
* v1.6 adds one pre-order condition of its own, **F-ECHO**: after uploading,
  save JLC's own resolved part table and diff it back against ours. A code JLC
  redirects is a substitution — `C82317 → C131025` happened on this very board's
  upload and nothing in this repo could see it.

Evidence for every number above: `../crow-recorder-central-v2-v1.6-2026-07-27/`
— `verification/replot_identity.txt`, `verification/bom_legibility.txt`,
`verification/power_topology.txt`, `verification/release_freshness.txt`.
