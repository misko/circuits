# R3 Q-2SOURCE delta — 2026-08-02

This is dated pre-selection evidence, not an order-day allocation promise.
Stock must be refreshed before payment. The exact MPN is the identity; a value,
tolerance, temperature-coefficient, or suffix variant does not count.

| exact MPN | role | Mouser API stock | DigiKey product-page stock | LCSC product-page stock | result |
|---|---|---:|---:|---:|---|
| `TNPW06034K64BEEA` | LM74810 OV-divider bottom leg, R3 | 11,128 | 8,323 | exact `C2078999`, stock 15 | Q-2SOURCE PASS: Mouser + DigiKey; LCSC is a thin third pool |

The Mouser observation came from a no-cache exact-plus-broad Search API run at
2026-08-02 12:06 UTC. The chosen catalog record was exact manufacturer MPN
`TNPW06034K64BEEA`, Mouser number `71-TNPW06034K64BEEA`, minimum/multiple 1/1,
at $0.26 for quantity one. Mouser reported factory stock 0 and a 154-day lead,
so the distributor stock is the whole near-term pool.

The DigiKey observation came from the exact product page recorded in
`manual_quotes.yaml`, not a search-results snippet. The LCSC exact product page
identified manufacturer MPN `TNPW06034K64BEEA` as `C2078999` and showed 15 in
stock. Five boards require five pieces, but release qualification relies on the
much deeper independent Mouser and DigiKey pools rather than that thin JLC/LCSC
inventory.
