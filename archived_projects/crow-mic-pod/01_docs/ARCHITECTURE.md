> Adopted 2026-07-21 from archived_projects/crow-array-pod (ADR-0005). Same Rev-A commission; RJ45 termination (v1.1 state) is the baseline here.

# crow-array-pod — architecture

Remote microphone pod of the Crow Acoustic Localization Array (commission:
../crow-array/01_docs/BRIEF.md, source sections 3/3A/4/8). One 2-layer board
per pod, 6 active + spares (order qty 10), living in a Hammond 1551WYBK IP68
enclosure at the end of a 30-35 ft custom-pinout Cat5e home run.

## Topology

```
                     Cat5e (NOT Ethernet, P4 pinout)
J1 RJ45 contact 1..8 (v1.1, ADR-0004) ======================  central board
 |1 AUDIO+   <- R10 68R <- OPA1678 A (x1.5, non-inv) <- C3 1u <- mic AOM-5024L
 |2 AUDIO-   <- R11 68R <- OPA1678 B (x-1 around VMID) <- from A out
 |3 +5V_BEEP -> R12 0R -> CMT-8504 (+)   [D2 SS14 flyback pop., D3 TVS empty]
 |6 BEEP_RET <- CMT-8504 (-)             (low-side switched AT CENTRAL)
 |4,7 +5V_AUDIO -> 5V rail -> R1 100R -> 5VF (mic bias + midpoint ref)
 |5,8 GND_AUDIO -> GND
 D1 TPD2E2U06 across AUDIO+/- at entry (populated, D5)
 L1 CM-choke footprint (EMPTY) bridged by R13/R14 0R; SHIELD pad + R15 (EMPTY)
```

## Power budget

| Load | Current | Source |
|---|---|---|
| Mic bias (3.9k from 5VF, capsule at ~3V) | ~0.5 mA | 5VF |
| Midpoint divider 10k+10k | 0.25 mA | 5VF |
| OPA1678 quiescent (2 ch) | ~4-5 mA | 5V |
| **Pod total (audio)** | **~6 mA** | 2x paralleled Cat5e pairs; drop ~4.5 mV over 35 ft (source doc §4) |
| Beeper burst (central-switched) | 150 mA pk | dedicated pair, ~0.27 V drop — never shares the audio loop |

The audio-supply and beeper-current paths share NOTHING but the board: the
beeper loop enters on J1.3, exits on J1.6, and its return current flows back
to the central board on its own pair (source doc figure 3 design intent).
Only the clamp (D2/D3) and R12 touch it locally.

## Signal chain gains and levels

- Mic sensitivity -24 dB re 1V/Pa => ~63 mV/Pa. Loud crow call at a few
  meters (~90-100 dB SPL ~ 0.6-2 Pa) => up to ~130 mVpk at the capsule.
- Stage A: non-inverting x1.5 around VMID (2.5 V) => ~200 mVpk.
- Stage B: unity inverter of A around VMID => differential output ~3 V/V
  total => ~400 mVpk differential, centered at 2.5 V. Headroom to the
  OPA1678 output limits (0.5-4.5 V at 5 V supply) is >4x — clipping starts
  near 116 dB SPL, above the mic's own 110 dB THD limit. PGA at the
  central PCM1865 does the fine ranging (source doc: start 0 dB).
- 68R per leg isolates the op-amps from ~35 ft of cable capacitance
  (~50 pF/m x 11 m ~ 0.5 nF per leg): f_RC ~ 4.3 MHz, phase margin
  preserved; audio-band effect nil.

## Boards/enclosure mechanics

Hammond 1551WY drawing (01_docs/hammond_1551wy_rev2023-08-31.pdf): max PCB
94.50 x 44.50 mm, four Ø2.60 holes on a 75.00 x 35.00 mm pattern whose
top-left hole sits 9.75 mm / 4.75 mm from the board corner, corners notched
(82.00 / 32.00 mm straight spans) to clear the #4 lid-screw bosses. The
board uses that maximum outline (D4): concave-arc corner cutouts, Ø2.7
mounting holes for the #2 self-tapping post screws.

Placement follows source §3A: microphone pads at the EAST end, transducer
at the WEST end near cable entry — maximum acoustic separation on the
board; the capsule itself mounts in its enclosure cavity on short leads.

## Deliberately configurable (P7)

| Feature | Ship state |
|---|---|
| Beeper clamp | D2 SS14 flyback POPULATED, D3 SMAJ6.0A TVS footprint EMPTY (D2#) |
| Beeper series element | R12 0R (swap point for a series R during range tests) |
| CM choke | L1 WE-SL2 footprint EMPTY; R13/R14 0R bridge the pair (D7) |
| Shield bond | TP6 SHIELD pad + R15 footprint EMPTY to GND (D7) |
| Gain | single-value R6/R7 (stage A) — change table in README/ORDER_README (D8) |
| ESD | D1 TPD2E2U06 POPULATED (D5) |
