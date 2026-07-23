# Fresh red-team — FIX-PASS re-review (crow-mic-pod-v2, 2026-07-23)

provenance:
  trigger: the fix pass made MATERIAL changes (D3 populate, J1 footprint
    certification, silk relocation, J1 GND SOLID, MK1 LCSC blank, route reuse
    reproducibility fix) — a FRESH independent zero-context 4-lens red-team was
    run on the FIXED board (NOT a fix-confirmation), reusing the original
    4-lens structure.
  reviewers: 4 zero-context adversarial sub-agents (general-purpose), each given
    ONLY 04_kicad + 01_docs + 02_parts + 03_src (NOT 08_reviews, to stay
    unbiased by the prior review). Full transcripts: session task outputs
    (topology, layout/thermal, pin, render/twin).
  method: netlist-traced ratings recompute; pcbnew-measured layout; datasheet-
    figure pin derivation; jlc_twin + render cross-check against board nets.

## CONSOLIDATED PRE-SEAL VERDICT: ORDER / SHIP — 4/4, NO NEW P0 OR P1.

| Lens | Verdict | New P0/P1 |
|---|---|---|
| topology / protection / ratings | **ORDER** | none |
| layout / thermal / manufacturability | **ORDER** | none |
| pin (datasheet-figure derivation) | **7 PASS / 0 FAIL** | none |
| render / digital-twin / BOM-CPL | **SHIP** | none |

The 3 original P0s are resolved: **P0-A/B (PoE injection)** is now the
documented, USER-signed-off accepted waiver ADR-0005 (both topology + the
docs classify it as accepted, not a new blocker); **P0-C (J1 footprint
mirror)** is independently CERTIFIED CORRECT (not mirrored) by the fresh pin
lens via contact-1-side + row-parity + chirality; **P0-D (D3 BOM-without-CPL)**
is resolved by populating D3 (now in both BOM and CPL, twin-verified).

## Verified clean (fresh, this pass)
- **DRC 0/0/0** re-run independently by the layout lens (not trusting cache).
- Gain 3.0 V/V, VMID 2.500V, AC-coupling/DC-bias, D1/D2/D3 directionality,
  beep-loop galvanic isolation — all re-confirmed from the netlist.
- E-MARGIN: 4.997V at the load, no brownout. E-OFF: N-A (external supply).
- J1.7/8 zone-connect = SOLID (FULL) verified physically; NOT-ETHERNET banner
  + full legend adjacent to & legible over J1; NPTH post clearance >=1.0mm;
  tier-floor geometry intact (no silent tier bump).
- pin lens re-derived the RJHSE-5384 footprint independently → NOT mirrored.
- jlc_twin exit 0, D3 now renders as an ordinary populated part.

## New findings — all P2 (non-blocking), dispositions
| ID | Lens | Finding | Disposition |
|---|---|---|---|
| FP-1 | topology | ARCHITECTURE.md shield-bond wording said "bond at pod end" — contradicts ADR-0001 + the board (shield FLOATS at pod, single-point at central). A builder reading it could create the 6× ground loop ADR-0001 prevents. | **FIXED** (this pass): ARCHITECTURE.md interface table + protection posture item 4 now state FLOAT-at-pod / bond-at-central. |
| FP-2 | topology | Net-name split: docs say `GND_AUDIO`, netlist/invariants/board say `GND`. | **FIXED** (this pass): added an explicit alias note (cable-contract `GND_AUDIO` = board net `GND`, same node). |
| FP-3 | render/twin | Stale D3 twin-adjudication note ("D3 remains DNP"). | **FIXED** (this pass): note updated — D3 populated, ordinary BOM code. |
| FP-4 | render/twin | J1 keeps its C99* consign code in the BOM (vs MK1 blanked). | **ACCEPT** — a C99* IS a JLC (consign) code, unlike MK1's MPN; J1 is a documented hand-solder line (exclude_from_pos, MANIFEST not_assembled). Confirm at order preview. |
| FP-5 | render/twin | BOM Comment column echoes the LCSC code for specialty parts (cosmetic). | **ACCEPT** — JLC keys on LCSC+designator; pre-existing exporter behavior, non-blocking. |
| FP-6 | layout | AUDIO_P/N copper ~2:1 length asym (~0.25 ns skew); D1 stub ~13 mm; beep loop ~12 mm. | **ACCEPT-WITH-EVIDENCE** — low-Z op-amp OUTPUTS at audio freq; slow 4 kHz beep drive; all documented in part.yaml / prior dispositions. Note for next spin. |
