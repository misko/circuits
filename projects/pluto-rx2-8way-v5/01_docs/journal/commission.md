# Commission journal

## 2026-08-12 18:52 — start

- did: Entered a fail-closed clean-room commission checkpoint using only the v5 tree.
- result: 0 approved requirements, 0 approved architectures and 0 generated design artifacts.
- next: Record user-authoritative clarifications and independently verify only the supplied evidence leads.

## 2026-08-12 20:15 — architecture checkpoint

- did: Locked receive-only one-of-N behavior, 100 MHz–5.9 GHz, SMA and JLCPCB; compared true SP8T, true SP4T, cascades, commercial modules and passive splitting; wrote proposed ADR-0001.
- result: 4 user locks, 5 architecture classes compared, N=8 true absorptive SP8T proposed, 14 requirement groups still open, floorplan still fail-closed, 0 downstream artifacts.
- next: Obtain user approval/selection and the exact control, power, RF, state/timing, mechanical/assembly and test decisions listed in BRIEF.md.

## 2026-08-12 20:20 — finish

- did: Added the official AD9363-versus-AD9361 boundary and ran YAML, content, floorplan, status, module-first and early-design source checks.
- result: YAML 11/11 PASS; content/floorplan PASS; beacon 1/1 PASS; P-MOD expected FAIL at 0/0 selected subsystems; EARLY-DESIGN expected FAIL at 1/3 green; 0 generated artifacts.
- next: Keep the pipeline blocked until the user approves N/switch class and closes or delegates the remaining requirements.

## 2026-08-12 21:27 — clarification

- did: Compared AD9363 and AD9361 from their official ADI ratings after the user's `AD9363 vs AD9361` follow-up.
- result: Both are RF 2x2 transceivers; AD9363 is rated 325 MHz–3.8 GHz with up to 20 MHz channel bandwidth, while AD9361 RX is rated 70 MHz–6 GHz with up to 56 MHz channel bandwidth. A Pluto+ software profile is not silicon identity.
- next: Confirm the exact device physically fitted to the user's Pluto Plus before making a complete-system 100 MHz–5.9 GHz claim.

## 2026-08-12 21:40 — user risk acceptance

- did: Recorded D5: physical AD9363 silicon running an AD9361 software profile, prior reliable 5.8 GHz use, and explicit acceptance of continued out-of-official-range operation.
- result: Silicon/profile blocker closed; prior 5.8 GHz evidence graded USER-REPORTED/INHERITED; selector target remains 100 MHz–5.9 GHz; ADI-guaranteed complete-system extended-band claims forbidden; 0 generated artifacts.
- next: Validate the updated source records and continue blocking generation on open RF loss/isolation/power, control/default-state and test limits.

## 2026-08-12 21:42 — risk-acceptance validation

- did: Parsed all v5 YAML, asserted the exact D5 quote/D-SPEC disposition/machine risk fields and reran the generic status beacon gate.
- result: YAML/content PASS; beacon 1/1 PASS; RF performance nulls remain intentionally open; floorplan pipeline remains closed; 0 generated artifacts.
- next: Await architecture approval and the still-open RF, control, power, state and test decisions.

## 2026-08-12 22:15 — autonomous-control architecture spike

- did: Recorded D6 and compared three small bare flash MCUs plus a module option using fresh manufacturer/JLC/LCSC evidence; analyzed dwell-code synchronization and fail-safe control.
- result: Onboard autonomous preprogrammed control and unique per-antenna dwells locked; STM32C011F4P6 leads the proposed 20-pin MCU class; fixed order, inter-state all-off guard and distinctive frame marker proposed; all numeric/procedural parameters remain open; 0 generated artifacts.
- next: Validate source records, then await approval of ADR-0001/ADR-0002 and the exact timing, safety, programming, power, RF and test decisions.

## 2026-08-12 23:05 — D7 port/power lock and early-schema cleanup

- did: Recorded D7 as selecting eight antenna ports and an independent USB-C nominal-5 V input; drafted ADR-0003 from fresh USB Type-C/manufacturer/JLC evidence; replaced active foreign example values in power, invariant, netclass, assembly and route YAML with v5-specific fail-closed sentinels.
- result: N=8 and the external power source are locked without inventing exact parts; three architecture ADRs remain proposed; no copied cook/load-cell, 3S-LiPo, LM5116 or foreign route target remains executable; 0 generated artifacts.
- reflection: Cheap schema/content inspection at commission caught plausible-looking inherited configuration before TSX. New projects should instantiate empty project-specific sentinels, not copy active example rows; examples belong only in contracts or references.
- next: Validate all source files, then pause for approval of the SP8T, controller/protocol and protected-3.3 V architecture classes before part dossiers or schematic work.
