# Brief: USB Hub 3S v4

status: in-progress
prompt_sha256: c0f3368c09c3a89e1bf7c547fde66484654514293198bac3d2090572751c03ef
current_release: no

## Original prompt

<!-- prompt-verbatim-begin -->
Can you please launch a new usb hub v4 lets run the full pipeline . after each stage lets pause and reflect how it went, where we spent time, what we might be able to generalize? what general instructions might need reworking
<!-- prompt-verbatim-end -->

- Date: 2026-08-10
- Channel: interactive Codex task

## End goal — definition of done

Produce an independently reviewed, reproducible, JLCPCB-orderable PCBA for a
power-only 3S-LiPo USB distribution board. Run the repository's full PCB
pipeline one stage at a time; after every green stage, stop and record measured
time, friction, reusable learning, and any instruction change suggested by the
evidence.

| # | Criterion | Source | Status |
|---|---|---|---|
| G1 | The product carries USB power only and no USB data. | D1 | unmet |
| G2 | It provides the inherited v3 service: three charge-only USB-A outputs and one USB-C power output for a Raspberry Pi 4 from a 3S LiPo pack. | A1 | unmet |
| G3 | No claim of active fail-high overvoltage cutoff is made; the resulting safety boundary is explicit. | D1 | unmet |
| G4 | The manufacturing package targets JLCPCB PCBA. | D1 | unmet |
| G5 | The complete bounded pipeline reaches an independently reviewed, reproducible, DRC-clean release package. | P | unmet |
| G6 | Each completed stage has a pause report with measured time and harvestable process learning. | P | unmet |

## Log

### D1 — 2026-08-10 — user directive

> v4 does not carry USB data, it does not need active over voltage cutoff, manufacturing target is JLCPCB

Impact: Locks the interface as power-only, excludes active overvoltage cutoff
from the required architecture, and selects JLCPCB as the fabrication and
assembly target. See `decisions/0001-power-only-supervised-prototype.md`.

### A1 — 2026-08-10 — assumption (not asked)

Assumed: “v4” inherits v3's service envelope: a 3S LiPo source (9.0–12.6 V),
three simultaneous USB-A charging outputs at 5 V / 2 A continuous each with
2.5 A short peaks, and one USB-C power-only output for a Raspberry Pi 4 at
5 V / 3 A. Authority: P names a v4 lineage and D1 narrows, rather than replaces,
the v3 purpose. Escalate if: the source, port count, load, continuous current,
peak duration, or simultaneous-use expectation differs.

### A2 — 2026-08-10 — assumption (not asked)

Assumed: Retain v3's enable-gated master shutdown concept and commission a
stored-state current budget of at most 1 mA; no hard battery disconnect is
required. Authority: P delegates a successor design and D1 rejects only active
overvoltage cutoff. Escalate if: shelf storage, unattended operation, or a true
galvanic battery disconnect is required.

### A3 — 2026-08-10 — assumption (not asked)

Assumed: JLCPCB standard four-layer, top-side PCBA, prototype quantity five.
Authority: D1 names JLCPCB; the remaining values are the conservative v3
prototype boundary. Escalate if: cost ceiling, board quantity, two-sided
assembly, impedance service, or another JLC capability tier is required.

### A4 — 2026-08-10 — assumption (not asked)

Assumed: With no active fail-high cutoff, v4 remains a supervised prototype
for a replaceable load. It must not be represented as protecting the load from
a sustained converter high-side failure. Authority: D1 accepts omission of
active overvoltage cutoff. Escalate if: the system becomes unattended,
hard-access, safety-critical, or powers valuable/irreplaceable equipment.

### A5 — 2026-08-10 — assumption (not asked)

Assumed: There is no rigid foreign-hardware mating geometry; loads connect by
cable. Authority: the inherited connector architecture. Escalate if: the board
must align to an enclosure, panel, heatsink, daughtercard, or fixed connector.

### A6 — 2026-08-10 — assumption (not asked)

Assumed: Modules are preferred for complex functions unless a measured trade
study establishes a lower-complexity bare-IC implementation. Authority: the
repository's commission default. Escalate if: a binding size, unit-cost, supply,
or performance requirement rules out modules.

## Decision register

| id | decision | decided by | depth |
|---|---|---|---|
| D1 | Power-only product, no active fail-high cutoff requirement, JLCPCB target. | user (D1) | `decisions/0001-power-only-supervised-prototype.md` |
| A1 | Inherit the v3 port, load, and 3S source envelope provisionally. | agent (A1 / P-delegation) | Log A1 |
| A2 | Retain enable-gated shutdown and a ≤1 mA stored-current budget. | agent (A2 / P-delegation) | Log A2 |
| A3 | Start at JLCPCB standard four-layer, top-side PCBA, quantity five. | agent (A3 / D1) | Log A3 |
| A5 | No rigid external mating geometry is currently in scope. | agent (A5 / P-delegation) | Log A5 |
| A6 | Apply the repository module-first default. | agent (A6 / P-delegation) | Log A6 |

## Spec tensions

| id | requirement | standard/part cap | how honoured | ADR | user-flagged |
|---|---|---|---|---|---|
| T1 | Product name says “USB hub”; D1 says no USB data. | A USB data hub requires upstream/downstream data paths and hub control; this product provides only power/charging ports. | Describe and verify it as a power distributor. No USB data nets or data-function compliance claim may appear. | `decisions/0001-power-only-supervised-prototype.md` | yes |
| T2 | No active overvoltage cutoff. | Passive clamps/current protection cannot guarantee prompt disconnection for every sustained converter fail-high fault. | Explicit supervised-prototype boundary; retain overload, reverse-feed and transient protections where justified, but make no fail-high protection claim. | `decisions/0001-power-only-supervised-prototype.md` | yes |
| T3 | USB-C powers a Pi 4 without USB-PD. | Raspberry Pi 4 takes fixed 5 V power and does not need a USB-PD source; Type-C source-current advertisement still needs correct CC termination. | Stage 1 must cite the Pi and USB Type-C primary sources; Stage 2 must implement power and CC only, with no data or PD controller. | `decisions/0001-power-only-supervised-prototype.md` | inherited; confirmation owed |

## Mating fact-lock

none — this board does not mate to hardware this repo did not design. A5 must
be revisited if a fixed enclosure/panel interface is introduced.

## Commission fact-lock

| Fact | Locked value | Locked by |
|---|---|---|
| Product/interface class | Power distribution and charge-only ports; no USB data | D1 |
| Input | 3S LiPo pack, 9.0–12.6 V operating envelope | A1 |
| USB-A service | 3 ports, all simultaneous, 5 V nominal, 2 A continuous per port, 2.5 A short peak per port | A1 |
| USB-C service | 1 power-only port for Raspberry Pi 4, 5 V nominal, 3 A continuous | A1 |
| Output measurement boundary | USB-A at each board receptacle; USB-C at the load after the nominated cable | A1 |
| Protection posture | No active sustained-overvoltage cutoff required; supervised-prototype limitation is mandatory | D1, A4 |
| Off/storage posture | Enable-gated master shutdown; ≤1 mA stored-state draw; no hard disconnect required | A2 |
| Manufacturing | JLCPCB standard four-layer, top-side PCBA, quantity five | D1, A3 |
| Mating | No rigid foreign mating geometry | A5 |
| Integration posture | Modules preferred; any bare-IC hard cell requires a cited comparison and ADR | A6 |
| Sourcing classes | JLC-assembled catalog parts preferred; consigned/user-fit exceptions must be measured and declared | D1, A3 |

Exact voltage tolerance, delivery-path IR budgets, peak duration, converter
selection, protection-part coordination, and sourceability remain Stage 1
obligations. The machine contracts fail closed where those facts are not yet
proved.
