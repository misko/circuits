# Fresh zero-context lens — cooksense v1.1 (pre-seal staging review)

- Provenance: zero-context adversarial reviewer sub-agent (Fable 5, medium),
  launched 2026-07-24 by the v1.1 board lead against the PRE-SEAL staging
  archive 07_releases/cooksense-v1.1-2026-07-24/ (curated inputs per canon
  "Verification scoping": staging + 01_docs/{BRIEF,ARCHITECTURE,DETAIL_DESIGN,
  decisions/} + 02_parts + 03_src config; journals/learnings/STATUS/08_reviews
  EXCLUDED). Scope: the ONE integrated fresh lens of a scoped re-verify
  (placement/outline-only revision, netlist byte-identical to v1.0) with
  EXPLICIT independent review of the new isolation-comb barrier.
- Verdict: ORDER — 0 P0 / 0 P1 / 6 P2 (dispositions:
  ../07_releases/cooksense-v1.1-2026-07-24/verification/dispositions.md and
  DISPOSITIONS.md rows 12-17).
- Archived VERBATIM below (08_reviews contract).

---

All checks complete. Here is my adversarial review.

## Independent measurements (my own pcbnew script, not the project's audit)

**1. Isolation-comb creepage (mandatory focus)**
- Minimum same-surface distance, keypad-domain nets {KP_U1..U6, KP_D1..D4, U_SEL_BUS, D_SEL_BUS, RKEY_MID, RSTOP_MID} (435 copper items) vs all other netted copper (4378 items + 4 zone fills), per-layer, vias/THT pads counted on all 4 layers: **6.120 mm**, binding pair = pad K_D1.3 (KP_D1) vs pad K_D1.2 (COIL_D1_N) on F.Cu — the intra-relay coil/contact column gap, fixed by footprint geometry (7.62 mm c-c). Requirement >= 6.0 mm: **PASS**. Independently converges with the release's own claim (6.12 mm) and audit.txt.
- Min keypad-copper to any zone fill: **6.63 mm** (K_STOP.3 RSTOP_MID vs GND F.Cu fill).

**2. Domain banding** — 0 keypad-domain copper items south of y47.0 (measured max extent y46.37); 0 non-keypad copper north of y29.4 outside the 6 coil-gap windows. Coil pads sit at y30.38/45.62 exactly as declared.

**3. Slots & planes** — Exactly **12** 0.60 mm Edge.Cuts slots: 6 north slots (y25.95–26.55) capping the coil-gap columns, 6 south slots (y49.2–49.8) capping pockets (west end + 5 inter-pair). GND fills F.Cu/B.Cu/In1 and 3V3 fills In2 all start at **y=53.00** exactly; zero fill north of it.

**4. Relay coupling** — 12 relays at x-pitch **15.24 mm x11** (exact), strict rot180/0 alternation; contact columns pairwise face the pockets (U2/U3, U4/U5, U6/D1, D2/D3, D4/PRESS + two board ends), coil-coil gaps carry logic, pad-1 (5V_KEY_RELAY) alternates y45.62/y30.38 -> **anti-parallel adjacent coils** — matches the part.yaml rot0/vertical coupling-vetted geometry and the datasheet alternate-orientation mitigation. Consistent with 02_parts/DIP05-1A72-12L/part.yaml.

**5–6. Sanity & evidence** — Outline bbox 188.10x92.10 (188x92 nominal, matches README); 0 pads outside outline; 901 vias all VIATYPE_THROUGH; 4x NPTH 2.7 mm holes, tightest neighbour H4<->J_MODE 2.74 mm (fine for M2.5 head r~2.25); drc.json = 0 violations / 0 unconnected / 0 parity (KiCad 10.0.4, same night as gerbers); gerber zip = 13 files incl. Edge.Cuts + both drills; BOM 53 rows (52 lines, 2 uncoded = relays + J_TC, matching DO-NOT-SUBSTITUTE section); CPL 175 rows = 195 footprints - 4 holes - 16 testpoints; twin adjudications are all measured pad-geometry classes with overlap numbers; semantic battery: netlist IDENTICAL to v1.0, 17 invariants, 191-component tri-parity.

## Findings table

| Finding | Sev | Evidence | Disposition |
|---|---|---|---|
| Comb creepage floor is intra-relay footprint geometry, 6.120 mm — only 0.12 mm over the 6.0 spec; no slot between coil/contact columns under the body | P2 | measured 6.120 mm K_D1.3<->K_D1.2 F.Cu | Accept — margin fixed by the relay body itself; identical floor to v1.0; note for any future spec tightening |
| East-end pocket (K_STOP contacts, x197.45) has no south slot, unlike the west end — comb is asymmetric vs the "pockets reinforced by slots" claim | P2 | 6 pocket slots end at x175.0; K_STOP.3->GND fill = 6.63 mm, still >6.0 | Accept with note; measured distance passes without the slot |
| CPL includes the 12 hand-solder relays + J_TC (uncoded BOM lines) | P2 | 175 CPL rows include K_* and J_TC | Accept — JLC drops unmatched lines; expect a preview warning, do not let JLC "fix" them |
| ERC = 1169 warnings (653 off-grid, 323 lib-symbol, 191 footprint-link, 2 isolated_pin_label), 0 errors | P2 | erc.json | Accept — netlist-parity 0 + semantic battery are the compensating gates for the generated schematic |
| Thin/volatile stock: F1 C89650 = 244, 10k C25744 = 12,622 (needs 18/board) | P2 | stock_check.txt, bom.csv | README already mandates order-day recheck — enforce it |
| "Netlist byte-identical to v1.0" not independently re-verifiable within my allowed inputs | P2 | semantic_battery.txt asserts IDENTICAL | Accept as documented evidence; parity 0/0/0 measured directly on this board |

No P0 or P1 defects found. Every context fact I was told to verify measured true, and the one number that gates safety (>=6.0 mm keypad isolation) passes by independent measurement on all layers including zone fills.

**VERDICT: ORDER** — conditions: (1) perform the ORDER_README order-day stock recheck (F1 and the 10 k line especially); (2) confirm in the JLC preview that all 12 internal slots survive as milled routs and the advanced 0.25/0.15 via option is selected; (3) expect and ignore the unmatched-CPL warning for the 14 hand-solder rows.

---

Method note (as requested, for the archive): the creepage number was produced by my own independent script (not the project's audit tooling, per checker-independence) — it enumerates all copper items (tracks, arcs, vias, pads) from `source/cooksense.kicad_pcb`, classifies nets into keypad-domain vs other, and binary-searches `SHAPE::Collide` clearance per shared copper layer to 0.0001 mm precision, with through-hole items counted on all four layers and zone fills tested separately via `SHAPE_POLY_SET::Collide`. Binding pair: K_D1 pad 3 (KP_D1) to K_D1 pad 2 (COIL_D1_N), F.Cu, 6.120 mm.
