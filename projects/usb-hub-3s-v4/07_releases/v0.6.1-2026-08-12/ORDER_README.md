# USB Hub 3S v4 — design archive and JLC order work order

Release v0.6.1 is a docs-only successor to v0.6.0. It corrects the canonical
project identity in three independent publication-review headers. The
fabrication, source and 3D trees are byte-identical to v0.6.0; no design,
copper, BOM, CPL or 3D geometry changed.

## STOP — DO NOT ORDER THIS ARCHIVE AS-IS

SOURCING: CLEAR
ORDER VERDICT: DO-NOT-ORDER
DESIGN VERDICT: SOUND

The local design and manufacturing-package gates pass, but the non-local JLC
upload preview, item-specific Type-VII acknowledgement, and first-article
acceptance have not been completed. This archive is intentionally sealed as an
inspectable design record; it is not evidence that an order has been placed or
accepted by JLCPCB.

Product boundary: protected 3S LiPo input; three charge-only USB-A outputs at
5 V / 2 A continuous each; one fixed-5-V Type-C source at 3 A for a Raspberry
Pi 4. There is no upstream USB, no USB data path, no USB-PD negotiation and no
active sustained-overvoltage/fail-high cutoff. Supervised use only.

PCB: 130 x 90 mm, 4 layers, 1.2 mm nominal, JLC advanced process.
Assembly: top-side SMT, quantity 5, 40 BOM lines, 70 CPL placements.
Not assembled by JLC: F1, J1, J2, J3, J4, SW1.
3D evidence: all 70/70 CPL bodies modeled; manual bodies 1/5, with J1-J4 exact
models absent and mechanical checks carried into the first-article plan.

Before any order is released, complete sections 1–3 below and have the order
verdict reviewed again. Do not infer uploader acceptance from catalog stock.

## 1. PCB order options

- Fabricator: JLCPCB; four copper layers; 1.2 mm finished thickness; standard
  green solder mask and white legend unless procurement records an equivalent
  controlled choice.
- Select the advanced process required by the board. Apply copper-paste fill
  and copper cap only to the complete 0.20 mm drill family: the explicitly
  protected 0.50/0.20 mm thermal vias. Ordinary 0.60/0.30 and 0.70/0.30 mm
  route/stitch/plane vias must not be filled or capped.
- Paste this exact fabrication remark into the order and obtain acknowledgement:

  > Copper-paste fill and copper cap only the 0.50/0.20 mm vias explicitly
  > marked Type VII in the KiCad board. This is the complete 0.20 mm drill
  > family. Do not fill/cap any 0.30 mm drill routing, seed, stitching, or
  > plane-transfer via (0.60/0.30 and 0.70/0.30 mm finished geometry).

- Upload `fab/usb_hub_3s_v4_gerbers.zip`. Confirm layer mapping, outline,
  plated/non-plated drills, copper-filled regions and no unexpected DFM edits.
- No impedance-controlled or RF option is required. Advanced processing is
  selected only because the integrated power modules require protected
  via-in-pad construction; it is not a blanket small-feature escalation.

## 2. Assembly upload and human preview gate

- Upload `fab/bom.csv` and `fab/cpl.csv` for top-side SMT assembly, quantity 5.
  JLC must resolve exactly 40 BOM lines and 70 placed designators.
- Save JLC's own resolved/matched BOM table. Compare every code/value/ref group
  with `verification/bom_echo_gate.txt`; any redirect, substitution, no-part,
  shortage or quantity mismatch stops the order.
- Compare every placement with the real JLC preview. Explicitly inspect C22 and
  C23 polarity, D1/D2-D6 cathodes, Q1 orientation, every IC pin 1, connector
  J5, and all transform-sensitive packages. Local rotation evidence is 70/70,
  but only JLC's preview shows how its current uploader interprets the files.
- Re-run same-day stock/allocation for quantity five. The sealed catalog check
  is 40/40 and `SOURCING: CLEAR`; it is necessary evidence, not a guarantee of
  assembly allocation.
- Confirm F1, J1, J2-J4 and SW1 are absent from the CPL and will not be fitted
  by JLC. Do not accept automatic replacement with a nearby catalog footprint.

## 3. Manual assembly and first article

- Hand-solder the exact Keystone 3568 fuse holder, Phoenix Contact 1715022
  terminal, three GCT USB1130-15-A receptacles and E-Switch EG1218. User-fit
  the specified Littelfuse 0297010.WXNV 10 A MINI blade fuse after inspection.
- Follow `verification/FIRST_ARTICLE_TEST_PLAN.md` in full. Its controlled map
  identifies TP1–TP12; TP3–TP12 do not carry full net-name captions on this
  prototype, so print that table at the bench and verify each refdes before
  probing.
- Required acceptance includes unpowered shorts/polarity, current-limited
  first power, OFF-state shutdown, reverse-input behavior, per-port and
  simultaneous load, attach/detach/backfeed/fault recovery, startup/load-step/
  ripple stability, full-path hot four-wire resistance and enclosure thermal
  equilibrium.
- The exact Type-C cable/Pi path must measure no more than 39 mOhm hot at 3 A.
  Retain waveforms, temperatures, four-wire data, photographs, serial number,
  ambient and instrument IDs. A failed result reopens the design.

## 4. Integrity and recovery

`MANIFEST.txt` hashes every file except itself and names the exact source
commit. `source/` contains the routed KiCad board/schematic/project/rules,
authoring TSX, exported netlist, `fp-lib-table`, and vendored footprint
libraries. `pdf/` and `verification/` make the archive inspectable without
re-running a network stage. The STEP file is a board-only mechanical envelope;
use the twin renders and exact connector datasheets for installed-body review.
