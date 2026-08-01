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

## 2026-07-31 22:15 — iterate 2
- did: Cross-built the target in an isolated environment with Pico SDK 2.1.1 at `bddd20f928ce76142793bef434d4f75f4af6e433` and Arm GNU Toolchain 13.3.Rel1, board target `waveshare_rp2040_zero`.
- result: Link and UF2 generation PASS. ELF size is 88,776 bytes text + 4,500 bytes BSS; initial UF2 sha256 was `0601fc02a826818b4fea2e67312bddb9a1c6b0b947463aaa1c894070508a7df3` before the DMA ring correction.
- next: Flash and exercise USB CDC on a physical RP2040-Zero; the cross-build closes source/API compatibility, not hardware behavior.

## 2026-07-31 22:20 — iterate 3
- did: Audited the Pico-SDK DMA shell after the first real target build and checked `channel_config_set_ring` against the SDK API's address-side boolean.
- result: Found and fixed a P0 control defect: `true` ringed the fixed TX-FIFO write address, so the incrementing DMA read address would walk beyond the eight-word schedule after the first frame. It is now `false` (read-side ring), with a source-level regression test pinning read-increment/write-fixed/ring-read as one invariant.
- result: Seven host tests PASS and the corrected real target cross-build PASSes; corrected UF2 sha256 is `7b884c032870ea50ed9784738b7992621c53e9c09227584cb06c22d971690d66`.
- next: Retain physical logic-analyzer confirmation as an independent bring-up gate.
