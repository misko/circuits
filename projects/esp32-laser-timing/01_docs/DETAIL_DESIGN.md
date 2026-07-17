# DETAIL_DESIGN — esp32-laser-timing

Every component value with its derivation. Circuit prescriptions marked
(P#) are user-pinned by the brief and not re-derived.

## Photodiode channels (x3) — P6

**Load resistor R_load = 1k (P6, pinned).** BPW34 photoconductive,
cathode at 5V via terminal pin 1, anode into the node. Expected
photocurrent 0.5–3mA under direct 650nm/5mW illumination ->
V_node = I_pd x 1k = 0.5–3V lit, ~0V blocked (dark current nA-class).
Max node voltage 3V < VCC(5V) − 1.5V = 3.5V common-mode ceiling of the
LM339 on the 5V rail — the reason the LM339 is 5V-powered (P6, pinned).

**Threshold divider: 10k top / 2.7k bottom, off 3.3V (A1: fixed).**
Vth = 3.3 x 2.7/(10+2.7) = **0.702V** ≈ 0.7V target (P6). Thevenin
impedance 2.13k; LM339 input bias 25–250nA gives < 0.5mV offset. 1%
resistors: Vth spread ±1.1%. Three independent dividers (brief wording
"the three fixed dividers"); the -IN side carries no feedback, so
dividers see no switching disturbance.

**Hysteresis: Rf = 33k from output to +IN.** With node source impedance
1k (the load R; the photodiode is a current source) and output pullup
Rpu = 10k to 3.3V:
- Output released: V_out = 3.3 − 10k·(3.3−0.7)/(10k+33k) = 2.70V;
  node Thevenin gain (1k∥43k)/43k → falling trip at I_pd·1k = 0.641V.
- Output low (V_OL≈0): rising trip at I_pd·1k = 0.7016·(1k+33k)/33k
  ≈ 0.723V.
- **Hysteresis ≈ 88mV** ≈ "roughly 100mV" (P6). No capacitors anywhere
  in the path (P6); LM339 response 1.3us dominates channel latency and
  is identical across channels.

**Output network: open-collector, Rpu = 10k to 3.3V (P6, pinned).**
Logic-high = 3.3V (MCU-safe); rise time ~10k x (LM339 output cap +
trace+GPIO ~15pF) ≈ 150ns — well under the microsecond requirement.
Fall is active (comparator sinks, 16mA capable): fast edge on the
beam-interruption direction.

**4th comparator (D13):** +IN4 -> GND, −IN4 -> VTH3 (retied for routability, D13; doc corrected 2026-07-17 — was written as 3V3) (defined levels,
output transistor on, output pin floating per P6).

## Laser channels (x3) — P5

AO3400A low-side switch: R_DS(on) 48mΩ @ VGS 2.5V -> at 40mA the drop
is 2mV; fully enhanced at 3.3V gate. Gate network 100R series (damps
gate ringing, limits GPIO transient current to 33mA < 40mA pad rating)
+ 100k pulldown (off at boot: ESP32 GPIOs are high-Z during reset;
100k holds VGS < 50mV) — both pinned by P5. Switching load 40mA
resistive; wire inductance ~0.5uH/50cm pair stores 0.4nJ at turn-off —
absorbed by the FET's 30V avalanche rating (ADR-0001).

## Buttons (x3) — P9

10k pullup to 3.3V; switch closes to GND: idle 3.3V, pressed 0V,
0.33mA contact wetting current. 100nF at the node: tau(discharge
via wire) fast, tau(charge)=10k·100n=1ms debounce corner. 1k series
into the GPIO isolates the MCU from the 50cm wire (with the internal
clamps this bounds fault current; ADR-0001). All values pinned by P9.

## Power — P3/P4

- **LDO**: AMS1117-3.3 (basic, C6186). Dropout 1.1V @ 800mA < 5−3.3 =
  1.7V margin. Dissipation: WiFi peak 355mA -> (5−3.3)·0.36 ≈ 0.61W
  peak, ~0.2W average; SOT-223 on a 3V3 tab pour (θJA ≈ 60°C/W with
  ~1cm² copper -> +37°C peak, transient) — acceptable for a bench
  instrument.
- **LDO caps**: 22uF/25V X5R 0805 on input AND output (P3 asks
  10–22uF; 25V rating at 5V = minimal DC-bias derating, effective
  ≥ 12uF). Same basic part reused at the module (D12).
- **Module decoupling**: 22uF + 100nF at pad 2 (3V3), per Espressif
  hardware design guidelines (>=10uF + 0.1uF).
- **Bulk**: 100uF/16V aluminum electrolytic near the laser terminals
  (P4 ≥100uF): sources the 120mA laser load steps so they never appear
  on the USB cable; 16V = 3.2x rating margin. Plus 100nF ceramic beside
  it.
- **Every IC power pin 100nF** (P4): LM339 VCC, module 3V3, plus OLED
  header VCC (the display module is an "IC" on a cable).
- **EN reset RC (D7)**: 10k pullup + 1uF to GND -> tau 10ms; satisfies
  the >50us EN-after-3V3 requirement with margin; RESET tactile shorts
  EN to GND.
- **USB CC**: 5.1k pulldowns on CC1+CC2 (P3, UFP sink advertising
  default USB power).
- **Current budget**: see ARCHITECTURE power tree; worst case ~0.55A
  < 1A budget (P4).

## OLED header — P8

4.7k I2C pullups to 3.3V (P8): 400kHz I2C on ~10cm module wiring,
rise tau = 4.7k x ~50pF = 235ns < 300ns limit. Header order
GND/VCC/SCL/SDA with prominent silk warning (swapped-pin modules).

## USB — P3

Native USB full-speed. USBLC6-2SC6 flow-through on D+/D− (pinned);
its pin-5 VBUS reference also gives a 5V-rail ESD clamp (ADR-0001).
No series resistors: the S3's integrated USB PHY expects direct
connection. D+/D− as a pair, connector -> ESD -> IO20/IO19.

## Timing-path care (task requirement)

The three COMP traces are placed to be similar length (LM339 sits
equidistant-ish from the module's IO4/5/6 corner; audit checks length
spread < 40mm) and routed away from the LSW drain traces and the FET
corner. At 1.3us comparator response and 80MHz+ capture clocks, the
residual sub-ns trace skew is negligible — the dominant fixed offset is
the LM339 response time, common-mode across channels; channel-to-channel
matching is what matters and is set by comparator + threshold matching,
not trace length.

## Value -> BOM summary

| Value | Qty | Where |
|---|---|---|
| 100R 0805 | 3 | laser gate series |
| 1k 0805 | 7 | PD loads x3, button series x3, LED |
| 2.7k 0805 | 3 | divider bottoms |
| 4.7k 0805 | 2 | I2C pullups |
| 5.1k 0805 | 2 | CC pulldowns |
| 10k 0805 | 10 | comp pullups x3, divider tops x3, button pullups x3, EN |
| 33k 0805 | 3 | hysteresis |
| 100k 0805 | 3 | gate pulldowns |
| 100nF 0805 | 7 | LM339, module, buttons x3, OLED VCC, bulk partner |
| 1uF 0805 | 1 | EN RC |
| 22uF 0805 | 3 | LDO in/out, module |
| 100uF elec | 1 | 5V bulk |
