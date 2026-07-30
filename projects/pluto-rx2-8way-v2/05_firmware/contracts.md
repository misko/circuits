# contract: 05_firmware/

**Purpose** — code that runs ON the board. Optional; delete this folder if
the board has no MCU.

**Mutability** — hand-edited.

## Allowed

| Path | What |
|---|---|
| `*.c\|*.h\|*.rs\|*.py` `src/**` `include/**` | the firmware — sources at the top level, or at any depth under `src/`/`include/`. **The pipes are BACKSLASH-ESCAPED because this is a markdown table cell**: an unescaped `\|` inside a code span is still a cell delimiter, and the auditor read this row as `*.c` alone until 2026-07-28, so every `.h`, `.rs` and `.py` in the repo failed C-ALLOW while the contract said they were permitted. A firmware tree is arbitrary depth, so it takes DEEP patterns rather than a nested `contracts.md` per source folder |
| `Makefile` / build config | must take the MCU as a VARIABLE, not a constant |
| `tests/` | host-runnable logic tests |
| `README.md` | how to build, how to flash, which connector |
| `contracts.md` | this file |

## Rules

- **The MCU part number is a variable.** A part swap is a sourcing decision,
  not a rewrite: one board's ATtiny816 became an ATtiny1616 (pin- and
  register-compatible superset) purely because of stock, and the only
  firmware change should be `MCU=attiny1616`.
- **Separate the logic from the hardware shell.** A pure state machine that
  runs on the host is testable before silicon exists; the AVR/ARM shell is a
  thin wiring layer. One project shipped 11 green host tests of its
  battery-cutoff logic before a board was fabbed.
- **Document the hardware-default behavior** — what the board does with the
  MCU unprogrammed. If the power path is hardware-default-on (enable
  ladders, pull-ups), the board WORKS unprogrammed and quietly lacks every
  protection. That is a footgun and belongs in `README.md`.
- The programming connector and its pinout belong in `01_docs/ARCHITECTURE.md`;
  reference it, do not restate it.

## Validate

- MCU target is a variable and matches the part in the BOM / `02_parts/`
- host tests pass
- `README.md` states: build command, flash method, connector, and the
  unprogrammed-board behavior

## Repair

- Hardcoded MCU → parameterize; cross-check against `02_parts/`.
- MCU in firmware disagrees with the BOM → they diverged during a part swap.
  The BOM is what gets soldered; fix the firmware and its README.
