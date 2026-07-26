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
| Assembly: BOM | `bom_jlc.csv` | Columns exactly: `Comment,Designator,Footprint,MPN,LCSC`. **The LCSC code is the SOURCE's per-refdes code** (`circuit.json supplier_part_numbers`, auto-discovered or `--lcsc-source`), NOT a value+footprint match. Grouped by **(LCSC, footprint)**: one line per code (JLC's uploader warns "multiple lines matched to same part" if two lines share a code), so two DISTINCT codes on one value+footprint — 10uF/50V C77102 vs 10uF/25V C77100 — stay on SEPARATE rows. Grouping by (value, footprint) instead collapsed them and shipped 25V input caps on a 50V rail (v1.1, 2026-07-23). Uncoded (hand-solder) lines stay per-value. Verify with `bom_source_check.py` before sealing. |
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
             zip; LCSC comes from the SOURCE circuit.json per refdes —
             auto-discovered, or pass --lcsc-source; stale fab files from an
             older KiCad version are excluded from the zip with a warning)
3. STOCK     python3 scripts/jlc_stock_check.py OUTDIR/bom_jlc.csv --search-missing
             then the SPEC-CONFIRMATION pass below; re-run until every line
             is coded + in stock
4. RE-EXPORT run export again after LCSC fills — source codes + carry-over keep
             the codes (per refdes), zip is rebuilt fresh
5. BOM-SOURCE /usr/bin/python3 scripts/bom_source_check.py OUTDIR/bom_jlc.csv \
                CIRCUIT_JSON --parts 02_parts    (canon M6 / policy_audit M-BOM)
             every BOM LCSC code == the source's per-refdes code — no merged
             row, no substitution, no dropped vendored code. MUST pass before
             sealing; ship the output in verification/bom_source_check.txt
6. UPLOAD    zip → PCB order; bom_jlc.csv + cpl_jlc.csv → assembly; then the
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
  consigned — zero-stock proposals there ESCALATE the line: either CONSIGN
  it (you ship the part, JLC PLACES it — it stays ON the CPL and needs an
  `assembly.yaml` `consigned:` entry with `msl:`), or re-specify to a
  placeable part. "Hand-solder" is the last resort, and it is a decision
  with a record: an `assembly.yaml` `not_assembled:` entry whose `evidence:`
  is the DATED catalog query and its result, plus
  `exclude_from_pos_files` on the board so the part actually leaves the CPL.
  An uncoded line left on the CPL is not a concession, it is a defect —
  cooksense v1.1 sealed 13 of them (canon A-POP).
- **The VERDICT LINE IS THE GATE.** Five sealed releases in this fleet ship
  stock evidence whose last line says `FAIL:` — crow-recorder-central-v2
  v1.0-v1.3 each record their own CPU (C6938291) at `LOW_STOCK(0)` —
  because nothing ever parsed it, and one release (cooksense v1.1) ships a
  raw `--out` CSV report with NO verdict line at all. Write the sidecar
  (`--json verification/stock_check.json`) and let
  `release_freshness_check.py` check (e) grade it: an unparseable verdict
  is a FAIL, not a skip. The only way past a non-OK line is an
  `assembly.yaml` `sourcing_plan:` entry with `measured_stock` +
  `measured_on` (canon A-STOCK).
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

1. **Rotations** — the classic CPL failure, and since 2026-07-25 a BLOCKING
   gate rather than a checklist item (canon **A-ROT**). JLC's zero-orientation
   is a PER-PART fact: the per-LCSC MEASURED table `scripts/jlc_lcsc_
   rotations.csv` is the ONLY authority, and the footprint-NAME DB
   `scripts/jlc_rotations_db.csv` is now ADVISORY — loaded, cross-checked,
   never obeyed. Authority inherited by pattern-matching a NAME produced P0s
   on five boards in one day (wrong key / negated offset / no rule fired /
   partial prefix / unevidenced rule). **`export_jlc_package.py` exits 2** on
   any placement with no measured row, writes `rotations_unsourced.csv` as the
   worklist, and deletes any stale BOM/CPL. The one exemption is MEASURED, not
   named: a footprint that is its own 180-degree reflection in BOTH pads and
   graphics has no orientation to source.
   - to clear a block: `jlc_rotation_measure.py BOARD REF=LCSC ... --row`
     reports the PAD-NUMBER fit and the NUMBERING-FREE channels SEPARATELY and
     proposes the row. `jlc_rotation_audit.py --table` grades the authority
     (M-PROV + A-POL); `--fleet` prints the per-board migration worklist.
   - **NEVER populate a row from `jlc_twin`'s `jlc_offset`** — that is the
     checker's own output and it was negated for the fleet's whole history
     (canon M1 / M-PROV).
   STILL eyeball the preview, and MANDATORILY for every ref the export names
   in `rotation_human_gate.txt` (canon A-POL single-channel: no numbering-free
   channel exists, or the two channels disagreed). THT connectors are
   hole-constrained but their orientation instructs the operator, and
   bottom-side parts need their own check.
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
- A part genuinely not in the JLC catalog (e.g. CNCTech USB-A jacks) is a
  FAILED SOURCING DECISION, not a style. Escalate in this order: re-specify
  to a placeable part → CONSIGN it (populated, stays ON the CPL, needs
  `consigned:` with `msl:`) → and only then leave it unplaced, which costs a
  `03_src/rules/assembly.yaml` `not_assembled:` entry with a
  closed-vocabulary `reason:`, a DATED `evidence:` measurement (the catalog
  query and its result — a sourcing wall you PROVE you hit), a
  `disposition:`, AND `exclude_from_pos_files` on the board so it leaves the
  CPL. The release MANIFEST `not_assembled:` line is GENERATED from that
  file, never hand-written beside it: cooksense v1.1's two homes disagreed on
  12 refs and shipped. Never a fake code. Graded by `assembly_coverage.py`
  (canon A-POP).
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
    --adjudications <project>/03_src/rules/twin_adjudications.yaml \
    --also J1=C98732,J2=C53133490   # hand-solder parts with known codes
```

Pass `--assembly 03_src/rules/assembly.yaml`: it pulls the REF=LCSC pairs for
coded-but-not-assembled and consigned parts out of the ONE declared home, so
their bodies render and the connector-overhang/orientation class of check runs
for exactly the parts a human solders by eye. This REPLACES hand-typing
`--also REF=LCSC` — a hand-typed list is a second home for the population set
and drifts from the first (cooksense v1.1's MANIFEST and CPL disagreed on 12
refs for precisely that reason). `--also` still works for an ad-hoc probe.

1. Fetches JLC's own footprint + 3D model per LCSC code (easyeda2kicad,
   cached per-code in OUTDIR/easyeda/; EasyEDA rate-limits bursts - the
   script retries with backoff, 4 attempts by default,
   `JLC_TWIN_FETCH_ATTEMPTS=N` to be more patient).
   **A fetch failure is NOT "this part has no CAD".** Transient network/API
   errors are classified `FETCH-FAILED` (distinct from `NO-CAD`) and are
   **BLOCKING** - the part was never checked, so the run is not twin
   verification for it. The tool prints the partial-retry command: the
   per-code cache keeps everything already fetched, so simply RE-RUNNING
   retries only the failed codes. Only adjudicate `FETCH-FAILED` when the
   part is genuinely absent from the library (verify the land pattern
   against the datasheet + flag the order-time preview).
   Why this exists: lipo3s-usb-hub v1.0 lost 11 parts (XT60, USB-C, 3x
   USB-A, 6 FETs, ICs) to EasyEDA API errors, each recorded as `NO-CAD`,
   and the gate **exited 0 having verified almost nothing** - the twin's
   whole value is checker-independence, so a vacuous pass is worse than a
   failure. A re-run once the API recovered gave 74 OK / 205 checked and
   immediately surfaced real pad-geometry findings (2026-07-20).
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
3a2. Mount anchor is the UNWEIGHTED common-pad centroid - by measurement,
   not principle. A wetting-force (pad-area-weighted) anchor was tried and
   made the known PAD-GEOM case WORSE: JLC's big tab pad center sits ~0.3mm
   off their own tab METAL, so every pad-anchoring flavor inherits pad-
   style offsets that have nothing to do with the part. When a PAD-GEOM
   part renders visibly off-pad, the fix is a per-part `model_dx` /
   `model_dy` in the adjudication entry (OUR footprint-local mm, +x east
   +y south at rot 0), chosen from pixel measurements of the metal vs our
   pads and recorded with that evidence - never a global anchor tweak.
   THREE traps, each hit live (2026-07-16), now with tool-side guards:
   (a) FRAME: write nudges as `board_dx`/`board_dy` (board frame, +x east
   +y south) and let the tool convert through each ref's rotation - a
   hand-converted `model_dx` shipped 90deg wrong once. Every applied
   nudge prints a `NUDGE ref: local(..)->board(..)` echo line: READ IT
   and check the board-frame vector matches your intent before trusting
   any render. Then verify the applied shift by DIFFING before/after
   renders (body-pixel centroid), never by re-eyeballing.
   (b) MEASUREMENT: classify model vs board pixels by the render DIFF,
   not by color - exposed pads are NOT reliably bright, lead metal IS; a
   color-rule scan validated a wrong nudge once, and a static bright
   board feature near a pad polluted the measurement twice.
   (c) MODEL-SELF (automated): the twin now checks each JLC model
   against JLC's OWN pads in THEIR frame - a model drawn off its own
   footprint (~1mm seen live) fires MODEL-SELF, which tells you a nudge
   will be needed and that bbox MODEL-REG numbers (including the
   180-flip hint) are untrustworthy for that part. When metal-vs-pad
   and bbox disagree, metal wins.
3b. PAD-GEOM gate (critical, exit 1): pairwise pad-center distances between
   our footprint and JLC's must agree within 0.3mm. Pairwise distances are
   rotation/translation-INVARIANT, so unlike the best-fit residual - which
   splits a land-pattern disagreement across the pads and reports an
   unexplained scalar - they pin the delta to a named pad pair. Case that
   forced this: a DPAK whose KiCad tab-to-lead distance was 6.70mm vs JLC's
   7.31mm rendered its body 0.4-0.9mm off-pad, while the old output showed
   only "fit=0.43mm" and a MODEL-REG that got adjudicated away as bbox
   asymmetry. Adjudicating a PAD-GEOM requires citing which pattern matches
   the part datasheet's recommended land pattern.
3c. POLARITY-CHECK (informational, every 2-pad polarized part): the
   pad-number fit orients the MOUNT, but a 180-flipped MODEL (wrong internal
   orientation vs JLC's own footprint - the XT60 class) is invisible to the
   fit AND to MODEL-REG when the body bbox is symmetric. The render's
   polarity marking is the only machine-unverifiable signal left: check it
   by eye against our silk (prefer structural markers - polymer-can base
   bevel = positive side - over ambiguous paint like top crescents), and if
   the model is unmarked (some LED models are), fall back to the JLC order
   preview + CPL rotation.
3d. pad_alias (adjudication field): naming-convention clashes - SOT-223
   (KiCad TabPin2 merges tab+lead as "2", JLC tab="4"), merged-drain DPAKs -
   yield PAD-MISMATCH best=none, an UNMOUNTED model, and silently skipped
   model-side checks. Add {pad_alias: {"4": "2"}} to the part's entry to
   rename JLC pads before the fit; validated live: an AMS1117 went from
   PAD-MISMATCH+PAD-GEOM(1.6mm artifact) to OK fit=0.27mm (2026-07-17).
   Prefer an alias over adjudicating the MISMATCH away: the alias RESTORES
   verification coverage instead of waiving it.
4. Known-different findings (merged drain pad vs JLC's split fingers, THT
   clip-pin counts, parts absent from EasyEDA) go in the project's
   twin_adjudications.yaml WITH the verification evidence - the gate is
   ZERO unadjudicated criticals, and the release MANIFEST cites the twin
   report in verification/. Adjudication decomposition rule: a position
   finding's delta must be accounted for BY MECHANISM - MODEL-REG now
   prints `incl. pad_geom_delta=X` when a land-pattern disagreement is
   part of the number, and "bbox asymmetry" may only explain the portion
   measured in the model's own frame. If per-pad measurements show a
   pad GROUP shifted systematically in one direction, that is a land-
   pattern delta and may NOT be filed under "fit residual" (an
   adjudication did exactly that and buried a real 0.6mm disagreement).
5. Twin render mounts JLC's WRL models on YOUR board (six views:
   twin_{top,bottom,iso_nw,iso_se,edge_west,edge_east}.png + twin.kicad_pcb
   to orbit in the KiCad 3D viewer; the edge profiles double as component-
   height / enclosure-clearance checks) - the
   local substitute for JLC's end-of-order preview. Adjudicated parts are
   mounted at their best non-mirrored fit precisely so a human can eyeball
   them. Transform gotchas encoded 2026-07-16: model offsets are
   FOOTPRINT-LOCAL mm (absolute coords put every body ~60mm off); the
   3D frame is y-UP while board coords are y-down; and the fit/mount must
   center on the COMMON pad set only - own-set centroids slide the model
   along the part axis whenever one side names extra pads (an XT60 rendered
   7mm off its holes, nose not overhanging the board edge).
   **Model z-rotation is `jlc_rot_z - fit_angle`, and the mount offset goes
   through `xform()` — one change, never one or the other (CORRECTED
   2026-07-25; the paragraph here used to assert `+fit-angle` "verified by
   pixel-measuring the render", and the shipped build did not exhibit the
   outcome that comment described).** The handedness incident had FIVE
   copies: `xform()` (fixed 1b69760), the mount offset, the mount z, and the
   model-frame rotation in BOTH `reg_check()` and `model_self_check()`.
   `formB(a) == formA(-a)` identically, so all five agreed at 0/180 and were
   exactly 180deg out at 90/270 — which is why five copies survived review
   and why a rotation fixture that omits 90/270 proves nothing. All five now
   route through ONE named operator each (`xform` / `local_to_board` /
   `model_rot`), and each operator is pinned against an authority OUTSIDE the
   file: pcbnew for pad geometry, `kicad-cli pcb render` for the model frame
   (measured 2026-07-25: an asymmetric bar at rot_z 90 renders SOUTH and at
   270 NORTH, 0.014mm residual, vs 8.000mm for the other form).
   `board_to_local()` is a LEGITIMATE inverse whose literal text is identical
   to the bug — **match on the FRAMES a site maps between, never on the
   expression.**

6. MODEL-REG invariant (automated, every part with CAD): parse the WRL plan
   bbox, push it through the mount transform, and require the mounted body
   to sit on OUR footprint's courtyard (center delta < 1mm). Catches flipped
   or mis-registered models, wrong-model swaps, and mount-math bugs; when a
   180 flip would fix it the finding names the adjudication override
   ({lcsc, model_rot_z: 180}). The detector is CALIBRATED: a deliberately
   mis-rotated model must flag ~8mm - keep that as the regression test when
   touching any transform code.
   **MODEL-REG is BLOCKING (2026-07-25).** It used to be emitted and never
   appended to `criticals`, so it could not fail a run at all: usb-hub-3s-v3
   v1.5 sealed with a TRUE 14.37mm finding on its XT60 sitting beside a green
   verdict, closed by an adjudication that asserted the four pads landed on
   model features when they were measurably 4.3mm outside the housing. A
   finding that cannot block is a comment. It still needs a disposition —
   adjudicate with model_rot_z / model_dx-dy + evidence, or record why it is
   cosmetic — but now the run stops until you do. A USB-C (HRO TYPE-C-31-M-12) shipped in a
   v1.0 with its 3D model 180deg-flipped because the MODEL-REG line was
   left un-acted through review; pads were perfect (0.00mm) so only the
   render lied. Gate the release on: zero unadjudicated MODEL-REG, not
   just twin exit 0. BUT the disposition is often "false alarm, NO
   rotation": JLC's OWN footprint model rotation (the (rotate ...) in
   jlc.pretty/*.kicad_mod, which the twin already applies) is
   AUTHORITATIVE. For an asymmetric body (connector with a mouth) the
   bbox-center-vs-courtyard metric is offset even when correct, so the
   "a 180 flip fixes it" arithmetic is a RED HERRING (same as the Q1
   DPAK) - it lured a wrong model_rot_z onto a USB-C twice before the
   JLC .kicad_mod rot_z was checked. NEVER apply a model_rot_z that
   deviates from JLC's own model rotation unless the RENDER shows leads
   off the pads. Verify leads-on-pads visually + read JLC's .kicad_mod
   rotation; do not chase the metric.

6b. NO-BODY gate (automated, BLOCKING, own adjudication key; 2026-07-25).
   After mounting, EVERY CPL designator (`--cpl fab/cpl.csv`) is walked, its
   3D model path expanded through KiCad's own `${VAR}` table, and required to
   be a file with size > 0. Headline `bodies mounted: N/M`; `verification/
   missing_models.txt` is GENERATED from this pass and must never be
   hand-authored again. Deliberately independent of the fit path (canon M1):
   it asks the FILESYSTEM, not the fitter, so a skipped part, a failed fetch
   and an uninstalled KiCad 3D library all land in the same place.
   Incident: usb-hub-3s-v3 v1.5 shipped 7 of 108 placements (Q1-Q6, R12) with
   NO rendered body while its hand-written `missing_models.txt` stated the
   gap was zero, and the release quoted "0 ROT-DB-SUGGEST over 231 checks" —
   231 being the number of finding ROWS, not a coverage count. The real
   coverage was 101 of 108, and the uncovered 7 were exactly the parts at CPL
   90/270. **A PAD-MISMATCH or FETCH-FAILED waiver cannot discharge NO-BODY**
   — one waiver used to close two unrelated obligations. Quote COVERAGE with
   a population denominator, never a check count.
   Two enabling fixes ship with it: `fit_err` falls back to per-pad-number
   CENTROIDS instead of `return None` on a multiplicity mismatch (a NAMING
   convention was discarding the whole audit — KiCad's
   PowerPAK_SO-8_Single names five entities "5"), reported as the non-fatal
   PAD-MULTIPLICITY; and the KiCad 3D library must actually be INSTALLED
   (`${KICAD10_3DMODEL_DIR}` unset + `/usr/share/kicad/3dmodels` absent means
   every KiCad-path fallback renders nothing, silently, on that machine).

6c. POLARITY-FIT (automated, BLOCKING, own adjudication key; canon A-POL,
   2026-07-25). For a 2-pad COLLINEAR polarized part the pad-number fit
   cannot see a polarity swap — the pads are symmetric. The twin now also
   measures the NUMBERING-FREE channel: which pad each footprint's polarity
   MARKING sits nearest, from SHAPES only (text is placed for legibility, not
   polarity — counting a refdes would let its position decide which end is the
   cathode). Disagreement BLOCKS and names the physically correct offset; no
   usable marking is reported POLARITY-FIT-BLIND rather than passed silently.
   MEASURED on C2296/C2297 (KT-0805 LEDs): the pad fit says 180 at 0.1125mm
   with the next candidate 1.9875mm away (17.7x margin) — precisely wrong,
   because JLC numbers pad 1 = ANODE while KiCad's Device:LED is pin1=K. Both
   draw the cathode WEST, so the correct CPL offset is 0. Resolve against the
   DATASHEET terminal drawing, put the LCSC on the order-preview human gate,
   and never let a fitted angle populate jlc_lcsc_rotations.csv unchallenged.

7. SWIG trap: iterating fp.Models() and assigning m_Rotation.z on the
   yielded items silently does nothing (the write lands on a temporary).
   Build a NEW FP_3DMODEL and push_back it; verify the saved file text when
   in doubt - two no-op probes masqueraded as evidence here.

Stock + selection gates recap (same stage): every assembled BOM line carries
an explicit LCSC code (bom_seed fails on unmapped/TBD - never rely on JLC
auto-match); stock re-checked at order time with min-stock >= qty x boards
and the VERDICT PARSED, not just printed (`--json`, canon A-STOCK); a part
not in the JLC catalog is ESCALATED (re-specify -> consign -> declared
not_assembled with dated evidence + `exclude_from_pos_files`), never left
uncoded on the CPL (canon A-POP).

## Stage: the ASSEMBLY battery (PCBA is the deliverable)

The board is not the deliverable; the POPULATED board is. Run both against the
STAGED release directory, before the seal commit — a finding here costs an
edit, the same finding after the seal costs a supersede:

```
python3 scripts/assembly_coverage.py   07_releases/<ver>-<date>   # A-POP
python3 scripts/release_freshness_check.py 07_releases/<ver>-<date>   # incl. A-STOCK
```

`assembly_coverage.py` is plain python3 and re-derives `{board} − {CPL}` from
the BOARD's own text and the CPL/BOM bytes — never from
`export_jlc_package.py`'s filter logic (canon M1: do not verify the exporter
with the exporter). It takes a sealed release dir or a project dir. Copy its
output into `verification/assembly_coverage.txt` and ship
`verification/stock_check.json` (`jlc_stock_check.py --json`) beside it.

ROTATION IS RESOLVED PRE-SEAL, not audited after. Measure → add the per-LCSC
ROW (`jlc_lcsc_rotations.csv`) → **re-export the CPL** → then seal. A row
added after the seal fixes nothing that shipped: crow-recorder-central-v2
needed a whole v1.3 release whose fab set differs from v1.2's in exactly one
file (cpl.csv) to move one consigned TQFP-128's angle.

**The A-ROT gate itself is HELD (2026-07-25).** `jlc_twin.xform()` uses the
opposite handedness to `local_to_board()` — verified against pcbnew over 72
pads: local_to_board exact to 0.000000 mm, xform off by up to 23.93 mm, wrong
at every 90/270 part and sign-invariant (so invisible) at 0/180. Every
`jlc_offset` was therefore NEGATED, and six `jlc_lcsc_rotations.csv` rows
populated from it were all 180 deg wrong. Until the sign is fixed: do not
populate a rotation row from `jlc_offset`, and do not build a gate that ranks
that table as authority — derive the angle from the BOARD plus JLC's cached
model with an operator verified against pcbnew itself.
