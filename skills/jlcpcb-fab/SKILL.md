---
name: jlcpcb-fab
description: Produce and verify a complete JLCPCB order package (gerber zip + BOM + CPL) from a KiCad board, including stock/availability checks against the JLC parts library. Use when exporting fab files, preparing a JLC/JLCPCB order, filling LCSC part numbers, or checking BOM stock.
---

# JLCPCB fabrication + assembly ordering

End-to-end: DRC-clean KiCad board → uploadable JLC order. Verified on the
SPF rover power board (4L, 136 parts, 2026-07) with KiCad 7.0.x and 10.0.4.
For board *design* rules (routing, DRC floors, escape geometry) see the
`kicad-pcb` skill — this skill starts where the board is already clean.

## What JLC needs (the deliverables)

| Upload slot | File | Contents |
|---|---|---|
| PCB order | `<board>_gerbers.zip` | Copper gerbers (2/4/6 layers), F/B mask, F/B paste, F/B silk, Edge_Cuts, PTH + NPTH Excellon drills, job file when present (KiCad 7 emits it, 10 doesn't; optional). **Nothing else** — no BOM/CPL inside the zip. |
| Assembly: BOM | `bom_jlc.csv` | Columns exactly: `Comment,Designator,Footprint,LCSC`. **One line per (LCSC, footprint)** — JLC's uploader warns "multiple lines matched to same part" if two lines share a code; the export script merges value-comment groups accordingly. Uncoded lines stay per-value. |
| Assembly: CPL | `cpl_jlc.csv` | Columns exactly: `Designator,Val,Package,Mid X,Mid Y,Layer,Rotation`. mm units, top/bottom in `Layer`. |

Format empirics:
- Protel extensions (.gtl/.gbl/.gts...) + gerber attributes on — JLC's
  uploader auto-detects the stackup from them.
- Inner-layer extensions are KICAD-VERSION-DEPENDENT: KiCad 7 plots
  In1/In2 as `.g2`/`.g3`, KiCad 10 as `.g1`/`.g2`. JLC accepts both, but
  any script that globs fab files must cover `.g1`–`.g6`.
- KiCad 10's headless PLOT_CONTROLLER no longer emits the `.gbrjob` job
  file (KiCad 7 did). JLC doesn't need it; don't chase the "missing" file.
- Plot content is stable across 7→10: draw-op counts matched exactly on
  outer layers, ±3 ops on inners (arc emission), on a 136-part 4L board.
- Drill files must use the board's AUX origin consistently with the plots
  (the export script handles this; don't mix origins).
- CPL Y axis is negated from pcbnew's internal coordinates (script handles).

## Pipeline

```
1. GATE      audit + classified DRC green (see kicad-pcb skill; on KiCad ≥ 9
             use `kicad-cli pcb drc --severity-all --refill-zones
             --schematic-parity` — the parity flag catches parts that exist
             in the schematic but never made it to the board, i.e. a BOM
             that silently omits a designed part)
2. EXPORT    /usr/bin/python3 scripts/export_jlc_package.py BOARD.kicad_pcb OUTDIR --layers 4
             (KiCad-bundled python; emits gerbers, drills, BOM, CPL, and the
             zip; stale fab files from an older KiCad version are excluded
             from the zip with a warning — delete them when it says so)
3. STOCK     python3 scripts/jlc_stock_check.py OUTDIR/bom_jlc.csv --search-missing
             then the SPEC-CONFIRMATION pass below; re-run until every line
             is coded + in stock
4. RE-EXPORT run export again after LCSC fills — carry-over keeps the codes
             (keyed by Comment+Footprint), zip is rebuilt fresh
5. UPLOAD    zip → PCB order; bom_jlc.csv + cpl_jlc.csv → assembly; then the
             human checklist below against JLC's rendered preview
```

## Spec-confirmation pass (between STOCK and RE-EXPORT)

The search proposals match value + package only — they cannot see voltage,
tolerance, dielectric, or power specs. Before a proposed code goes into the
BOM, confirm per part class (the BOM Comment usually encodes the intent —
"2u2 VCC", "100u hybrid 25V", "20k RILIM3 (~3A)"):

- **Ceramic caps**: voltage rating ≥ rail with derating headroom (X5R/X7R
  lose real capacitance with DC bias — a 6.3V-rated 2.2uF at 5V is not
  2.2uF), dielectric X5R/X7R for decoupling, never Y5V.
- **Resistors**: tolerance where it matters (dividers, RILIM, feedback:
  1%; pull-ups: 5% fine), power for shunts/bleeders.
- **Electrolytics/polymer**: voltage, ripple current, physical
  height/diameter vs the footprint and enclosure.
- **ICs/diodes**: exact MPN match, or a datasheet-verified equivalent —
  never accept a "similar" MPN on string match alone (TPUSBLC6-2SC6 is a
  clone of USBLC6-2SC6; decide clone-acceptability deliberately).
- **Connectors**: exact series + pin count + orientation (vertical vs
  horizontal changes the footprint).
- **Part CLASS beats value string**: a comment like "10k NTC 3380K" on an
  R_0402 footprint is a THERMISTOR, not a resistor — value-token matching
  coded it as a plain 10k and nearly shipped it as the temperature sensor
  (SPF power board, caught at upload). Grep comments for NTC/PTC/fuse/
  ferrite/bead and confirm the part class explicitly.

Record confirmed codes in the BOM's LCSC column; the export carry-over
preserves them across regenerations. Leave a line blank rather than
half-confident — verify mode will keep failing it, which is the point.

## Stock checking (the part people skip)

`scripts/jlc_stock_check.py` queries JLC's parts search endpoint
(`POST https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList`,
JSON body `{"currentPage":1,"pageSize":N,"keyword":"..."}`). Unofficial but
verified working without auth 2026-07. Returns per part: `componentCode`,
`stockCount`, `componentLibraryType` (`base` = basic, no setup fee;
`expand` = extended, ~$3 setup per reel), price breaks, LCSC URL.

- **Verify mode** (default): every BOM line with an LCSC code → exact-match
  lookup; FAIL on not-found or stock below `--min-stock × qty`.
- **Search mode** (`--search-missing`): lines without a code → keyword
  search from Comment + package token, candidates ranked basic-first then
  stock-desc. Candidates are PROPOSALS — a human confirms each before it
  goes in the BOM (the ranking cannot see voltage/tolerance/temp specs).
- Be polite: the script sleeps ~1.2 s between calls; a 96-line BOM takes
  ~2.5 min. Don't parallelize — this is an unofficial endpoint.
- Search-quality empirics (all verified live): JLC's search wants
  datasheet notation, NOT RKM — "2.2uF" finds the 4M-stock basic part,
  "2u2" finds only zero-stock noise (the script normalizes 2u2/4k7/0R22
  automatically). `C99xxxxxx` codes are consigned-sourcing placeholders,
  permanently stock=0. THT connectors (USB-A, headers) are usually ONLY
  consigned — zero-stock proposals there mean "hand-solder or consign",
  not "search harder".
- If the endpoint breaks (it's unofficial): fallback is the jlcparts
  mirror (github yaqwsx/jlcparts, daily-updated dump of the same library),
  or manual search at jlcpcb.com/parts.
- Basic-vs-extended matters at order time: each extended reel adds a
  setup fee, so prefer `base` parts for passives when specs allow.

## Deterministic rotation/polarity verification (beats preview squinting)

JLC's own footprint per part is fetchable:
`https://easyeda.com/api/products/<LCSC>/components?version=6.4.19.5` —
CloudFront-403s plain curl but works through a browser-grade fetcher
(WebFetch). The returned PAD entries are in JLC's model-zero frame (units:
10 mil, y-down). Compare their pad1→padN vector against the board's
absolute pad vector to COMPUTE the exact CPL rotation (rot = θ_board −
θ_jlc, y-up CCW) instead of iterating preview screenshots — then bank the
offset as a rotation-DB rule. The same data cross-checks POLARITY: their
pad/pin polarity vs your pad nets found a reversed battery connector
(KiCad's AMASS_XT60PW-M pad 1 is the "−" blade; a pin1="+" symbol shipped
+ into GND). Run the polarity audit (kicad-pcb skill: pad 1's net vs the
footprint's own marker) on every 2-pad polarized part BEFORE ordering.

## Order-review empirics (reading JLC's BOM/preview screens)

- **Qty 0 + no price on a matched line** = JLC wants manual confirmation,
  NOT stock-out — click the row, search the code, confirm. ICs and
  higher-value extended parts trigger this; exact MPN in the BOM largely
  prevents it (see MPN column below).
- **Qty > refs x boards** on small extended passives = attrition padding
  (feeder loss allowance). Normal, costs cents.
- **3D preview color semantics**: white = your silkscreen; magenta glyphs
  = THEIR model's pin-1/polarity markers. Missing body = no 3D model
  (part still mounts — check the BOM tab, not the render).
- **THT preview offsets are cosmetic** (holes constrain assembly) but THT
  ROTATION is real operator instruction; **SMD preview rotation is exactly
  what the machine does** — fix it, don't rationalize it.
- **Re-uploading the BOM resets part matching and Do-Not-Place marks**;
  CPL re-upload only redoes placements. Sequence edits accordingly.
- **MPN column**: the exporter emits `Comment,Designator,Footprint,MPN,LCSC`
  when `OUTDIR/lcsc_mpn_map.csv` (LCSC,MPN) exists — populate it from the
  stock-check attribute data. Code + exact MPN together auto-match lines
  that token comments ("LM5145") leave at "No Part Selected".

## Order-time human checklist (JLC preview, before paying)

1. **Rotations** — the classic CPL failure. JLC's rotation zero differs
   from KiCad's per package family; the exporter auto-corrects via
   `scripts/jlc_rotations_db.csv` (community DB + local rules — extend it
   when a new package family shows up rotated). STILL eyeball the preview:
   diode/LED reel orientations vary per part (not in the DB), THT
   connectors are hole-constrained but their orientation instructs the
   operator, and bottom-side parts need their own check. Missing 3D models
   (e.g. Sunlord inductors) render as empty space — that's cosmetic, the
   part still mounts.
2. **Small-via option** — if the board has vias < 0.45/0.2 mm, the
   "advanced" PCB option must be selected or JLC rejects/holes drift.
3. **Stock re-check on order day** — stock moves; re-run verify mode the
   same day you order.
4. **DNP semantics** — parts with "DNP" in Value are excluded from BOM/CPL
   but still in the gerbers (pads present, unpopulated). A real MPN
   containing "DNP" would be silently dropped — grep the BOM if in doubt.
5. **H\* refs are skipped as mounting holes** — if a project uses H* for
   real parts, fix the refs before export.
6. Confirm layer count / stackup in the order form matches `--layers`.
7. **First-power ritual when boards arrive**: before the first real power
   source, multimeter the power-entry connector blades against the board
   nets (polarity + continuity to the fuse/protection). Thirty seconds of
   beeping beats every upstream analysis — polarity bugs are electrically
   self-consistent and invisible to all checks (three found on one board).

## Provenance & maintenance

Everything here was validated on a real 4-layer JLC order flow (SPF power
board, 2026-07); the stock endpoint response shape was captured live
2026-07-14. When JLC changes the endpoint or CSV formats, fix the scripts
AND update this file in the same change. Board-design empirics stay in
`kicad-pcb`; only JLC-facing knowledge lives here.


## Learnings 2026-07-16 (usb-power-3s order prep)

- Template-derived projects number-prefix their folders in pipeline order
  (01_docs, 02_parts, 03_src, 04_kicad, 05_firmware, 06_build, 07_releases);
  generic references like `parts/<MPN>` mean the parts folder whatever its
  prefix.

- `PLOT_CONTROLLER.SetOutputDirectory(relative)` resolves against the BOARD
  file's directory, not the cwd — the zip step then ships a drills-only
  "gerber" zip (2 files instead of 13). The export script now resolves the
  outdir absolute; always sanity-check the zip file count (4-layer = 13).
- Sourcing lives in `parts/<MPN>/part.yaml`; the BOM seed step maps BOM
  comments -> MPN -> lcsc and FAILS on unmapped lines or TBD sourcing.
  Inline `# comments` inside YAML flow mappings (`{lcsc: C123  # note}`)
  are a parse error that hides until the first automated read — use block
  mappings with a `note:` key.
- `jlc_stock_check.py --search-missing` resolves value-only passives to
  live LCSC candidates (basic-first) well; still confirm V/tol/dielectric
  by eye before adopting, then create the real-MPN parts/ entry and delete
  the TBD placeholder.
- Parts genuinely not in the JLC catalog (e.g. CNCTech USB-A jacks) stay
  UNCODED in the BOM on purpose: an explicit hand-solder list in the seed
  script + `not_assembled:` line in the release MANIFEST, not a fake code.
- Every release also ships `pdf/`: `kicad-cli sch export pdf` (schematic),
  `kicad-cli pcb export pdf --mode-multipage -l <coppers,silk,mask>
  --cl Edge.Cuts` (layer review), and a `--mode-single -l
  F.Fab,F.Silkscreen,Edge.Cuts --sketch-pads-on-fab-layers` assembly view
  (hand-solder/rework aid). Render each to PNG and eyeball before shipping;
  list all three in the MANIFEST sha256 table.


## Stage: JLC digital twin (run before EVERY order - scripts/jlc_twin.py)

What JLC will assemble is their CAD at your CPL coordinates - not your
footprints. This stage verifies the correspondence offline:

```
python3(pcbnew) scripts/jlc_twin.py BOARD bom_jlc.csv OUTDIR \
    --adjudications <project>/03_src/rules/twin_adjudications.yaml
```

1. Fetches JLC's own footprint + 3D model per LCSC code (easyeda2kicad,
   cached per-code in OUTDIR/easyeda/; EasyEDA rate-limits bursts - the
   script retries with backoff).
2. Pad-correspondence best-fit over rotation {0,90,180,270} x mirror.
   **A MIRRORED best-fit means a mirror-numbered land pattern = dead board.**
   On its FIRST run this found a live one: a vendored VQFN-20 wound CW
   (pin 1 bottom-left going up-left-side) where the datasheet + KiCad TI
   convention wind CCW - invisible to DRC/parity/LVS because the netlist is
   self-consistent either way. Adjudicate against the DATASHEET pinout
   figure + the same-family KiCad std footprint (three independent sources).
3. Rotation audit: fitted angle vs jlc_rotations_db.csv; disagreements print
   suggested rows. The DB stays the empirical layer (JLC's assembly-zero is
   not always their EDA-zero) - verify in the JLC preview, don't blind-apply.
4. Known-different findings (merged drain pad vs JLC's split fingers, THT
   clip-pin counts, parts absent from EasyEDA) go in the project's
   twin_adjudications.yaml WITH the verification evidence - the gate is
   ZERO unadjudicated criticals, and the release MANIFEST cites the twin
   report in verification/.
5. Twin render mounts JLC's WRL models on YOUR board (OUTDIR/twin_top.png,
   twin_bottom.png + twin.kicad_pcb to orbit in the KiCad 3D viewer) - the
   local substitute for JLC's end-of-order preview. Adjudicated parts are
   mounted at their best non-mirrored fit precisely so a human can eyeball
   them. Transform gotchas encoded 2026-07-16: model offsets are
   FOOTPRINT-LOCAL mm (absolute coords put every body ~60mm off) and the
   3D frame is y-UP while board coords are y-down.

Stock + selection gates recap (same stage): every assembled BOM line carries
an explicit LCSC code (bom_seed fails on unmapped/TBD - never rely on JLC
auto-match); stock re-checked at order time with min-stock >= qty x boards;
parts not in the JLC catalog stay uncoded with a hand-solder plan.
