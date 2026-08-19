# Two-USB-C power and data selection — 2026-08-18

## Result

The v2 architecture uses two identical HRO TYPE-C-31-M-12 receptacles but
assigns them non-overlapping electrical roles. `J_DATA` is a USB 2.0 sink with
independent 5.1 kOhm Rd resistors; its VBUS contacts feed only USB2517I
`VBUS_DET`. `J_POWER` exposes CC1/CC2 only to CH224K and feeds no USB data.
There is no conductive connection between `USB_UP_VBUS` and the board's power
tree.

## Selected parts

| Function | Exact part / JLC code | 2026-08-18 catalog observation | Reason |
|---|---|---:|---|
| Two USB-C receptacles | TYPE-C-31-M-12 / C165948 | 425,659; about $0.185 | Proven exact drawing/STEP; one mechanical family for both roles |
| Hardware PD sink | CH224K / C970725 | 7,523; about $0.49 | K-specific 0/1/1 strap requests 15 V without project firmware |
| 5 V regulator | TPS56637RPAR / C841386 | 2,665; about $2.52 | TI 8–28 V to 5 V / 6 A reference design and routed layout example |
| 3.3 uH inductor | MWSA0804S-3R3MT / C17700166 | 304; about $0.262 | 15 mOhm max DCR, 11 A minimum saturation, 10 A heat current |
| Input fuse | 0466003.NRHF / C14165 | 33,615; about $0.075 | 3 A, 32 V, reflowable 1206 |
| Input TVS | SMF16A / C207257 | 5,097; about $0.148 | 16 V standoff, 26 V maximum clamp, below 32 V buck absolute maximum |
| Input ceramics | TCC1206X7R106K500HT / C5449000 | 173,199; about $0.297 | 10 uF, 50 V, X7R; coordinated with TVS clamp |

Catalog stock is not allocation. Preorder MOQ/cash authority remains zero under
`01_docs/sourcing/procurement-policy.yaml`; an exact quantity-five JLC assembly
response is required before release.

## Power contract and corners

- Required external source: 15 V fixed PDO at 3 A (45 W).
- CH224K: exact K-table straps `CFG1=0, CFG2=1, CFG3=1`.
- TPS56637 UVLO: 200 kOhm / 27.4 kOhm external divider prevents operation from
  default USB-C 5 V.
- Feedback: 75.0 kOhm + 499 Ohm upper, 10.0 kOhm lower, all 0.1%.
- Full-corner regulated output: 5.04408–5.21609 V.
- Loaded port floor after retained shared and per-port resistance budgets:
  approximately 4.801 V at 500 mA, above the 4.75 V contract with about 51 mV
  modeled margin. First article must verify this with four simultaneous loads.

The original 15 V / 2 A idea was rejected by the source topology gate: at the
13.5 V conservative low input, 5 A output corner and 90% efficiency, the model
requires about 2.1 A. Selecting 15 V / 3 A avoids relying on source overload.

## Reuse impact

All already-purchased expensive functional parts are retained: USB2517I,
MCP2221A, MCP23017, five TPS2557 switches, four FSUSB42MUX switches,
TPS259474L aggregate eFuse, AP63203Q 3.3 V converter, logic and all four USB-A
connectors. Removed items are the USB-B receptacle, screw terminal, blade-fuse
holder and blade fuse. The new island is approximately $5–6 per board at the
observed low-volume catalog prices before assembly fees.
