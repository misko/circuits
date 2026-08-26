# Review dispositions

This living ledger records the pre-seal review of commit `48688aa3`. `open`
means the finding is confirmed or not yet independently closed and therefore
blocks use of that review as seal evidence. A later fresh review must supersede
both defective red-team verdicts; this ledger never edits those source reports.

| id | review file | finding (one line) | severity | verification | disposition |
|---|---|---|---|---|---|
| PIN-ACT-01 | `2026-07-31_48688aa3_pin-review_active-parts.md` | U_MCU generated dossier omitted MPN/function provenance. | P1 | confirmed in the original generated dossier; a later dedicated audit BOM regenerated the dossier with `RP2040-Zero` provenance | open — re-run fresh pin review on the repaired candidate |
| PIN-ACT-02 | `2026-07-31_48688aa3_pin-review_active-parts.md` | U_MCU pad 23 power-source intent was not visible in the permitted evidence. | P1 | confirmed; carrier intentionally leaves pad 23 open and the module is powered/programmed from its own USB-C | open — bind intent in final pin dossier and obtain fresh pin verdict |
| PIN-ACT-03 | `2026-07-31_48688aa3_pin-review_active-parts.md` | U_SW RF pins require 0 VDC and RF8/RX1 is intentionally asymmetric. | P1 | confirmed; asymmetry is the documented RX1 tap, while the 0 VDC interface precondition was not binding in commit `48688aa3` | open — close with RTPR-01 and fresh pin review |
| RTPR-01 | `2026-07-31_48688aa3_redteam_topology.md` | RF interfaces did not bind the switch's 0 VDC requirement. | P1 | confirmed against PE42482 dossier/netlist; no series DC blocks are fitted | open — bind receive-only, 0 VDC, no-bias interface in source/docs/silk and re-review |
| RTPR-02 | `2026-07-31_48688aa3_redteam_topology.md` | No board-level RF input/hot-switch envelope existed. | P1 | confirmed against PE42482 PDF pp. 9/11 and commit `48688aa3` docs | open — publish conservative frequency/mode/power limits and re-review |
| RTPR-03 | `2026-07-31_48688aa3_redteam_topology.md` | 47 ohm source resistors did not independently prove the 3.6 V control-pin limit. | P1 | confirmed; worst case with zero credited GPIO resistance produces 4.040 V | open — 100 ohm ±1% repair and firmware pad settings are in progress; rebuild and re-review |
| RTPR-04 | `2026-07-31_48688aa3_redteam_topology.md` | The 100 mA rail model was not a conservative total-load maximum. | P2 | confirmed; module typical evidence can exceed 100 mA with WS2812 active | open — replace with a bounded supported-firmware/ambient operating envelope and physical-current bring-up gate |
| RTPR-05 | `2026-07-31_48688aa3_redteam_topology.md` | Ten exposed RF ports have no system-level ESD network. | P2 | confirmed; deliberate RF-performance tradeoff | open — explicitly classify as ESD-controlled bench equipment and document handling |
| RTPR-06 | `2026-07-31_48688aa3_redteam_topology.md` | Candidate was unsealed and uploader/plugin/rotation gates remained open. | P1 | confirmed by candidate manifest and order-time gate files | open — regenerate, finish pre-seal gates, and retain uploader-only checks in ORDER_README |
| LTPI-P1-001 | `2026-07-31_48688aa3_redteam_layout.md` | RP2040 underside keepout was only drawing text and 3V3 crossed the live-pad field. | P1 | confirmed by board zone enumeration and segment geometry | open — add real keepout, reroute, machine-check, rebuild, and re-review |
| LTPI-P1-002 | `2026-07-31_48688aa3_redteam_layout.md` | Hand-fitted module had no controlled joint height/support. | P1 | confirmed against module STEP dossier and assembly rules | open — define sample-measured nonconductive fixture/gap/inspection procedure and re-review |
| LTPI-P1-003 | `2026-07-31_48688aa3_redteam_layout.md` | SW_V4 paralleled ANT4 on F.Cu contrary to authored routing intent. | P1 | confirmed by independent board geometry | open — move crossing to In2 with uninterrupted In1 GND and re-audit all controls |
| LTPI-P1-004 | `2026-07-31_48688aa3_redteam_layout.md` | Board/fab package lacked authored stackup and advanced-via/impedance instructions. | P1 | confirmed; board has no `(stackup)` block | open — add regenerable stackup schema, masked-CPWG order note, and process requirements |
| LTPI-P1-005 | `2026-07-31_48688aa3_redteam_layout.md` | Ten plugin SMA connectors lacked executable assembly-service instructions. | P1 | confirmed by CPL/stock evidence and absent ORDER_README | open — add assembly drawing/order instruction and retain written uploader acceptance gate |
| LTPI-P2-006 | `2026-07-31_48688aa3_redteam_layout.md` | Power-path length/model and ferrite-side capacitor description were wrong. | P2 | confirmed by routed-length extraction and netlist | open — move C_BULK downstream, recompute route model, rebuild, and record |
| RENDER-P2-01 | `2026-07-31_48688aa3_render-review_full.md` | Schematic signal/power flow required excessive label hopping. | P2 | confirmed in reviewed schematic | recorded — redraw for teaching clarity if schematic source is touched before seal |
| RENDER-P2-02 | `2026-07-31_48688aa3_render-review_full.md` | Switch decoupling was not drawn adjacent to U_SW. | P2 | confirmed; physical placement itself passed | recorded — redraw next schematic revision |
| RENDER-P2-03 | `2026-07-31_48688aa3_render-review_full.md` | LED cathode silk marker collided visually with adjacent text. | P2 | confirmed in bare/twin top renders | open — move marker before final render review |
| RENDER-P2-04 | `2026-07-31_48688aa3_render-review_full.md` | Twin report named a different CPL provenance path. | P2 | confirmed in `missing_models.txt` | open — regenerate twin from final CPL and bind hashes/path before seal |

## v1.1 closure

The exact-artifact v1.1 reviews supersede the blocking pre-seal reports above.
They do not rewrite those historical findings; they verify the repaired board
and archive at source commit `bc1fb1003cd9b7f06c70b15d973c5c018d0ff458`
and board SHA-256
`72875d5ea92a52baa9962be3a69f4e69c1fb1ec3b9faf5ba4412934c18296bf7`.

| review phase | exact report | result |
|---|---|---|
| pin use | `2026-08-01_v1.1_pin_review.md` | SOUND; 100/100 high-risk pads checked, zero mismatch |
| render | `2026-08-01_v1.1_render_review.md` | SOUND; repaired module/resistor spacing visible and legible |
| topology/protection | `2026-08-01_v1.1_redteam_topology.md` | SOUND / ORDER; zero open P0/P1 design defects |
| layout/manufacturability | `2026-08-01_v1.1_redteam_layout.md` | SOUND / ORDER; P-PADSEP and exact geometry pass |
| RF schematic | `2026-08-01_v1.1_rf_schematic.md` | SOUND; 4/4 declared requirements pass |
| RF PCB | `2026-08-01_v1.1_rf_pcb.md` | SOUND; 7/7 declared requirements pass |
| RF fabrication | `2026-08-01_v1.1_rf_fab.md` | READY; 5/5 declared requirements pass |

The remaining uploader confirmations and first-article measurements are
order-execution and production/service acceptance controls. They do not reopen
the sealed design verdict or create a circular prerequisite for ordering the
article on which those measurements must be made.
