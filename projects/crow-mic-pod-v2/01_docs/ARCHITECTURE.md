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
