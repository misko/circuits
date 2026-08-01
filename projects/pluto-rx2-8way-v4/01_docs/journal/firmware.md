# Firmware journal

## 2026-07-31 21:30 — start
- did: Defined RX2CTL/1 and split the implementation into a hardware-independent C schedule/state core, RP2040-Zero Pico-SDK shell, and Python host utility.
- result: Manual states 1..8 map to PE42482 RF1..RF8, OFF maps to V4=1, and the default schedule computes 62,464 samples per frame and 499,712 samples per eight frames.
- next: Test the core and host paths without assuming unavailable target tools.

## 2026-07-31 21:42 — finish
- did: Compiled the C core with `-std=c11 -Wall -Wextra -Werror`, ran its executable test, ran six Python unit tests, and exercised simulated STATUS and OFF commands.
- result: C core PASS; 6/6 Python tests PASS; simulator reports the required 62,464-sample frame and `sync=FREE_RUNNING`. CMake correctly stops with `PICO_SDK_PATH is required` because this workspace has neither Pico SDK nor an ARM cross-compiler.
- next: Cross-build and exercise USB CDC/PIO/DMA on a fitted module; correlate the free-running schedule against Pluto samples before accepting timing.

## 2026-07-31 22:00 — iterate 1
- did: Hardened repeated RUN/STOP behavior by restarting the PIO execution state at schedule word zero and separated IRQ-observed counters from main-context state with interrupt-safe snapshots.
- result: Native C compilation remains warning-clean under `-Werror`; core executable PASS and Python host protocol tests PASS 6/6. Target compilation remains ungraded because `PICO_SDK_PATH` and an ARM cross-compiler are absent.
- next: Cross-build against Pico SDK, then confirm first-state timing and counters on a fitted RP2040-Zero with a logic analyzer.
