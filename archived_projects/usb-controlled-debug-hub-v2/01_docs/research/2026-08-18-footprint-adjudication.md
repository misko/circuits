# Exact-footprint adjudication: USB-C PD power cell

Date: 2026-08-18  
Stage: footprint authority before placement  
Scope: U_PD (CH224K), U_PD_BUCK (TPS56637RPAR), and L_PD (MWSA0804S-3R3MT)

## Decision

The source footprints are owned by this project and are not accepted solely because a JLC/EasyEDA CAD record exists. Each land pattern was compared against the exact manufacturer package drawing before placement.

| Ref | Exact identity | Manufacturer authority | JLC CAD disposition | Source result |
|---|---|---|---|---|
| U_PD | WCH CH224K, ESSOP-10 EP | WCH CH224 manual v2.1 physical drawing: 4.9 x 3.9 mm body, 6.0 mm lead span, 1.0 mm pitch | Pad geometry agrees with the exact C970725 package and is retained; courtyard, fab, model path, and identity are source-owned | `WCH_CH224K_ESSOP10_EP` |
| U_PD_BUCK | TI TPS56637RPAR, RPA0010A | TI SLVSEG1A pp.28-30, drawing 4224047/A | Asymmetric HotRod lands agree with the exact package drawing and are retained; documentation/model path are source-owned | `TI_RPA0010A_VQFN-HR-10_3x3mm` |
| L_PD | Sunlord MWSA0804S-3R3MT | Sunlord MWSA-S catalog p.2: I=2.75 mm, J=4.00 mm, H=5.50 mm | JLC CAD lands were 2.10 x 5.50 mm at +/-3.90 mm and do not match the manufacturer recommendation; those lands are rejected | `Sunlord_MWSA0804S`, pads 2.75 x 5.50 mm at +/-3.375 mm |

The exact JLC STEP bodies are retained for mechanical visualization. A STEP model is not treated as land-pattern authority.

## Placement consequences

- U_PD CC1/CC2 and its VDD bypass remain immediately behind J_POWER.
- U_PD_BUCK input ceramics, bootstrap capacitor, SW land, L_PD, output capacitors, AGND/PGND join, and Kelvin feedback must follow TI Figure 34.
- No USB differential pair or clock route may pass through or below the PD buck switching cell.
- Placement-only 3D views are a human gate before routing; passing model registration does not approve connector direction.
