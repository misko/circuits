# Fresh-context pin review — shitty-kitty v1.0 (2026-07-18)

Method: pin_audit.py generated conclusion-free dossiers (pad positions/sides,
computed winding, board nets); FIVE fresh-context agents (no session context)
independently derived each expected pinout from the datasheet figure/table and
judged every pin. Protocol: kicad-pcb/references/pin-review-protocol.md.
Gate = zero FAIL. Result: **PASS** (0 FAIL; 2 QUESTIONs resolved below).

| Part | MPN | Verdict | Key checks |
|---|---|---|---|
| U1 | ESP32-S3-WROOM-1-N8R2 | PASS* | winding CCW pin1 top-left NON-mirrored; 40 pads + EP41 on GND; USB_DP/DM pins 14/13 not swapped; strapping pins (IO0 boot, IO45/46/3) unloaded; IO35-37 free (quad PSRAM); *UART resolved below |
| U3,U4,U5,U6 | MPR121QR2 x4 | PASS | all CCW no-mirror; ADDR distinct → **0x5A/5B/5C/5D**; VREG/REXT not on rails; VDD=3V3, VSS/EP=GND; 6 electrodes/chip = 24 total |
| U2 | TMC2209-LA-T | PASS | CCW no-mirror; EP=GND; VS=12V; OA/OB→MOT_A1/A2/B1/B2 no A/B swap; BRA/BRB sense correct; ENN pull-HIGH via R8 10k→3V3 (motor DISABLED at boot) |
| U7 | LIS2DH12TR | PASS | bottom-view datasheet reconciled to top-view — NOT mirrored; VDD/VDD_IO=3V3; CS=3V3 (I2C); SA0=GND (0x18); RES=GND; INT1=ACC_INT |
| U8 | AP63205WU-7 | PASS | CCW no-mirror; FIXED-5V variant → FB tied to 5V VOUT (datasheet Fig21); EN→VIN_12V always-on (within 35V abs-max); SW→L1; BST cap |
| U9 | AMS1117-3.3 | PASS | pin1=GND, pin2=VOUT(=tab)=3V3, pin3=VIN=5V — no VIN/VOUT swap |
| D1 | USBLC6-2SC6 | PASS | CCW no-mirror; I/O1(1,6)=USB_DP, I/O2(3,4)=USB_DM, pin5=VBUS, pin2=GND |
| J2 | TYPE-C-31-M-12 | PASS | VBUS/GND/shield correct; DP/DM row-tied pairs; CC1/CC2 distinct via R4/R5 5.1k Rd (sink); SBU NC (data-only) |
| J3,J4 | 1x13 electrode hdr | PASS | pins 1-12 = INNER/OUTER 1-12 (each once), pin 13 = GND shield; no electrode on a rail |
| J5 | JST XH-4 (B4B-XH-A) | PASS | pin1-4 = MOT_A1/A2/B1/B2; coil A & B pairs adjacent; no coil pin on rail/GND |
| J8 | 1x6 host header | PASS* | 5V/5V/GND/GND/HOST_TX/HOST_RX; *UART resolved below |
| SW1,SW2 | TS-1187A | PASS | BOOT/EN on top rail, GND on bottom rail (opposite internal rails) — press shorts strap→GND, NO permanent short |
| J1 | DC-005C-20A | PASS | center-positive verified: pad1=TIP=VIN_RAW(+12V), pad2=SLEEVE=GND, pad3=SWITCH=GND (twin adjudication + part.yaml Rev A) |
| J6 | KF128L-3.5-2P | PASS | pad1=ENDSTOP_N, pad2=GND (endstop screw terminal) |

## Resolved QUESTIONs

- **U1 pins 36/37 & J8 UART TX/RX direction** (raised by ESP32 + connector
  reviewers, unresolvable from dossier alone): net HOST_TX = U1 pin37 TXD0
  (module transmit), silk-labeled "TX" on J8 pad5; HOST_RX = U1 pin36 RXD0
  (module receive), silk "RX" on J8 pad6. Labels are BOARD-PERSPECTIVE per
  decision D8 (header spec "5V 5V GND GND ESP_TX ESP_RX"). Standard board-side
  convention: user crosses over in the cable (board TX → host RX). No swap.
  → ORDER_README notes "TX/RX are board-side".
- **J8 5V supply** vs 3V3: 5V is intended (host budget 1.5A on 5V, D5/P6). OK.

## No FAILs. No mirrors. No swapped power/rail/coil pins. Order not blocked.
