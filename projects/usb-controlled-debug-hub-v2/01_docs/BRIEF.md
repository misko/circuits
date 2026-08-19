# brief: usb-controlled-debug-hub-v2

status: architecture-and-sourcing
current_release: none

## Original board prompt

<!-- prompt-verbatim-begin -->
once you are done with the changes for improvements , please make a new board, similar to the usb pi switch, but instead of 4 x USB host connectors, lets have the board act as a USB hub and usb device. The usb hub controls the 4 x USB A ports on the board, and the usb device lets you toggle on and off power and or data to each USB A.
<!-- prompt-verbatim-end -->

## v2 revision prompts

<!-- prompt-verbatim-begin -->
Lets go with the two USBC design (one for power, one for data)
<!-- prompt-verbatim-end -->

SHA-256: `772da6eb1223366fa84c20b9eb201a83f7b99c0b8a4c388c6aa00dec86c01c3e`

<!-- prompt-verbatim-begin -->
we already ordered the components for the current board, so lets try to keep any high cost components the same if we can. Please go for it
<!-- prompt-verbatim-end -->

SHA-256: `f3aacba9de95cd7e440aaed3619d55de91da16ac65338882524f75a0fee2de6e`

## End goal

Deliver an assembled, source-reproducible USB 2.0 debug hub with two clearly
distinct USB-C receptacles. `DATA` connects the hub upstream data path to a
computer but cannot power the board. `POWER` is a dedicated USB-PD sink but has
no USB data path. Four USB-A ports retain independent data and power control.
The already-purchased v1 functional core is reused unless a measured electrical,
package, or sourcing incompatibility requires a change. No project firmware is
generated.

| # | Criterion | Source | Status |
|---|---|---|---|
| G1 | One USB-C `DATA` receptacle enumerates a USB 2.0 High-Speed hub and its internal management device | P, inherited v1 | pending schematic and first article |
| G2 | One separate USB-C `POWER` receptacle accepts a USB-PD source and never carries USB data | P | architecture locked; implementation pending |
| G3 | The DATA receptacle's VBUS is sense-only and can neither power nor back-power the board | P, safety interpretation | architecture locked; implementation pending |
| G4 | Four USB-A ports retain full-off, power-only, and fully-connected states independently | original P | inherited circuit to be parity-checked |
| G5 | Each USB-A supplies 500 mA at 4.75–5.25 V at the mated test plug, all four simultaneously | inherited v1 contract | power math pending exact v2 divider/path |
| G6 | A failed/no PD contract leaves the protected 5 V trunk off; a 5 V-only USB-C source does not brown-out the hub | conservative interpretation | architecture locked; implementation pending |
| G7 | Reuse USB2517I, MCP2221A, MCP23017, five TPS2557s, four FSUSB42s, TPS259474L, AP63203Q and compatible purchased passives | latest P | reuse matrix locked; parity pending |
| G8 | Generate no firmware, descriptor image, or host utility | standing user directive | met by architecture |
| G9 | Produce a JLCPCB PCBA release with early allocation/MOQ economics, electrical/SI review, connector review, and exact release evidence | pipeline contract | pending |

## Commission fact lock

| Fact | Locked value | Authority |
|---|---|---|
| External outputs | Four USB-A 2.0 receptacles; four simultaneous 500 mA loads | inherited v1 |
| Output measurement plane | Qualified mated USB-A test plug, including onboard converter/protection/switch/copper/joints/contacts | inherited v1 |
| DATA input | USB-C USB 2.0 UFP/upstream data; host VBUS is detector-only | user + D12 |
| POWER input | Dedicated USB-C PD sink; require a source advertising a 15 V fixed PDO at 3 A (45 W) | D13 |
| Internal 5 V setpoint | 5.13 V nominal; calculated full-corner window must remain within 5.25 V and preserve 4.75 V at loaded outputs | D13; exact values pending gate |
| Normal board load | 2.58 A maximum on the regulated trunk under the inherited v1 contract | inherited v1 power model |
| Fault transient | Existing aggregate breaker may demand up to 5 A for no more than 6 ms; v2 PD/buck path must tolerate it without making it continuous | inherited v1 A6 |
| Protection | USB-C input fuse/TVS, wide-input buck, existing reverse-blocking latch-off aggregate eFuse, existing per-port current limiting and ESD | D13 |
| Storage/off | Unplug USB-C POWER; DATA VBUS cannot energize the board | D12 |
| Assembly | JLCPCB, four layers, least-cost tier that meets USB/package constraints | user history + pipeline |
| Firmware | forbidden | standing user directive |
| Foreign mating | Standard USB-C and USB-A cables only; no device-specific body alignment | D12 |

## Specification tensions

| id | Tension | Resolution | ADR |
|---|---|---|---|
| T1 | A USB-C upstream data receptacle can expose 5 V while a separate power receptacle also supplies the board | DATA VBUS terminates only in a high-impedance detector; the two VBUS domains never connect | [0012](decisions/0012-two-usbc-domain-separation-and-reuse.md) |
| T2 | 9 V / 3 A is adequate for normal load but marginal for the inherited 5 A / 6 ms 5 V fault transient after conversion losses | Request the standard 15 V PDO and require at least 30 W; use a 6 A, 28 V synchronous buck | [0013](decisions/0013-pd-input-and-5v-regulator.md) |
| T3 | A USB-C source may provide only default 5 V or omit 15 V | Set buck UVLO above default 5 V; incompatible supplies leave the board off instead of undervolting it | [0013](decisions/0013-pd-input-and-5v-regulator.md) |
| T4 | Reusing every purchased part would retain the high-drop manual 5 V fuse/holder and make the output-voltage corner unnecessarily tight | Preserve high-cost functional ICs; replace only the input connector/fuse boundary and add the PD/buck island | [0012](decisions/0012-two-usbc-domain-separation-and-reuse.md) |

## Reuse constraint

| Function | v1 part | v2 disposition |
|---|---|---|
| Seven-port hub | USB2517I-JZX | reuse unchanged |
| USB management | MCP2221A-I/SL + MCP23017T-E/SS | reuse unchanged |
| Port power control | TPS2557DRBR x5 | reuse unchanged |
| Port data disconnect | FSUSB42MUX x4 | reuse unchanged |
| Aggregate protection | TPS259474LRPWR | reuse unchanged, now fed by regulated buck output |
| Logic/interlocks | 74LVC08APW x2 + 2N7002K | reuse unchanged |
| 3.3 V supply | AP63203QWU-7 and its local magnetics/passives | reuse unchanged |
| USB-A ports and ESD | KH-AF90DIP-112 + PESD2USB3UX x4 | reuse unchanged |
| Upstream connector | USB-B | replace with USB-C DATA |
| External power entry | screw terminal + blade fuse/holder | replace with USB-C POWER + high-voltage input protection |

## Decisions and assumptions

- **D1 — firmware forbidden.** The existing fixed-function USB bridge and I/O
  expander remain; no firmware scope is inferred.
- **D12 — two USB-C domains.** User explicitly selected one power and one data
  connector. They will be mechanically separated and unambiguously labeled.
- **D13 — 15 V PD power island.** Request 15 V rather than 9 V so the existing
  breaker transient has real power headroom. A 5 V-only supply is not qualified.
- **A14 — build quantity.** Early sourcing economics use five boards unless the
  user provides a different quantity; final order evidence must use the actual
  quantity.
- **A15 — reuse priority.** “If we can” means electrical and manufacturing
  correctness outrank reuse. Any changed purchased high-cost part requires an
  explicit exception and cost explanation.

## Decision register

| id | Decision | Depth |
|---|---|---|
| C1 | Preserve the v1 hub, management, interlock, port-switch and aggregate-protection architecture | [0012](decisions/0012-two-usbc-domain-separation-and-reuse.md) |
| C2 | Replace USB-B with a USB-C data-only upstream connection | [0012](decisions/0012-two-usbc-domain-separation-and-reuse.md) |
| C3 | Add a separate USB-C PD power-only connection with no D+/D-/SBU route | [0012](decisions/0012-two-usbc-domain-separation-and-reuse.md) |
| C4 | Use CH224K hardware straps for 15 V; no MCU or configuration firmware | [0013](decisions/0013-pd-input-and-5v-regulator.md) |
| C5 | Use TPS56637 plus MWSA0804S-3R3MT to generate the 5.13 V trunk | [0013](decisions/0013-pd-input-and-5v-regulator.md) |
| C6 | Use HRO TYPE-C-31-M-12 / C165948 for both USB-C receptacles | [0012](decisions/0012-two-usbc-domain-separation-and-reuse.md) |

