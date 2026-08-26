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
| G7 | Reuse USB2517I, MCP2221A, MCP23017, internal TPS2557, four FSUSB42s, AP63203Q and compatible purchased passives; replace externally exposed switches where reverse blocking is required and the aggregate eFuse where regulator transient/drop margin requires it | latest P + electrical exceptions | [0014](decisions/0014-power-path-adversarial-hardening.md) and [0016](decisions/0016-low-loss-aggregate-and-transient-margin.md) accepted; parity pending |
| G8 | Generate no firmware, descriptor image, or host utility | standing user directive | met by architecture |
| G9 | Produce a JLCPCB PCBA release with early allocation/MOQ economics, electrical/SI review, connector review, and exact release evidence | pipeline contract | pending |

## Commission fact lock

| Fact | Locked value | Authority |
|---|---|---|
| External outputs | Four USB-A 2.0 receptacles; four simultaneous 500 mA loads | inherited v1 |
| Output measurement plane | Qualified mated USB-A test plug, including onboard converter/protection/switch/copper/joints/contacts | inherited v1 |
| DATA input | USB-C USB 2.0 UFP/upstream data; host VBUS is detector-only | user + D12 |
| POWER input | Dedicated USB-C PD sink; require a source advertising a 15 V fixed PDO at 3 A (45 W) | D13 |
| Internal 5 V setpoint | about 5.01 V nominal; calculated 4.92511–5.10424 V tolerance-and-TCR-charged window plus a 100 mV dynamic reserve must remain within 5.25 V and preserve 4.75 V at loaded outputs | [0016](decisions/0016-low-loss-aggregate-and-transient-margin.md) |
| Qualified ambient | 10–40 °C bench operation; wider-temperature operation is not claimed by this release | [0015](decisions/0015-characterized-current-limits-and-input-clamp.md) |
| Normal board load | 2.58 A maximum on the regulated trunk under the inherited v1 contract | inherited v1 power model |
| Fault transient | Aggregate breaker may demand up to 5.776 A for no more than 6.65 ms; v2 PD/buck path must tolerate a qualified 5.78 A / 7 ms pulse without making it continuous | [0016](decisions/0016-low-loss-aggregate-and-transient-margin.md) |
| Protection | USB-C input fuse/TVS, wide-input buck, low-loss latch-off aggregate eFuse, true-RCB per-port current limiting and ESD | D13 + D16 |
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
| T5 | Purchased TPS2557 port switches do not block a powered target from back-driving an off/disabled hub | Retain the internal TPS2557 only; use true-RCB TPS259470A eFuses on the four cable-exposed ports | [0014](decisions/0014-power-path-adversarial-hardening.md) |
| T6 | TPS56637 needs more input capacitance than a Type-C sink may expose at initial attach | Put the buck bank behind a UVLO/dVdt-controlled TPS259470A; expose only the 1 uF input damping capacitor before negotiation | [0015](decisions/0015-characterized-current-limits-and-input-clamp.md) |
| T7 | The v0.1.2 5.90 kOhm port setting was not a characterized TI guarantee, and changing it alone would upset aggregate selectivity | Use TI's characterized 3.32 kOhm local row, then use TPS259804's characterized 300 Ohm aggregate row; charge both for resistor tolerance/TCR and verify one-, two- and all-channel cases | [0015](decisions/0015-characterized-current-limits-and-input-clamp.md), [0016](decisions/0016-low-loss-aggregate-and-transient-margin.md) |
| T8 | SMF16A was checked against the regulator while the upstream eFuse has the lower 28 V limit | Use TVS1800 and coordinate its 24.7 V worst-temperature specified clamp against `U_PD_IN` | [0015](decisions/0015-characterized-current-limits-and-input-clamp.md) |
| T9 | The corrected DC feedback corner still left only 5.78 mV after a 30 mV assumed ripple allowance | Replace only the aggregate eFuse with 5 mOhm-max TPS259804, trim the upper feedback leg to 73.2 kOhm, and reserve a real 100 mV dynamic envelope | [0016](decisions/0016-low-loss-aggregate-and-transient-margin.md) |

## Reuse constraint

| Function | v1 part | v2 disposition |
|---|---|---|
| Seven-port hub | USB2517I-JZX | reuse unchanged |
| USB management | MCP2221A-I/SL + MCP23017T-E/SS | reuse unchanged |
| External port power control | TPS2557DRBR x4 | replace with TPS259470ARPWR x4; electrical safety exception |
| Internal management power | TPS2557DRBR x1 | reuse unchanged |
| Port data disconnect | FSUSB42MUX x4 | reuse unchanged |
| Aggregate protection | TPS259474LRPWR | replace with TPS259804ONRGER; electrical-margin exception, about USD 0.38/board incremental catalog cost |
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
| C7 | Put Type-C bulk behind a negotiated-voltage inrush switch and true-reverse-block all external USB-A VBUS paths | [0014](decisions/0014-power-path-adversarial-hardening.md) |
| C8 | Use characterized local/aggregate current-limit rows, lower the 5 V setpoint, and coordinate TVS1800 against the upstream eFuse | [0015](decisions/0015-characterized-current-limits-and-input-clamp.md) |
| C9 | Replace only the aggregate eFuse, use the exact RGE0024M split-pad land, and reserve 100 mV of regulator dynamic headroom | [0016](decisions/0016-low-loss-aggregate-and-transient-margin.md) |
| C10 | Accept a fresh 53/53 public-catalog PASS for the pre-layout checkpoint only; retain the exact-release JLC PCBA uploader as a mandatory order hold | [0017](decisions/0017-public-catalog-prelayout-checkpoint.md) |
