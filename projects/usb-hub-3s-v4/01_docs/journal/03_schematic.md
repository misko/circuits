# Schematic journal

## 2026-08-11 08:00 — start

- did: Entered Stage 2 after D3 accepted JLC four-layer advanced with resin-filled/copper-capped via-in-pad for the already selected module architecture.
- result: MEASURED from the tree: ADR-0004 is accepted; the Stage 1 checkpoint is `f630b9c0`; `03_tscircuit/` contains zero schematic source/generated artifacts, so no pre-decision schematic work can be mistaken for current evidence.
- next: Derive the exact support BOM and pin/net topology from the selected datasheets, author TSX plus its declared manifest, and run preflight before the first build.

## 2026-08-11 08:34 — complete and paused

- did: Authored the 76-component power-only TSX, exact JLC codes, manifest, pad/rail maps, one new exact Panasonic capacitor dossier, complete electrical invariants, and both human/KiCad schematic audiences. Re-derived the TI module, TPS25810 and TPS2557 support circuits from the exact vendored datasheets; compared the Type-C, Pi and via-in-pad boundaries against current official primary material; and wrote the exact-hash pre-route topology review.
- result: MEASURED final run `2afa66dd752e` passed P-MOD 4/4, RF applicability 1/1, TSX-PRE 17/17, TSX-DIAG 0 embedded errors, M-FRESH 9/9, 76/76 components and 270 pins, label survival 39/39 plus pin map 43/43, E-INV 53/53, E-ADR 1/1, EARLY-DESIGN 3/3, E-TOPO 4/4, E-MARGIN 8/8 reported assertions, E-OFF, S-COUNT 76/76, coded-value BOM, and ERC 0 errors. PR-REVIEW passes 1/1 with normalized netlist `a05e2e137168...`, parts `489acc5734a...`, rules `6ad7729dc81e...`, verdict SOUND / DO-NOT-ORDER. The full ERC baseline contains 562 nonblocking generated-render/library warnings and the TSX artifact contains 367 advisory diagnostics; both distributions are named in the review rather than hidden.
- spent: MEASURED wall clock 34 minutes from the 08:00 stage marker. Five driver attempts were informative: a 0.5-second module-contract stop; a roughly 25-second post-build label-map schema stop; a first exact-review stop; a rerun after removing a real D6 proxy-pad clearance error; and the final zero-error diagnostic run. Datasheet/application re-derivation and exact JLC passive matching dominated authoring time; each TSX build/render was roughly 25 seconds.
- friction: The integration schema initially treated a simple TPS2557 as a complex exception; label-survival rejected rows containing only no-connect assertions; `tsci build` returned zero despite printing “completed with errors” for the first D6 proxy footprint; `route.yaml` still said `standard` after ADR-0004 selected advanced; and one TPS2557 dossier sentence still named the superseded 39.4k value. The hash review caught the last two before placement.
- generalized: Freshness, parity and ERC can all be correct while the foreign producer has rejected its own geometry. Added shared `circuit_json_diagnostics.py`, wired it into all TSX entry points and the canonical rebuild template, documented the boundary in both PCB skills/contracts, and added clean/known-bad coverage; the template suite is 40/40 and the checker unit suite is 3/3. Future projects now stop on embedded `*_error` records even when `tsci` exits zero.
- instruction-change candidate: Run rule/config schema lint before the expensive TSX build, not after netlist export; the label-map schema failure spent a full generation cycle without needing circuit bytes. Also add an explicit human-render readability lens: this one-page auto-layout is electrically coherent and zoom-readable but less conventional than a sectioned left-to-right schematic, a distinction no connectivity gate measures.
- next: PAUSE. On user continuation, begin Stage 3 placement from the exact reviewed netlist. Preserve JLC advanced processing, manufacturer module example geometry, filled/capped thermal-via fields, a continuous layer-2 ground plane, connector-edge ESD, short high-current paths and quiet feedback takeoffs. Do not route until the exact placed board passes pin/layout/render/A-RENDER review.

## 2026-08-11 08:51 — handoff

- did: Promoted the two Stage 2 instruction-change candidates into the governed repository-level `improvements.md` ledger as IMP-001 and IMP-002.
- result: MEASURED both items now have explicit `proposed` status, source evidence, intended canonical landing points and executable completion criteria; neither is represented as already implemented.
- next: Keep the items visible through later stage harvests and change status only when implementation plus tests land, or when a dated rejection rationale is recorded.
