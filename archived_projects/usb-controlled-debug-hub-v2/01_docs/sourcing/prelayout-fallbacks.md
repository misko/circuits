# Pre-layout sourcing fallbacks

Status: contingency research only — no substitution authorized  
Exact circuit subject: `3015d410603e89d1d3936f0b144b67deeb9997964589eff704fbfddbeb21c4e9`  
Observed: 2026-08-19

The exact 53-code request remains authoritative. Public LCSC/JLC catalog stock
is only a negative filter and can differ from the JLCPCB assembly pool. A
fallback may replace an exact request row only after its official authority,
pinout, geometry, ratings and economics have been admitted to source and all
affected gates have been rerun. Silent uploader substitution is forbidden.

| Exact requested identity | Risk and preferred response | Unapproved candidates if exact allocation fails |
|---|---|---|
| `C1985204`, Kyocera `CX3225SB24000H0FLJCC` | Public API returned 8 for five required. Prefer exact-part consignment/manual procurement because oscillator identity is load-bearing. | `C251612`, `C5181479`, `C164058` are catalogued as 3225-4P, 24 MHz, 12 pF parts with deeper public stock. Before selection, verify official ESR, tolerance plus stability, 1/3 signal and 2/4 ground assignment, exact land geometry and the existing load network. |
| `C3708426`, Nexperia `PESD2USB3UX-TR`, five per board | Public API returned 66 for 25 required. Preserve the exact part where JLC can allocate it. | `C3709087` / Nexperia `PESD2USB5UX-TR` is the preferred candidate because Nexperia specifies SOT23, USB 2.0 suitability and 0.47 pF capacitance. `C3704436` / `PESD2USB3UV-TR` is another same-package candidate but its official 1 pF maximum capacitance must be charged into the already narrow USB channel budget. Both require exact pin/land verification and new signal-integrity evidence. |
| `C640876`, Microchip `MCP2221A-I/SL` | Public API returned 27 for five required. Prefer exact-part allocation or consignment. | MCP2221A TSSOP/QFN variants are functionally related but not footprint-compatible; using one would reopen placement, routing, assembly and model review. No drop-in alternate is approved. |
| `C2878936`, TI `TPS259804ONRGER` | Public API returned 122 for five required. Prefer exact allocation, preorder within an explicitly approved cost, or consignment. | No pin-compatible alternative is approved. A different TPS25980 suffix can change OVLO or retry behavior; a different family reopens current coordination, transient margin, split PowerPAD, Type VII via fill and routing. |

## Evidence boundary

- [Nexperia PESD2USB5UX-T product authority](https://www.nexperia.com/product/PESD2USB5UX-T)
- [Nexperia PESD2USB3UV-T product authority](https://www.nexperia.com/product/PESD2USB3UV-T) — the exact JLC `-TR` ordering identity still requires its own admitted dossier.
- [Microchip MCP2221A official data sheet](https://ww1.microchip.com/downloads/aemDocuments/documents/APID/ProductDocuments/DataSheets/MCP2221A-Data-Sheet-DS20005565D.pdf)
- [TI TPS25980 official data sheet](https://www.ti.com/lit/ds/symlink/tps25980.pdf)

The local ignored build evidence is under `06_build/sourcing/`:
`fallback_catalog_probe.csv`, `fallback_catalog_stock.csv` and
`fallback_catalog_stock.json`. These files prove neither assembly availability
nor acceptable MOQ/surplus cost. The completed hash-bound JLC response remains
the only pre-layout release gate.
