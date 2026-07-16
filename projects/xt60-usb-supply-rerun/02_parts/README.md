# 02_parts — status & deviations register

See `contracts.md` for the rules. Each `<MPN>/` holds `part.yaml` + the
committed datasheet PDF (also in the global cache `~/.cache/datasheets/<sha256>.pdf`).

## Deviations register

Per contract, every departure from the contract is listed here with why and
what must happen before bring-up.

| # | Part(s) | Deviation | Why | Before bring-up |
|---|---|---|---|---|
| 1 | 0603WAF1002T5E, 0603WAF2202T5E, 0603WAF3001T5E, 0603WAF1001T5E, 0603WAF1003T5E | One shared SERIES datasheet (`UNIROYAL_ThickFilm_V3_2019-02-12.pdf`, same sha256 in all five dirs), not per-part sheets | UNI-ROYAL publishes only the series sheet; per-part facts derived from the 0603 rows + MPN decode (allowed deviation per contract) | Nothing — values verified against LCSC listings |
| 2 | CL31B106KAHNNNE, CL10B104KB8NNNC | Shared Samsung general MLCC catalog (Nov 2015, 84 pp), not per-part sheets | Samsung/LCSC serve the same catalog PDF for both codes; MPNs validated by decoding against the catalog's part-numbering table | Nothing — values verified against LCSC listings |
| 3 | XT60PW-M, MA25V100M6x6, CL32B226KOJNNNE | Datasheet PDFs carry no printed document ID / revision code; filenames marked `noRev` | Chinese vendor spec sheets without doc control numbers | If a re-download sha256-mismatches, treat as unknown revision change and re-verify `pins:`/limits |
| 4 | XT60PW-M | Datasheet rated current is 20 A (UL1977), below the "30 A" marketing figure commonly quoted for XT60 | The LCSC-served Amass sheet tests 20 A / 4 h / <60 C rise; 40 A instantaneous | Design VBAT path assuming 20 A continuous unless bench-verified higher |
| 5 | MA25V100M6x6 | MPN casing differs between sources: JLC lists `MA25V100M6x6`, manufacturer table prints `MA25V100M6X6` | Same part; directory follows the orderable JLC/LCSC string (C46550465) | Use C46550465 for ordering; either MPN string matches |

## Polarity facts recorded (do not re-derive)

- **XT60PW-M**: KiCad footprint pad 1 = "−" blade, pad 2 = "+" (7.2 mm away).
  Triple-sourced; see `XT60PW-M/part.yaml` gotchas for the evidence trail.
- **MA25V100M6x6**: KiCad `CP_Elec_*` pad 1 = POSITIVE; the beveled base
  corners of the can are on the + side. Do not trust the colored top mark.
- **KT-0805G / NCD0805R1**: KiCad `LED_0805_2012Metric` pad 1 = CATHODE.
  KT-0805G's own drawing numbers 1=anode (mismatch — see its part.yaml);
  cathode end is the green-marked end on both LEDs.
