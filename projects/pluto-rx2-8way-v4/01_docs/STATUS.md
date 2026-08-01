# Status

- Stage: layout complete; fabrication candidate prepared; release unsealed.
- Board identity: `pluto_rx2_8way_v4`.
- Architecture: PE42482A-X radial RF star plus Waveshare RP2040-Zero module.
- Fab target: `jlc_4layer_advanced`, controlled impedance.
- Assembly posture: carrier assembled by JLC; RP2040-Zero user-fitted; SMA
  plug-in process must be confirmed at order time.
- Routing: promoted three-candidate winner; every candidate was clean before
  stitching. Deterministic rebuild and final DRC are 0/0/0.
- Verification: P-MOD 1/1, TSX-PRE 6/6, S-COUNT 28/28 across artifacts,
  E-INV 20/20, P-LAND 0 failures, policy audit 0 failures, and R-LEN pass with
  0.1657 mm realized eight-arm spread and no RF vias.
- Handoff note: contract-only source normalization exposed nondeterministic
  stitching-via UUID/order churn on a reseal attempt. The reviewed board was
  retained and independently rechecked at DRC 0/0/0, P-LAND zero failures, and
  P-MOD 1/1; the broad source-tree handoff hash remains intentionally stale
  until a future reviewed seal regenerates board and candidate together.
- Firmware: host-tested RX2CTL/1 scaffold complete (native C core plus 7 host
  tests); Pico SDK 2.1.1 + Arm GNU 13.3.Rel1 target cross-build passes for
  `waveshare_rp2040_zero`. Flashing and USB hardware exercise remain physical
  bring-up work.
- Fabrication candidate: Gerber/drill/BOM/CPL/PDF/STEP set generated in
  `06_build/fab` without exporter escape hatches. A-POP passes,
  BOM source/legibility pass, live stock passes 11/11, and the twin mounts
  27/27 CPL bodies. U_MCU is absent from BOM/CPL/paste as required.
- Candidate policy regrade: 28 PASS, 6 HUMAN, 11 N-A, and one expected pre-seal
  A-POP `MANIFEST-UNDECLARED` failure against the project root. The direct
  candidate gate passes against `06_build/fab/MANIFEST.txt`; the aggregate
  failure closes only when a real release manifest is generated at seal time.
- Current blockers: no layout or source blocker. Fresh independent pin,
  topology/protection, layout/thermal, and render reviews plus dispositions and
  M-REV remain before sealing. Order-time JLC through-hole acceptance,
  PE42482/LED preview, target hardware exercise, and measured RF
  characterization also remain.
- Release: no.
