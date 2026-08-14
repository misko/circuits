review_kind: render_review
subject: Pluto RX2 8-Way v5 final exact J11-role rebind 4cf5c818
date: 2026-08-13
reviewer: Codex fresh independent final render/mechanical/copper reviewer
independence: independent-from-design-author
context-given: exact final source commit, native 3D models, fresh copper plots, J11 dossier, exact assembly contract and current manufacturer evidence
source_commit: 4cf5c818684e4c39f594b50a567fb086b9cf6f13
board_sha256: 39251c24d4b3cc878824f26c48178cbc4a4d418fa528045c6c13f2308e017acd
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
p0_design_findings: 0
p1_design_findings: 0
p2_design_findings: 0

# Final fresh physical and render rebind

## Verdict and exact boundary

The exact source/board pair above is **SOUND** through render, physical-fit,
orientation, mating-access, mounting, copper-presentation and assembly-
visibility review. P0/P1/P2 design findings: **0/0/0**. All views and copper
plots were regenerated after commit `4cf5c818` with KiCad 10.0.4 and reopened
at original resolution; this verdict was not copied from an earlier review.

The order verdict is **DO-NOT-ORDER**. The design may advance into release and
fabrication-package work, but no review of a candidate board can substitute
for the actual JLC uploader, sealed output or first-article evidence.

## Fresh render and copper evidence

| Evidence | SHA-256 / result |
|---|---|
| top render | `17a1538d9c5bba44391cc2b3098531a876b0b7c9648098598915245e8f75abe0` |
| isometric render | `97706f7d92461e05828ec32a8000a2f8b1efd56e0d67922fcf8e0b34666f5bbd` |
| front render | `89f26c3934e94e8ac4d821fd75457a3224caa5adf537abd81f7c67c36fe3cb70` |
| right render | `fc1ac233de928c496e695ec94ac2582bacde888a44c2b4489756c4726a32c380` |
| bottom render | `e534bd87583c67d65a136031217ecd012284f4352af3d0b6e0efe633b9fc90be` |
| F.Cu / B.Cu raster plots | `9c9125d0556d313f4ba66fba01e539646b1162d87361929a52f8a52ed048a008` / `1790f73030df31d7679a230635483bdbb69ccb695b6f04e6642158612b54f710` |
| In1.Cu / In2.Cu raster plots | `1b60f1cb287093fcaa61a487b00d1dbe7ffbbe1af90b89afd7211d0aa8c618d8` / `1b60f1cb287093fcaa61a487b00d1dbe7ffbbe1af90b89afd7211d0aa8c618d8` |
| fitted-model coverage | 29/29 renderer-resolvable bodies; zero missing |
| exact-board DRC | 0 violations / 0 unconnected / 0 schematic-parity discrepancies |

## Population, access and J11 role

- All 29 fitted bodies are seated on their intended top-side lands. U1/U2
  pin-one cues and D1 polarity align with their footprint marks; no body is
  reversed, shifted, floating, on the wrong side or colliding.
- Five north-edge and two-per-side SMA connectors face outward with practical
  mating and coupling-nut access. Their manufacturer-pattern legs align with
  all plated holes. Normal THT tails below the board require ordinary trimming
  and standoff/enclosure clearance.
- J1 has a clear south-edge USB-C insertion path. J11 is visibly a board-side
  keyed vertical male Cortex-SWD header with accessible pins, keying feature
  and cable approach. The corrected dossier role `mates: plug` agrees with
  that physical construction; the note correctly names the mating cable side
  as a keyed 1.27 mm FFSD-family receptacle.
- All four 3.2 mm mounting holes and three top fiducials remain unobstructed.
  `PLUTO RX`, `ANT1`-`ANT8`, `100MHz-5.9GHz`, `USB-C POWER ONLY`, and
  `KEYED SWD J11` remain readable and correctly associated.

## Copper, fence and process geometry

- Fresh F.Cu inspection shows nine continuous, via-free 0.295 mm RF arms with
  no crossover or unintended branch. B.Cu contains only short low-speed
  fragments. In1.Cu and In2.Cu remain continuous GND reference planes with no
  signal route or split beneath the RF fanout.
- All 18 route-local RF fence flanks pass, with 1.3979 mm worst aperture versus
  1.4000 mm. The fence does not obstruct a connector or hide an operational
  marking.
- J11.3 remains free of the rejected ordinary via-in-pad. The only via-in-pad
  construction is U1's intended nine-site protected field. Fresh grading finds
  nine filled/capped 0.45/0.25 mm sites and 629 ordinary untreated
  0.45/0.20 mm vias.

## Source and assembly checks

The J11 schema correction is source-only and causes no board/model transform,
land, outline or cable-envelope change. Fresh P-ESC grades all 13/13 part
dossiers with zero problem. The board-side plug versus cable-receptacle
relationship is now both schema-valid and explicit to a human reader.

The machine-readable J2-J10 bought-THT declaration also remains effective. A
fresh 29-placement candidate plus the generated empty population manifest
passes A-POP with all datums graded and 0.00050 mm worst error. Exact C429844
still requires the real uploader's wave/manual-assembly echo; refusal stops
this release and requires a separately generated hand-solder CPL.

No physical-fit, orientation, mating-role, connector-access, mounting, model,
silk, RF-fence or rendered-copper defect was found.
