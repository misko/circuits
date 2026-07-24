# journal: 02 parts

## 2026-07-22 — start
- did: entering parts stage from the committed commission (6272aa0). Driving
  the CookSense board (A+B merged, ADR-0001; firmware-less, ADR-0002).
- plan: (1) derive BOM, split ledger-hits (cook-hub v1.0 reuse) vs new; (2)
  fan out max-effort research on the new multi-pin parts -> part.yaml each
  (pinout from datasheet FIGURE + verified: + escape_check block + layout:
  block for every IC/power-sense per P-LAYOUT + LCSC + alternates); (3) merge,
  escape_check + policy_audit P-ESC/P-LAYOUT gate. E-TOPO N-A (all-linear).
- result: pending fan-out.
- next: BOM derivation + research fan-out (workflow, MAX effort).

## 2026-07-22 — BOM classified (cook-hub reuse is huge)
- did: copied 21 cook-hub v1.0 part.yaml (pinout+escape already verified). Core
  reuse: DIP05-1A72-12L relay, ULN2803ADWR driver, SN74HC595DR shift reg,
  MAX31856MUD+T TC, the SN74LVC1G123 one-shot (PRESS timer), SN74LVC1G11 3-in
  AND (AND-chain), protection (MF polyfuse, SMBJ5.0A TVS, SS34, PESD, 2N7002/
  AO3401A FETs, LTV-817S opto for the contactor, RVT220UF bulk, AMS1117 LDO,
  GZ2012D601 ferrite), B5B-XH loadcell + KF350 terminal.
- CORRECTION: X9555WV-2x16-6TV01 is a 2x16 BOX HEADER (not a GPIO expander) —
  the I2C expander (MCP23017) stays on the NEW list.
- NEW parts to research (~11): MCP23017 expander; SN74HC138 + SN74HC139
  decoders (one-hot U/D select, ADR-0002); TPS3823 watchdog supervisor; an
  eFuse w/ OV cutoff; MCP3208 8ch ADC; LM393 comparators (TEMP_OK); a K-type
  TC PCB connector; JST-GH 8/5/10-pin; Micro-Fit 2-pin power; 2x20 Pi stacking
  header; AQY212GS PhotoMOS (optional alt). Plus layout: backfill on the reused
  multi-pin parts (P-LAYOUT).
- next: fan-out research + layout-backfill (workflow, MAX effort).

## 2026-07-22 — finish (workflow wf_b362be66, 9 agents, 0 err, ~1.17M tok)
- did: fanned-out MAX-effort research on the ~11 new multi-pin parts + layout:
  backfill on the reused ICs. Each new part.yaml: pinout from the datasheet
  FIGURE + verified: + escape block + layout: + LCSC + datasheet sha256.
- result: new parts complete & part-level gated (escape_check + S-VER/P-ESC/
  P-LAYOUT per the workflow): MCP23017-E-SS (C506653, SSOP-28), SN74HC138DR
  (C6818) + SN74HC139DR (C132996) decoders, TPS3823-33DBVR (C7719) watchdog,
  LM393DR (C67470) comparator, TPS259573DSGR (C2653844) eFuse, MCP3208 ADC,
  the SM0xB-GHS JST-GH + 43650 Micro-Fit connectors. Reuse ICs backfilled.
- DESIGN FLAGS to carry to schematic/ADR (do NOT lose these):
  1. **TPS3823 watchdog = 1.6s FIXED** (0.9-2.5s, DS 6.8) vs brief's 300-500ms
     heartbeat -> MISMATCH. The fast press-timeout is the SN74LVC1G123 one-shot
     (already in BOM); the TPS3823 is the COARSE brown-out/MR supervisor, not
     the heartbeat. Schematic must wire the fast heartbeat to the 1G123, not
     expect it from the '3823. (candidate ADR at schematic.)
  2. **TPS259573 eFuse: the "x3" = programmable OVLO die is LOAD-BEARING** (the
     brief's OV cutoff). NOT the x1 (C471038, no OV clamp) that generic searches
     surface. TSD is AUTO-RETRY (hiccup), not latch-off -> confirm SELV
     fault-mode in power review (a latch part would lose the OV clamp).
  3. **MCP23017 pin 12 = SCL** (I2C part). The DS package figure + pin table
     mislabel it SCK (shared MCP23S17 SPI template); pins 11/14 = NC on I2C.
     Recorded with a pin-note + gotcha — do NOT "correct" back to SCK.
  4. **Escape corridors are a PLACEMENT commitment (D-ADJ):** MCP23017 SSOP-28
     0.65mm dense side (~11 escapes: GPA0-7+INTA+INTB+/RESET) AND TPS259573
     WSON-8 0.5mm both hit the ADR-0008 dense wall — declared CONDITIONAL
     tier_required: jlc_2layer_default + [escape-corridor / outward-only-local].
     Floorplan MUST reserve outward fan-out corridors or the board tier rises
     to jlc_4layer_advanced. **03_src/rules/nets.yaml has NO fab_tier yet** —
     set it at commission of the routing stage.
  5. Decoder + ULN2803 sourcing = genuine TI (safety one-hot chain), not the
     house-brand cost floor — mirrors the shipped cook-hub precedent.
  6. Slash-MPN dir: MCP23017-E/SS -> dir MCP23017-E-SS (LM5116.../NOPB
     precedent); parity gate normalizes '/'->'-'.
- REMAINING parts-gate gaps (NEXT increment, not blockers to this checkpoint):
  (a) escape blocks on 14 reused SIMPLE leaded parts (SOT-23 FETs, SOIC logic,
      the DIP relay, opto) — trivial outward escape, deferred to the board-stage
      P-ESC sweep; (b) 2 hand-part LCSCs open (DIP05-1A72-12L relay, PCC-SMP-K
      TC connector — special/hand items); (c) 3 passive interconnect (2x20 PPC,
      B5B-XH, X9555 box header) flagged by the local scan's broad regex but NOT
      in real P-LAYOUT scope (no datasheet layout section) — a scan false-positive.
- next: parts is at a solid checkpoint; the board-stage gate (with 04_kicad)
  runs P-ESC/P-LAYOUT/P-ADJ properly. Schematic stage next (carry the 6 flags).

## 2026-07-22 — provenance correction (cook-hub / cook-loadcell reuse is REAL, just archived)

- did: audited the "cook-hub v1.0 / cook-loadcell v1.0 reuse" claim after noting
  NEITHER project exists under projects/. TRUTH: both are real, SEALED boards that
  live under **archived_projects/** (archived after sealing, not deleted) — cook-hub
  v1.0 sealed 2026-07-19 (git d0ed295, 07_releases/v1.0-2026-07-19/, 4-layer
  185x120mm) and cook-loadcell. The reuse is GENUINE, not "freshly researched then
  mislabelled as reuse": byte-level diffs prove a real copy —
  02_parts/B5B-XH-A/part.yaml is IDENTICAL to
  archived_projects/cook-hub/02_parts/B5B-XH-A/part.yaml (empty diff); 2N7002 and
  DIP05-1A72-12L match on every core fact (mpn / pins / footprint / verified), the
  ONLY local additions being this session's layout: backfill. B5B-XH-A is also in
  archived_projects/cook-loadcell/02_parts (the J6 loadcell link, cook-loadcell D6).
- CORRECTION to the 2026-07-22 "BOM classified" + "finish" entries: the phrase
  "copied 21 cook-hub v1.0 part.yaml (pinout+escape already verified)" OVERSTATED
  the escape half. cook-hub carried **NO escape blocks — 0 of 31** cook-hub 02_parts
  part.yamls have an `escape:` block (grep-verified). Pinouts WERE verified on
  cook-hub and are legitimately reused; escape blocks were NEVER present and are
  authored for the FIRST time in the finish entry below. So: pinout reuse = real &
  verified; escape verification = net-new work here, not inherited.
- verdict: the "reused from a shipped board" claim STANDS (true + evidenced), with
  two fixes recorded — the path is archived_projects/ (not projects/), and the
  "escape already verified" wording is retracted. No inherited-defect risk: the copy
  is from a real sealed board, and the one thing cook-hub lacked (escape blocks) is
  exactly what this increment supplies.

## 2026-07-22 — finish (parts-gate close-out: 14 escapes + 2 hand-LCSC ratified + fab_tier rec)

- did: closed the three REMAINING parts-gate gaps from the prior finish entry.
- (1) ESCAPE BLOCKS — added `escape:` to all 14 reused multi-pin parts that lacked
  one (the cook-hub copy carried none). Each block is exactly what escape_check.py
  --style/--pitch emits, gate-verified in check-part mode (escape_check over all 36
  part.yaml exits 0). ALL 14 = **jlc_2layer_default UNCONDITIONAL**:
    * leaded: 2N7002 (0.95), AMS1117-3.3 (SOT-223 2.3), AO3401A (0.95),
      DIP05-1A72-12L (DIP 2.54), LTV-817S-TA1 (SMD-4 1.27), MAX31856MUD+T
      (TSSOP-14 0.65), SN74HC14DR (SOIC-14 1.27), SN74HC595DR (SOIC-16 1.27),
      SN74LVC1G00DCKR (SC-70-5 0.65), SN74LVC1G11DBVR (SOT-23-6 0.95),
      SN74LVC1G123DCTR (SSOP-8 0.65), ULN2803ADWR (SOIC-18W 1.27)
    * connector: B5B-XH-A (XH 2.5), X9555WV-2x16-6TV01 (IDC 2.54)
  MAX31856 (the only one flagged "may be conditional"): at 0.65mm the dense-leaded
  wall (ADR-0008) ARMS only when a side declares >=6 escapes. escape_check
  --style leaded --pitch 0.65 (package geometry, no escape-count) emits
  jlc_2layer_default UNCONDITIONAL, so that is what is recorded — consistent with
  the reused note "TSSOP-14 0.65mm is coarse, no escape wall" (digital side routes
  <6 real escapes; analog side terminates in the local input filter). Declaring 7
  escapes/side WOULD flip it to CONDITIONAL escape-corridor / jlc_4layer_advanced —
  not this design; no editorializing added to the block.
- (2) TWO HAND-LCSC PARTS ratified (fresh web research 2026-07-22; mirrors the
  usb-hub-3s Keystone-3568 hand-solder precedent — `lcsc: ""`/null + note + real
  alternate MPN):
    * DIP05-1A72-12L (reed relay): GENUINELY UNCODED for JLC assembly — JLC catalog
      entry C1561362 exists but stock 0. Live-stocked only at Western distributors:
      DigiKey 1949339, Newark 96K8590, Arrow, TME, Bürklin. -> HAND-SOLDER line;
      note stands; added structured `alternates: [DIP05-1A72-12D]` (internal-diode,
      same pinout, ADR-0006). DO-NOT-SUBSTITUTE (spec 15.4).
    * PCC-SMP-K (Type-K TC jack): GENUINELY UNCODED — LCSC/JLC library has no Type-K
      thermocouple connector. Stocked at Newark (PCC-SMP-K-5 = 30AC8089,
      PCC-SMP-K-5-R = 71AC1688), RS, SparkFun, SK Pang. -> HAND-SOLDER; note +
      alternates [PCC-SMP-K-R, PCC-SMP-K-5] stand, with JLC-stocked fallback
      KF350-3.5-2P (C474892, already J5) if the keyed alloy jack is dropped at
      assembly. Neither part gets a C-number: hand-solder by evidence, not omission.
- (3) FAB_TIER RECOMMENDATION for the cooksense board (RECORDED HERE ONLY —
  03_src/rules/nets.yaml is owned by the concurrent schematic agent and still has no
  fab_tier). Two parts hit the dense-escape wall: MCP23017 SSOP-28 0.65mm (~11
  escapes/side: GPA0-7 + INTA + INTB + /RESET) and TPS259573 WSON-8 0.5mm.
    RECOMMEND **jlc_4layer_advanced** (4-layer + via-in-pad / POFV), UNCONDITIONAL.
    Reasoning:
      - The BRIEF already mandates 4-layer for Board A (DELIVERABLES 15) and cook-hub
        v1.0 shipped jlc_4layer_standard, so LAYER COUNT is settled — the only open
        question is STANDARD vs ADVANCED (the paid via-in-pad option), NOT a layer
        jump. via-in-pad is WITHIN the brief's 4-layer envelope -> no D-TIER ADR
        needed for advanced (a 2-layer downgrade WOULD contradict the brief).
      - jlc_4layer_STANDARD does NOT buy escape feasibility for these two: the binding
        constraint is the 0.5mm hole-to-hole floor, identical at standard and 2-layer
        (0.65 - 0.30 drill = 0.35 < 0.50), and via_in_pad is False at standard. So at
        standard BOTH parts stay CONDITIONAL — MCP23017 owes a reserved
        escape-corridor, TPS259573 owes outward-only-local. ONLY advanced (0.25
        hole-to-hole + via_in_pad) makes them unconditional.
      - MCP23017's 11-escape 0.65mm side IS the ADR-0008 dense-leaded wall that
        stalled usb-pwr-hub-3s v3 across many routing iterations; via-in-pad retires
        that risk outright instead of betting placement can reserve an 11-wide
        surface fan-out corridor. Advanced also gives the WSON eFuse EP proper in-pad
        thermal vias and the mixed-signal board (analog TC ~40uV/C + relay switching)
        clean In1-GND / In2-power planes.
    ALTERNATIVE (honest, cheaper): jlc_4layer_standard + HONOURED [MCP23017
      escape-corridor, TPS259573 outward-only-local]. Viable IF the floorplan
      reserves the corridor off the GPA side AND keeps every WSON fine pin local to
      an adjacent passive. If placement cannot guarantee BOTH, the tier rises to
      advanced mid-route anyway — committing up front avoids that stall. The two
      part.yaml escape blocks already record these conditional forms, so EITHER board
      tier passes P-TIER; the choice is a cost-vs-routing-risk call for the routing
      stage.
    Owner action: schematic/routing agent sets nets.yaml `fab_tier:
      jlc_4layer_advanced` (recommended) or `jlc_4layer_standard` + the two placement
      conditions. Do NOT downgrade to 2-layer (contradicts the brief).
- result: parts-gate gaps CLOSED. Completeness re-scan (36 part.yaml):
    ESCAPE gaps (multi-pin, no block):   0
    LCSC gaps (uncoded, NO hand-note):   0
    hand-solder (uncoded, note+alt MPN): 2 — DIP05-1A72-12L, PCC-SMP-K (intended)
  escape_check.py over all 36 part.yaml exits 0. PARTS STAGE closed.
- next: schematic stage — carry the 6 design flags + this fab_tier recommendation
  (concurrent agent is swapping the U/D decoders to active-high SN74HC238; those two
  part dirs left untouched here by design).

## 2026-07-24 — interposer parts (Board C)
- did: authored 02_parts/10FDZ-BT (JST FDZ ZIF, self-supplied THT) from the
  OFFICIAL eFDZ datasheet (jst-mfg.com, sha256 586ab321...): 10x phi0.9 PTH at
  2.54 pitch (span 22.86), phi1.8 NPTH polarization boss COLINEAR with the row
  2.54 outside pin1 (p.3 top-entry land pattern, verified on the rendered
  drawing), housing 36.26x7.7. Hand-authored land pattern
  cooksense:JST_10FDZ-BT_1x10_P2.54mm_Vertical_ZIF (pads 1.6/drill 0.9, NPTH
  1.8). escape_check connector/2.54 -> tier_required jlc_2layer_default.
- result: NEEDS-PHYSICAL-CONFIRM flag carried in part.yaml (drill pattern +
  boss end/sense are reference-drawing reads; blocks fab ORDER via ORDER_README
  ritual, NOT the seal — user directive 2026-07-24). Breakout connector =
  existing verified SM10B-GHS-TB (C2683602); sealed main board J_KEY_MATRIX
  read back read-only: pins 1..10 = KP_U1..U6,KP_D1..D4, MP floating — the
  interposer mirrors it exactly (1:1 GHR-10V-S ribbon). TPs = tscircuit pad
  testpoints (no part entries).
- next: 03_tscircuit/src/interposer.tsx (10 floating nets, 3 connectors,
  20 TPs) + schematic gate battery.
