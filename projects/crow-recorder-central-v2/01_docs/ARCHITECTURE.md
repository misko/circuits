# ARCHITECTURE — crow-recorder-central-v2

Class: **mixed-signal-audio-hub** (floorplan-archetypes.md): many cable ports
fan IN to one board; a quiet analog ADC spine sits between two noisy bands
(switching supplies + beeper-return currents) so ADC copper never shares a
band with either.

## Signal chain (fan-IN)

```
6x POD (RJ45) --Cat5e--> [port bank, north]
   orange 1,2  AUDIO+/-  --> TPD2E2U06 ESD --> AC-couple + anti-alias RC -->
                                                PCM1865 diff input (VINxP/M)
   blue4,7/brn = +5V_AUDIO --> MINISMDC050F-2 PTC <-- 5V rail
   blue5,8/brn = GND_AUDIO  --> GND_A (audio ground)
   green3 = +5V_BEEP <-- 5V rail (bus)
   green6 = BEEP_SWITCHED_RETURN --> AO3400A drain (shared low-side switch)

2x PCM1865 (TDM daisy: U-ADC1 = ch1-4, U-ADC2 = ch5-8)
   shared MCLK (SCKI p15, XI->GND), BCLK, LRCK via 33R source-series links
   TDM DOUT daisy-chained -> XU316
        |
   XU316-1024-TQ128 xcore.ai  ---- QSPI ----> W25Q16 flash (boot)
        |                       ---- I2C ----> both PCM1865 (0x4A/0x4B) + SHT40
        |                       ---- GPIO ---> AO3400A beeper gate (slow RC)
        |
   USB HS D+/D- --> TPD4EUSB30 ESD --> USB4105 USB-C (device, to host PC)
```

## Clock tree (D4, ADR-0004)

```
FA-238 24MHz xtal --> XU316 (xcore.ai PLL derives MCLK)
XU316 MCLK_OUT --> NC7NZ34 clock buffer (1->2 fanout, all 3 inputs tied) -->
   Y1 --33R--> PCM1865 U-ADC1 SCKI (pin 15)
   Y2 --33R--> PCM1865 U-ADC2 SCKI (pin 15)
XU316 BCLK --33R--> both PCM1865 BCK (shared)
XU316 LRCK --33R--> both PCM1865 LRCK (shared)
Both PCM1865 XI (pin 10) TIED TO GND  (abs-max 2.1V — never feed MCLK here)
```
One physical sample clock for all channels: the XU316 xcore.ai is the timing
authority (USB Audio Class 2 ASYNC), MCLK fans to both ADCs, all channels
sampled coherently.

## Power tree (ADR-0001 protection, ADR-0005 sequencing)

```
GST25A05 5V/5A brick --barrel jack J_PWR--> [RPP P-FET Q_RPP] --> 5V rail
   5V --> TVS D_TVS (5.0V) + bulk cap
   5V --> AP61102 buck U_B1 --> 3V3  (digital: XU316 VDDIO banks, PCM1865
                                       DVDD/IOVDD, flash, clock buf, SHT40)
   5V --> AP61102 buck U_B2 --> 0V9  (XU316 VDD core; EN gated by U_B1 PG)
   3V3 --> TCR2LF18 LDO U_L1 --> 1V8 (XU316 VDDIOB18 + USB_VDD18)
   3V3A: 5V --> XC6227 LDO U_L2 --> 3V3A (quiet analog: 2x PCM1865 AVDD only)
   5V --> per-port PTC --> +5V_AUDIO (to pods)
   5V --> +5V_BEEP bus (to pods, always-on)
```
Sequencing (ADR-0005, per XMOS ref): 3V3 comes up first, its PG enables the
0V9 core buck (core after IO), 1V8 LDO comes up right after 3V3 (never last).
3V3A analog LDO is independent off 5V.

Worst-case 5V trunk current (E-TOPO): digital ~0.5A + analog ~0.1A + pods
(6*20mA audio + 6*150mA beep peak) ~1.0A => ~1.6A worst case << GST25A05 5A.

## Calibration-burst drive level — a BINDING CROSS-BOARD CONSTRAINT

**This board's beep drive is bounded ABOVE by the input ceiling of the preamp
on the sibling board, `crow-mic-pod-v2`. Raising it breaks the pod.** This is
the one system rule that neither board can see on its own, so it is recorded
on both.

The pod carries its calibration transducer LS1 **45.61798 mm** from its own
microphone MK1 (pcbnew, sealed pod v1.3 board), so the burst lands on the
capsule at `SPL(10 cm) + 20·log10(100.000/45.61798)` = `SPL(10 cm) + 6.8173 dB`,
and the pod's OPA1678 runs out of **linear input common-mode range** first
(SBOS855E §6.7, `VCM = (V−)+0.5 … (V+)−2`) at a worst-case ceiling of
**101.3144 dB SPL** — mic sensitivity +3 dB at V+ = 4.75 V, which is the same
instant the burst peaks. That is defect **CAL-1**
(`projects/crow-mic-pod-v2/08_reviews/DISPOSITIONS.md`): the calibration
transducer saturates the preamp it exists to calibrate.

**The acceptance criterion changed on 2026-07-28 (user decision).** CAL-1 as
filed sized the shortfall against LS1's datasheet MINIMUM output — the wrong
end of the tolerance for a CLIPPING problem, because the unit that clips is a
LOUD one. The criterion is now **"clears a unit on the datasheet's TYPICAL
curve"** (~104 dB @ 10 cm at 3.9 kHz, rev 1.04 p.3):

| LS1 output | burst at the capsule | shortfall vs the 101.3144 dB ceiling |
|---|---|---|
| datasheet MINIMUM, 100 dB @10 cm | 106.8173 dB SPL | 5.5028 dB *(the old basis)* |
| **datasheet TYPICAL, 104 dB @10 cm** | **110.8173 dB SPL** | **9.5028 dB** *(binding)* |

It is fixed HERE, not on the pod — the pod's VMID divider was measured unable
to clear the guaranteed spec by any value (best +0.86 dB, optimum in the
opposite direction). The pod's v1.3 release stays live and is NOT superseded.

**There is no analog level control on this board**, measured from the SEALED
v1.7 netlist rather than the source:

| net | nodes | consequence |
|---|---|---|
| `PLUS5V_BEEP` | 11 — `FB_BEEP.2` (bead off the 5 V rail, ~0 Ω DC), `C_BEEP.1`, `TP12`, pin 3 of all EIGHT RJ45s | fixed 5 V; **no series resistor, no regulator** |
| `BEEP_RETURN` | 10 — pin 6 of all EIGHT RJ45s, `TP11`, `Q2.3` | **ONE AO3400A for every pod** (BRIEF D1) |
| `BEEP_GATE` | **2** — `U1.122` (XU316 GPIO) and `R_bg1.1` | the GPIO waveform is the ONLY lever |

So the level is a FIRMWARE constant by construction. It lives, with its full
derivation, both models and the trim ladder, in **`05_firmware/cal_burst.c`** —
`CAL_BURST_DUTY_NUM/DEN = **1/20**`:

| model | attenuation | typical unit at MK1 | clears by |
|---|---|---|---|
| NOMINAL `20·log10(sin(π/20))` | −16.1134 dB | 94.7039 dB SPL | +6.6105 dB |
| **WORST CASE** (gate RC + L-R) | **−11.9165 dB** | **98.9008 dB SPL** | **+2.4136 dB** |

`make test` re-derives all of it from the physics, and its **fatal** assertion
is the WORST-CASE form — so duties 1/2, 1/6 and 1/12 all fail it.

**`sin(πD)` is NOT a conservative bound here.** It is re-verified from scratch
at every retune rather than extrapolated, because the L-R term is **not
monotonic in duty** — and extrapolating it is exactly the mistake the 1/6 → 1/12
carry-forward made:

1. **L-R regime change.** Exact-exponential integration of `i' = (v−iR)/L` with
   the SS14 freewheel over L = 10 µH…3 mH, at the **commanded** duty: at 1/6
   every corner conservative; at 1/12 the 3 mH corner ran **+0.835 dB
   non-conservative**; at **1/20 every corner is conservative again** (worst
   slack −0.087 dB). At the shipped duty this term is benign on its own — it
   re-enters only through (2), which pushes the *effective* duty back into the
   7–11 % region where the 3 mH corner misbehaves (+0.75 dB).
2. **Gate-RC duty bias — now the DOMINANT term, and previously unnoticed.**
   Turn-ON waits only for the gate to CLIMB to `Vgs(th)`; turn-OFF waits for it
   to FALL from the 3.069 V gate peak all the way DOWN to `Vgs(th)`. Asymmetric
   ⇒ the conduction window is **STRETCHED** by +0.77 µs (Vth 1.45) to
   **+6.19 µs** (Vth 0.65). Being an ABSOLUTE time its fractional cost grows as
   the duty shrinks — 5.2 % of the pulse at 1/2, 31.1 % at 1/12, **49.5 % at
   1/20.** Nearly half the conduction window at the shipped duty is gate-RC
   artefact, not commanded drive. DETAIL_DESIGN documents this RC purely as an
   EMI slew-limiter; nobody had noticed it also biases the duty upward, which
   only matters once duty is used to control LEVEL.

**Combined worst case −11.9165 dB against the law's −16.1134 — slack
+4.197 dB.** The criterion is nevertheless met **under the worst-case model**
(+2.4136 dB typical, +6.4136 dB minimum-spec).

**Why 1/20 and not 1/14** (the least value that clears, +0.11 dB): the risk is
asymmetric. Clipping destroys the timing reference outright; a low level only
costs SNR, and the local path still sits ~77 dB above the mic's self-noise.
With the open-loop uncertainty (+4.20 dB) still larger than the criterion,
1/14's +0.11 dB is a rounding error against a model that has already moved 3 dB
once.

**What is open is the MODEL, not the margin** — the stretch has never been
measured on hardware. The **TP11 bring-up measurement is NORMATIVE** and is
written up in `01_docs/CHECKLIST.md`: scope `U1.122` (commanded pulse) against
`TP11`/`BEEP_RETURN` (actual conduction window), subtract, record. It
**licenses tightening the duty back toward 1/14–1/16 with evidence**, worth
~2–4 dB of burst level and far-pod SNR. Until then 1/20 stands.

Trim floor **36**, re-derived at 1/20 and bound by the gate reaching the
AO3400A's 2.5 V Rdson spec point (fails at den ≈ 37.5). An earlier revision set
it at 24 on a "the worst case saturates" argument that measurement
**retracted**: over 1/20 → 1/40, nominal gains 5.99 dB and worst case 5.24 dB —
they track within ~0.75 dB per doubling.

Nothing about this touches copper, the BOM, or any release: `07_releases/`
payloads are `fab/ source/ verification/ 3d/ pdf/ MANIFEST.txt ORDER_README.md`
and carry no firmware. **v1.7 stays sealed and live.** The operator-facing copy
of this constraint is owed to the NEXT release's `ORDER_README.md` (the sealed
ones are immutable and cannot be retro-filled).

## Ground strategy

- Digital GND (GND) + analog GND (GND_A) joined at a single point / star at
  the ADC AVSS region (join only at GND inside the ADC die + one bridge).
- 6-layer: In1 + In4 solid GND planes; F/B pours; heavy stitch.
- Beeper switched-return current stays ENTIRELY in the north port band —
  never crosses south into the analog spine (placement invariant).

## Board regions (mixed-signal-audio-hub archetype)

- NORTH edge: 8x RJ45 port bank (6 populated) + per-port ESD/PTC + the shared
  beeper FET; switched-return current confined here.
- CENTER band: analog ADC spine — 2x PCM1865 flanking centreline, XC6227 3V3A
  LDO between them; every ADC bias/coupling web within 2-5mm of its pins;
  the input RC/anti-alias sits in this band, fed from its own analog rail.
- SOUTH: digital cell — XU316 centred, flash + FA-238 xtal + NC7NZ34 buffer on
  its hard-net side; USB-C at the south edge (controlled short HS pair).
- WEST/SW corner: power cluster — barrel jack + protection + 2x buck + 1V8 LDO,
  off the analog spine.
- Test points along edges; same-signal injection header near the ADC spine.
```
