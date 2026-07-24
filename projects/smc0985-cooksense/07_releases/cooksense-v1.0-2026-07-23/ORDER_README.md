# ORDER README — cooksense MAIN board **v1.0** (project smc0985-cooksense)

Cooktop safety-interlock sidecar for a Raspberry Pi: keypad reed-relay matrix
(isolated north band), watchdog + hardware AND-chain interlock, 12× reed coil
drivers, Type-K thermocouple front-end (MAX31856), thermistor comparator,
contactor dry-contact loop. Release **cooksense-v1.0-2026-07-23**.
Board **252 × 92 mm**, **4 layer**, CPL 175 parts, BOM 52 lines.

---

## 1. JLCPCB order options
| Setting | Value |
|---|---|
| Layers | **4** (In1 = GND plane, In2 = 3V3 plane; NO plane in the keypad isolation band) |
| Dimensions | 252 × 92 mm |
| Via tier | **ADVANCED small-via option required** — 0.25 mm via / 0.15 mm drill (via-in-pad escapes). Do NOT order standard 0.45/0.30. |
| Assembly | BOM `bom.csv` + CPL `cpl.csv`. 2 BOM lines are deliberately uncoded (self-supplied, below). |

## 2. ⚠️ SELF-SUPPLIED / HAND-SOLDER — DO-NOT-SUBSTITUTE
| Ref(s) | Part | Notes |
|---|---|---|
| **K_U1..K_U6, K_D1..K_D4, K_PRESS, K_STOP** (×12) | **Standex DIP05-1A72-12L** reed relay | NOT JLC-cataloged. Footprint is pinout-12-specific (Relay_StandexDIP_1A_pinout12). **No substitutes** — the isolation barrier creepage (6.12 mm measured) and the coil/contact pinout are designed around this exact body. THT hand-solder. |
| **J_TC** | **Omega PCC-SMP-K** panel Type-K thermocouple jack | NOT JLC-cataloged. Ø1.77 mm PC pins + 2 NPTH bracket holes match the Omega PCC-OST-SMP drawing exactly. **No substitutes** (chromel/alumel jack contacts ARE the cold-junction interface). THT hand-solder. |

Other hand-solder THT lines (uncoded in BOM, standard parts): see `fab/bom.csv`
rows without LCSC codes — none besides the two above.

## 3. ⚠️ MANDATORY ORDER-DAY STOCK RECHECK (low-stock coded lines)
Re-run `jlc_stock_check` on order day; confirmed 2026-07-23:
| Ref | LCSC | Stock 2026-07-23 |
|---|---|---|
| U_EFUSE (TPS259573) | C2653844 | 160 |
| F1 polyfuse | C89650 | 244 |
| J_PWR Micro-Fit | C587657 | 778 |
| U_ADC (MCP3208) | C16939 | 223 |

All ≫ 5× need for qty 1, but these four are the thin ones — recheck before upload.

## 4. JLC assembly-preview rotation checklist
- **J_PI (2×20 socket, C35165):** JLC's library winds pin numbering by ROW where
  ours winds by COLUMN (adjudicated twin MIRRORED finding — identical symmetric
  2.54 mm hole grid, hole-constrained, no physical mirror possible). In the JLC
  preview confirm the part sits ON the grid; pin-1 identity comes from our
  netlist + silk, not JLC's numbering.
- Confirm U_OPTO pin-1 dot, CE1 polarity crescent, and all diode cathode bands
  against silk in the preview (all verified in the twin renders; preview is the
  backstop).

## 5. First-power ritual (BEFORE any power)
1. **J_PWR pin-1 harness check (BRING-UP-CRITICAL):** the Molex Micro-Fit
   pin-1-vs-polarizing-peg orientation was never confirmed against the SD
   drawing. Multimeter the mating harness: pin 1 blade must beep to +5 V, pin 2
   to RTN, with the peg orientation noted. Keyed housing prevents reverse
   MATING only — it cannot fix a mis-assumed pin-1 side.
2. Continuity: 5V_IN → F1 → 5V_FUSED → Q_REV → 5V_RPP → U_EFUSE → 5V_PROTECTED.
3. Power at current-limited 5 V / 0.5 A; check 3V3 (U_LDO) and 3V3_ANALOG rails.

## 6. First-use functional checks
- **J_TC thermocouple polarity:** the Omega drawing does not unambiguously mark
  which blade is chromel(+). Before trusting readings, dip the probe in a known
  reference (ice water / boiling water) — a REVERSED junction reads an inverted
  delta from ambient: obvious and harmless. Swap is at the MAX31856 inputs if
  needed (jack is keyed; the plug cannot be reversed).
- **KEY_RESET_N floats during Pi boot** — R_OE holds the 595 outputs disabled;
  no relay can fire until the Pi drives the interface. Low risk; observe on
  first boot.

## 7. Pi interconnect (J_PI — ribbon SIDECAR, NOT a direct stack)
- Use a 40-way ribbon with a **MALE DIL-IDC transition plug at the board end**
  — standard Pi ribbons are FEMALE-FEMALE and cannot mate this board's socket.
- The socket is UNSHROUDED: mark pin 1 on both ribbon ends and observe strict
  pin-1 keying discipline at every mating.
- The socket's 12.46 mm stack tails protrude ~12 mm below the board — trim
  them or fit standoffs of at least that height.

## 8. Harness labeling discipline (unkeyed 5-pin GH family)
J_MODE / J_DOOR / J_ESTOP share the same unkeyed 5-pin JST-GH housing and a
common 3V3(1)/GND(5) convention. Pinouts are arranged so any single cross-plug
is fail-safe (COIL_EN's neighbours are the AND-chain output and GND), but a
cross-plugged E-STOP harness silently closes the contactor loop through GND.
**Label every harness at both ends and match labels before power.**

## 9. Contactor loop rating (J_ESTOP 3/4)
The loop is the LTV-817S opto DRY CONTACT: design bound ≤30 V / ≤50 mA
(LTV-817 collector abs-max 50 mA is the limiting element). 20× current margin
against the 1.0 A / 50 V JST-GH contact rating. Do not repurpose this loop to
switch the contactor coil directly.
