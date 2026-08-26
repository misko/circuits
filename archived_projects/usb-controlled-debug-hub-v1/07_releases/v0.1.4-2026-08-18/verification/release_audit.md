# Independent release-package audit — v0.1.2-2026-08-17

audit_date: 2026-08-17
subject: exact pre-seal design-release payload
board_sha256: c5cd719571e216224c83aca142ac84e1f11facdfb48b1bcb771c9d5b97c06e68
source_git_sha: 6a93295fbfa40cb90f80a116fc0364d8dd8de9ae
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
release_contract_verdict: READY-TO-SEAL

## Verdict

The exact routed design and self-contained archive are suitable to seal as a
first-article design release. Do not place the JLC order until the explicitly
listed order-time stackup, impedance, via-process, BOM/CPL, polarity, rotation
and THT previews are accepted. Production remains held until physical
first-article qualification. No firmware was generated or included.

## Exact identity and payload

- Both staged PCB copies and the live project PCB are byte-identical at the
  board hash above. The source scope was clean at the stated git commit.
- The exact standalone nested and root KiCad source copies pass DRC with zero
  violations, zero unconnected items and zero schematic-parity findings.
- The fabrication upload contains exactly 13 Gerber/drill members. BOM has 33
  data rows and 138 expanded designators. CPL has 138 unique placements: 129
  top and 9 bottom. `F_IN` is the sole real manually assembled footprint.
- Native model and exact-twin coverage are 139/139, including the manual fuse
  holder. The archive retains source, schematic/layer/assembly PDFs, loose fab
  files, Gerber ZIP, BOM/CPL, 3D exports, exact renders and machine evidence.

## Re-graded design gates

- ERC has zero errors; all 840 warnings are retained rather than suppressed.
  Netlist/board parity, 82/82 electrical invariants, placement, pad separation,
  10/10 critical routes and the full policy audit pass with zero blocking
  findings.
- Strict realized-copper length passes 6/6 groups and 12/12 members. The
  machine artifact is strict JSON. Reference-plane projected-obstacle checks
  pass 2/2; this is geometric evidence, not a field solve.
- Via-process evidence covers all 526 vias: 498 protected 0.46/0.20 mm
  Type-VII fill/cap barrels and 28 ordinary 0.70/0.35 mm barrels. All 87
  via-in-pad sites are enumerated.
- Independent topology, pin, layout and render reviews report SOUND with no P0
  or P1 design finding. Exact JLC/EasyEDA C503996 symbol/footprint evidence
  resolves the Kinghelm USB-A contact-number ambiguity without a board edit.
- Connector geometry passes 5/5. The user/product owner approved exact subject
  `8a7f766c33855e7c9b325d1f792f928b0fd38197eb61d7f13969415eaea65f97`
  on 2026-08-17; `orientation_approval.md` binds the decision and invalidation
  rule.
- Stock evidence reports 33/33 coded BOM lines available for five boards on
  2026-08-17. This is catalog evidence, not a reservation or assembly
  allocation.

## Retained limitations and dispositions

- Three intentional low-speed In1.Cu signal segments total 9.3024 mm and do
  not cross a USB corridor. The exact waiver is retained; a broad plane waiver
  is not used.
- Four external 0.5 A switched branches and the 0.1 A control branch use
  bounded wide tracks/package necks rather than local pours. The common 3 A
  input path is poured. First-article four-wire drop and hot thermal validation
  remain mandatory.
- Strict part-facts reach is 25/27 because the exact manual fuse and holder do
  not travel through the JLC BOM/LCSC chain. Their procurement, installation
  and continuity checks are explicit in the order and first-article documents.
- The top F.Fab assembly page is visually dense; the exact twin, silk, CPL and
  side-specific renders are the operational placement references.

## Order-time holds

1. Select JLC04161H-7628, nominal 1.6 mm, ENIG, and obtain/accept JLC's final
   90-ohm differential solve for the declared trace geometry. Any changed
   construction or geometry reopens engineering review.
2. Obtain explicit selective Type-VII paste-fill/copper-cap acknowledgement
   for the complete 0.46/0.20 mm family only; do not fill the 0.70/0.35 mm
   ordinary family.
3. Verify the resolved BOM echo, 129-top/9-bottom CPL count, every listed
   rotation, `C_TRUNK_USB` polarity, and all six THT side/mapping previews.
4. Refresh real JLC stock/allocation immediately before payment. Any redirect,
   substitution, DNP, side, rotation, polarity or placement mismatch is STOP.

## First-article hold

`first_article.yaml` covers the exact 139-part installed set and names the six
exposed-pad packages, unpowered resistance probes, supply limits and rail
measurements. `FIRST_ARTICLE_TEST_PLAN.md` governs inspection, current-limited
power-up, hardware-safe-state truth table, enumeration/cycling, simultaneous
four-port load, fault coordination, waveform, thermal and USB 2.0 traffic/eye
work. The machine check correctly remains INCOMPLETE until physical evidence
is written; this blocks first power and production, not the design-release
seal.
