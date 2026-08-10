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
12-24 V terminal -> 10 A fuse -> LM74810 + CSD18533Q5AT back-to-back FETs
  -> VIN_PROTECTED -> SMBJ24A
       +-> LTC3889 buck A -> 5V_A / 4 A -> ports 1,2
       +-> LTC3889 buck B -> 5V_B / 4 A -> ports 3,4
       +-> LMR36510 -> AUX_6V -> LTC3889 EXTVCC
                              +-> AP63203 fixed 3.3 V -> hub, MCU, logic
```

Both LTC3889 channels run at 250 kHz and are commanded to 5.21484375 V. Each
4 A rail uses one 6.8 uH inductor and one 10 mOhm Kelvin shunt. The programmed
7.5 A peak-current threshold has a 6.733-8.283 A guaranteed corner range; its
low corner clears the 4 A load plus worst-case ripple and its high corner is
below the inductor saturation rating. The 5.183925-5.246075 V rail window
funds a 135 mOhm complete port path at 2 A with 20% loss margin. Each
TPS259470 uses 1.47 kOhm RILM, giving approximately 2.02-2.52 A over tolerance.
ADR-0007 contains the arithmetic and supersedes the unauthorized 3 A design.

The 24.0 V continuous input ceiling includes source tolerance and ripple. The
separate admitted transient is a 50 V maximum open-circuit, at least 1.6 ohm
Thevenin source with a 10/1000 us-or-shorter pulse. Against SMBJ24A's 26.7 V
minimum breakdown this bounds current to 14.563 A; even the independent
14.563 A x 38.9 V worst-case product is 566.5 W, below its 600 W rating. The
LM74810 disconnects Q2 within 5.7 us maximum. Q1/Q2/U1 tolerate the upstream
50 V ceiling; Q3-Q6/U2/U3 remain behind the 38.9 V protected-rail clamp. This
is not an automotive load-dump or lightning rating. AP63203 is cascaded from
regulated AUX_6V. First articles still measure layout-induced overshoot.

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
2. Hardware holds both LTC3889 RUN inputs low while the MCU writes and reads
   back the complete load-bearing PMBus image. A mismatch leaves both rails
   off. The MCU then releases the two 5 V rails and verifies power-good.
3. The MCU releases USB2517I reset so the configuration pins latch SMBus mode.
   The hub waits unattached while the MCU writes and reads back the complete
   image; only then does firmware issue `USB_ATTACH`. Ports 6-7 stay disabled.
4. Port power requires both hub policy and the MCU command through hardware
   AND logic. A fault is limited by the eFuse, reported to hub and MCU, and
   latched off by firmware.
5. Removing the external feed is the whole-board de-energization method.
