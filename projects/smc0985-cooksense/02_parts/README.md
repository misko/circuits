# 02_parts — folder status + deviations register

One directory per MPN actually used (or ADR-recorded alternate), holding the
datasheet + facts extracted from it. See `contracts.md` for the schema and the
three-tier rule (NO committed stock). This register lists every departure from
that contract, with why + what must happen before bring-up.

## Deviations register

| Part | Deviation | Why | Before bring-up |
|---|---|---|---|
| `PCC-SMP-K` | NOT in the JLC/LCSC library (`sourcing.lcsc: ""`) → HAND-SOLDER, global sourcing (DigiKey/Newark/SparkFun). | Omega/Newport Type-K miniature jack; LCSC stocks no Type-K thermocouple connector (searched 2026-07-22). Same posture as `DIP05-1A72-13L`. | Confirm hand-solder in the assembly plan; OR fall back to the JLC-stocked `KF350-3.5-2P` screw terminal (C474892, already J5) — loses the keyed alloy jack + TO-92 CJC mount. |
| `PCC-SMP-K` | `footprint: cookhub:Omega_PCC-SMP-K_TypeK_PCpin` does NOT exist yet (no KiCad std footprint for this connector). | 2 contacts @ 7.9mm (0.31") + 4× ø1.77mm (0.070") PC/bracket holes — must be drawn from the Omega drawing (spec p.2). Same pattern as `cooksense:Relay_StandexDIP_1A_pinout13`. | Draw `cookhub:Omega_PCC-SMP-K_TypeK_PCpin` from Omega PCC-OST-SMP spec p.2; twin-verify pad/hole positions; polarity + / − from the shell marking. |
| `AQY212GS` | `Package_SO:SOP-4_3.8x4.1mm_P2.54mm` land is drawn for the CPC1017N body (3.8×4.1mm, 5.5mm pad-center span); the AQY body is 4.4×4.3mm and the datasheet land is ~6.0mm span. | Nearest existing KiCad std footprint by pin count + 2.54mm pitch; pitch matches, row span is ~0.5mm narrow. | Twin / JLC-CAD confirm the SOP-4-2.54mm land vs Panasonic p.4 recommended pad; widen to a `cookhub:` variant if reflow yield needs it. |
| `MCP3208-CI-SL` | Dir/`mpn` use the dash rendering `MCP3208-CI-SL`, not the Microchip ordering string `MCP3208-CI/SL`. | A `/` cannot be a filesystem path component; LCSC's own slug is `MCP3208-CI-SL` (C16939). `mpn == dirname` is preserved. | None — same orderable part (C16939). Canonical slash form recorded in `datasheet` + gotcha. |

## Notes

- `AQY212GS` is the ADR-0006 selector-relay ALTERNATE (default selector = reed
  `DIP05-1A72-13L`; PRESS/STOP stay reed). Its `part.yaml` exists so the
  reed-vs-PhotoMOS selector call can be made from stock + price at parts stage.
- Committed PDFs present for all three (used/candidate parts): `DS21298E.pdf`,
  `AQY212GS_Panasonic_GU-SOP.pdf`, `PCC-OST-SMP_spec.pdf` — `sha256` in each
  `part.yaml` matches the committed file.
