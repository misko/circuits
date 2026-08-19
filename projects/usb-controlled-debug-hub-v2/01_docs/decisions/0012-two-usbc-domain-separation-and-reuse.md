# ADR-0012: two USB-C domains and purchased-core reuse

- Status: accepted
- Date: 2026-08-18
- Decision owner: user for two connectors and reuse preference; engineering
  derivation for the isolation boundary
- Partially supersedes: ADR-0002 external screw-terminal input and ADR-0004
  connector/module disposition; all downstream v1 behavior remains inherited

## Context

The v1 board uses USB-B for upstream data and a separate 5 V screw-terminal
input. The user selected two USB-C connectors—one power and one data—and has
already purchased the current board's components. Combining power and data on
one Type-C port would either depend on host power or require a more complex
dual-role/source-selection architecture.

## Decision

Use two HRO TYPE-C-31-M-12 receptacles:

1. `J_DATA` is a USB 2.0 upstream-facing data port. Its VBUS contacts feed only
   the hub detector divider. CC1 and CC2 each receive Rd. It cannot power or
   back-power the board.
2. `J_POWER` is a power-only USB-PD sink. CC1/CC2 feed the PD controller;
   D+/D-/SBU are explicit no-connects.

Preserve the purchased USB2517I, MCP2221A, MCP23017, TPS2557, FSUSB42,
TPS259474L, AP63203Q, interlock, ESD, USB-A, and compatible passive population.
Only the input connectors and power front end change unless a gate proves a
further incompatibility.

## Consequences

- Laptop VBUS and supply VBUS cannot be paralleled.
- The board needs two cables to operate, which is intentional and visually
  explicit.
- USB-C connector geometry and orientation become new placement gates.
- The low-cost screw terminal and blade fuse may not be reused; correctness and
  output-voltage margin outrank low-value inventory reuse.
- The previous accepted HRO land-pattern correction is reused as precedent,
  but v2 owns a self-contained exact dossier, footprint, model, and review.

