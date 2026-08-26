# Pre-route schematic readability review — USB Controlled Debug Hub v2

review_stage: pre-route
review_kind: schematic_render
design_verdict: SOUND
order_verdict: BLOCKED-SOURCING
schematic_pdf_sha256: 692e90e849111244066af76ca7af15222b459a58fed71263ca73217db7152e29
netlist_sha256: e5999cc54248976423e736eab7e72b4fcb04b68170b4b8ad3903ba4a2af3ea59
parts_sha256: d089da4ca84240ff3077e02bdc909dcb3e9d23a41b4967a3f785297b722e626a
design_rules_sha256: be908d898837e6c1d23774e5f97d0f29b5829a160e13bc45da40d42c103a2e82
circuit_sha256: e4a1bbc31c38d0a517834234fd2b190af1af34699b76841324892be2e485bd14
reviewed_at: 2026-08-19T14:48:00-07:00

## Readability result

The exact ten-page vector PDF was inspected page by page using fresh 110 dpi
rasters and a separate 220 dpi inspection of the broad USB-C POWER page.

- Page one reads left-to-right from POWER USB-C through fuse/TVS, CH224K,
  negotiated-voltage eFuse and TPS56637 regulation. Exact TVS1800, 1 uF exposed
  capacitance, 73.2 kOhm + 374 Ohm / 10 kOhm feedback and 3.3 nF input dV/dt
  values are present without clipped bodies or conductor-obscuring labels.
- Page one is intentionally broad and needs ordinary vector-PDF zoom for
  reference/value inspection. Signal flow and support networks remain spatially
  separated; this is a usability limitation, not hidden or overlapping content.
- Page two clearly shows the 26-pin TPS259804 identity, split IN/GND PowerPAD
  nets, 300 Ohm ILIM, 6.8 nF ITIMER and 3.3 nF dV/dt network. USB bulk and the
  3.3 V converter remain separate from the aggregate support components.
- Pages three through six isolate the hub, straps, management and hardware
  interlocks. Intentional NC notes remain explicit and no new occlusion was
  observed.
- Pages seven through ten are consistent one-channel external-port sheets.
  Each visibly carries 3.32 kOhm ILIM, open ITIMER/DVDT intent, FLT-to-OCS,
  true-reverse-blocking VBUS, hardware data-disable and connector polarity.
- No stale 5.90 kOhm port setting, TPS259474 aggregate, 750 Ohm aggregate
  programmer, 75 kOhm feedback, 30 mV dynamic allocation or SMF16A identity
  remains in the exact PDF.

The generated schematic has zero ERC errors. Advisory warnings associated with
synthesized symbols remain baselined and do not alter this readability verdict.
The rasters are retained under `06_build/pre_route/schematic_render_current/`
as review evidence; the PDF remains the authoritative zoomable artifact.

The exact ten-page PDF was regenerated and reinspected at the sourcing-resume
boundary. Page count, functional partitioning, component counts and the
readability conclusions above remain unchanged; only the exact artifact hashes
were refreshed.
