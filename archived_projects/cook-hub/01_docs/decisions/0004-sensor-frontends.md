# ADR-0004 — Sensor front-ends (I2C buses, MAX31856, thermistors, door/E-stop)

- Two I2C buses because both SHT45s answer 0x44 (§3.4a): J3=I2C0
  (MLX90640 0x33 + ambient SHT45), J4=I2C1 (exhaust SHT45). Selectable
  pullups by 3-pin jumper per bus (2.2 k fitted / 4.7 k selectable, D11);
  33 Ω series damping; USBLC6-2SC6 low-C ESD (3.5 pF ≪ bus budget); TPs at
  connectors. Differential-extender option (§3.3g) deferred to the cable
  spec — records as §17 open item (cable <300 mm target).
- MAX31856MUD+T (C2653162, genuine ADI, $4.07/3.5 k stock): SPI0 CS0;
  datasheet input network (100 Ω/100 n diff/10 n cm, BIAS→T−); at NW edge
  next to keyed PCC-SMP-K socket (hand-solder, D9), diagonal-opposite the
  relay bank (§3.6a/b). Second CS → J15 DNP header for MAX31865 (D10).
- Thermistors: 10 k 1% refs (UNI-ROYAL 0603 F), RC 1 k/100 n, PESD clamps,
  spare third channel on GP28 (§3.10a: port + enclosure + spare).
- Door/E-stop: RC + Schmitt. E-stop uses a real 74HC14 stage because
  ESTOP_OK feeds the HARDWARE coil-rail AND-gate (can't rely on the Pico);
  door uses the RP2350's built-in input Schmitt (datasheet-documented) after
  RC — a second HC14 stage would add nothing (the door path is
  firmware-consumed only). EOL per D8.
- HX711 stays on cook-loadcell (§3.7a); J6 carries only DVDD-level digital
  (DAT/CLK) + power; USBLC6 on DAT/CLK at the connector.
