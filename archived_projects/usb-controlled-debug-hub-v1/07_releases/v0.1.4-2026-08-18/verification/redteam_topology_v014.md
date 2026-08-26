# v0.1.4 topology and sourcing-delta red-team

design_verdict: SOUND
order_verdict: BLOCKED-SOURCING
- PCB subject SHA-256: `c5cd719571e216224c83aca142ac84e1f11facdfb48b1bcb771c9d5b97c06e68`

This is a sourcing-only supersede of v0.1.3. The exact PCB and CPL are
unchanged, the normalized Gerber/drill payload is unchanged, and the BOM keeps
the same 33 designator groups in the same order. Ten rows change only paired
MPN/LCSC identities. Source/BOM parity and all 18 coded passive-value checks
pass; no electrical value, footprint, pin, net, topology or firmware changes.

The active substitutions restore exact qualified design identities
`TPS2557DRBR / C130056` and `74LVC08APW,118 / C6053`, both already used in
v0.1.2. The passive substitutions retain the reviewed nominal value,
tolerance, dielectric/voltage class where applicable, and land pattern.

Blocking order finding: the exact final 33-row BOM has no completed schema-v2
JLCPCB receipt. Availability, resolved identity, fulfillment path, MOQ/order
multiple, preorder cash, gross surplus cost and assembly excess cost are
therefore unproven. The zero-implicit-spend policy makes this a deliberate
DO-NOT-ORDER checkpoint rather than an inferred pass from public stock.
