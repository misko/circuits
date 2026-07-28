# Journal — 02 parts (pluto-rx2-8way)

## 2026-07-27 23:30 — start (D-SPEC sourcing spike)

- did: opened the timeboxed D-SPEC sourcing spike for the spec-critical
  function — the 8-way selector. Constraints inherited from stage 0: parallel
  3-bit control (SPI excluded by arithmetic, 1-10 us against a 4.27 us blanking
  budget), single positive 3.3 V supply, 70 MHz-6 GHz, AoA-grade constant phase.
- result: `skills/pcb-design/references/proven-parts.yaml` does not exist; the
  ledger is `skills/kicad-pcb/references/proven-parts.yaml` and contains NO RF
  switch, no SPDT/SP4T/SP8T and no SMA connector. Neither the sibling board's
  BGS12WN6 nor its KH-SMA-KE-Z was ever harvested into it, so this board pays
  the research again. **Recorded as a ledger gap, not worked around.**
- next: part-universe search.

## 2026-07-28 00:10 — iterate 1 (the monolithic SP8T universe)

- did: keyword-swept the JLCPCB parts library (unofficial
  `selectSmtComponentList`) for SP8T-class parts and checked every named
  candidate; web-verified control scheme and supply from manufacturer PDFs.
- result: **exactly one family clears all three hard constraints and is stocked
  in depth — pSemi PE424xx.** `PE42482A-X` (LCSC **C5121458**, stock **1498**,
  **$6.09** @1+, QFN-24 4x4): SP8T, **10 MHz-8 GHz** with min/max columns at
  both band ends, **3-bit parallel** (V1 MSB / V3 LSB, V4 all-off, LS polarity),
  **single 2.3-5.5 V** rail, 227 ns typ / 290 ns max switching, **absorptive**.
  Everything else fails on one of: throw count (PE42462 is an **SP6T**,
  SKY13322-375LF is an **SP4T**, MASW-008322 is an SPDT), band (SKY13418-485LF
  is 100 MHz-3.8 GHz), supply (HMC321ALP4E needs a negative control rail), or
  stock (HMC321/HMC322 at 0; PE42582A-X at 7; ADRF5040 at 27).
- next: cost the SPDT tree honestly against it.

## 2026-07-28 00:40 — iterate 2 (the SPDT tree, refuted)

- did: worked the 7x SPDT binary tree (4+2+1) from the BGS12WN6 Rev 2.9 tables.
  Re-fetched the vendor PDF independently; sha256 matched the sibling project's
  recorded `6cd5d36c…` byte for byte.
- result, three findings in order of weight:
  1. **The "no decoder" claim is TRUE.** Verified against Table 12
     (`CTRL=0 -> RFIN-RF1`, `CTRL=1 -> RFIN-RF2`): with RF1 on the even/lower
     branch and RF2 on the odd/upper branch at every node, stage-1 on b0,
     stage-2 on b1, stage-3 on b2 selects antenna `4*b2 + 2*b1 + b0`
     algebraically. Zero logic. But it is **not a differentiator** — PE42482's
     own truth table is also a straight 3-bit binary with no decoder.
  2. **Isolation does NOT add across tree stages, and that kills the tree.**
     For each of the three stages there is exactly one deselected antenna whose
     leakage crosses only ONE switch: the sibling at stage 1, the stage-1 output
     that lands on stage 2's deselected port, and the stage-2 output on stage
     3's. Three of the seven deselected antennas therefore sit at a SINGLE
     switch's isolation. At 6 GHz that is BGS12WN6's `ISO_RFIN-RFx` = **20 dB
     min**, and the aggregate leakage-to-signal ratio is **-14.6 dB worst-case /
     -19.6 dB typical** against PE42482's **-21.5 / -30.7 dB**. A -14.6 dB
     coherent interferer is up to **10.8 deg** of AoA phase error.
  3. **BGS12WN6 IS STOCK 0** at LCSC on all three catalogue codes (C1854968,
     C27749420, C9900027832), live 2026-07-28. The only stocked BGS12 is
     `BGS12P2L6E6327` (C3312945, 1225) — the part the sibling board explicitly
     REFUTED for having no published RF row at 70 MHz or 6 GHz and a 3.4 V VDD
     ceiling. So the tree would have to be built seven times over on the
     uncharacterized part.
  Cumulative IL, 3 switches in series, MAX column: 0.75 dB @ 70 MHz,
  ~1.20 dB @ 3 GHz (**ESTIMATED** — 2690-3300 MHz is a characterization HOLE
  with no published row), **3.00 dB @ 6 GHz** — worse than PE42482's 2.3 dB
  worst-path max, before the two extra inter-stage interconnects.
- next: the pickoff arithmetic.

## 2026-07-28 01:10 — iterate 3 (the T2 resistive pickoff, arithmetic checked)

- did: re-derived the three pickoff formulas from the circuit rather than
  checking the arithmetic of the given ones, then evaluated parasitics.
- result: **all three of the brief's formulas and all three of its numbers are
  CORRECT.** `V_node/V_node0 = 1/(1 + Z0/(2*Rp))` falls straight out with
  `Rp = Rs + 50`, so `IL = 20log10(1 + Z0/(2*Rp))`; both tap and main port hang
  off the same node so the tap ratio is exactly `50/Rp`; and `Zin = 50 || Rp`
  gives the return loss. At `Rs = 450`: tap **-20.000 dB**, IL **0.4238 dB**,
  RL **26.44 dB** (VSWR 1.100). Claimed -20 / 0.42 / 26.4. No correction owed.
  **But 450 ohm is not a stocked value** — not E24, not E96, not E192. The
  nearest JLC **Basic** 0402 is **470 ohm (C25117, 1.88 M in stock)**: tap
  -20.34 dB, IL **0.408 dB**, RL **26.77 dB** — strictly better on both of the
  numbers that cost anything.
  **The "flat DC-6 GHz" claim in T2 is the one thing that does NOT hold.**
  Vishay TN 60107 Table 1 p1 gives an 0402 wrap-around chip C = 0.0392 pF /
  L = 0.1209 nH (CITED for the class, ESTIMATED for this thick-film part:
  0.04 +/- 0.02 pF). That shunt C across a 470 ohm arm drops |Z| from 470 to
  ~386 ohm at 6 GHz, so the tap rises: -20.34 dB at DC, -20.28 @ 1 GHz,
  -19.84 @ 3 GHz, **-18.60 @ 6 GHz — a +1.74 dB tilt**, within 0.5 dB only to
  ~3 GHz. The **main line is unaffected** (0.408 -> 0.433 dB, RL 26.8 -> 25.1),
  which is the half that matters, and the tilt is smooth and monotonic with no
  resonance — a characterizable path response, exactly the class brief D4
  already commits to publishing.
  **Fix if wanted: split the arm.** 2x 220 ohm (C25091, also Basic) halves C_p
  to ~0.020 pF and cuts the tilt to **~0.5 dB** for one extra 0402.
- next: escape/tier and the dossiers.

## 2026-07-28 01:30 — finish (D-ESC / D-TIER, dossiers)

- did: ran `escape_check.py` on every candidate package; wrote three
  `part.yaml`; verified both pin maps from rendered figures.
- result: **`jlc_4layer_advanced` either way** — QFN-24 at 0.5 mm pitch and
  TSNP-6 at 0.4 mm both land there, so D-TIER is a WASH between the two
  architectures and cannot be used to break the tie. SMA (connector, 5.08) and
  the 0402 are `jlc_2layer_default`. PE42482 escape budget: worst side is
  pins 7-12 (GND, VDD, V1-V4) at **5** — the digital side, with no RF on it,
  which is also where the RP2040 belongs.
  Pin maps read VISUALLY from rendered figures: PE42482 Figure 22 (PDF p20) at
  300 dpi cross-checked against Table 8 on the same page; KH-SMA-KE-Z drawing
  sheet 2/2 at 200 dpi.
  D-LAYOUT: pSemi publishes no prose layout section but **Figure 21 (PDF p19)
  is a routed reference board** — octagonal, QFN at the geometric centre, nine
  equal-length radial 50 ohm traces to edge launches, ground-via fences between
  them, the whole digital section on the pin-7..12 edge escaping on the bottom
  layer. That radial star IS the AoA floorplan: equal length is equal phase by
  construction.
- result (the number that decides it): **PE42482 publishes RELATIVE INSERTION
  PHASE with min/typ/max** (Table 3, PDF p8) — at 6 GHz, RF2-RF1
  -9.4/-2.8/+3.8 deg, RF3-RF1 -11.2/-5.7/-0.3, RF4-RF1 -35.8/-26.3/-16.9.
  **BGS12WN6 publishes no phase data of any kind** (the word does not occur in
  the document). Brief D4 makes the 8-path phase deltas a published, measured
  release artifact; only one of these two parts gives that artifact a vendor
  bound to be checked against.
- next: ADR for T2 (D3 confirm) and the D-TIER line; then stage 1. Two things
  are OWED and named in `02_parts/README.md`: the KH-SMA-KE-Z and 0402 PDFs,
  and port-to-port isolation across ten SMA barrels on one laminate — which
  bounds the AoA leakage budget from below independently of the switch.
