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
