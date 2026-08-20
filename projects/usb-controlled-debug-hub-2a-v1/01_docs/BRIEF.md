# brief: USB-controlled debug hub, four 2 A ports

status: commissioned — architecture candidate under verification
prompt_sha256: e0b832f16e214ef4991868765e56df25eb1f72712e93c3bee58014dbd8b59b4f
current_release: no

## Original prompt

<!-- prompt-verbatim-begin -->
> Can we please commission a new board, similar to this board, but we want each USBA port capable of 2A output
<!-- prompt-verbatim-end -->

- date: 2026-08-20
- channel: Codex task

## End goal — definition of done

Create a source-reproducible, JLCPCB-assembled successor to
`usb-controlled-debug-hub-v2`. It retains four independently controlled USB 2.0
downstream data paths and the separate USB-C DATA and USB-C POWER connectors,
while each USB-A VBUS output can continuously deliver 2 A at the qualified
mated test plug, with all four outputs loaded simultaneously. No firmware is
created by this project.

| # | Criterion | Source | Status |
|---|---|---|---|
| G1 | Four USB-A ports independently support full-off, power-only and data+power states | inherited functional intent | pending schematic |
| G2 | Each port delivers 4.75–5.25 V at 2.0 A at the qualified mated test plug | prompt + D1 | architecture candidate |
| G3 | All four 2.0 A loads operate simultaneously (8.0 A delivered total) | conservative D1 interpretation | architecture candidate |
| G4 | USB-C DATA carries USB 2.0 upstream data but cannot power or back-power the board | inherited v2 safety contract | pending parity |
| G5 | USB-C POWER carries power/PD only and requires a 20 V, 3 A fixed PDO | D2 | architecture candidate |
| G6 | Preserve already-purchased/high-cost v2 parts unless a measured rating, sourcing or topology incompatibility forces a change | user directive | reuse audit in progress |
| G7 | JLCPCB PCBA target; early exact-part, allocation, MOQ and surplus-cost gates precede placement | user history + pipeline | pending preliminary BOM |
| G8 | Generate no firmware, descriptor image or host utility | standing user directive | locked |

## Spec tensions

| # | Requirement | Standard / parts cap it exceeds | Resolution | User flagged |
|---|---|---|---|---|
| T1 | 2 A from a USB-A data port | USB 2.0 enumeration normally authorizes no more than the standard unit-load contract; the 2 A capability is not itself a USB 2.0 current advertisement | Treat 2 A as an electrical service capability for known devices/test loads. Do not claim universal USB-compliant 2 A negotiation. A charging-signature feature is outside scope unless requested. | no — conservative interpretation D1 |
| T2 | Four simultaneous 2 A outputs | The v2 15 V/3 A input and one 6 A buck cannot provide 40 W output plus losses | Require 20 V/3 A PD and two retained 6 A buck cells, each serving two ports | no — D2 |
| T3 | Reuse the v2 USB-A receptacle | KH-AF90DIP-112 has no manufacturer contact-current rating in its pinned drawing | Replace it with the already-qualified GCT USB1130-15-A, rated 3 A/contact; do not spend an undocumented rating | no — D3 |
| T4 | Reuse v2's 18 V input TVS and TPS259470A negotiated-voltage gate | TVS1800 cannot stand off a 20 V contract and the gate's existing OVLO intentionally rejects 20 V | Use publicly stocked 60 V TPS16630 programmable UVLO/OVP eFuse with TVS2200; exact current/power closure still blocks freeze | no — D4 provisional |

## Commission fact-lock

| Fact | Value | Locked by |
|---|---|---|
| Output rail | Four 5 V USB-A VBUS rails; 4.75–5.25 V at 2.0 A continuous | prompt + D1 |
| Simultaneous outputs | 4 of 4, 8.0 A delivered total | D1 conservative interpretation |
| Duty | 2.0 A continuous per port; transient/short envelope remains to be derived | D1 |
| Measurement plane | Qualified mated USB-A test plug; includes converter, protection, copper/vias/joints and connector contacts; excludes external cable and appliance | D1 |
| Input envelope | Dedicated USB-C PD sink; 20 V fixed PDO at 3 A required; default 5 V and lower PDOs must leave high-current output disabled | D2 |
| Protection posture | Per-port current limiting, thermal shutdown, always-on reverse-current blocking, aggregate bank protection, controlled input inrush, input UV/OV and transient coordination | inherited v2 + D2/D4 |
| Off/storage | Unplug USB-C POWER; DATA VBUS is sense-only and cannot energize the board | inherited v2 |
| Hard-cell parts | PD input protector, both 6 A buck cells, four port eFuses, 3 A USB-A receptacles and high-current magnetics | D2–D4 |
| Assembly | JLCPCB PCBA, nominal quantity five for early economics | inherited v2 + pipeline default |
| Fabrication ceiling | Start at JLC four-layer advanced because retained bottom-terminated power packages require it; no more advanced tier without an ADR | D5 |
| Firmware | forbidden | standing user directive |
| Foreign mating | none beyond standard USB cables/connectors | D1 |

## Mating fact-lock

None — this board does not mate to hardware this repository did not design.

## Reuse boundary

| Function | Candidate disposition |
|---|---|
| USB2517I hub, MCP2221A management bridge, MCP23017 expander | reuse unchanged, re-run exact pin/topology gates |
| Four FSUSB42 data switches, logic interlocks and USB ESD | reuse unchanged unless exact sourcing gate fails |
| CH224K PD controller and TYPE-C-31-M-12 receptacles | reuse; change hardware strap to 20 V and re-prove input network |
| TPS56637RPAR + MWSA0804S-3R3MT | reuse as two identical 6 A cells; one cell per two-port bank |
| TPS259470ARPWR port eFuses | reuse; change ILIM programming for a guaranteed >2 A service threshold below the 3 A connector rating |
| TPS259804ONRGER aggregate eFuse | reuse one per 5 V bank; thresholds and timers must be re-derived |
| AP63203QWU-7 3.3 V supply | reuse; leading topology moves its input to the negotiated 20 V rail to keep control load off the 5 V port banks |
| KH-AF90DIP-112 USB-A | do not reuse for a 2 A claim; no authoritative current rating |
| TVS1800 and the 15 V input divider | incompatible with 20 V; replace only this protection boundary |

## Log

- **D1 — conservative 2 A interpretation (2026-08-20).** Each of four ports
  must continuously deliver 2 A at the mated receptacle simultaneously. This is
  an electrical capability, not a promise that arbitrary USB 2.0 devices may
  draw 2 A without an appropriate charging/power agreement.
- **D2 — 60 W input and dual retained converters (2026-08-20).** Require a
  20 V/3 A PD source and split the outputs into two independent two-port 5 V
  banks using two TPS56637 cells. This preserves the purchased regulator family
  and gives each cell a 4 A continuous service load instead of asking one 6 A
  converter to supply 8 A.
- **D3 — rated output connector (2026-08-20).** Use GCT USB1130-15-A because
  its manufacturer drawing states 3 A/contact. The v2 KH-AF90DIP-112 drawing
  gives no contact-current limit and cannot substantiate the new claim.
- **D4 — input protection backtrack (2026-08-20).** The early surge gate
  rejected the initially considered 24 V operating TPS259827O because the
  TVS2200 worst published clamp is 28.35 V. TPS26630 was electrically suitable
  but public stock was zero. Use the electrically equivalent-function 60 V
  TPS16630PWPR in a stocked HTSSOP package instead. Its divider passes initial
  machine corners; current-limit, inrush and live JLC allocation remain open.
- **D5 — fabrication tier (2026-08-20).** Begin at `jlc_4layer_advanced`; the
  retained QFN/HotRod power parts and existing high-speed USB implementation
  already require this tier.
- **A1 — build quantity (2026-08-20).** Use five boards for early JLC quantity,
  MOQ and surplus-cost checks until the user supplies the actual order count.

## Decision register

| id | decision | decided by | depth |
|---|---|---|---|
| D1 | Four simultaneous 2 A ports; electrical service capability | conservative interpretation of prompt | BRIEF + rules |
| D2 | 20 V/3 A PD, dual TPS56637 two-port banks | derived architecture | ADR 0001 |
| D3 | GCT USB1130-15-A replaces unrated KH-AF90DIP-112 | rating boundary | ADR 0001 |
| D4 | Re-open 20 V input protection | rating boundary | ADR 0001 |
| D5 | JLC four-layer advanced starting tier | retained package escape | ADR 0001 |
