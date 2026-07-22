# pin dossier: LED1  (KT-0805G)

- footprint: LED_SMD:LED_0805_2012Metric
- board position: (93.0, 52.3) rot 0
- computed winding of pins 1..N: **n/a (too few perimeter pins)**
- datasheet: https://www.kento-led.com/
- part.yaml verification note: polarity fact pad1=cathode carried from crowsync-recorder/usb-power-3s footprint marker check (2026-07-14); re-verify green dot/cathode mark on first reel

Coordinates are FOOTPRINT-LOCAL mm, rotation undone; +y is DOWN
(so this table reads like the top view of the part on the board).

| pad | local (x,y) | side | size | function (part.yaml) | NET on board |
|---|---|---|---|---|---|
| 1 | (-0.94,+0.00) | W | 0.97x1.4 | K (cathode) -> GND | GND |
| 2 | (+0.94,+0.00) | E | 0.97x1.4 | A (anode) <- resistor | LED1A |
