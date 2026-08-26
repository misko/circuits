# Changelog

## v1.0 — 2026-08-01

- Initial four-port programmable USB 2.0 hub release: four USB-A downstream
  sockets, independently switched 5 V / 3 A power paths, independently
  connectable data paths, per-port power/status telemetry, and USB-host control.
- Preserved every physical MOSFET drain-pin identity and added an early
  P-PINMAP gate so symbol/footprint collapses fail before placement or routing.
- Added pad-separation and same-camera populated-minus-bare render gates; the
  final board is DRC 0/0/0, pin-reviewed, and mechanically modeled 194/194.
- U4 remains an exact-part consignment line because JLC catalog stock is zero;
  the sealed design is valid but ordering stays blocked until consignment and
  uploader human gates clear.

Released: v1.0-2026-08-01
