# 02_parts — status & deviations register

## Deviations from contract

| Part | Deviation | Why | Before bring-up |
|---|---|---|---|
| MPR121QR2 | PDF not fetched from the canonical NXP URL (`nxp.com/docs/en/data-sheet/MPR121.pdf` returned an HTML "page not available" error to non-browser fetches, 2026-07-17). Committed copy fetched from `https://cdn-shop.adafruit.com/datasheets/MPR121.pdf`. | NXP CDN blocks scripted downloads. | Copy is self-consistently MPR121 Rev. 4, 02/2013 (latest known rev). If NXP becomes reachable, re-download and confirm sha256 `f4416f3c...` matches; if it differs, STOP and re-verify pins per contract. |
| TMC2209-LA-T | PDF not fetched directly from analog.com (`analog.com/media/en/technical-documentation/data-sheets/TMC2209_datasheet_rev1.09.pdf` aborted every scripted fetch with HTTP/2 INTERNAL_ERROR / stalled over HTTP/1.1, 2026-07-17). Committed copy fetched from the Wayback Machine snapshot of that exact URL. | analog.com CDN blocks non-browser downloads. | Copy is self-consistently "Rev. 1.09 / 2023-FEB-16" on every page header (86 pp), sha256 `1d9e8eed...`. If analog.com becomes reachable, re-download and confirm the hash; if ADI has published a newer rev, re-verify pins per contract before ordering. |
| LIS2DH12TR | PDF not fetched from the canonical ST URL (`st.com/resource/en/datasheet/lis2dh12.pdf` refused scripted fetch, 2026-07-17). Committed copy fetched from GitHub mirror `QuecPython/QuecPython_lib_bundles` (libraries/lis2dh12/LIS2DH12.pdf). | ST resource server blocks non-browser downloads. | Copy is DocID025056 **Rev 6** (May 2017); ST has since published later revisions (Rev 7+). Facts extracted (pinout, RES-to-GND, CS/SA0 straps, decoupling) are stable across known revs, but re-verify against the current ST rev when reachable before ordering. |
| SMBJ16A | PDF is the RUILON **SMBJ series** sheet (rev DEC-16), not part-specific. | Vendor publishes only the series sheet; the SMBJ16A row (p.2) is extracted into `part.yaml`. | None — row + cathode-band figure verified. |
| SMD1812P200TF16 | PDF is the RUILON **SMD1812 series** sheet (SP-PTC-008 ver A6). | Series-only publication; part row (p.4) extracted. | None. |
| SWPA6045S100MT | PDF is the **Sunlord SWPA catalog** (revised 2023/09/01), image-only scan with no text layer. | Series-only publication; 6045S 10uH row (p.13) read from a 200-dpi zoom render. | None — row values cross-checked (Isat 3.2/3.5A, Irms 2.45/2.7A, DCR 48 typ/62 max mR). |
| KH-2.54PH180-1X13P-L11.5 | PDF is a **generic 1xN series drawing** (Rev A 2019/09/19); 13-pin column extracted. | Kinghelm publishes one drawing per family. | None — generic 2.54mm header, stock KiCad footprint fits (phi1.02 hole vs 1.0 drill: standard). |
| B4B-XH-A | Dir name omits the finish suffix; orderable/LCSC-listed MPN is `B4B-XH-A(LF)(SN)` (C144395). PDF is the JST **eXH catalog** (series sheet, no rev string; 2021-01 upload date used as revision). | `(LF)(SN)` is a plating/label code, not a different part; parentheses are hostile in paths; JST publishes catalog-level docs only. | BOM must carry `B4B-XH-A(LF)(SN)` as the order string. |
| DC-005C-20A | Declared footprint `Connector_BarrelJack:BarrelJack_Horizontal` matches pin NUMBERING/roles (1=tip, 2=sleeve, 3=switch) but **not hole positions**: KiCad pin2 at 6.0mm vs jack 6.65mm axial; pin3 axial 3.0 vs 2.55mm; stock slots only 1.0mm wide. | No stock KiCad barrel-jack footprint matches the DC-005C drawing exactly (closest: `BarrelJack_Kycon_KLDX-0202-xC_Horizontal`, still 0.45mm off on pin 2). | **BLOCKER for layout**: make a project footprint with 1.5x0.8mm slots at (0,0)/(6.65,0)/(2.55,4.70) per the drawing before routing; do not order with the stock footprint. |
| 1206W4F150LT5E | No PDF committed (commodity series thick-film resistor); electricals taken from the JLC parts-library search result for C37936, 2026-07-17. | Extraction cost exceeds value for a series chip resistor; specs recorded in `part.yaml`. | None — value/tolerance/power re-verified at BOM-stock check time by the fab flow. |

## Notes

- `RVT100UF25V67RV0011/` is contract-compliant (KNSCHA spec-for-approval PDF
  committed) but mind the polarity trap recorded in its `part.yaml`: KiCad
  `CP_Elec` marks pad 1 "+", while the part's can-top band marks the NEGATIVE
  side — opposite ends.
- Stock/price figures appear only inside dated `sourcing.note` strings, never
  as fields (contract "Forbidden").
