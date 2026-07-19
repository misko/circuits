# DETAIL_DESIGN — ble-bus-bar

Every schematic value derives from a line here. Datasheet facts cite
`02_parts/<MPN>/part.yaml`.

## 1. Ampacity (THE crux — ADR-0002)

Conservative IPC-2221 external-conductor model (more pessimistic than
IPC-2152 with nearby copper, which is the margin direction we want):

I = 0.048 · ΔT^0.44 · A^0.725  (A in mil², ΔT °C rise, external layer)

2 oz copper = 2.74 mil thick. Design rise ΔT = 30 °C over a 40 °C
ambient → ≤70 °C copper.

| Path | I | A needed | width @2oz single | built as | margin |
|---|---|---|---|---|---|
| Trunk | 60 A | 2374 mil² | 22.0 mm | F.Cu 16.5 mm + B.Cu 16.5 mm paired pours = 33 mm eq. | 1.50× |
| Port (fuse→shunt→stud) | 30 A | 911 mil² | 8.5 mm | F.Cu pour 10.5 mm single layer | 1.24× (ΔT ≈ 21 °C at 10.5 mm) |
| Electronics tap | 0.6 A | — | 0.5 mm floor | tracks | ≫2× |

- Layer pairing is via THT parts, not via farms: the input stud barrel
  and all 24 fuse-holder THT pins bond F.Cu↔B.Cu inside the trunk band,
  so each fuse is fed from both layers in parallel.
- Local necks: the pour narrows to the shunt pad width (5.71 mm) for
  ~3 mm at each shunt. The IPC curve (infinite trace) predicts ΔT≈53 °C
  there, but axial conduction into the 10.5 mm pours a few mm away
  dominates for a 3 mm neck; treated as a documented hotspot, not a
  violation. The shunt element itself rises only ≈2.7 °C (see §3).
- Port continuous rating note: ATO/ATC fuses are conventionally derated
  to 80 % for continuous load — a 30 A fuse means ≈24 A continuous per
  port in practice; 30 A is the peak/rating bound (P2). Aggregate is
  the user's responsibility to keep ≤60 A (A1); the trunk survives any
  single-port 30 A regardless of distribution.
- Ampacity floors ride into DRC as netclass minimum-width rules
  (`rules/nets.yaml` → `.kicad_dru`): TRUNK/PORT 3.0 mm track floor
  (pours carry the current; the floor makes any accidental thin power
  track a hard DRC error), KELVIN rule areas scoped down to 0.30 mm.

## 2. Fusing

- Port fuses: ATO/ATC blade, user-supplied, ≤30 A (A3). Holder:
  Keystone 3557-2, UL 30 A @ 500 V AC, THT (02_parts/3557-2).
- Electronics tap fuse F7: Littelfuse 0466002.NRHF, 2 A fast, 63 V
  rated. Buck peak input current: Iout·Vout/(Vin·η) = 0.6·3.3/(12·0.8)
  = 0.21 A max continuous → 2 A gives ≈10× headroom yet blows on a
  shorted TVS/buck (fault current ≫ 2 A).

## 3. Shunt + sense chain (ADR-0003)

- Shunt RS1..6: Vishay WSLP2726 L5000 (0.5 mΩ ±1 %). At 30 A:
  V = 15 mV, P = I²R = 0.45 W; element θ = 6 °C/W (datasheet table) →
  ΔT ≈ 2.7 °C. Rated to 12 W-class construction — ≥10× thermal margin.
- Monitor U1..6: INA238AIDGSR (16-bit, I2C, ±40 V diff abs-max, −0.3 to
  +85 V common-mode abs-max — survives SMCJ33A-clamped load dump
  (≤53.3 V) with 31 V of headroom; the 36 V INA226 does not. ADR-0003).
- Range: ADCRANGE = 1 → ±40.96 mV full scale; 30 A → 15 mV (37 % FS).
  Shunt LSB = 1.25 µV → 2.5 mA/LSB current resolution. A dead-short
  fault (~hundreds of A until the fuse clears) produces <0.5 V
  differential — far inside the ±40 V diff abs-max.
- Input filter (per INA238 datasheet §applications): 10 Ω series in
  IN+ and IN− + 100 nF differential across them at the device:
  f_c = 1/(2π·(10+10)·100 nF) ≈ 80 kHz — kills conducted switching
  noise, passes load dynamics. 10 Ω keeps gain error from input bias
  negligible (INA238 IB ≈ nA-class).
- VBUS pin: sensed at the PORT side (VPi) through a matched 10 Ω — a
  blown fuse reads as VBUS collapsing to the load-pulled level while
  current reads 0: fuse-out detection for free.
- Kelvin: sense taps attach at the shunt pad inner edges through the
  pad gap (audit I-KELVIN); pours feed current from the opposite edges.
- I2C addresses (A1,A0 straps): U1 (GND,GND)=0x40, U2 (GND,VS)=0x41,
  U3 (GND,SDA)=0x42, U4 (GND,SCL)=0x43, U5 (VS,GND)=0x44,
  U6 (VS,VS)=0x45. ALERT is shared open-drain, one 10 kΩ pull-up.

## 4. Input protection (ADR-0001)

- Bus TVS D9: SMCJ33A — standoff 33 V (clears a 24 V system's 28.8 V
  charge voltage with margin), V_BR 36.7 V, clamp ≤53.3 V @ 28 A
  (1500 W/10 ms). Everything on the bus is rated beyond the clamp:
  INA238 85 V, LMR16006 abs-max 65 V (operating 60 V), SS310 100 V.
- Electronics branch: F7 2 A fuse → D7 SS310 series schottky (reverse
  blocking, 100 V, Vf ≈ 0.45 V @ 0.2 A → 0.09 W) → D10 SMBJ33A local
  clamp + input caps at the buck.
- Reverse polarity at the bus (no series element is realistic at 60 A):
  D9 conducts forward and holds the reversed bus near −1 V; INA input
  pins see −1 V through 10 Ω (≈70 mA into ESD structures — above the
  5 mA abs-max, tolerable for the seconds a first-power check lasts,
  fatal if sustained). D7 blocks the electronics entirely. Mitigations:
  oversized silk polarity marks at both input studs, ORDER_README
  first-power polarity ritual. Residual risk accepted and documented.
- UVLO: buck SHDN divider 560 k/100 k from VIN_E: enable threshold
  1.25 V (part.yaml) → V_on = 1.25·(660/100) = 8.25 V — below any
  sagging 12 V battery worth logging, above the buck's dropout
  region; firmware also watches VBi (INA bus voltage) and flushes the
  log ring to flash below 10 V. SHDN at 30 V bus = 30·100/660 = 4.5 V,
  within the pin's high-voltage tolerance (part.yaml).

## 5. Buck (12–24 V → 3.3 V, ADR-0006)

LMR16006XDDCR: 60 V, 0.6 A, fixed 0.7 MHz (X version — part.yaml;
2.1 MHz Y version would violate min-on-time at 24 V→3.3 V:
D = 3.3/24 = 0.14 vs t_on_min·f ≈ 0.17).

- FB divider: V_FB = 0.765 V → R_top/R_bot = 3.3/0.765 − 1 = 3.31.
  R13 = 33 kΩ / R14 = 10 kΩ → V_out = 0.765·4.30 = 3.29 V.
- Inductor L1 = 22 µH (SWPA6045S220MT): ΔI_L = V_out·(1−D)/(L·f) =
  3.3·0.86/(22 µ·0.7 M) = 0.18 A p-p at V_in = 24 V. I_pk =
  0.4 + 0.09 = 0.49 A < 1.9 A saturation, < 1.1 A typ current limit.
- Catch diode D11: SS310 (100 V ≥ 2× max clamped input; 3 A ≫ 0.6 A).
- C_in: 2× 4.7 µF/50 V X7R 1210 (GRM32ER71H475KA88L) + 100 nF —
  ≥50 V rating for the 33 V-standoff bus with clamp headroom + DC bias
  derating. C_out: 2× 22 µF/25 V X5R 1206 (CL31A226KAHNNNE):
  ΔV = ΔI/(8·f·C) = 0.18/(8·0.7M·44µ) ≈ 0.7 mV ripple.
- C_boot: 100 nF CB→SW (datasheet standard value).

## 6. USB bench power + data (ADR-0006)

- TYPE-C-31-M-12 receptacle, CC1/CC2 → 5.1 kΩ Rd (UFP sink default).
- VUSB → U9 AMS1117-3.3 (10 µF in / 22 µF out) → D8 B5819W → 3V3:
  rail ≈ 3.0 V in USB-only mode — inside ESP32-C3 (3.0–3.6 V), W25Q64
  (2.7–3.6 V), INA238 VS (2.7–5.5 V) operating ranges. When the bus
  powers the board, the buck's 3.29 V wins and D8 is reverse-biased;
  buck back-feed into the dead LDO is blocked by D8. USB never powers
  the bus (no path).
- USB data: D+/D− direct to IO19/IO18 through U10 USBLC6-2SC6 ESD array
  (native USB-Serial-JTAG — flashing with no UART bridge).

## 7. MCU + memory (ADR-0004)

ESP32-C3-WROOM-02-N4 (BLE 5.0, 4 MB internal flash for app+OTA).
Dedicated logging flash U11: W25Q64JVSSIQ 8 MB SPI NOR (P5's "onboard
memory" is a first-class part, not a leftover of the app partition):
at one 16-byte stats record per port per 10 s, 8 MB ≈ 10 months of
wear-leveled ring.

Pin map (module pin = physical pad from part.yaml):
| Module pad | GPIO | Net | Function |
|---|---|---|---|
| 3 | IO4 | SDA | I2C to 6× INA238 (4.7 kΩ pull-up R15) |
| 4 | IO5 | SCL | I2C clock (4.7 kΩ pull-up R16) |
| 5 | IO6 | SPI_CLK | W25Q64 CLK |
| 6 | IO7 | SPI_MOSI | W25Q64 DI |
| 16 | IO2 | SPI_MISO | W25Q64 DO (strap: 10 kΩ pull-up R18 — DO is Hi-Z while CS high) |
| 10 | IO10 | FLASH_CS | W25Q64 /CS (10 kΩ pull-up R19 keeps flash deselected at boot) |
| 15 | IO3 | ALERT | shared INA238 ALERT (10 kΩ pull-up R17) |
| 17 | IO1 | LED_ST | status LED (1 kΩ) |
| 7 | IO8 | IO8 | strap, 10 kΩ pull-up R20, else free |
| 8 | IO9 | BOOT | boot button SW2 to GND (internal + strap default) |
| 2 | EN | EN | 10 kΩ pull-up R21 + 1 µF C_EN + reset button SW1 |
| 13/14 | IO18/IO19 | USB_DM/DP | native USB via USBLC6 |
| 11/12 | IO20/21 | RXD/TXD | J10 debug header 1×4 (DNP) |

W25Q64 /WP (pad 3) and /HOLD (pad 7) tie to 3V3 (quad-IO unused).

## 8. Indicators / misc

- LED1 (green, KT-0805G) 3V3 power: R = (3.3−2.1)/2 kΩ ≈ 0.6 mA (dim
  intentionally — always-on device).
- LED2 (green) on IO1 via 1 kΩ ≈ 1.2 mA.
- Decoupling: 100 nF at every INA238 VS, module 3V3 (+ 22 µF bulk),
  W25Q64 VCC, AMS1117 in/out per §5–6.
- All resistors E24 1 % UNI-ROYAL 0805 (fleet standard).
