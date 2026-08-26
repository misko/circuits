# ADR-0017 — accept public catalog evidence for the pre-layout checkpoint

Status: accepted
Date: 2026-08-19

## Context

The exact quantity-five sourcing request contains 53 JLC/LCSC codes and is
bound to circuit SHA-256
`e4a1bbc31c38d0a517834234fd2b190af1af34699b76841324892be2e485bd14`.
The JLC public parts endpoint returned 53/53 catalog lines with stock at least
five times the per-board quantity on 2026-08-19. The account-bound PCBA
component-matching response was not captured, and the user directed the
project to use the public result for now.

The lowest-headroom public observations were:

- `C1985204`: 8 catalog units for 5 required, with an endpoint-reported MOQ
  of 11;
- `C3708426`: 66 catalog units for 25 required;
- `C640876`: 27 catalog units for 5 required;
- `C2878936`: 122 catalog units for 5 required.

Catalog inventory is volatile and is not proof that JLC has allocated a part
to a particular PCBA order.

## Decision

- The fresh 53/53 public-catalog PASS is sufficient to close only the
  **pre-layout negative-filter checkpoint** and allow PCB regeneration,
  placement, routing and verification to proceed.
- Do not populate `prelayout_response.csv` with invented `AVAILABLE` evidence
  and do not describe public catalog stock as PCBA allocation.
- Preserve the exact requested LCSC identities while routing. A substitution
  still requires its normal dossier, pin, footprint, electrical and model
  review before it can enter source.
- The final release remains `DO-NOT-ORDER` until its exact BOM clears the
  logged-in JLC PCBA component-matching/uploader review. That order-time
  evidence must cover actual selected parts, shortfalls, MOQ/preorder cost,
  rotations, polarity and assembly previews.
- Treat `C1985204` as the first order-time sourcing risk. If it does not clear,
  prefer exact-part consignment; do not silently select a catalog substitute.

## Consequences

This decision avoids blocking layout on unavailable account/API automation,
while keeping the manufacturing claim honest. It accepts some bounded
backtracking risk: a later PCBA shortfall may require a reviewed substitution
and corresponding placement or routing revision. It does not waive the final
uploader echo or authorize preorder/MOQ expenditure.

## Evidence

- `06_build/sourcing/prelayout_request.json`
- `06_build/sourcing/catalog_stock_check_programmatic_2026-08-19.json`
- `06_build/sourcing/catalog_stock_check_programmatic_2026-08-19.csv`
- User directive on 2026-08-19: “lets just use the public for now”
