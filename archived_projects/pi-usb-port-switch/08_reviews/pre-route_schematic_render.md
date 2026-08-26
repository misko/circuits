# Pre-route schematic-render review — Pi USB port switch

review_stage: pre-route
review_kind: schematic_render
design_verdict: SOUND
schematic_pdf_sha256: 3adbeebd84a328d9d9d0454748763289b21427e6711e5e58bfd09b05f1cdbe8f
netlist_sha256: 529988394f74bcb6a8f292e0a16d610ff8140f240ce9c0122af9966d4a1e0992
parts_sha256: 9f07c5382cde77e74e0f5f0c7c8396b62a9678f2a1e090422b2ac5f3d0379683
design_rules_sha256: 8bd0fe7492a4ae67bf266d9840e25c14eee8f1bda228593f36cebd87fcf97b71

## Artifact and coverage

The exact regenerated 27-page PDF named above was rasterized on 2026-08-15 and
every page was visually inspected as a 3-by-9 contact sheet, with pages 1--9,
22, and 27 additionally inspected at full resolution. Its 190 components agree
with the manifest/circuit/KiCad/netlist
parity checks, so the visual review is not being used to excuse omitted
electrical content.

Pages 1--3 cover the protected 5 V input, Raspberry Pi GPIO header, and six
independent TUSB522 strap pulldowns.  Pages 4--9 then establish the six-sheet
channel pattern: upstream connector/ESD, upstream SuperSpeed series and AC
paths, redriver core/straps, downstream connector/ESD, downstream SuperSpeed
series and AC paths, and power/USB 2/hardware interlock.  Pages 10--27 repeat
that complete pattern for channels 2--4.

## Readability findings

- Connector pin numbers, ESD pins, lane direction names, series resistors, AC
  capacitors, redriver pins, power-switch pins, and interlock signals are
  visible and traceable at normal review zoom.
- All eight regenerated connector/ESD pages (4, 7, 10, 13, 16, 19, 22, and
  25) were re-inspected after adopting TI's straight-through land usage. The
  protected I/O pins and opposite NC land pin numbers are visible, and each
  opposite pair carries the same exact USB net label. RX, USB2, and TX remain
  individually traceable to their connector pins. The repeated four-channel
  presentation is consistent; no label overlap conceals a lane, polarity, or
  the new same-net flow-through assignment.
- The four SuperSpeed lanes are separated into one horizontal chain per row;
  P/N identity and upstream/downstream direction are not hidden by bus graphics.
- Redriver supply/strap pins, RX2 bias resistors, and ground pins are exposed
  rather than collapsed into an opaque symbol presentation.
- Each channel's power/USB 2/interlock page shows the AND gate, selector pull,
  FET-controlled OE, current limiter, output bulk/decoupling, and fault pullup
  together, which makes the no-data-without-power behavior reviewable.
- The input page has modest label density, but every connection remains
  distinguishable.  No crossing, clipping, or overlapping annotation was found
  that changes or conceals the interpreted circuit.
- The regenerated USB 2 upstream N/P pins are now visibly separated on all four
  TS3USB221 pages. The machine geometry audit independently graded all 1,461
  drawable objects, finding zero text occlusions and zero apparent joined-net
  conductors; the visual pass confirmed the repeated pages remain consistent.
- The 2026-08-15 supplier-only update binding upstream connectors to exact JLC
  C5334230 changed no symbol, wire, label, page allocation, or rendered
  electrical content. The regenerated 27-page artifact was nevertheless
  re-rasterized and re-inspected rather than inheriting the earlier visual hash.

## Verdict boundary

The schematic is readable enough to serve as the human design document and is
approved for physical floorplanning.  This review does not approve footprint
geometry, placement, routing, impedance, assembly rotations, 3D registration,
fabrication, or the refined physical-placement allocations subsequently bound
through the current part-dossier hash; those remain explicit downstream gates.
