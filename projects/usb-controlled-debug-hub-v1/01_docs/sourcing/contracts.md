# contract: 01_docs/sourcing/

**Purpose** — durable procurement policy plus dated sourcing observations. The
policy is a user decision consumed by manufacturing readiness; mutable stock,
MOQ and quote facts remain hash-bound build evidence under `06_build/sourcing/`.

**Mutability** — `procurement-policy.yaml` is a hand-written durable input.
Dated sourcing observations are append-only. Never edit a past observation to
make current sourcing appear acceptable.

## Allowed

| File | What | Rule |
|---|---|---|
| `procurement-policy.yaml` | currency and per-line/aggregate limits for preorder cash, gross MOQ surplus cost, and nonrecoverable assembly excess cost | HAND-WRITTEN user policy; zero means no implicit spending authority |
| `shopping-list-<YYYY-MM-DD>.md` | dated generated distributor report | GENERATED, append-only |
| `shopping-list-<YYYY-MM-DD>.json` | machine sidecar for the dated report | GENERATED with explicit verdict |
| `parts-selection-<YYYY-MM-DD>.md` | dated part-selection interpretation | HAND-WRITTEN evidence, not executable identity |
| `two-source-qualification-<YYYY-MM-DD>.md` | dated interpretation of Q-2SOURCE evidence | HAND-WRITTEN evidence |
| `exact-parts.csv` | frozen pre-schematic candidate identities and quantities | HAND-WRITTEN selection input; no volatile claims |
| `manual_quotes.yaml` | dated manually captured distributor quotes with URL and identity | HAND-WRITTEN evidence input |
| `contracts.md` | this file | |

## Forbidden

- Volatile stock, MOQ or price presented as timeless truth.
- A quote with no exact manufacturer/MPN, URL, currency and read date.
- A substituted part recorded against the authoritative part's identity.
- Any credential.

## Audit

- Bind every schema-v2 JLC request to the exact policy bytes.
- Capture actual cart/quote subtotals at the selected quantity break.
- Grade public stock, My Parts, preorder, global sourcing and consignment as
  distinct fulfillment paths.
- Report gross surplus cost even when future reuse appears possible.
- Re-run availability, economics and final allocation on order day.
