# PCB mechanics and impedance journal — 2026-08-13

## Exact SMA drawing closure

- input: D12 confirms `901-143-6RFX` for J2–J10.
- did: resolved the current exact Amphenol product page, its current customer-
  drawing identity and PCN-031726; retained hash-bound drawing/PCN bytes.
- caught before PCB generation: the draft dossier named unrelated drawing
  `901-40129` and therefore carried a 1.52-mm ground-hole value. Exact drawing
  `SMA6252A2-3GT50G-50` Rev C specifies a 1.50-mm RF-contact hole and four
  1.70-mm ground holes on a 5.08-mm square.
- result: connector identity and drawing lifecycle are closed for footprint
  authoring. The custom footprint and placed mating directions are not yet
  approved.

```text
connector evidence stack
  current exact product page (901-143-6RFX, active, jack, RA, THT)
    -> current drawing link identity (SMA6252A2-3GT50G-50)
      -> retained Rev-C bytes + SHA-256
        -> role-labelled dimensions (RF hole != ground holes)
          -> custom footprint
            -> realized-pad measurement + render review (still owed)

  PCN-031726 (901-143-6RFX listed)
    -> CN to VN origin change
      -> explicit no form/fit/function/material/process change
```

## JLC 50-ohm geometry closure

- selected stack: four-layer 1.6-mm `JLC04161H-7628`, F.Cu over continuous
  In1.Cu, 0.2104-mm 7628 dielectric, Dk 4.4, 1-oz outer copper.
- method: use JLC's current coated-coplanar single-ended model and forward-
  evaluate metric candidates; retain the exact tool inputs and result.
- selected source geometry: 0.295-mm base trace width, 0.200-mm trace-to-ground
  gap, solder mask present. Live result: 49.971863887 ohm.
- discrepancy: the live calculator configuration supplied 1.0-mil mask over
  substrate while JLC's written guide publishes 1.2 mil. A cross-check using
  the written value remained within about 0.6% of 50 ohm. The order interface
  must echo the intended stack/impedance row and the calculator must be rerun
  before release; VNA evidence remains authoritative for the board.

```text
impedance execution stack
  official stackup page
    -> exact build JLC04161H-7628
      -> live calculator model + live configuration
        -> fixed gap 0.200 mm
          -> candidate width 0.295 mm
            -> forward result 49.9719 ohm / valid=1
              -> rf.yaml source geometry
                -> realized route audit
                  -> order-time JLC echo
                    -> first-article VNA
```

## Time and generalization reflection

- useful work was short: the exact drawing inspection and live impedance calls
  each took seconds once the authoritative identities were known.
- most elapsed effort was authority resolution: the vendor PDF endpoint
  rejected unattended access, a stale asset looked plausible, and JLC's prose
  and live configuration disagree on one mask parameter.
- general lesson: bind a footprint to exact part-page -> document identity ->
  retained hash before transcribing dimensions, and label holes/features by
  physical role. Bind impedance geometry to the exact live model/input/output,
  surface documentation discrepancies, and retain a late order-time recheck.

## Exact footprints and unrouted placement

- authored the exact Amphenol and pSemi lands from their manufacturer drawings;
  authored the exact-suffix GCT land from Rev B and cross-checked it against
  KiCad 10's exact GCT footprint plus fresh JLC `C5184243` CAD;
- retained fresh exact-code JLC CAD for all three specialty parts as an
  independent assembly comparator, never as a replacement for the current
  manufacturer land pattern;
- selected a 100 x 100 mm outline so the board remains inside JLC's common
  low-cost size while giving nine right-angle SMA bodies, four M3 torque paths,
  three assembly fiducials and a clear radial routing field;
- mapped the switch's cyclic RF-pad order to the board perimeter in the same
  cyclic order. All eight throw corridors are therefore topologically
  non-crossing before the router starts;
- put the GCT local `PCB Edge` datum and every SMA mating-face datum exactly on
  the outline; the saved-board measurement reports 0.000 mm error at all ten
  connector datums;
- moved U1 and U2 decouplers closer during render review rather than accepting
  a mechanically green but electrically lazy first placement.

```text
unrouted-placement execution stack
  exact manufacturer land patterns
    -> project-owned footprints + exact logical pads
      -> fresh JLC / stock-KiCad comparison
        -> 100 x 100 mm outline + M3 torque points
          -> cyclic RF edge order
            -> generated 33-part track-free board
              -> realized geometry measurement
                -> placement gates + pin-map + DRC
                  -> top / oblique / edge renders
                    -> human/fresh-context approval (this pause)
```

The generated board has 33/33 anchored parts, 162 copper pads, nine selective
0.45/0.20-mm filled/capped vias in U1 pad 25, no inter-footprint pad or
courtyard collision, and no placement-stage DRC or schematic-parity finding.
The 39 unconnected items are the expected track-free ratsnest. Straight-line
switch-to-throw spans are 41.265–46.580 mm, a 5.315-mm spread; these are
placement metrics, not routed lengths or phase claims.

## First mechanical grind and what generalized

The first generated board itself took less than one second. The useful
correction loop was bounded and visible:

1. exact GCT geometry exposed four 0.1944-mm NPTH-to-land gaps against a
   provisional 0.200-mm generic hole-clearance rule;
2. exact SOT-553 geometry exposed 0.150-mm device-land gaps against the
   provisional 0.200-mm default netclass;
3. the authored SMA silkscreen crossed its own plated lands and board edge;
4. P-PINMAP exposed that TSX's numeric USB logical ports had not yet been
   explicitly reconciled with GCT's alphanumeric physical contacts;
5. the critical-route gate required an explicit zero denominator and reason,
   because this board has controlled-impedance single-ended routes but no
   differential pairs.

Each was fixed in source: exact-package local clearance, manufacturer-compatible
hole floor, removal of decorative SMA silk, explicit evidence-backed pin
aliases, and a declared no-critical-pair reason. The second DRC returned zero
violations and zero parity findings. The general improvement is to run the
cheap package/footprint reconciliation and placement DRC immediately after the
first board generation, before any routing: all five defects were source-level
and would have been expensive noise inside a route grind.

## Checkpoint reflection

- elapsed cost was dominated by evidence reconciliation and 3D rendering, not
  board generation or DRC;
- the cyclic port-order decision creates a large, legible and routable board
  without asking a stochastic router to discover topology;
- the paid advanced option is justified only by U1's RF exposed-pad POFV field;
  no small escape trace or via is otherwise needed;
- the JLC SMA CAD uses drills 0.10 mm larger than the Amphenol recommended
  holes. The manufacturer land remains design authority, but this exact delta
  must be put through JLC assembly DFM at order time rather than being silently
  normalized now;
- the JLC SMA WRL is only a visualization comparator and does not match every
  Rev-C envelope dimension. F.Fab, the retained drawing and realized holes are
  dimensional authority.

## Final render-completeness catch

The first final render still showed J1 as bare lands even though its footprint
named KiCad's exact GCT STEP model. The headless renderer completed
successfully: the `${KICAD10_3DMODEL_DIR}` token simply did not resolve in that
process. This was an evidence failure, not a pad or orientation failure, but it
would have made the connector-edge judgement vacuous. The exact KiCad model was
copied into the project, hash-bound, and referenced through `${KIPRJMOD}`; the
board and all gates were regenerated. The final top, oblique and edge renders
now show the USB shell and mouth, including its exact south-edge alignment. A
bare/modelled top-view pair is promoted into `01_docs/renders/` so the visual
subject survives beyond the ignored build cache.

General lesson: render exit zero does not prove body coverage. Before a visual
review, enumerate every mechanically significant assembled ref, resolve its
model path in the same headless environment, and compare the expected-body
denominator with bodies actually rendered. This reinforces IMP-055 rather than
creating another overlapping process item.

Next: pause for the connector/RF/render judgement review. Routing remains
blocked until that review signs the exact board hash.

## D14 fitted-body closure

The connector-specific repairs still left the host-dependent stock package
models invisible in the promoted image: U2 was bare TSSOP lands and the small
U3/U4/D1/F1/R/C bodies were absent or visually ambiguous. The footprints had
valid `${KICAD10_3DMODEL_DIR}` entries, but a model token plus renderer exit
zero was again weaker evidence than the human-visible result.

Eight unmodified official KiCad 10.0.4 model files cover the 17 affected
references. They are now retained below `03_src/lib/3dmodels/`, bound through
`${KIPRJMOD}`, licensed and SHA-256 inventoried. Regeneration changed exactly
17 model path lines and no placement, pad, via, net or copper geometry. The
independent saved-board resolver reports 29/29 fitted bodies; placement gates,
pad separation and fresh placement DRC remain green at 0 violations, 39
expected unrouted connections and 0 schematic-parity findings. D14 top,
oblique and edge images visibly show every affected package, with U2 leads and
the smaller package bodies registered to their stock KiCad lands.

This was a cheap early correction once the denominator existed: generation
took under one second and the three complete renders under fifteen seconds.
The general process change is P-MODEL immediately after board generation and
before modeled human review. It closes missing/unresolved files; it does not
close body registration, which remains a separate mechanical visual review
until IMP-055's attachment-field projection is implemented.

## Route-preflight correction

The three preflight findings were corrected in source before any route prep.
The common router clearance is now the strictest adopted class value,
0.20 mm, rather than the advanced tier's merely manufacturable 0.09-mm floor.
Ordinary routing uses JLC's preferred 0.45/0.20-mm via: 8:1 at nominal 1.6-mm
thickness and 8.8:1 at JLC's published +10% thickness corner, beneath the
declared 10:1 PTH limit. The legalizer pocket is 0.58 mm—the actual 0.20-mm
route drill plus twice the board's 0.19-mm hole clearance—not only the
0.53-mm threshold the tier-minimum warning requested.

R-PREFLIGHT changed from 2 FAIL / 1 WARN to 0 / 0 in about one tenth of a
second. Because all fitted parts are anchored, regenerating with the larger
legalization input produced the identical `8429ce851ed4` board. The process
lesson remains IMP-078: these were source-known facts and should be checked
before TSX and human review. The current late check did its job before copper,
but still later than economically necessary.

## D15 compact five-top/two-per-side placement

The original 100 x 100 mm ring was a conservative topology proof, not a
component-density limit. D14 requested five SMAs on the north edge and two on
each side, then accepted 90 x 65 mm as the comfortable target. The existing
PE42482 cycle was cut between ANT4 and ANT5 and laid onto an open-bottom U:
ANT4, ANT3, ANT2, ANT1, COMMON, ANT8, ANT7, ANT6, ANT5. This preserves boundary
order and gives zero proper intersections between the nine straight
pad-to-port corridors without consuming the south edge.

The exact `901-143-6RFX` body is 7.0 mm wide. North-edge centres are 15 mm
apart, leaving 8 mm nominal body-to-body space; the two side pairs are 18 mm
apart. Four M3 holes, three fiducials, keyed SWD and the USB-C datum remain.
The board area falls from 10,000 to 5,850 mm2 (41.5%). The common straight span
falls from 36.501 to 14.502 mm; the eight throw spans are 19.983–35.676 mm and
the former maximum was 46.580 mm. These values are topology/placement evidence,
not routed length, loss, phase or matching claims. A conservative screen of
each straight RF corridor against every foreign courtyard bounding box finds
1.535 mm minimum clearance (ANT4 versus C4), leaving visible route/fence
planning margin without claiming final routed geometry.

The first compact generation completed in 1.46 s. All pin/placement/model/pad/
policy/DRC/escape/tier checks completed in 4.7 s, and the first full top,
oblique and edge evidence set took about 21.5 s. That render exposed one
minor automatic-silk ownership warning: J1's reference was 0.32 mm closer to
F1 than to its own anchor. Moving F1 1 mm north preserved the power topology,
cleared the warning, and the final board regenerated in 0.56 s with 29/29
owned reference labels. Fresh final 3D evidence took 19.3 s. The expensive
part of this stage was engineering judgement and evidence updates, not board
generation or verification.

General lesson: derive a first floorplan from both the electrical boundary
order and operational connector envelopes. A closed radial ring proved
routability but silently selected a large square. Testing whether the same
cycle can be cut into an open perimeter exposed a much smaller embedding.
Report a geometric minimum separately from a comfortable target, using mating
hardware/tool access, mounting torque paths and routing/fence space—not KiCad
courtyards alone. This is recorded as IMP-079.

The user then made “Great means its approved” explicit. D15 binds that approval
to exact board SHA-256
`3fffbc690051998618880c63afcc559ddd37370e516f4869f670cf51288f2c42`
and the retained top/oblique/edge renders. This closes the human placement
pause and authorizes route preparation. It does not approve copper that does
not yet exist; routed launch, return-path and fence geometry still require an
exact-board RF PCB review.
