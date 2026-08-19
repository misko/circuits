# Power-path hardening study — 2026-08-18

## Decision

Use `TPS259470ARPWR` (`C3662799`) for each of the four externally exposed USB
VBUS switches and for the negotiated-voltage input gate. Retain the already
purchased `TPS2557DRBR` only on the captive management-device rail. This is the
smallest architecture change that closes powered-target backfeed, Type-C attach
capacitance and internal-channel fault-coordination findings without replacing
the hub, controller, data switches, regulators, connectors, or aggregate eFuse.

## Candidate comparison

| Candidate | Result | Reason |
|---|---|---|
| TPS2557DRBR | Rejected for external ports | Current limit and OCS are suitable, but it does not guarantee disabled-state reverse-current blocking. |
| TPS2553DRVR (`C55266`) | Rejected | Reverse-voltage response is millisecond-scale and its 135 mOhm maximum on-resistance consumes too much of the USB plug-voltage budget. |
| TPS25210 | Rejected | Strong reverse blocking, but its status semantics do not directly preserve the USB2517I active-low OCS path. |
| TPS259470ARPWR (`C3662799`) | Selected | True reverse-current blocking, 45 mOhm maximum on-resistance, active current limiting, auto retry and active-low open-drain FLT in the already-qualified RPW land pattern. |

Catalog observations were design-phase only: `C3662799` showed 1,123 units,
5.90 kOhm `C23071` showed 70,175, and 187 kOhm `C163486` showed 6,092 on
2026-08-18. An exact quantity-five JLC allocation/economics receipt remains a
release gate; catalog counts do not authorize ordering.

## Calculated contracts

- External `RILM = 5.90 kOhm, 1%`: TI equation `ILIM = KILM/RILM`, with device
  error and resistor tolerance, gives approximately 0.503–0.628 A.
- Retained internal TPS2557 with 187 kOhm, the largest TI-recommended
  programmer, gives 0.468–0.706 A from the datasheet's three limit equations
  after charging 1% resistor tolerance. The commissioned captive
  MCP2221A/MCP23017 load remains bounded to 0.10 A; the switch limit is fault
  containment, not the load budget. A previously considered 210 kOhm value
  was rejected because it is outside TI's recommended 20–187 kOhm range.
- Four external high corners, the internal-switch high corner and the 0.48 A
  3.3 V budget total 3.698 A. This is deliberately inside the timed aggregate
  breaker's trip envelope at the simultaneous worst-case fault corner; the
  commissioned 2.58 A normal load retains at least 0.410 A to the breaker's
  worst-low threshold.
- The PD-input TPS259470A 470 kOhm / 28.7 kOhm / 35.7 kOhm divider gives a
  full-corner UVLO rising range of 9.646–10.329 V and OVLO rising range of
  17.381–18.653 V. It therefore rejects default 5 V attach and admits the
  specified 15 V ±5% contract.
- Changing the buck feedback trim resistor to 1.00 kOhm gives a full-corner
  5.074–5.247 V output. With 50.2 mOhm switch, 25 mOhm copper and 100 mOhm
  connector budgets, the modeled 500 mA plug floor is about 4.812 V.
- `R_PD_VDD` is now a 1 kOhm, 0.5 W 1210 part. At the former conservative
  16.5 V analysis point it dissipates about 176 mW, below half its rating.

## Authorities

- Texas Instruments, *TPS25947 Load Switch With Adjustable Current Limit and
  True Reverse Current Blocking*, SLVSFC9C.
- Texas Instruments, *TPS2553/53-1 Precision Adjustable Current-Limited Power-
  Distribution Switches*, SLVS841E.
- WCH, *CH224K/CH224D USB PD Sink Controller User Manual*, V2.1.
- USB Type-C sink attach-capacitance constraint as summarized in TI Type-C
  power-path guidance; the first directly exposed board capacitor is 100 nF.

The executable bounds and topology are owned by `03_src/rules/power_tree.yaml`,
`protection_paths.yaml`, and `electrical_invariants.yaml`; ADR-0014 records the
supersession scope.
