# Routing journal

## 2026-08-13 — D16 deterministic route preparation

Input authority is the D15-approved, segment-free 90 x 65 mm board at SHA-256
`3fffbc690051998618880c63afcc559ddd37370e516f4869f670cf51288f2c42`.
The source board remains byte-identical; preparation writes only the derived
`06_build/route/r0.kicad_pcb` route input.

### Route contract

- Nine RF nets are explicit source-owned F.Cu polylines at 0.295 mm over the
  continuous In1.Cu ground plane. They have zero vias, zero stubs and no
  meanders or phase-matching requirement. Path-loss balance is measured on the
  first article rather than approximated by adding copper.
- U1 RF pins first escape normal to their QFN side and each SMA is approached
  normal to its edge launch. The middle span then uses the shortest exact-
  collision-clean line available. This avoids cutting through the interleaved
  package-ground lands or SMA ground posts.
- GND is excluded from stochastic routing. Plane-pad rescue runs before KRT;
  six U1 perimeter ground lands receive 0.6 mm under-package links directly
  into the exposed-pad copper and its separately authored filled/capped 3 x 3
  via field. Ordinary vias are not placed in component lands.
- Remaining nets are partitioned into five bounded waves: switch controls,
  Type-C CC, VBUS, 3V3 and SWD/reset. One candidate is attempted first; a race
  is justified only by a measured incomplete/dirty quick verdict.
- The 5 mm rectangular via lattice is ordinary board stitching only. It is not
  credited as a 5.9 GHz RF fence. The actual routed RF centrelines require
  collision-checked fence rows and an independent saved-board aperture gate
  before RF PCB approval.

The route choices agree with pSemi DOC-75785-4 Figure 21 and its instruction
to use good RF ground, short ground connections and the evaluation layout as
the application reference. Analog Devices' [RF and mixed-signal PCB layout
guidance](https://www.analog.com/en/resources/technical-articles/pcbs-layout-guidelines-for-rf--mixedsignal.html)
likewise recommends grounded coplanar routing, fences on both sides and an
unbroken plane under the line. Its [MMIC layout application
note](https://www.analog.com/media/en/technical-documentation/application-notes/layout_guidelines_for_mmic_components.pdf)
gives a conservative `lambda/20` maximum hole spacing. Applying that to the
retained JLC calculator effective dielectric constant gives 28.691 mm guided
wavelength at 5.9 GHz and a rounded-down 1.40 mm realized-fence bound. This is
an authored engineering constraint, not a claim that a rectangular requested
lattice will survive collision rejection at that pitch.

### Execution stack

```text
approved source board (SHA 3fffbc690051, zero segments)
  -> YAML/schema parse
  -> tier_preflight
       -> effective clearance / via / aspect / hole checks
  -> prep
       -> refuse any pre-existing routed segment
       -> unfill copied zones
       -> emit edge / M3 / NPTH router keepouts
       -> exact-collide every deterministic RF/GND primitive
       -> rescue every remaining SMD GND pad to In1.Cu
       -> partition every stochastic net exactly once
  -> r0 route input (SHA d598d305f5d7)
  -> quick copper/connectivity classification
       -> RF absent from open-net set
       -> only five declared stochastic wave groups remain open
       -> zero quick copper violations
  -> intentional D16 reflection pause (no KRT run yet)
```

Equivalent pseudocode:

```text
assert sha(source_board) == approved_D15_sha
assert source_board.routed_segments == 0
assert tier_preflight(route_contract) == PASS

r0 = copy_and_unfill(source_board)
emit_router_keepouts(r0)
for polyline in deterministic_rf_and_u1_ground:
    assert touches_declared_pin(polyline)
    assert exact_foreign_copper_collisions(polyline) == 0
    emit(polyline)
assert rescue_plane_pads(r0, net=GND, plane=In1) == 32/32
assert partition(remaining_nets) == [switch, typec, vbus, rail, debug]
assert quick(r0).copper_violations == 0
assert quick(r0).open_non_deferred_nets == union(partition)
stop_before_stochastic_route()
```

### Measured iterations and reflection

| Step | Time | Result | Learning |
|---|---:|---|---|
| tier preflight | 0.07 s | initially found one unsafe normalizer threshold, then 0 FAIL / 0 WARN | effective tool defaults belong in cheap source preflight |
| first exact seed attempt | 0.41 s | refused 7/9 straight RF segments | zero courtyard intersections did not prove copper clearance against adjacent U1/SMA ground pads |
| package/launch-normal RF correction | 0.62 s | 9/9 RF nets emitted; 26/32 SMD GND pads served | exact endpoint escape geometry is part of an RF launch, not a router cosmetic |
| U1 ground closure | 7.60 s | 15/15 banks, 29 seed segments, 32/32 SMD GND pads | short ground-to-EP links avoid unjustified ordinary via-in-pad and close the excluded-net denominator before KRT |
| quick route-input check | 1.03 s | 0 copper violations; 30 expected non-deferred open items, exactly the five declared waves; 60 GND items deferred to fill | the next router run has a precise denominator and cannot look “stuck” without a named wave/heartbeat |

The final r0 contains 23 RF segments, six under-package U1 ground links, 22
additional plane-rescue stubs, 22 ordinary rescue vias and the nine source-
owned filled/capped U1 exposed-pad vias. RF lengths are 14.504 mm common,
22.408 mm ANT1/8, 35.097 mm ANT2/7, 31.501 mm ANT3/6 and 36.593 mm ANT4/5.
Every RF segment is 0.295 mm on F.Cu and every RF via count is zero.

KiCad CLI run directly on the build-located r0 reported the expected 30
unconnected route-wave items plus 36 `lib_footprint_issues`: moving the copied
board under `06_build/route` changes `KIPRJMOD` resolution and there is no
annotated schematic beside that derived board. That is not used as a clean DRC
claim. The authoritative source-board placement DRC remains 0/39/0; the r0
quick check is used only for copper and open-net classification until import,
stitch, final rule regeneration and canonical full DRC run on the real board.

Generalized actions are recorded under IMP-034, IMP-035 and IMP-080.

The first repeatability check then found that two geometrically identical prep
runs minted fresh UUIDs for keepouts and deterministic copper, producing
different r0 byte hashes. Because route resume authenticates the r0 SHA, this
was a real process defect rather than harmless serialization noise. The shared
prep backend now seeds KiCad's UUID generator from the source-board namespace,
and a regression fixture prepares the same seed/rescue board twice. The v5
reruns completed in 0.56 s and 0.53 s and are byte-identical at SHA-256
`d598d305f5d75dd5bcebdd8320ef0949ca787bd0f5c7e53a573c66c995e726de`.
This completed general improvement IMP-081 before any route progress was
recorded.

## 2026-08-13 — rejected first KRT chain and endpoint-escape repair

The first five-wave chain did not lock up: it completed in 4.6 seconds with
heartbeats and named wave boundaries. It was nevertheless not promotable.
`quick_r5.json` measured 61 remaining connections: 60 deliberately deferred
GND/plane items and one routed-net open, `SW_V1` at U1.9. A three-candidate
race was then justified by that measured dirty result. All three candidates
completed at about 13.7 seconds, produced the same one routed-net open and
zero quick copper violations, and were correctly rejected with `chosen:null`.
The repeatability is useful evidence: this was a deterministic endpoint escape
failure, not a stochastic candidate-quality problem, so another race would
only spend time.

Inspection found a more important contract violation behind the superficially
small open. KRT printed `Via-in-pad unblock` and added ordinary vias directly
in seven SMD lands:

| net | land | emitted via (mm) |
|---|---|---:|
| SW_V2 | U1.10 | 0.300 / 0.150 |
| SW_V3 | U2.9 | 0.400 / 0.200 |
| SW_V3 | U1.11 | 0.300 / 0.150 |
| USB_CC2 | J1.B5 | 0.300 / 0.150 |
| USB_CC1 | J1.A5 | 0.300 / 0.150 |
| 3V3 | U1.8 | 0.300 / 0.150 |
| NRST | C6.1 | 0.450 / 0.200 |

Only U1's separately authored, filled/capped 3 x 3 exposed-pad field permits
via-in-pad on this board. The rejected chain's fine ordinary vias also account
for the deferred annular/minimum-drill/via-diameter warnings. Preparation had
exposed a related generic bug: although `pad_rescue.via_in_pad` was false, the
adjacent-via search for one J11 GND land could legally see another same-net
J11 land and placed a via at J11.5. Same-net copper clearance is not assembly
permission to drill a component land.

### Repair before retry

The repair moves only the boxed package escape into deterministic source
geometry. It adds short, exact-collision-refusing dogbones for U1/U2 V1--V4,
U1.8-to-C4 3V3, J1-to-U4 CC1/CC2, C6 NRST and the three J11 GND lands. The
remaining trunks are still KRT work. J11 is excluded from automatic rescue
because its three explicit 0.45/0.20-mm drops now own that obligation. The
first guessed geometry was not forced through: the emitter refused two
diagonals that crossed adjacent U1 pins, two CC diagonals that crossed unused
USB contacts, and then the SW_V1 path beside C4. The corrected paths use
package-normal exits and a measured lane beside C4; the exact emitter accepts
30/30 banks with 66 segments/vias and zero foreign-copper collisions.

The generalized correction landed before the board retry:

```text
for each successful KRT wave(input, output):
    new_vias = multiset(output vias by net + exact position)
               - multiset(input vias by net + exact position)
    for via in new_vias:
        if via.center intersects any SMD land:
            record(via net, position, size, drill, REF.PAD)
            fail wave before progress authentication or next wave

if pad_rescue.via_in_pad == false:
    reject every adjacent candidate whose center intersects any SMD land

remove stale FINAL before starting any single-chain, resume or race attempt
```

The shared regression suite is 108/108 non-slow tests, including 47
known-bad fixtures that make their gates fail, and schema-reader governance is
616/616 with zero orphan keys. It now covers source-owned-via allowance,
failed-wave progress exclusion, clean and race paths, early stale-`FINAL`
invalidation and mask-only apertures; gate-contract audit passes 59/59. Two
fresh preparations are byte-identical at
SHA-256 `cab54a0b9f9d304bdd9cf68c0d4ed756e8e93814dfe845db9de4e923756ca695`.
The source-to-r0 via comparison finds zero newly-created vias in SMD lands.
Fresh r0 DRC has no copper, clearance, hole or edge defects; its 36 library
context warnings and 41 pre-fill dangling-via reports are expected on the
derived, unfilled route input and are not a fabrication verdict.

Reflection: the expensive part was not router runtime; it was discovering
that a zero-exit router had satisfied connectivity by violating a physical
assembly policy that existed only in prose. Per-wave semantic gates and
source-owned minimum dogbones turn that late inspection into an immediate,
named failure. This is recorded generally as IMP-083. The next action is to
renew the exact design-rule-bound placement reviews/checkpoint, rerun one
five-wave chain, and stop again for a measured quick verdict before import.

### First executable-wave-gate result

After the exact reviews/checkpoint were renewed, the new switch wave reached
its semantic gate and stopped there. KRT's initial multi-point pass connected
10/12 switch pads; its reconciliation then used `Via-in-pad unblock` at U2.8
and U2.9 and independently placed a third via in R6.1. The guard recorded all
three exact sites and failed the wave before sidecar promotion, route-progress
append or the next wave. `route_progress.json` remains an empty authenticated
prefix and `FINAL` is absent. This is the intended stage boundary: the board
did not need a later quick/full DRC cycle to discover the assembly violation.

The measured blocker was the geometry of the first dogbone repair, not random
router quality. Four U2 via endpoints had been placed on one 0.65-mm-pitch row;
KRT's 0.10-mm search cells around the middle two endpoints were all blocked by
adjacent switch nets. The renewal fans V4..V1 monotonically to four separated
sites `(62.40,58.50)`, `(63.40,58.80)`, `(64.40,59.20)`,
`(65.40,59.70)` and supplies explicit signal dogbones for R4.1, R5.1, R6.1 and
R3.2. A guessed V4 straight escape was refused against C6.1; the accepted
fan-out shifts it clear rather than weakening clearance. The stable prep now
accepts 34/34 banks / 78 items, adds no via in an SMD land, and has no fresh
copper/clearance/hole/annular/parity DRC findings. One bounded switch-wave
retry is appropriate only after the renewed exact review/checkpoint; another
race is not.

## 2026-08-13 — guarded five-wave route promoted

The repaired deterministic escape now contains 35/35 accepted seed banks and
80 prepared segments/vias. Two consecutive preparations are byte-identical at
r0 SHA-256
`31594a8e29417cf6b5a1a374918b1d6979329c38a8f9d4c84182d17a46d7c872`.
The source-to-r0 comparison still reports no newly created via in an SMD land,
and the fresh r0 DRC contains no copper, clearance, hole, annular-ring or
schematic-parity defect. Its remaining findings are the expected derived-board
library-context and pre-fill dangling-via classes; they are not a fabrication
verdict.

One five-wave run then completed and authenticated every boundary:

| wave | denominator | KRT time | new-via-in-pad gate |
|---|---:|---:|---:|
| switch | 12/12 pads | 0.592 s | PASS, 0 findings |
| typec | 2/2 nets | 0.570 s | PASS, 0 findings |
| vbus | 10/10 pads | 0.577 s | PASS, 0 findings |
| rail | 9/9 pads | 0.577 s | PASS, 0 findings |
| debug | 3/3 pads | 0.624 s | PASS, 0 findings |

The final chain is SHA-256
`2e8c4a1fa9909391778244080a22387cf0ac38a56bb5dd1fc336c9c57aa40896`.
The route-progress record pins the exact r0 and all five intermediate output
hashes. Its `config_sha256` remains the pre-promotion execution identity
`d23e6bd72cf49c6542444800f37425329cf667ed5010c9ecf5695c7562f38a2a`;
the current route source selects that result as the promoted import candidate
and P-ROUTEBASE independently proves it retains all 36 footprints, 46 base
vias and 83 prepared segments from the exact r0.

The 4.8-second quick verdict is `CLEAN`: zero routed-net opens and zero copper
violations. All 61 remaining ratsnest items are GND and are explicitly deferred
to plane fill/stitch. This is deliberately not a full-board or fabrication
claim: the promoted route has not yet been imported into the canonical board,
the zones are unfilled, and the full post-stitch DRC has not run.

### Routing-stage reflection

- Router search consumed only 2.94 seconds for the accepted chain. Most elapsed
  engineering time was exact failure classification, deterministic endpoint
  repair, review renewal and evidence capture—not silent computation.
- A multi-candidate race cannot repair deterministic package-access geometry.
  The identical three-candidate failure was enough evidence to stop racing and
  move only the minimum package escapes into source-owned dogbones.
- A zero-exit router result is not a physical-policy verdict. Running the
  no-new-via-in-pad semantic guard after every wave found the defect at the
  first offending boundary and prevented it from contaminating progress or a
  stale `FINAL` marker.
- Small, named waves plus authenticated input/output hashes make a slow or
  failed run localizable. The useful general denominator is not "routing is
  running" but "wave N owns these exact nets and has/had not crossed its gate."
- Prepared endpoint escapes should remain short and deterministic; stochastic
  routing still owns the long trunks. This preserves flexibility without
  asking a grid router to invent assembly-safe fan-out inside fine-pitch or
  connector pin fields.

The renewed placement checkpoint pins 24/24 reviewed inputs at SHA-256
`ff882e7bc4923f97f1d747a3d30a86a2ac2ca61ddd4953cf8a4811d1ab01b86a`.
The routing pause checkpoint pins 19/19 source, prepared, intermediate,
per-wave guard and quick-verdict artifacts at SHA-256
`8c61f08ee72ae6468f9c0ad83b2425197623ece2817bd695912497f2e51cd5e3`.
No import, stitch, fill or canonical-board mutation is included in this stage.
