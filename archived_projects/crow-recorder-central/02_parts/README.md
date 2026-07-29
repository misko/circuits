# 02_parts — status & deviations register

Six entries created 2026-07-17 (power tree + USB ESD + T/RH sensor for crow-array-central).
Format per `crow-array-pod/02_parts/contracts.md`.

## Deviations

| # | Part | Deviation | Why | Before bring-up / order |
|---|------|-----------|-----|------------------------|
| 1 | AP61102Z6-7, XC6227C331PR-G, TCR2LF18,LM(CT), MWSA0402S-1R0MT | PDF fetched from LCSC-hosted mirror, not the vendor URL | diodes.com 404s the direct asset URL, torexsemi.com is Akamai-gated, Toshiba download is session-gated; LCSC mirrors are the vendors' own PDFs (doc ids/revisions match: DS42004 Rev 6-2, ETR03054-006, 2014-11-06, Sunlord rev 2023/09/13) | optional: re-verify sha256 against a browser-fetched vendor copy |
| 2 | TCR2LF18,LM(CT) | 0 stock at JLC/LCSC (C150173) on 2026-07-17 | Toshiba part thinly stocked there | either confirm restock or approve one of the pin-compatible alternates recorded in its `sourcing.alternates` (LP5907MFX-1.8/NOPB C92498 preferred for low noise) and record the swap as a decision |
| 3 | XC6227C331PR-G | Package is SOT-89-5, **not** SOT-25 as the design brief assumed | Torex suffix decode (datasheet p.2): MR-G=SOT-25, PR-G=SOT-89-5 | decide: keep PR-G (SOT-89-5 footprint, better thermals, 268 stock) or switch BOM to XC6227C331MR-G (SOT-25, C216640, 2719 stock) — new 02_parts entry if swapped |
| 4 | TPD4EUSB30DQAR | KiCad `Package_SON:USON-10_2.5x1.0mm_P0.5mm` differs slightly from TI DQA0010A land example (pad 0.3 vs 0.2 mm wide; outer span 1.32 vs ~1.4 mm) | closest stock footprint; pitch and pad count match | acceptable for JLC assembly; derive a custom pad from DQA0010A if strict IPC wanted |
| 5 | AP61102Z6-7 | Brief said "1.5A buck" — the part is a **1A** converter (DS42004 title & EC table) | datasheet fact | keep rail budgets <= 1A per buck |
