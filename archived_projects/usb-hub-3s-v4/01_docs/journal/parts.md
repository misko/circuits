# Parts and architecture journal

## 2026-08-10 19:38 — start

- did: Began Stage 1 after D2 authorized proceeding with the explicitly restated commission assumptions; inspected v3 only as a candidate/failure ledger.
- result: v3 identifies candidate functions (dual LM5116 bucks, TPS2557 port switches, TPS2513A charging advertisement, fixed-5 V Type-C source) and known defects to re-check; no v3 part or value has yet been adopted into v4.
- next: Verify interface requirements and manufacturing limits from current primary sources, then compare architectures before creating any part dossier.

## 2026-08-10 20:02 — iterate 1: architecture and local gates

- did: Selected a dual-module 5 V architecture, independent USB-A current limiting/charging advertisement, a fixed-5 V Type-C source controller, passive input protection and mechanical shutdown; calculated rail, input-current, loss, surge and off-state budgets from manufacturer data.
- result: The applicable local early-design gates passed. A first JLC/LCSC catalog probe found all 15 then-selected exact MPNs, but this was assembly-catalog evidence only and did not satisfy the independent-source requirement.
- next: Join each exact manufacturer MPN against an authorized independent distributor before freezing the selection.

## 2026-08-10 20:26 — iterate 2: sourcing backtrack

- did: Probed the exact candidate set at Mouser and reviewed the ambiguous/missing identities manually. The independent check covered only 9/15, so the input connector, reverse-polarity FET, gate clamp, bulk capacitor, Type-C receptacle and mechanical switch were backtracked. Added explicit CC1/CC2 ESD protection after inventorying every exposed Type-C pin.
- result: No schematic had been generated, so the six substitutions and one added protection device were confined to architecture, rules and dossiers. This invalidated the earlier JLC-only green result without creating board rework.
- next: Re-run both assembly-catalog and independent-authorized-source checks on the replacement set, then repeat all applicable electrical gates.

## 2026-08-10 20:43 — finish: Stage 1 engineering candidate

- did: Qualified the final 16-part set at JLC/LCSC and across a composed Mouser/DigiKey independent pool; pinned exact identities and primary datasheets in part dossiers; repeated P-MOD, D-SPEC, E-PATH, E-TOPO, E-MARGIN and E-OFF checks and reviewed the rules as structured YAML.
- result: JLC/LCSC selection-time stock passed 16/16; the independent two-source pool passed 16/16 (Mouser 15, DigiKey 1); early-design passed 3/3, topology passed 4/4, module-first passed 4/4, margin passed 8 checks, shutdown passed at a 250 uA estimate, and 27/27 current YAML documents parsed. The board-dependent rules audit is intentionally not applicable before a `.kicad_pro` exists. Stage wall time was about 65 minutes; live stock/API checks consumed under one minute, while primary-source research, identity adjudication, backtracking and evidence writing dominated.
- next: Pause for the required ADR-0004 decision. If JLC advanced processing with resin-filled/copper-capped via-in-pad is accepted, begin the schematic; otherwise backtrack the converter architecture before generation.

## 2026-08-10 20:49 — regate: separate escape geometry from thermal process

- did: Recomputed all 16 dossier escape blocks with `escape_check.py` during the pre-commit pass.
- result: The gate caught four stale/overloaded tier declarations: three 0.65 mm TI packages used `tier_required` to describe advanced thermal via processing rather than the lowest geometric escape tier, while the 0.65 mm reverse FET understated its escape tier. Corrected all four to the computed `jlc_4layer_standard` geometry and retained filled/capped thermal-via requirements separately in gotchas, layout references, ADR-0004 and the board fab tier. P-ESC then passed 16/16. TPS25810's 0.50 mm QFN independently still computes as `jlc_4layer_advanced`, so the user decision remains necessary.
- next: Repeat the complete applicable gate battery, commit/tag/push, and pause without creating schematic artifacts.

## 2026-08-10 20:59 — harvest regate: stage-applicable rules audit

- did: Added and ran the shared `rules_audit.py --phase source` entry, which grades authored net-class intent without requiring future KiCad artifacts.
- result: The new gate rejected 2/9 v4 classes because their `current:` prose was unreadable: `bootstrap pulse only` and `configuration-channel signal`. Both classes carry low-energy signal behavior rather than an external ampacity path, so their declarations were corrected to explicit `signal (...)` exemptions. The source audit then passed 9/9 without weakening the later full artifact audit.
- next: Finish the composed Q-2SOURCE implementation/tests, rerun the complete Stage 1 battery and push the harvested tooling checkpoint; remain paused at ADR-0004.

## 2026-08-10 21:10 — harvest finish: composed sourcing and visible progress

- did: Replaced the hand-composed selection verdict with a machine Q-2SOURCE join over the candidate BOM, a fresh JLC JSON observation and the Mouser/DigiKey evidence; added exact manufacturer identity and per-row START/DONE timing. The live run then exposed and fixed a UTC/local-date mismatch and buffered JLC output.
- result: The unchanged v4 candidate passed 16/16 rows at two authorized pools each: JLC plus Mouser for 15, and JLC plus the dated DigiKey product-page quote for USBLC6. The terminal now names the active row and denominator; the JLC probe flushes each completed row instead of appearing idle. Distributor gaps stay visible but do not override the composed policy verdict.
- next: Run repository contract/schema regression audits, commit/tag/push this Stage 1 harvest, and remain paused at ADR-0004 without creating schematic artifacts.
