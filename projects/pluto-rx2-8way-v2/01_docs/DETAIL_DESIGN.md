# DETAIL_DESIGN — pluto-rx2-8way-v2

Every component value with the equation, the inputs and the result.

**Every number below was RE-DERIVED for this board, not copied from v1.** Where
v1 published the same quantity, the agreement (or disagreement) is stated. That
matters here more than usual: v2 exists to be compared against v1, and a shared
arithmetic error would be invisible to the comparison.

Each section carries a **runnable one-liner** so the value is regenerated, not
typed (canon M4/M-BOUND). Copy-paste them; they take no arguments.

---

## 1. Stackup constants — the root of every RF number

Declared stackup: `JLC04161H-7628`, top prepreg **h = 0.2104 mm**, declared
**Dk = 4.4**, outer copper **t = 0.035 mm** (1 oz), RF50 width **w = 0.36 mm**.
**Cross-section: CONDUCTOR-BACKED COPLANAR WAVEGUIDE, gap s = 0.2005 mm on both
sides, BARE** — measured off the board, not assumed (`03_src/line_type.py`).
Method: quasi-static conformal mapping, Ghione / Naghed-Wolff CBCPW form.

| quantity | value |
|---|---|
| `eps_eff` | **3.1557** |
| `Z0` at w = 0.36 mm | **51.249 ohm** |
| `t_pd` | **5.9255 ps/mm** |
| `lambda_g` at 6 GHz | **28.1269 mm** |
| phase | **12.7991 deg/mm** at 6 GHz |
| ground-stitch bound, `lambda_pp/20` | **1.1910 mm** -> lattice pitch **0.80 mm** |

```
/usr/bin/python3 projects/pluto-rx2-8way-v2/03_src/gcpw_constants.py
```

**THESE SUPERSEDE A BARE-MICROSTRIP SET (ADR-0003 -> ADR-0004, 2026-07-30).**
This section used to publish `eps_eff 3.3286 / Z0 50.29 / t_pd 6.0857 /
lambda_g 27.387 / 13.145 deg-per-mm / fence 1.3693 -> 1.35`, from
Hammerstad-Jensen with the Wheeler thickness correction. That is the right
answer for a strip over a plane with nothing lateral, and **this board has no
such strip**: a GND pour flanks every RF arm at 0.2005–0.2010 mm edge-to-edge
on BOTH sides (`g/h = 0.955`) over 61–93 % of its length, and the remainder is
the SMA launch, not microstrip. The old command is preserved in ADR-0003, which
is `superseded-by-0004`; it was never wrong arithmetic, only the wrong
cross-section.

**Width choice.** 0.36 mm gives **51.25 ohm** as a coplanar line (it gives
50.29 as a microstrip). Still the closest of {0.35, 0.36, 0.37} to 50 and
**unchanged**, because the width was chosen against a target the correction
moves by only +1.9 %. This is an IMPEDANCE width. Widening it "for safety"
detunes the line exactly as much as narrowing it, and both directions are wrong.
Note which quantity survived: the correction is **−5.19 % on `eps_eff`** and
only **+1.9 % on `Z0`**, so the impedance the width was chosen for held and the
PHASE CONSTANT — the number this board publishes — did not.

**DISAGREEMENT WITH v1 AND WITH THE CANON, stated rather than smoothed over.**
v1's `nets.yaml` phase block and `rf-design.md` 4(d) publish eps_eff 3.350 /
t_pd 6.105 / lambda_g 27.29 / 13.19 deg-per-mm. The command above does not
produce them at any w in {0.35, 0.36, 0.37} x t in {0, 0.035}. v1 also carries
a THIRD value in the same file (lambda_g 27.41 mm, implying eps_eff 3.3229),
which is the one its 1.37 mm fence was actually computed from. **ADR-0003 is the
full account.** v2 uses its own derivation.

---

## 2. The RX1 pickoff — `R_T1` = `R_T2` = 220 ohm (0402, 1 %)

**Topology.** `J_ANT8` (the RX1 antenna), `J_RX1` (to PlutoSDR RX1) and the tap
arm meet at ONE node, `RX1_MAIN`. The tap arm is a SERIES PAIR, not a single
resistor, and that is a decision (v1 ADR-0002, user-confirmed): two 220 ohm
0402s put their ~0.04 pF parasitics in SERIES, halving C_eff — the 6 GHz tap
tilt drops from +1.69 dB to +0.43 dB and the UNKNOWN band narrows from 2.73 dB
to 0.83 dB. **A single 440 ohm part satisfies the topology and destroys the
property**, which is why both the chain AND each value are machine-asserted in
`03_src/rules/electrical_invariants.yaml`: the netlist, DRC, ERC and parity are
IDENTICAL for any resistance.

| quantity | equation | result |
|---|---|---|
| tap-arm impedance | `Rp = R_T1 + R_T2 + Z0 = 220 + 220 + 50` | **490 ohm** |
| load at `RX1_MAIN` | `Z0 \|\| Rp = 50*490/540` | **45.3704 ohm** |
| main-line insertion loss | `-10*log10(((RL/(Z0+RL))/0.5)^2)` | **0.4322 dB** |
| tap coupling vs available power | `10*log10(4*(V_node*Z0/Rp)^2)` | **-20.2567 dB** |
| return loss at `RX1_MAIN` | `-20*log10(\|(RL-Z0)/(RL+Z0)\|)` | **26.2773 dB** |

```
/usr/bin/python3 -c "import math; Z0=50.; Rp=220.+220.+Z0; RL=Z0*Rp/(Z0+Rp);
v=RL/(Z0+RL); print('Rp %.0f  RL %.4f  IL %.4f dB  tap %.4f dB  RL_dB %.4f dB'
%(Rp,RL,-10*math.log10((v/0.5)**2),10*math.log10(4*(v*Z0/Rp)**2),
-20*math.log10(abs((RL-Z0)/(RL+Z0)))))"
```

**AGREES WITH v1 to the last published digit** (v1: -20.26 dB tap, 0.432 dB
main-line IL, 26.28 dB RL). Re-derived here from the topology alone, without
reading v1's arithmetic — which is what makes the agreement evidence rather
than a copy.

**Carried forward from v1's T3, and it stays true on v2:** the tapped reference
dwell is LEAKAGE-limited above ~2 GHz and no tap value fixes it, because the
ceiling is the seven live ports' aggregate isolation. The zero-board-cost lever
also survives: populating `R_T2` as 0 ohm buys reference SIR at the price of
RX1 loss, decidable on order day as a BOM change. INHERITED from v1's ADR-0002
and NOT re-derived here.

---

## 3. Control-line source termination — `R_S1..R_S4` = 47 ohm (0402, 5 %)

**This is a protection value, not a convention.** PE42482A-X's digital absolute
maximum is **3.6 V** while its VDD absolute maximum is 5.5 V — the control pins
are NOT rated to the supply, leaving 300 mV of headroom on a 3.3 V rail
(PE42482A-X Table 1, PDF p2).

An unterminated fast edge into a ~67 ohm control line doubles at the open far
end. With the RP2040 at its STRONGEST drive (Z_drv ~ 25 ohm at the 12 mA
setting):

    V_peak = 2 * Vdd * Z_line / (Z_line + Z_drv + R_S)

| `R_S` | far-end peak | vs the 3.6 V absolute maximum |
|---|---|---|
| 0 ohm | **4.807 V** | **EXCEEDS by 1.2 V** |
| **47 ohm** | **3.181 V** | 0.42 V of margin |

```
/usr/bin/python3 -c "
[print('Rs=%5.1f -> %.3f V' % (r, 2*3.3*67/(67+25+r))) for r in (0.,47.)]"
```

**Protection that lives in a firmware register is not protection.** The RP2040's
drive strength is software-selectable; the resistor is not.

**The module makes this MORE necessary, not less.** The line is now our copper
PLUS the module's internal trace from the RP2040 pad to the castellation, so the
electrical length grows and the reflection analysis becomes more relevant. The
driver silicon is identical, so Z_drv is unchanged and 47 ohm carries over.
**MEASURED-ON-v1-and-CARRIED, with one INHERITED input:** Z_drv ~ 25 ohm is
back-solved from v1's published 4.807 V figure and is NOT independently read out
of the RP2040 datasheet here. It is the one number in this section I did not
re-source; flagged rather than presented as derived.

---

## 4. Control-line pull-downs — `R_PD1..R_PD4` = 10 k (0402, 1 %)

**MANDATORY, not defensive.** `V1..V4` have NO internal pull of any kind (5 uA
max input current, PE42482A-X Table 2, PDF p3), so all four FLOAT through reset
and supply ramp — and a floating `V4` selects the ALL-PORTS-TERMINATED state,
which **silently mutes the receiver**. Power-on default is `0000` = RF1, a real
antenna.

They sit at the **SWITCH end**, on the far side of `R_S`, because that is the
only position that guarantees a level when the module is absent, unpowered, or
still in reset.

| check | equation | result | requirement |
|---|---|---|---|
| level when driven HIGH | `3.3 * 10000/(10000+47)` | **3.2846 V** | > V_IH 1.17 V ✓ |
| level when undriven | `5 uA * 10 k` | **50.0 mV** | << V_IL ✓ |
| DC per line when HIGH | `3.3/(10000+47)` | **328.5 uA** | — |
| all four HIGH | `4 x 328.5 uA` | **1.314 mA** | sourced by module GPIOs, not by our 3V3 net |

```
/usr/bin/python3 -c "V,Rs,Rp=3.3,47.,10000.;
print('high %.4f V | leak %.1f mV | %.1f uA/line | %.3f mA x4'
%(V*Rp/(Rp+Rs), 5e-6*Rp*1e3, V/(Rp+Rs)*1e6, 4*V/(Rp+Rs)*1e3))"
```

**NO SHUNT CAPACITANCE ANYWHERE ON THIS CLASS.** A 1 k + 1 nF RC settles in
4.6 us to 99 %, which is more than the entire **4.267 us** blanking allowance
(128 samples at 30 Msps). The control plane is deliberately un-filtered.

---

## 5. Status LED — `LED_ST` (KT-0603R red) + `R_LED` = 680 ohm

`KT-0603R` publishes **Vf 1.8 V min / 2.4 V max at IF = 20 mA and NO TYPICAL**
(dossier `limits.vf`, cited from the committed datasheet). The bin spread is the
design input, so the current is stated as a RANGE, not a point:

| Vf | `I_F = (3.3 - Vf)/680` |
|---|---|
| 1.8 V (min bin) | **2.206 mA** |
| 2.0 V (nominal working figure) | **1.912 mA** |
| 2.4 V (max bin) | **1.324 mA** |

```
/usr/bin/python3 -c "
[print('Vf=%.1f -> %.3f mA' % (v,(3.3-v)/680*1e3)) for v in (1.8,2.0,2.4)]"
```

All three are comfortably visible for an indicator and far below the part's
rating. Driven from a module GPIO, so it loads a module pin, not our 3V3 net.

**`LED_PWR` is DELETED relative to v1**, and that is a decision rather than an
oversight: with no board-level power entry there is no board rail whose presence
a power LED would testify to, and the module carries its own WS2812 which lights
on power. One fewer continuously-conducting part on a receiver board.

---

## 6. Switch supply — `FB_3V3`, `C_SW1`, `C_SW2`, `C_BULK`

**The load is negligible and that is the point.** `U_SW` draws **120 uA typ /
200 uA max** (Table 2, PDF p3) from a module regulator rated **500 mA** — our
board consumes **0.04 %** of it. The pull-downs and the LED are sourced by module
GPIO pins, not by this net, so they do not enter the budget.

| part | value | why |
|---|---|---|
| `FB_3V3` | BLM21SP601SN1D, 600 ohm at 100 MHz, 0805 | the ONE place this board's supply meets its RF part. RP2040 core + QSPI transients ride the module's 3V3; PE42482A-X publishes no PSRR |
| `C_SW1` | 100 nF X7R 0402 | AT pin 8, span <= 3 mm. For CONTROL-LINE transients, not load current — which is why position is the whole value |
| `C_SW2` | 1 uF X7R 0603 | mid-frequency, beside `C_SW1` |
| `C_BULK` | 4.7 uF X7R 0805 | on `3V3_MOD`, the module side of the ferrite: gives the bead something to work against |

**Ferrite DC drop is not a consideration and the number says so:** DCR 0.06 ohm
max (Murata Specifications table, PDF p2) at 200 uA = **12 uV**. The bead is
chosen entirely for its impedance at the QSPI comb's fundamentals (~31-66 MHz)
and their low harmonics.

**A gotcha carried from the dossier, and it applies here in the direction that
helps:** a bead's impedance FALLS as DC bias approaches its rating. At 200 uA
against a 2.3 A rating we are at 0.009 % of rated current, so the 600 ohm figure
is not derated at all. The `+/-25 %` tolerance on it stands.

**HONEST LIMIT.** The 600 ohm / 100 MHz figure is CITED from Murata's
specifications table, but the impedance-vs-frequency curve in the dossier's
`limits:` is marked ESTIMATED (read off a 300-dpi render of PDF p3). **No
attenuation figure is published in this document**, because computing one from
an estimated curve and an idealised capacitor would produce a confident number
with no measurement behind it. The filter is sized by topology and by the
part's one cited number; its performance is a bench measurement owed at
bring-up.

---

## 7. What is NOT in this document, and why

- **The 8192/4096/128 dwell arithmetic and the 499,712-sample frame closure.**
  INHERITED from v1's D1, unchanged, and not re-derived — v2 changes the MCU's
  packaging, not its behaviour.
- **The octilinear floor and the per-pad landable width.** Both are PAD
  arithmetic and both are stage-5 obligations; they cannot be computed before a
  floorplan exists. Recorded in ARCHITECTURE section 7 so they are not
  rediscovered by routing for hours, which is how v1 found them.
- **Any length-match tolerance tighter than the part's own 13.2 deg
  part-to-part window (= 1.00 mm of copper).** v1's "+/-0.10 mm" was 1.3 deg,
  was unreachable by any router and unheld by any process, and was withdrawn.
  v2 does not re-adopt it (BRIEF A5).
- **A spur budget.** The board's spur story changed materially (QSPI moved off
  the laminate, a WS2812 arrived). Both effects are argued in ADR-0001 and
  NEITHER is measured. A spur survey of the first physical unit is owed before
  any phase table is published.
