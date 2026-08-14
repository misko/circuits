# Firmware and field programming

The control timing source of truth is
`../03_src/rules/control_protocol.yaml`.  Do not hand-copy dwell values into
firmware or host analysis.  Regenerate both consumers from the project root:

```sh
python3 ../../skills/kicad-pcb/scripts/control_profile_codegen.py . --write
python3 ../../skills/kicad-pcb/scripts/control_profile_codegen.py . --check
```

The generated outputs are:

- `include/control_profile.h` for the STM32 firmware;
- `host/control_profile.json` for capture/decoder software.

The initial profile is `fast20-v1`, revision 1.  Its eight nominal antenna
dwells are 20, 23, 26, 30, 34, 39, 44 and 50 ms.  They are deliberately
different: the downstream decoder identifies the selected antenna by measured
dwell duration.  A requested change therefore means a new synchronized profile
revision, not a runtime command sent to the board.

## Direct Raspberry Pi SWD programming through J11

No programmer IC is required on the PCB. A Raspberry Pi can drive the STM32
SWD signals directly through OpenOCD using a keyed 10-pin Cortex cable plus a
small Pi GPIO breakout/adapter harness. The Cortex cable does not plug directly
onto the Pi's 40-pin header because the two connector pinouts differ. Power the
target normally through its USB-C connector; the Pi supplies logic signals and
a common ground only.

| Raspberry Pi | Physical pin | J11 pin | Signal |
|---|---:|---|---|
| GPIO11 | 23 | 4 | SWCLK |
| GPIO8 | 24 | 2 | SWDIO |
| GPIO24 | 18 | 10 | NRST (recommended) |
| GND | 20 | 3, 5 or 9 | GND |
| no Pi power connection | — | 1 | Target-powered VTref/3V3 sense only |

Do **not** connect Raspberry Pi 5 V or Pi 3V3 to J11 pin 1. Pin 1 is a
target-powered VTref/test point, not a supply input. A conventional debug probe
uses it to sense I/O voltage; a direct Pi harness may leave it open after
independently verifying that the USB-C-powered target rail is 3.3 V. J11 pins
6, 7 and 8 remain unconnected on this SWD-only target.

For Raspberry Pi 1–4, a typical OpenOCD invocation is:

```sh
sudo openocd \
  -f interface/raspberrypi-native.cfg \
  -f target/stm32c0x.cfg \
  -c "program firmware.elf verify reset exit"
```

For Raspberry Pi 5, use `interface/raspberrypi5-gpiod.cfg`.  Exact GPIO-chip
numbering and permissions remain host-image dependent and must be verified on
the programming Pi. An external ST-LINK remains the recovery and production
fixture fallback through the same standard J11 interface.

There is intentionally no runtime control protocol in v5.  Timing changes are
made by generating a new profile revision, rebuilding the firmware and decoder,
then reflashing over SWD.
