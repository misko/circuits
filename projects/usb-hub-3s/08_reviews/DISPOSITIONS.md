# Findings ledger — usb-hub-3s

All findings from all reviews, verified against artifacts before
disposition (reviews are claims). Verification evidence 2026-07-21:
release netlist/board parsed directly (session record: orchestrator
re-measurement pass).

| id | review file | finding | severity | verification | disposition |
|---|---|---|---|---|---|
| X1 | 2026-07-21_v1.0_external-llm_full.md | D1 (unidir SMBJ15A) cathode on VBAT_F before Q1 — reverse battery forward-biases it into a crowbar; ADR-0001 internally ambiguous; fuse has no MPN | P0 | confirmed — netlist: D1.1→VBAT_F, D1.2→GND; Q1 D=VBAT_F S=VIN; ORDER_README lists clips only | v1.1 work order item 1 (in progress) |
| X2 | 2026-07-21_v1.0_external-llm_full.md | PD power cell over-spread; LX pours 35.5mm on F+B.Cu, B.Cu facing VIN plane | P0 | confirmed — measured: Q4↔Q5 14.8mm, Q6↔Q7 11.2mm, C3→Q5 30.7mm, L1 ~26mm; zones [55,68.5,62,104] F+B | v1.1 item 2 (in progress) |
| X3 | 2026-07-21_v1.0_external-llm_full.md | AON6354 30V FETs vs SMAJ30A (vclamp_max ~48.4V) not a coordinated pair | P0 | confirmed as risk — part.yaml vds=30V, vspike_10us=36V; own gotcha cites IP6559 Fig.8 provenance | v1.1 item 4: coordination ADR (in progress) |
| X4 | 2026-07-21_v1.0_external-llm_full.md | 4 gate-R footprints promised (DETAIL_DESIGN) but absent — Q4-Q7 gates direct on HG/LG | P0 | confirmed — netlist: HG1/HG2/LG1/LG2 are 2-node nets | v1.1 item 3 (in progress) |
| X5 | 2026-07-21_v1.0_external-llm_full.md | L1 at 100% of irms_40C rating at 100W/9V | P1 | confirmed — part.yaml irms_40C=12A + own gotcha admits it | v1.1 item 5 (in progress) |
| X6 | 2026-07-21_v1.0_external-llm_full.md | PDO strap R25 DNP; nondeterministic config | P1 | confirmed — known from design session (ADR + ORDER_README first-power PD-analyzer gate) | deferred — vendor confirmation pending; ORDER_README gate stands |
| X7 | 2026-07-21_v1.0_external-llm_full.md | UVLO computed at typicals; worst-case ~8.3V; pack-level only; residual drain post-cutoff | P1 | partially confirmed — ADR math is typicals-only (verified); worst-case rederivation = v1.1 item 6 | v1.1 item 6 (in progress) |
| X8 | 2026-07-21_v1.0_external-llm_full.md | USB-C: D3 SMAJ24A clamp above IP6559 25V abs-max; Q8 single-FET body-diode backfeed; CC unprotected beyond IC | P1 | confirmed topology — netlist: Q8 S=VBUSC D=VOUT_PD single FET; D3 on VBUSC | v1.1 item 7: ADR fix-vs-documented-limitation (in progress) |
| X9 | 2026-07-21_v1.0_external-llm_full.md | USB-A 2A/2.5A exceeds receptacle contact class | P1 | confirmed — documented spec-tension (D-SPEC ADR exists); receptacle rating unstated on drawing | deferred — existing ADR + ORDER_README; test-plan item |
| X10 | 2026-07-21_v1.0_external-llm_full.md | Doc drift: ARCHITECTURE TLV431/Q13 residue; Cout 1812/6.3V doc vs 1210/16V BOM; TPS2513 vs 2513A; dossiers missing MPN (F1/Q8/J4) | P2 | confirmed — all four verified in-tree | v1.1 item 8 (in progress) |
| X11 | 2026-07-21_v1.0_external-llm_full.md | Not a data hub — charging distributor (naming) | P2 | confirmed — TPS2513A terminate D+/D-; no upstream USB | recorded; docs to clarify in v1.1 |
