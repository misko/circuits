# Placement checkpoint — 2026-08-16

> Historical v1-derived material follows. The current v2 checkpoint is the
> 2026-08-18 section appended at the end of this file.

## Outcome

The track-free four-layer board is ready for placement review, not routing or
fabrication. All 133 schematic parts are anchored; four USB-A receptacles form
the north-edge port bank, the upstream USB-B and protected 5 V input occupy
separate edges, and the hub/management/power cells remain visually distinct.
Five connector ESD devices and four FSUSB42 switches are deliberately on B.Cu beneath
their connector/data cells. No firmware was generated.

Measured checkpoint:

- generator: 133/133 anchored, 9 B.Cu, 18 source-bound exact model overrides,
  zero inter-footprint copper overlaps and zero same-side courtyard overlaps;
- placement policy: 5/5 checks and all 38/38 declared adjacency budgets pass;
- placement geometry: P-OUT/P-CAP/P-BODYCLR pass, including one evidence-bound
  USB-B mating-edge courtyard exception while every drilled/copper land stays
  on board;
- identity: P-PINMAP passes 293 declared physical identities over 27 multi-pin
  references; S-COUNT is 133/133 in board, circuit JSON, KiCad schematic,
  manifest and netlist;
- models: P-MODEL passes 133/133 fitted footprints; P-MODEL-REG passes the
  USB-A, USB-B and power-terminal tuples with 32/32 drilled attachment centres;
- pad geometry: 576 copper pads, 129168 inter-footprint pad pairs and 205535
  paste-to-foreign-copper pairs pass the current overlap/touch screen.

## Where the stage spent time

The largest effort was not moving parts. It was making the placement evidence
tell the truth:

1. the generic floorplan needed a first-class top/bottom-side declaration so
   ESD and data-switch paths could be short without top-side body collisions;
2. adjacency rules needed optional net scoping so the D+/D- clamp path was not
   graded through an unrelated shared VBUS reference branch;
3. exact connector STEP files needed explicit source-owned transforms and
   manufacturer-derived F.Fab/courtyard envelopes;
4. native connector models are multipart, so nearest-component pixel
   extraction measured one shell edge instead of the whole body;
5. a raw headless render lacked `KICAD10_3DMODEL_DIR`, exited zero, and omitted
   every stock KiCad package body despite P-MODEL resolving those files;
6. tscircuit's private `pin5_internal_1` identity for a repeated shell pad had
   to be normalized to physical pin 5 before pin-map comparison.

Each class was corrected in the shared pipeline and regression-tested before
the board was accepted. The resulting general changes are IMP-107 through
IMP-112 in `improvements.md`.

## What generalized well

- Exact native CAD before routing paid off. It caught a translated terminal,
  a too-small upstream-connector courtyard and incomplete render evidence while
  placement changes were still cheap.
- Electrical-path-specific adjacency is more faithful than whole-net-pair
  distance for ESD/filter devices that also share power or ground.
- Bottom-side placement should be an explicit authored property, not a
  per-board pcbnew postprocessor.
- Durable reports must list every finding; console truncation is acceptable,
  report truncation creates serial repair loops.
- Model-path coverage, XY registration, vertical/side-view registration and
  final pixels remain distinct claims. Passing one must never stand in for the
  others.

## Before routing

Placement approval still requires the exact-board pin/layout/render/A-RENDER
review receipts. Route preparation must replace the inherited example
`route.yaml`, declare every upstream/internal/downstream USB pair, select the
JLC advanced four-layer process and solve/lock the 90-ohm differential geometry
against the provisional stackup. Pre-route DRC and critical-pair inventory must
then pass. The first routing wave will contain USB data pairs only; power and
control follow after their geometry is preserved.

## 2026-08-16 correction before routing

This checkpoint describes the reviewed pre-correction placement and is retained
as an incident record, not current approval. Independent topology review found
four source defects before routing: the USB hub bulk bank was too small, the
simultaneous current-limit envelope was unbounded, the ESD selection exceeded
the channel capacitance budget, and prose overstated a command-state interlock
as actual VBUS sensing. Source now uses a TPS259474L aggregate eFuse, a charged
180 uF polymer plus 22 uF ceramic bank, and PESD2USB3UX shunt protectors. All
generated placement artifacts and prior receipts are stale until regenerated
and independently reviewed again.

## 2026-08-16 corrected placement-review boundary

The corrected 139-part design has now regenerated to the intended placement
pause. Routing has not started; route preparation produced only the
deterministic `r0` seed subject needed by the next reviews. No firmware was
generated.

Current measured checkpoint:

- 139/139 anchored footprints, 9 on B.Cu, 17 explicit source-bound model
  overrides, zero inter-footprint pad/courtyard collisions;
- S-COUNT 139/139, P-PINMAP 265 identities over 22 multi-pin references, and
  placement policy PASS=5 with 26/26 keep-short and 6/6 adjacency budgets;
- placement geometry, 574-pad separation, P-OUT/P-CAP/P-BODYCLR and exact
  refilled placement DRC all pass with zero violations and zero schematic-
  parity findings;
- P-LAND grades 281 pads, including 19 package-scoped launches, with zero
  failures; the TPS259474L power pins use a bounded 0.35 mm package neck before
  widening to the 1.50 mm input trunk;
- P-MODEL resolves 139/139 fitted bodies; P-MODEL-REG passes 4/4 groups across
  24 USB-A holes, 6 USB-B holes, 2 terminal holes, and 10/10 TPS259474L SMD pad
  centres.

This stage spent most of its correction time on evidence boundaries rather
than footprint movement. Two retired dossiers continued to impose executable
placement rules, a bottom-side footprint flip was later undone only for its
reference text layer, three custom footprint silks crossed exposed pads, and
the small eFuse lands could not launch the global trunk width. Every issue was
found before routing and fixed in its owning source rather than waived.

The general lessons are now IMP-090, IMP-115 and IMP-116 in
`improvements.md`: review freshness needs semantic dependency projections;
active dossier authority must bind to the live population; and generated text
must derive side, layer and mirroring together. The existing early P-DRC and
P-LAND gates worked as intended and should remain before human placement
review.

The only expected stop is now the missing exact-board pin, layout, render and
A-RENDER receipts. Those are the next stage; they must be completed before any
router wave is allowed to run.

## 2026-08-16 final digital-twin evidence correction

The catalog and pixel evidence now cover both assembly sides without a waiver.
The first twin run exposed two shared-checker defects rather than board
defects: catalog lands were compared to realised B.Cu coordinates without
undoing the side flip, and the image checker consequently refused to form any
bottom-side expected body. Both checkers now normalize through an independently
tested unflipped footprint frame. The exact board passes catalog fitting for
all nine bottom devices and bottom A-RENDER measures 9/9 expected bodies within
1.00 mm. Top A-RENDER measures 30/30 resolvable bodies within the same limit;
the other 99 expected top bodies are explicitly below the declared 2.0 mm
pixel-resolvability floor, not silently omitted.

Machine image evidence uses the 4K shadow-free `*_gate.png` populated/bare
pairs. High-quality renders remain for human presentation only: their cast
shadows inflated otherwise correct connector envelopes by approximately
1.50 mm and produced a repeatable false failure. No board, placement, model or
tolerance was changed to obtain the clean result. These two generalized fixes
are recorded as IMP-117 and IMP-118 in `improvements.md`.

## 2026-08-16 placement approval and pause

The exact-board pre-route review boundary is closed. Hash-bound topology and
schematic-render renewals remain SOUND after the display-model adjudication
register was added. Independent pin, layout and render lenses each judged the
track-free board SOUND and suitable to route. `pre_route_review_check.py`
passes 2/2 schematic evidence and 4/4 placement evidence against board SHA256
`c5b7bd72e8495044be1db8d6d7a95504b6fe7b09bdc99ba1b33aeea581da4e6c`.

No copper routing wave has run. The placement stage therefore ends at a real
pause, with these non-blocking obligations carried explicitly:

- give every USB layer transition close reference-ground vias and verify the
  adjacent planes remain uninterrupted;
- preserve the AP63203 switch loop and aggregate-eFuse current path, then
  verify thermal copper and trunk widening after the package-local necks;
- add unambiguous J_PWR `+5V`/`GND` and useful connector/function captions
  before layout seal, and decide whether dedicated rail/command/status probes
  materially improve bench use;
- inspect bottom ESD proximity to the USB-A THT joints in JLC's selective-
  solder/assembly preview and retain the order-preview polarity check for the
  symmetric C_TRUNK_USB body;
- before release seal, add a digest-bound local TPS259474L datasheet and make
  `pin_audit.py` resolve slash/comma-bearing manufacturer identities through
  path-safe dossier directories. Independent official-datasheet review found
  no pin defect, so this evidence-tool gap does not block routing.

The most expensive work in this stage was again evidence repair, not physical
placement: closing source-stage electrical envelopes, separating active and
retired dossier policy, making bottom-side geometry frame-explicit, and
separating presentation shadows from pixel metrology. Those lessons are now
IMP-114 through IMP-119 in `improvements.md`.

## 2026-08-16 USB-A functional-orientation reopening

The exact registered models exposed a functional placement defect that the
registration gates did not own: J_PORT1..4 were seated correctly on their
through holes but their mating mouths pointed toward increasing Y, into the
board.  Views from board centre showed all four openings; the outside-edge view
showed their rear shells.  The rejected board/r0 hashes are
`8ec5de2f491e...` / `aca7a449d4a...`; none of their placement receipts may
authorize routing.

The manufacturer/native drawing puts the mating plane 13.49 mm from the
contact-row origin in footprint local +Y.  The corrected source rotates all
four receptacles 180 degrees.  An initial y=33.5 mm origin put the plane almost
exactly on the edge but P-OUT measured only 0.02 mm courtyard margin and
rejected all four parts.  Moving the origins to y=33.7 mm recesses the plane by
approximately 0.2 mm and is expected to provide about 0.22 mm courtyard
margin.  Each complete ESD/data-switch cell and its deterministic connector-
side copper had already moved inward by 9.5 mm, preserving the reviewed local
geometry; only the final connector stubs shorten by 0.2 mm.

That mechanical correction reverses the physical lane handedness.  Rather than
cross USB traces, the electrically symmetric FSUSB42 channels now carry D+
through pins 6-to-4 and D- through 7-to-3; the hub uses normal physical
DM=D-/DP=D+ polarity with PRT_SWP2..5 low.  Eighty-two executable invariants
bind the ESD channels, both switch ends, hub pads and strap rails.  The fresh
139-part schematic passes 30/30 TSX preflight, 82/82 invariants, 139/139 source
parity and zero ERC errors, then stops on intentionally stale human reviews.

The shared fix is IMP-126: semantic `edge_faces` assertions bind mating
direction to a board edge independently of model registration.  Its known-bad
regression brings the generator suite to 56/56.  Corrected board generation,
native registration and outside/inside perspective review remain mandatory
before routing resumes.

## 2026-08-16 exact corrected USB-A evidence

The corrected placement is now realised as board SHA256
`f5be5f723e712cfb3f74797a39fbf79f78e2c7304433374f1669a2ff93f295c9`
and prepared r0 SHA256
`d006e5f09c7eaefdf304a506e275e1f95fe727d2a4e22ea8058d852f0277715a`.
J_PORT1--4 are at x=55/83/111/139 mm, y=33.7 mm, rotation 180 degrees.
Their native local +Y mating direction therefore maps to global -Y through the
north board edge; the measured mating plane is y=20.21 mm against a nominal
y=20.00 mm outline, giving the accepted 0.21 mm P-OUT margin.  Exact native
registration passes all 24 USB-A drilled centres, and the refreshed top pixel
overlay measures all four connector bodies within 0.240 mm centre error and
zero outward error.

The populated/bare 4K pairs and both A-RENDER reports were regenerated rather
than reusing pre-fix pixels; both reports now bind the corrected board hash.
Top passes 30/129 measurable bodies with all other 99 explicitly below the
resolution floor, and bottom passes 9/9.  The two directional perspective
images were also regenerated with corrected camera semantics: the north-edge
outside view shows all four mating mouths and the board-centre view shows the
rear shells.  Independent pin, layout and render reviews are SOUND.  The
exact-hash placement aggregate passes 4/4, closing this stage and authorizing
routing from the corrected r0; it does not authorize fabrication or ordering.

This correction also exposed two pipeline lessons.  Package-owned rule areas
must follow realised footprints rather than remain as stale absolute
rectangles (IMP-127), and directional render filenames need an authenticated
camera/hash manifest rather than relying on prose naming (IMP-128).

## 2026-08-18 v2 two-USB-C placement checkpoint

The two-connector architecture is now promoted into a track-free 162-part
four-layer placement. J_DATA is USB 2.0 upstream data plus VBUS detection only;
J_POWER is the physically separate 15 V PD-only inlet. Both use the exact HRO
TYPE-C-31-M-12 footprint/model, face the west edge, and have their mating planes
at exactly 0.00 mm signed offset from Edge.Cuts. The four USB-A ports retain
their already-approved north-edge orientation.

Placement generation reports 162/162 anchored parts, nine bottom-side parts,
674 copper pads, zero inter-footprint pad shorts, and zero anchored courtyard
overlaps. The board grew from 130 x 90 mm to 130 x 100 mm so the PD converter,
6 A inductor/output bank, aggregate eFuse, and retained 3.3 V buck form a
serviceable south-edge power corridor instead of being compressed into the USB
and command-control field.

Exact-footprint review caught a source discrepancy before placement: JLC's
MWSA0804S CAD used 2.10 x 5.50 mm lands at +/-3.90 mm, while Sunlord specifies
I=2.75 mm, J=4.00 mm and H=5.50 mm. The source footprint therefore uses 2.75 x
5.50 mm lands at +/-3.375 mm; only JLC's exact STEP body is retained. CH224K
and TPS56637 lands match their exact WCH/TI drawings.

P-MODEL-REG passes all three declared groups: four USB-A connectors, both
USB-C connectors, and the aggregate eFuse. P-ORIENT independently grades all
six connectors PASS. Its first visual run exposed a shared crop defect: KiCad
renders the heavily occluded reverse-camera board edge cool grey-blue rather
than olive, and a low-blue threshold rejected that physical strip. The crop
detector now admits both rendered board faces while retaining three-channel
background rejection; the exact rerun produced top/outside/inside views and
stopped at the intended explicit human-approval gate.

No routing and no firmware have been generated. After approval, routing starts
with upstream and downstream USB pairs, then the TPS56637 switching cell and
high-current power spine, followed by control nets. Every prior v1 route is
stale by construction and is not imported into v2.
