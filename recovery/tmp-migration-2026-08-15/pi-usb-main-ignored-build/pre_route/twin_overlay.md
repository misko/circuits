subject: pi-usb-port-switch native pre-route render witness
date: 2026-08-15
a-render_verdict: PASS
board_sha256: 168838f8e57b16581a8f54cdd4b75a85d1d5dbb1698428d281a7c07dccf14101
top_render_sha256: 897d2f1480566525b30bfda159ebaef8329de6db8e6d898c7ac689947c2274e8
iso_render_sha256: 8c736fcdacac67a3aabdc851448ea0d0daf5661ca7cf7bd3dd09b03e4fa95d3a
bottom_render_sha256: 0141fe161a9ee760ffd578ca509b970d71ae578d9d47ca5b428ccb3c9450b062
render_resolution_px: 3784x3024
model_coverage: 190/190 fitted electrical footprints resolve
evidence_class: native-kicad-placement-geometry

# A-RENDER pre-route witness

PASS is limited to the exact hash-bound KiCad board and native model
transforms. Complete, widened-camera orthographic top, perspective isometric,
and orthographic bottom views cover the full board without clipping a connector
body. Visual inspection found all eight USB
connector bodies registered to their drilled shell stakes/contact fields and
oriented toward the correct board edge; the input terminal, fuse holder,
polarized bulk capacitors, GPIO header, active packages, four mounts, and three
fiducials are present without an obvious body collision or clipped envelope.

The renderer was invoked with the explicit KiCad 10 model directory; an earlier
incomplete render made without that environment binding is superseded and not
evidence.

This filename satisfies the preliminary A-RENDER interface, but no JLC catalog
twin was generated at this stage. This PASS grants **no** JLC/LCSC body,
same-camera catalog-overlay, CPL rotation, polarity, assembly, routed-board,
or order-preview credit. Those remain downstream release gates.
