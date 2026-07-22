# 02_parts — status & deviations register

## Deviations from contract

| Part | Deviation | Why | Before bring-up |
|---|---|---|---|
| 0805W8F1001/2001/3302/4701/5101/1002/1003/5603 T5E, CC0805KRX7R9BB104, CL21A106KAYNNNE, CL21B105KBFNNNE, KT-0805G | No per-value PDF committed (commodity series parts); electricals from live JLC attribute checks (dated in each `verified:`). One series sheet IS committed under 0805W8F100JT5E/ as the family reference. | Extraction cost exceeds value for series passives (fleet precedent: shitty-kitty). | Values re-verified at BOM stock-check time by the fab flow. |
| SS310, SMCJ33A, SMBJ33A, B5819W, 0466002.NRHF, GRM32ER71H475KA88L, CL31A226KAHNNNE, SWPA6045S220MT | PDFs are LCSC-hosted uploads of the actual manufacturer sheets (BORN/MDD/CJ publish primarily through LCSC; Murata/Samsung/Littelfuse/Sunlord canonical URLs block scripted fetch). doc_id = LCSC upload id. | Vendor CDNs block non-browser downloads; LCSC copy is the sheet JLC assembles against. | Electricals cross-checked against JLC attribute data 2026-07-18 (matched). |
| B5819W | Dir name drops the "SL" plating suffix; LCSC model string is "B5819W SL" (C8598). | Space in the model string is path-hostile; suffix is plating/packaging. | BOM carries the LCSC code; no action. |
| 3557-2 | "Datasheet" is the Keystone M65 catalog page 41 (Keystone publishes catalog pages, not per-part sheets). | Vendor practice. | Hole pattern verified against the JLC/EasyEDA footprint at twin stage. |
| J7/J8, J1–J6 (studs) | M5/M4 ring-lug studs are bare plated holes (project footprints `bbar:Lug_M5`/`Lug_M4`), no purchasable part, excluded from BOM. Bolt hardware user-supplied. | The plated hole IS the terminal (ADR-0005). | Torque specs + hardware list in ORDER_README. |
| Port fuses | User-supplied ATO/ATC blades, ≤30 A; not in BOM (ADR-0005). | User-replaceable protection (A3). | ORDER_README fuse-not-included note. |
| J10 debug header | DNP (pads only); no part entry. | Bench-only UART fallback; USB covers normal use. | none |

## Notes

- INA238 selection hinges on abs-max (85 V) vs the SMCJ33A clamp — do not
  substitute INA226/INA3221 on price (ADR-0003).
- SS310 is used in two polarized positions (D7 series block, D11 buck
  catch); pad-1-cathode asserts live in generate_board (audit I9).
