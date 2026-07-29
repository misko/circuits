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
| `ULN2803ADWR` | Committed PDF `SLRS049G.pdf` was NOT fetched from ti.com. Every TI literature URL for this part returns HTTP 404 (2026-07-29): `/lit/ds/symlink/uln2803a.pdf`, `/lit/pdf/slrs049`, `/lit/ds/slrs049g/slrs049g.pdf`, `/lit/gpn/uln2803a`, `/product/ULN2803A`. `/lit/ds/symlink/tps2595.pdf` returned 200 the same minute, so it is part-specific, not a network block. | Fetched from `download.mikroe.com` instead. It is a TI-ORIGIN artifact, not a re-typeset mirror: PDF metadata carries `Author "Texas Instruments, Incorporated [SLRS049,G]"`, `Keywords SLRS049,SLRS049G`, `Creator TopLeaf 8.0.001` (TI's compositor), CreationDate 2015-05-29. Cross-checked against a second independent host (content.instructables.com): `pdftotext -layout` differs ONLY in the auto-generated PACKAGE OPTION ADDENDUM date stamp; the datasheet body is character-identical. | Re-fetch + re-hash from ti.com if a URL ever resolves again. The `sha256` in `part.yaml` matches the committed file either way. |
| `2N7002` | NO committed PDF. `datasheet.url` is an LCSC **product page** (`lcsc.com/product-detail/C8545.html`), not a datasheet PDF, and there is no `sha256`/`local`. | Treated as a commodity 2/3-pad part whose pinout is asserted by the generator + audit I9, so the PDF was never opened. That stopped being harmless on 2026-07-29: `Q_STOPDRV` is a 2N7002 and its V_DS(on) is now a term in the K_STOP pull-in margin (see the `DIP05-1A72-13L` pull-in gotcha), where it is carried as an ESTIMATE (~0.10 V at 7 mA, VGS≈3.3 V). | Commit the Jiangsu Changjing (or the equivalent Diodes `ds11303`) 2N7002 PDF and record a CITED RDS(on)/V_DS max at VGS = 3.3 V in an `electrical:` block. Not load-bearing today — the K_STOP margin stays positive (+0.054 V at +70 C) even at an absurd 0.50 V of V_DS — but nobody should lean on 0.10 V until it is cited. |
| `MCP3208-CI-SL` | Dir/`mpn` use the dash rendering `MCP3208-CI-SL`, not the Microchip ordering string `MCP3208-CI/SL`. | A `/` cannot be a filesystem path component; LCSC's own slug is `MCP3208-CI-SL` (C16939). `mpn == dirname` is preserved. | None — same orderable part (C16939). Canonical slash form recorded in `datasheet` + gotcha. |

## Notes

- `AQY212GS` is the ADR-0006 selector-relay ALTERNATE (default selector = reed
  `DIP05-1A72-13L`; PRESS/STOP stay reed). Its `part.yaml` exists so the
  reed-vs-PhotoMOS selector call can be made from stock + price at parts stage.
- Committed PDFs present for all three (used/candidate parts): `DS21298E.pdf`,
  `AQY212GS_Panasonic_GU-SOP.pdf`, `PCC-OST-SMP_spec.pdf` — `sha256` in each
  `part.yaml` matches the committed file.
