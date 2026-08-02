# Architecture — programmable USB 2.0 hub

## Functional partition

The board is a self-powered USB2517I seven-port USB 2.0 high-speed hub. Four
ports feed external USB-A sockets, port 5 connects an internal STM32G0B1
management device, and ports 6-7 are disabled by configuration.

```text
USB-B upstream -> USBLC6 ESD -> USB2517I

hub ports 1..4 -> FSUSB42 physical data disconnect -> USBLC6 ESD -> USB-A
hub PRTPWR ----+-> 74LVC08 AND -> TPS259470 EN -> switched 5 V / 2 A
MCU command ---+                     |-> FLT and ILM telemetry

hub port 5 -> STM32 management USB device
STM32 -> power/data commands, FLT, VBUS/ILM ADC, hub SMBus/reset
host utility -> MCU telemetry plus operating-system attach/enumeration state
```

Every externally visible port has independent power enable, fault/current and
post-switch voltage sensing, plus a separate D+/D- disconnect switch. Hardware
pull-downs hold power off and pull-ups hold data disconnected through reset.
The MCU reports commanded and electrical states; the host utility owns the
separate claim that a child device actually attached or enumerated.

## Power tree

```text
12-24 V terminal -> 10 A fuse -> LM74810 + BSC016N06NS back-to-back FETs
  -> VIN_PROTECTED -> SMBJ24A
       +-> LM5116/AON6266E buck A -> 5V_A / 4 A -> ports 1,2
       +-> LM5116/AON6266E buck B -> 5V_B / 4 A -> ports 3,4
       +-> AP63203 fixed 3.3 V buck -> hub, MCU and control logic
```

Both LM5116 cells run at approximately 99 kHz nominal; 110 kHz is the bounded
high corner used for maximum gate-drive current. Their effective feedback top
leg is 3.92 kOhm 0.1% plus 11 Ohm 1%, over 1.21 kOhm 0.1%. The calculated
5.0769-5.2478 V window funds a 135 mOhm complete path at 2 A with 20% loss
margin. Each TPS259470 uses 1.47 kOhm ILM, giving approximately 2.02-2.52 A
over tolerance. ADR-0004 contains the arithmetic and module trade studies.

The 24.0 V input ceiling includes source tolerance and ripple. SMBJ24A's
38.9 V specified clamp remains below the 60 V power devices. AP63203's exact
absolute-maximum table admits 40 V for less than 400 ms, covering the declared
1 ms clamp waveform; first articles still measure layout-induced overshoot.

## USB and RF/SI topology

All USB pairs target 90 ohm differential geometry on L1 over uninterrupted L2
ground using 0.25 mm width and 0.15 mm gap on the declared JLC04161H-7628
four-layer stack. Exact-board RF reviews grade topology, return continuity,
uncoupled launches, via transitions and switch-node separation. The order-time
impedance calculator/coupon and USB 2.0 eye/packet testing remain first-article
acceptance checks, not assumptions.

## Physical architecture

The 130 mm x 90 mm four-layer board places four USB-A mouths along the north
edge, USB-B on the west edge, and input power/fuse at the south-west. Hub,
crystal and USB switching occupy the low-noise center. Per-port protection sits
behind each receptacle. The two buck hot loops remain in the south/east power
region, with switch nodes kept away from the USB bank. Four M3 holes, SWD
access, fuse access and functional silk remain available after assembly.

## Startup and fault behavior

1. Protected input and 3V3 logic start; power commands default low and data
   disconnect commands default high.
2. The MCU configures the USB2517I while hub reset is asserted, then releases
   it. External ports remain off until host commands arrive.
3. Port power requires both hub policy and the MCU command through hardware
   AND logic. A fault is limited by the eFuse, reported to hub and MCU, and
   latched off by firmware.
4. Removing the external feed is the whole-board de-energization method.
