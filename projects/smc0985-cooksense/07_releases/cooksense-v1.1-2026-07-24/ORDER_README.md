# ORDER README — cooksense MAIN board **v1.1** (project smc0985-cooksense)

Cooktop safety-interlock sidecar for a Raspberry Pi: keypad reed-relay matrix
(now an isolated COMB — vertical relays, contact columns pocketed between
pairs), watchdog + hardware AND-chain interlock, 12× reed coil drivers, Type-K
thermocouple front-end (MAX31856), thermistor comparator, contactor dry-contact
loop. Release **cooksense-v1.1-2026-07-24** — supersedes cooksense-v1.0
(mechanical repack 252×92 → **188×92 mm**, relays rot0 @ 15.24 mm pitch,
isolation-comb barrier; **schematic/netlist byte-identical to v1.0**).
Board **188 × 92 mm**, **4 layer**, CPL 175 parts, BOM 52 lines.

---

## 1. JLCPCB order options
| Setting | Value |
|---|---|
| Layers | **4** (In1 = GND plane, In2 = 3V3 plane; NO plane north of y53 — keypad band, relay row, pockets and coil gaps are plane-free) |
| Dimensions | 188 × 92 mm (12 milled 0.6 mm isolation slots on Edge.Cuts — confirm the fab preview keeps them as internal routs) |
| Via tier | **ADVANCED small-via option required** — 0.25 mm via / 0.15 mm drill (via-in-pad escapes). Do NOT order standard 0.45/0.30. |
| Assembly | BOM `bom.csv` + CPL `cpl.csv`. 2 BOM lines are deliberately uncoded (self-supplied, below). The CPL carries the 14 hand-solder THT positions (12 relays + J_TC + refs without BOM codes): **expect and IGNORE the JLC "unmatched CPL entries" preview warning — do NOT let JLC 'fix' or delete them** (fresh-lens P2-3). |

**Order-day gate (fresh-lens ORDER conditions):** (a) stock recheck per §3;
(b) JLC preview confirms ALL 12 milled 0.6 mm slots survive as internal routs;
(c) the ADVANCED 0.25/0.15 via option is selected; (d) unmatched-CPL warning
acknowledged per the Assembly row above.

## 2. ⚠️ SELF-SUPPLIED / HAND-SOLDER — DO-NOT-SUBSTITUTE
| Ref(s) | Part | Notes |
|---|---|---|
| **K_U1..K_U6, K_D1..K_D4, K_PRESS, K_STOP** (×12) | **Standex DIP05-1A72-12L** reed relay | NOT JLC-cataloged. Footprint is pinout-12-specific (Relay_StandexDIP_1A_pinout12). **No substitutes** — the isolation-comb creepage (6.12 mm measured, track-aware) and the coil/contact column pinout are designed around this exact body. THT hand-solder. Approved alternate: DIP05-1A72-12D (same pinout, internal diode). Order 16 (12 + 4 spares). |
| **J_TC** | **Omega PCC-SMP-K** panel Type-K thermocouple jack | NOT JLC-cataloged. Ø1.77 mm PC pins + 2 NPTH bracket holes match the Omega PCC-OST-SMP drawing exactly. **No substitutes** (chromel/alumel jack contacts ARE the cold-junction interface). THT hand-solder. |

Other hand-solder THT lines: none besides the two above (see `fab/bom.csv`
rows without LCSC codes).

## 3. ⚠️ MANDATORY ORDER-DAY STOCK RECHECK (low/volatile coded lines)
Re-run `jlc_stock_check` on order day; confirmed 2026-07-24:
| Ref | LCSC | Stock 2026-07-24 |
|---|---|---|
| U_EFUSE (TPS259573) | C2653844 | recheck (thin at v1.0: 160) |
| F1 polyfuse | C89650 | 244 |
| J_PWR Micro-Fit | C587657 | recheck (v1.0: 778) |
| U_ADC (MCP3208) | C16939 | recheck (v1.0: 223) |
| 10 kΩ 0402 ×18 | C25744 | **12,622 — fell from 192k in one day; API also returned transient 0s.** If genuinely out: any JLC 10 kΩ ±1% 0402 substitutes (e.g. C60490 RC0402FR-0710KL, stock 6.5M on 2026-07-24). |

## 4. JLC assembly-preview rotation checklist
- **J_PI (2×20 socket, C35165):** JLC's library winds pin numbering by ROW where
  ours winds by COLUMN (adjudicated twin MIRRORED finding — identical symmetric
  2.54 mm hole grid, hole-constrained, no physical mirror possible). In the JLC
  preview confirm the part sits ON the grid; pin-1 identity comes from our
  netlist + silk, not JLC's numbering.
- **SOIC-16 rotation (U_DECU/U_DECD, C5620/C10092):** twin ROT-DB-SUGGEST 90°
  offset class — confirm pin-1 in the preview.
- Confirm U_OPTO pin-1 dot, CE1 polarity crescent, and all diode cathode bands
  (D_ESD_IN/D_ESTOP/D_DOOR/D_LCCLK/D_LCDAT/D_REVCLAMP/D_TVS) against silk in
  the preview (twin POLARITY-CHECK class; verified in renders, preview is the
  backstop).

## 5. First-power ritual (BEFORE any power)
1. **J_PWR pin-1 harness check (BRING-UP-CRITICAL):** multimeter the mating
   harness: pin 1 blade must beep to +5 V, pin 2 to RTN, with the polarizing
   peg orientation noted. Keyed housing prevents reverse MATING only — it
   cannot fix a mis-assumed pin-1 side.
2. Continuity: 5V_IN → F1 → 5V_FUSED → Q_REV → 5V_RPP → U_EFUSE → 5V_PROTECTED.
3. Power at current-limited 5 V / 0.5 A; check 3V3 (U_LDO) and 3V3_ANALOG rails.
4. **Isolation spot-check (new comb):** with relays UNPOPULATED, megger/DMM
   between any keypad net (J_KEY_MATRIX pin) and GND — must be open (the comb
   carries no galvanic path; only the reed contacts bridge domains).

## 6. ⚠️ RELAY-COUPLING BENCH MEASUREMENT (new for v1.1 — licenses any future denser repack)
This board places the reeds at the **15.24 mm coupling-vetted pitch in the
rot0 orientation the figure came from, with anti-parallel adjacent coils**
(the datasheet's own alternate-orientation mitigation). To license any FUTURE
revision below 15.24 mm pitch or a two-row repack, measure ON THIS BOARD:
- Energize a **U + D + PRESS triple** (worst-case simultaneous neighbours,
  e.g. K_U6 + K_D1 + K_PRESS via the decoder/one-shot paths).
- For the relay ADJACENT to each energized one, sweep its coil voltage and
  record the **operate (pull-in) voltage shift** vs. the datasheet 3.5 V max
  in isolation, both coil polarities.
- A shift < 10% of the 1.5 V worst-case margin (i.e. operate stays ≤ 3.65 V)
  is a CLEAN result → record it in 01_docs/decisions/ as the coupling
  evidence. Any larger shift: keep ≥ 15.24 mm forever and note the -12M/Q/R/S
  magnetic-shield variants as the fallback for denser layouts.

## 7. First-use functional checks
- **J_TC thermocouple polarity:** dip the probe in a known reference (ice
  water / boiling water) — a REVERSED junction reads an inverted delta from
  ambient: obvious and harmless. Swap at the MAX31856 inputs if needed.
- **KEY_RESET_N floats during Pi boot** — R_OE holds the 595 outputs disabled;
  no relay can fire until the Pi drives the interface. Observe on first boot.

## 8. Pi interconnect (J_PI — ribbon SIDECAR, NOT a direct stack)
- Use a 40-way ribbon with a **MALE DIL-IDC transition plug at the board end**
  — standard Pi ribbons are FEMALE-FEMALE and cannot mate this board's socket.
- The socket is UNSHROUDED: mark pin 1 on both ribbon ends and observe strict
  pin-1 keying discipline at every mating.
- The socket's stack tails protrude ~12 mm below the board — trim them or fit
  standoffs of at least that height.

## 9. Harness labeling discipline (unkeyed 5-pin GH family)
J_MODE / J_DOOR / J_ESTOP share the same unkeyed 5-pin JST-GH housing and a
common 3V3(1)/GND(5) convention. Pinouts are arranged so any single cross-plug
is fail-safe, but a cross-plugged E-STOP harness silently closes the contactor
loop through GND. **Label every harness at both ends and match labels before
power.**

## 10. Contactor loop rating (J_ESTOP 3/4)
The loop is the LTV-817S opto DRY CONTACT: design bound ≤30 V / ≤50 mA
(LTV-817 collector abs-max 50 mA is the limiting element). Do not repurpose
this loop to switch the contactor coil directly.
