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
