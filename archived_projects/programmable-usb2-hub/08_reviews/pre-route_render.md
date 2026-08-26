subject: programmable-usb2-hub exact placed board a03a05e83f32
date: 2026-08-02
reviewer: fresh independent render-review agent (GPT-5, same-camera mechanical/polarity lens)
context-given: exact placed board, hash-current populated/bare/overlay evidence, twin report, assembly/twin adjudication registers, and exact connector/diode geometry as needed; prior review verdicts excluded as authority
source_commit: 809b38af6bc085de5c9b1e6d045e8fade359240c (dirty working tree; artifact hashes below are authoritative)
review_stage: pre-route
review_kind: render
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
board_sha256: a03a05e83f32df6a6104a24dea888683618e7b5fe40e6b70904f6959b98f63ed
design_rules_sha256: d732d22b90dbae6f31d9099d2c789ab06df32d96e2c43e207232c55faa24100e
twin_top_sha256: ae2f060af49a57573944b70e82855b49e896aa1a1616211469f8cdfbf425d4af
twin_bare_top_sha256: 70e77db846ddfb4ca146a476c6312dbf1053b13b39231ca892a14f56782cd641
twin_top_courtyard_overlay_sha256: 9da9f9c5146164dc1afe87fce1217682385684270514618dae8e3f1d5fac1597
twin_report_sha256: eb33a63b29dcc455db527df5e824db3233e57cfcfe85f437d8368ff29822fd39
twin_overlay_report_sha256: d5824ee3b1685cbf9f400bda7d65a702bf30b8b7dd820d4caf0a159bc6ec738e
missing_models_sha256: 9a22d2d271188500c15859704c1ffe6a9e0959c971d8d5821a7301f151f9ed31
twin_adjudications_sha256: 08cb3549b2a4baa23a1d1e81735cc83c62f6ab9a41c13e94ac5c6e2366a4e388
assembly_sha256: 4aaca983f237e564cb15532d305e4da64f41112f49fdcbf7408841d0816fdee5
bom_sha256: 72111f4302b4d5c78a8b08e1ed9dd09fd10c4ddebb57916b41f9643cbc968b1a
cpl_sha256: 325bb4b8f212c1d551d1039a1ac8c30b70e31b5de35ccfa0e27841a154d3bb91

# Independent pre-route render review

## Verdict

No P0 or P1 render, body-registration, connector-access, polarity, or
wrong-artifact finding remains on the exact board and evidence bytes above.
The placed design is **SOUND to proceed to routing** under this lens.

This is not an order authorization. There is no routed copper, filled-zone or
DRC/parity proof, and the first-order JLC preview checks named below have not
occurred. Consequently `order_verdict` remains `DO-NOT-ORDER`.

- P0 findings: none.
- P1 findings: none.
- P2 findings: none.
- A-RENDER: **PASS**, board hash current, orthographic calibration valid.
- Body-file coverage: **211/211** intended placements resolve a nonempty 3D
  body (206 CPL placements plus five declared manual-install bodies).
- Pixel coverage: **51/196** refs with expected bodies measured; 145 are
  named as unresolvable by construction, zero resolvable refs were missed,
  and no measured body exceeded the 1.00 mm centre/outward tolerance.

## Same-camera faithfulness and body placement

The populated and bare top images are the same 1536 x 1024 orthographic
camera. Their subtraction calibrated at 7.4174 px/mm in X and 7.4251 px/mm in
Y (anisotropy 0.9990). The overlay reports all 218 footprints with a
courtyard and places the board edge at x=19.950..150.050 mm and
y=19.950..110.050 mm, matching the exact board's 130.1 x 90.1 mm edge box.
The reviewed board has 218 footprints, zero tracks/vias, and three unfilled
GND zones, so no routed-board behavior is inferred here.

The largest measured centre delta is 0.740 mm (U13), within the 1.00 mm gate.
J1 measures 0.193 mm centre delta and 0.067 mm outward delta; its slight
0.225 mm model-to-courtyard excursion is visible and does not approach another
body or foreign pad. J2 and J7 show the expected asymmetric connector/header
body excursions, while populated-minus-bare pixels agree with the declared
mounts at 0.180/0.296 mm and 0.133/0.083 mm centre/outward delta respectively.
Their leads/hole fields register to the fabricated lands. No obvious
body-to-body collision, body-to-pad overlap, floating body, duplicated model,
or foreign-board artifact appears in the top, isometric, or edge views.

R3's EasyEDA C2078999 fetch remains unavailable, but this does not leave the
render body absent: the exact board's standard 0603 resistor STEP resolves in
the twin, the generated body-file manifest remains 211/211, and the installed
body sits on the R3 lands without a visible collision. The exact Vishay body
and land-envelope evidence is recorded in the current adjudication register.
Because the JLC-specific CAD could not be independently compared, R3 remains
on the mandatory first-order order-preview list; it is not silently credited
as a catalog-twin match.

## Connector orientation and access

- **J1, Phoenix Contact 1935161:** the corrected green two-position body is
  present, not the prior Kangnex/generic terminal-block artifact. The exact
  board uses `Phoenix_1935161_PT_1p5_2_5p0_H` at (25.5,97.0) mm, rotation 90,
  with 5.00 mm pin pitch and the local C3819953 model. The wire-entry face is
  west/outward, both top screws are unobstructed, and the body retains visible
  clearance to F1 and the board edge. The twin pad fit is 0.00 mm and the
  render contains no displaced or doubled terminal body.
- **J2, upstream USB-B:** the receptacle mouth faces west/outward. Its two
  signal/power rows and shell stakes align with the six board holes; the large
  courtyard excursion is the intentional right-angle shell overhang, not a
  centre-registration error. The mating face and cable approach are clear.
- **J3-J6, downstream USB-A:** all four exact GCT dimensional envelopes are
  present with their mouths facing north/outward. They are evenly spaced,
  separately labelled PORT 1-4 / 5V / 2A, and neither their shells nor their
  cable approaches intersect adjacent bodies. These are the declared
  manual-install envelope models, so the render proves access/orientation but
  does not claim a JLC catalog identity.
- **J7, keyed SWD header:** the 2x5 pin field is fully on-board and accessible
  from above. The declared display-model nudge removes the JLC model's own
  internal pad-origin error; the board holes themselves fit at 0.00 mm. Pin-1
  and keying still require the named first-order preview check before buying.

## Polarity review

D1, D2, and D3 each report `POLARITY-FIT-OK`: the geometry-only marking
channel and pad-number fit agree at pad 1. The human render agrees. D2's body
band is on its west/pad-1 `BOOST_A` end and the matching footprint bracket is
west. D3 is intentionally rotated 180 degrees: its body band and footprint
bracket are both east at pad 1 `BOOST_B`. The adjacent D2/D3 parts therefore
look opposite because their physical cathodes are opposite; this is expected,
not an accidental model flip or overlapping pad field. D1's marked end also
agrees with its pad-1 cathode orientation.

D4-D7 have no usable numbering-free mark in the JLC footprint/model and are
correctly reported `POLARITY-FIT-BLIND`, never auto-passed. Their board pad 1
is the port-VBUS cathode and pad 2 is GND, and the four instances are visually
consistent. The mandatory JLC order-preview polarity check remains the final
independent control for those four bodies.

## Prior wrong-artifact classes re-tested

The render is recognizably the programmable USB2 hub: one west-edge 12-24 V
input, one west-edge USB host, four north-edge USB-A ports, two LTC3889 power
stages, one auxiliary regulator, and the labelled controller/hub core. It does
not contain an RP2040 module, SMA connector set, or the pad-overlap/wrong-board
geometry seen in the previously questioned screenshot. Component bodies sit
on their own fabricated lands; the yellow areas under Q1-Q6 and U2 are their
exposed copper pads, not overlapping resistor footprints.

The prior missing-body blockers are closed: J3-J6 now have exact mechanical
envelopes, F1 uses the complete Keystone 3568 local body rather than the
rejected loose-clip catalog near-match, and U9-U12 are populated in the twin.
The corrected Phoenix J1 is also present and registered. No fresh render-side
placement defect is found.

## Downstream human gates retained

Before an order, the JLC preview must still confirm D4-D7 polarity, J7 pin 1
and key, R3 registration, and the measured per-LCSC rotations for Q7/Q8/U3.
Those are explicit order-stage controls and are why this pre-route review does
not claim `ORDER`; they do not make the exact placed-board render defective.

## Post-review process-order rebind

After the physical review, `03_src/route.yaml` inserted `fresh_reload`
immediately after the second/final `fill` and before
`unify_zone_priorities`/`heal_islands`. The one-line pass-order delta changes
the adopted rules digest, so this review is rebound above to
`41fbbdfa4c9871aa1dbe0e2a057ad28fd3b5fd2758d3007974a1755f544c23e4`.
The exact board, populated render, same-camera bare render, courtyard overlay,
twin report, and A-RENDER report remain byte-identical to the hashes recorded
in the header. This is a downstream route/stitch execution-order correction;
it changes no footprint, placement, pad, body, camera, or polarity evidence,
so the physical findings and `design_verdict: SOUND` are unchanged.

A final route-contract preflight correction then removed the nonexistent
`FB_B` net from `final_recover` and assigned all six current SWITCH_POWER nets
(`SW_A`, `SW_B`, `SENSE_A`, `SENSE_B`, `AUX_SW`, and `SW_3V3`) to the
existing F.Cu-only switch wave at 1.0 mm. Those edits change only router group
membership and width policy; no board or render artifact changed. The final
aggregate rules digest is therefore rebound above to
`d732d22b90dbae6f31d9099d2c789ab06df32d96e2c43e207232c55faa24100e`,
with every physical finding and verdict unchanged.
