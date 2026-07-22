# ARCHITECTURE — cook-loadcell

55 x 45 mm 2-layer board under the appliance platform. One HX711 (U1),
its excitation transistor (Q1 S8550), the bridge-node network, six XH
connectors, test points. BOM ≈ $4 (target < $20).

```
 J1..J4 (XH-3: B/R/W per 50kg half-bridge)     J5 (XH-5: full bridge + SH)
      ring splices B(n)-W(n+1) on board             │
      RED taps ──► bridge nodes: E+  S+  E-  S- ◄───┘
                        │    │    │   │
   Q1 S8550 ◄─ BASE ────┤    ├────┼───┤        (E+ = AVDD ≈ 4.3V, D2)
   5V ─► Q1 ─► E+/AVDD  │  INA+  INA- │  E- = AGND = GND
   VFB divider 20k/8.2k ┘              │
   U1 HX711: DVDD=3V3, RATE=JP1 (10/80SPS), XI=GND (internal osc)
   DOUT/PD_SCK ─ PESD ─ J6 (XH-5: 5V 3V3 GND DAT CLK) ─► cook-hub J6
```

Layers: F.Cu components/short analog stubs + GND pour; B.Cu solid GND.
Analog corner (bridge nodes + INA pins + VFB) NW; digital + power SE.
Channel A gain 128 fixed (INB unused, tied AGND per DS). Shield bond D4.

§3.7 compliance map: (a) separate daughterboard ✓ (b) both sensor modes by
population (D1) ✓ (c) shield termination (D4) ✓ (d) JP1 rate select,
default 10 SPS (D3) ✓ (e) analog nodes < 15 mm, guarded, no relays/clocks
on this board; DAT/CLK on the far edge ✓ (f) TP set (D8) ✓ (g) no cal
storage on board ✓.
