# ARCHITECTURE — crow-mic-pod-v2 (remote microphone POD, board a)

## What this board is

A passive-cable remote acoustic node. One Cat5e home-run from the central
recorder powers, references and (for calibration) drives it. The pod has NO
energy source, NO converter, NO clock, NO switching element. Signal flows
EAST→WEST: electret capsule (far east) → active-balanced line driver
(center) → ESD → RJ45 (west). The calibration transducer lives in the SW
corner, driven from central, and never touches the analog ground.

Board class = **analog-audio-pod** (skills/kicad-pcb/references/
floorplan-archetypes.md): sensor capsule → analog cell → line driver →
single cable port. 2-layer, GND = both-layer pours + stitch ring.

## Interfaces (the shared cable contract — honored, not owned)

The cable/pinout is the contract shared with the sibling CENTRAL board.
This POD honors it; it does not define it. ONE RJ45 jack (RJHSE-5384),
custom NON-ETHERNET pinout (T568-colour → net):

| RJ45 pin | Cat5e pair/colour | Net | Direction (pod POV) |
|---|---|---|---|
| 1 | orange tip | AUDIO_P | OUT (balanced hot) |
| 2 | orange ring | AUDIO_N | OUT (balanced cold) |
| 3 | green tip | 5V_BEEP | IN (transducer supply from central) |
| 6 | green ring | BEEP_SWITCHED_RETURN | OUT (return, switched low-side AT central) |
| 4 | blue ring | 5V_AUDIO | IN (pod supply from central) |
| 5 | blue tip | 5V_AUDIO | IN (paralleled with pin 4) |
| 7 | brown tip | GND_AUDIO | IN (analog ground / return) |
| 8 | brown ring | GND_AUDIO | IN (paralleled with pin 7) |
| shield / tabs | cable drain | (float at pod) | shield FLOATS at the pod; single-point bond at CENTRAL (ADR-0001) |

**Net-name note:** `GND_AUDIO` is the CABLE-CONTRACT name for the analog
ground/return pair (pins 7,8); on this pod it is implemented as the single
board net **`GND`** (native KiCad ground) — the netlist, electrical
invariants, and floorplan asserts all use `GND`. The two names are the same
node (cable-side vs board-side aliases), not two nets.

Blue pair (4,5) and brown pair (7,8) are each PARALLELED (two conductors
per rail) to halve delivery IR over the 25 ft run. Silk MUST carry
"NOT ETHERNET - CUSTOM 5V AUDIO PINOUT" + the full pin legend (ADR-0003).

## Signal chain (east → west)

    AOM-5024L-HD-R          OPA1678IDR (U1)                     RJ45 (J1)
    electret  ── Cin ──►  U1A non-inv  ── OUTA ──► Rout ─ Cout ─► AUDIO_P (1)
    (MIC_OUT)   1µF       gain +1.5           │                    │ D1 ch1
       ▲                                       └─► U1B inv ─► OUTB ─ Rout ─ Cout ─► AUDIO_N (2)
       │ 3.9k bias                                 gain −1                          │ D1 ch2
    VMIC_F ◄─ 100R+100µ ◄─ 5V_AUDIO                                    (TPD2E2U06 to GND_AUDIO)

- Vdiff(AUDIO_P − AUDIO_N) = (+1.5 − −1.5)·Vsig = **3·Vsig** = 3 V/V
  differential (symmetric ±1.5 split for best single-supply CMRR/headroom).
- Single +5V supply: VMID = 2.5V virtual ground (22k/22k + 10µF) is the AC
  reference for both stages; all outputs sit at 2.5V DC, blocked from the
  cable by the 10µF series coupling caps.
- ESD (D1, TPD2E2U06) clamps the two EXPOSED audio pins to GND_AUDIO, on
  the connector side of the coupling caps.

## Calibration transducer (SW corner, isolated)

    5V_BEEP (3) ──►┬─ LS1(+) ── LS1(−) ──►┬── BEEP_SWITCHED_RETURN (6)
                   │                        │        (low-side switched
                   └─ D2 SS14 (cathode↑)────┘         at CENTRAL)
                   └─ D3 SMAJ6.0A (populated over-clamp, cathode↑)

CMT-8504 is an INDUCTIVE magnetic transducer driven from central in coded
4 kHz bursts (5V, ~150 mA). D2 (SS14) freewheels the inductive kick back
into 5V_BEEP each time central opens the low-side switch; D3 (SMAJ6.0A) is
a POPULATED redundant over-clamp (same net orientation, cathode→5V_BEEP —
populated in the 2026-07-23 fix pass, D5, to resolve the P0-D assembly
defect; forward-conducts alongside D2 during flyback and clamps a >6 V
surge on 5V_BEEP). The 5V_BEEP / BEEP_SWITCHED_RETURN pair is
GALVANICALLY SEPARATE from 5V_AUDIO / GND_AUDIO on the pod — they meet only
at the central — so beeper switching current never shares the analog ground
(G8). This is the analog-audio-pod archetype's SW-corner switched block.

### BINDING CROSS-BOARD CONSTRAINT — the burst level is CAPPED at central

**This pod's preamp sets an UPPER BOUND on the LS1 drive that the sibling
`crow-recorder-central-v2` is allowed to apply. If that drive is ever raised
back to a plain 50 % duty, this board clips on its own calibration tone.**
Recorded here because a constraint recorded on only one side of a two-board
system is how it gets undone.

LS1 sits **45.61798 mm** from MK1 (pcbnew, sealed v1.3 board: LS1 (33.000,
46.000), MK1 (74.000, 26.000)), so the burst reaches the capsule at
`SPL(10 cm) + 20·log10(100.000/45.61798)` = `SPL(10 cm) + 6.8173 dB`, against a
U1 worst-case LINEAR INPUT COMMON-MODE ceiling of **101.3144 dB** (SBOS855E
§6.7 `VCM = (V−)+0.5 … (V+)−2`; mic sensitivity +3 dB at V+ = 4.75 V, the same
instant the burst peaks). That is finding **CAL-1** —
`08_reviews/2026-07-27_v1.3_adversarial-audit_first-principles.md`, re-derived
in `08_reviews/2026-07-28_v1.3_fix-verification_cal1.md`.

**The criterion changed 2026-07-28 (user decision).** CAL-1 as filed sized the
shortfall against the transducer's datasheet MINIMUM — the wrong tolerance end
for a CLIPPING problem, since the unit that clips is a LOUD one. The binding
case is now a unit on the datasheet's TYPICAL curve:

| LS1 output | burst at MK1 | shortfall vs 101.3144 dB |
|---|---|---|
| ds MINIMUM, 100 dB @10 cm | 106.8173 dB SPL | 5.5028 dB *(old basis)* |
| **ds TYPICAL, 104 dB @10 cm** (rev 1.04 p.3) | **110.8173 dB SPL** | **9.5028 dB** *(binding)* |

**It is fixed at CENTRAL, not here.** This pod's VMID divider was measured
unable to clear the guaranteed spec by ANY value (best +0.86 dB worst-case, and
its optimum sits at VMID ≈ 2.07 V — the OPPOSITE direction from the audit's
proposed 33k/18k). Central instead reduces the burst drive at duty **1/20**:

| model | attenuation | typical unit at MK1 | clears the ceiling by |
|---|---|---|---|
| NOMINAL `20·log10(sin(π/20))` | −16.1134 dB | 94.7039 dB SPL | +6.6105 dB |
| **WORST CASE** (gate RC + L-R) | **−11.9165 dB** | **98.9008 dB SPL** | **+2.4136 dB** |

**No copper, BOM or release on this board changes; v1.3 stays live and is NOT
superseded.**

The fix lives in `projects/crow-recorder-central-v2/05_firmware/cal_burst.c`
(`CAL_BURST_DUTY_NUM/DEN = 1/20`), because central has no analog level control
at all — its `PLUS5V_BEEP` is the 5 V rail through a ferrite bead with no
series resistor, one AO3400A switches all eight ports, and `BEEP_GATE` is a
2-node net between the XU316 GPIO and a 1 k series resistor. The GPIO waveform
is the only lever. Central's `01_docs/ARCHITECTURE.md` and `DETAIL_DESIGN.md`
carry the same rule and the full derivation.

**The margin now holds under the worst-case model**, not merely nominally —
central's self-test asserts the worst-case form as its fatal check. But
`sin(πD)` is NOT a conservative bound there, and the reason matters to this
board because the burst it receives is what is affected: an L-R term that is
**non-monotonic in duty** (conservative at 1/6, non-conservative at 1/12,
conservative again at 1/20) plus a **gate-RC duty bias** at central that
stretches the conduction window by up to **+6.19 µs — 49.5 % of the commanded
pulse** — together leave **+4.197 dB** of slack against the law. Central took
duty 1/20 rather than the least-clearing 1/14 precisely because that
uncertainty is larger than the criterion, and **the risk is asymmetric: a burst
that clips destroys this pod's channel, while a quiet one only costs SNR.**

Two things this does NOT do, stated so they are not assumed:
- **It does not resolve PSR-1.** The drive change is on the galvanically
  SEPARATE beep domain. PSR-1's dominant path is the 16 Hz R1·C1 mic-bias
  corner (−11.4 dB at 60 Hz), which nothing here touches.
- **It does not touch POE-1, DC-1 or MECH-1**, which remain open.

**This pod is an INSTRUMENT in central's bring-up procedure.** MK1 with the
recorder as the meter is the acoustic cross-check on the burst level
(acceptance: measured capsule level ≤ 101.3 dB SPL); central's TP11 scope
measurement is the electrical half. See
`projects/crow-recorder-central-v2/01_docs/CHECKLIST.md`, "Bring-up".

Benign side effects at this pod: the beep-loop burst current falls from
~150 mA to **~4–15 mA** (deep DCM; 5V_BEEP cable IR drop 0.19 V → ~0.01 V),
and MK1's headroom to its own 110 dB THD<3 % limit improves from 3.18 dB to
**15.30 dB** (typical unit) / 19.30 dB (minimum-spec).

## Power / budget (E-TOPO: no converter — externally powered)

(24AWG solid Cat5e ≈ 0.084 Ω/m; 25 ft = 7.62 m. ROUND-TRIP resistance below —
corrected 2026-07-23 per the topology red-team P2: the earlier table counted
only one leg.)

| Rail | Source | On-pod load | Delivery IR (25 ft Cat5e, round-trip) | Margin |
|---|---|---|---|---|
| 5V_AUDIO | central, pins 4+5 (paralleled) + return 7+8 (paralleled) | ~2 mA typ, <5 mA max | supply 0.32Ω + return 0.32Ω = **~0.64Ω → 3.2 mV @5 mA** | op-amp works to 2.7V — vast |
| GND_AUDIO | central, pins 7+8 (paralleled) | return | — | — |
| 5V_BEEP | central, pin 3 (single conductor) + return pin 6 (single) | 150 mA burst (transient) | 0.64Ω + 0.64Ω = **~1.28Ω → ~0.19V @150 mA** | transducer 1.0–6.0V — tolerant |
| BEEP_RET | central, pin 6 (switched) | 150 mA burst | (return leg of the 1.28Ω above) | — |

No E-TOPO topology to derive (no converter). No E-OFF (external supply,
de-energized by unplugging the cable / powering down central). No E-MARGIN
brownout risk (5 mA over a paralleled pair). All recorded in
03_src/rules/power_tree.yaml.

## Protection posture (ADR-0001)

1. **ESD on the exposed audio pair** — TPD2E2U06 (D1), 2 channels, at the
   RJ45. The outdoor cable is the ESD/surge aperture; the op-amp outputs
   are the exposed nets.
2. **Inductive flyback** — SS14 (D2) across the transducer, clamp AT the
   driven (pod) end; POPULATED SMAJ6.0A (D3) redundant over-clamp (D5).
3. **Beep-return isolation** — the switched pair never bonds to analog GND
   on the pod (G8).
4. **Shield bond** — RJ45 shield/tabs FLOAT at the pod; the cable shield is
   single-point-ground bonded at the CENTRAL star ground (ADR-0001 dec. 4 —
   both-end bonding on six 25 ft home-runs would form six ground loops). The
   "SH" pads carry no net on this board.
5. **No reverse-polarity FET AND no PoE-injection protection on pod power**
   (BRIEF D3/A1) — keyed RJ45 + mandatory NOT-ETHERNET labeling, ~5 mA load,
   controlled fixed install. The custom power pins 4,5/7,8 alias exactly onto
   802.3af/at Alternative-B PoE (5V_AUDIO ties to U1 V+, abs-max 40 V, with
   zero series impedance), so a PoE switch or a mis-crimped cable is
   DESTRUCTIVE. This exposure is an ACCEPTED deployment-constraint waiver with
   USER sign-off — the pod is never plugged into PoE infrastructure (ADR-0005,
   ADR-0001 amended). No protection network, no re-pin, this rev.

## Fab / stackup

2-layer, fab_tier = jlc_2layer_default (0.6/0.3 vias, 0.15 track floor,
no advanced option). GND = F.Cu + B.Cu pours + stitch ring. Power/signal as
DRU-floored tracks. See 03_src/rules/nets.yaml + power_tree.yaml.
