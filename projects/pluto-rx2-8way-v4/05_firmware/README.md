# Pluto RX2 8-way v4 firmware

This tree contains a host-tested control core, a Pico-SDK shell for the
Waveshare RP2040-Zero, and a reference USB-CDC host utility. The target drives
GP0..GP3 as PE42482 V1..V4 and GP4 as the status LED. Manual state numbers are
1..8 and correspond directly to RF1..RF8. `OFF` drives V4 high, selecting the
PE42482 all-ports-terminated state.

The hardware default is important: an unprogrammed or reset-held module leaves
the carrier's four 10 kΩ pull-downs active, so V1..V4 = `0000` and RF1 is
selected. The board is receive-only and no RF power path depends on firmware,
but it is not muted until firmware accepts `OFF`.

## Build and flash

The module is a variable, not a hard-coded source assumption:

```sh
PICO_SDK_PATH=/path/to/pico-sdk make firmware MCU_BOARD=waveshare_rp2040_zero
```

Flash `build/pluto_rx2_8way_v4.uf2` by holding the module's BOOT button while
connecting its own USB-C connector, then copying the UF2 to the RPI-RP2 drive.
There is no carrier programming connector; the module USB-C/BOOT interface is
the programming and control connector documented in `01_docs/ARCHITECTURE.md`.
The target was cross-built on 2026-07-31 with Pico SDK 2.1.1
(`bddd20f928ce76142793bef434d4f75f4af6e433`) and Arm GNU Toolchain
13.3.Rel1 for `waveshare_rp2040_zero`. The resulting ELF measured 88,776 bytes
text + 4,500 bytes BSS; the UF2 sha256 was
`7b884c032870ea50ed9784738b7992621c53e9c09227584cb06c22d971690d66`.
The build proves the target API and link surface; flashing and USB behavior
still require a physical module.

Run all host-available tests with:

```sh
make test
```

## RX2CTL/1 USB-CDC protocol

One ASCII command and one `OK ...` or `ERR ...` response occupy one line:

- `INFO?`, `STATUS?`
- `SELECT 1` through `SELECT 8`
- `OFF`, `RUN`, `STOP`, `ZERO_COUNTERS`
- `CONFIG <sample_rate_hz> <ordinary_clean> <reference_clean> <blank>`

The defaults are 30,000,000 samples/s, 8192 ordinary clean samples, 4096
reference clean samples, and 128 blank samples. The resulting frame is 62,464
samples and the existing 499,712-sample host buffer holds exactly eight frames.
PIO emits one schedule cycle per nominal sample and DMA rings the eight state
words, preventing USB/CPU latency from stretching a dwell.

There is no Pluto sample-clock input on this carrier. The RP2040 PIO divider is
therefore free-running from the module crystal; `STATUS?` reports both requested
and quantized actual rate plus `sync=FREE_RUNNING`. Exact alignment to Pluto
sample indices is not claimed. Bring-up must correlate the RX1 reference marker,
measure long-run drift, and either calibrate the requested rate or revise the
hardware to accept a shared clock/trigger before treating the nominal sample
counts as phase-locked boundaries.

The reference host utility requires no dependency in simulation:

```sh
python3 host/rx2ctl.py --simulate status
python3 host/rx2ctl.py --simulate select 8
```

Real access requires `pyserial` and an explicit OS device, for example
`python3 host/rx2ctl.py --port /dev/ttyACM0 status`. Pico-SDK's default USB
identity is development-only; production VID/PID and product strings remain an
owner decision before distribution.
