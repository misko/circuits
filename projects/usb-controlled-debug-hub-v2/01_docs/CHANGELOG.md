# Changelog

## v0.1.1-2026-08-18 — protected two-USB-C power path

- Replaced the four downstream port switches with TPS259470ARPWR eFuses that
  provide true reverse-current blocking while retaining the purchased hub,
  controller, expander, USB data switches, and management power switch.
- Added a TPS259470ARPWR input eFuse between the PD sink and 5 V buck, with
  source-owned UVLO/OVLO, inrush, current-limit, and protected-via evidence.
- Completed deterministic source-owned routing and canonical replay: route
  acceptance 9/9, DRC/unconnected/schematic-parity 0/0/0.
- Retained separate USB-C DATA and USB-C POWER connectors and the standing
  no-firmware requirement.
- Release remains DO-NOT-ORDER / BLOCKED-SOURCING until an exact quantity-five
  JLCPCB uploader allocation, BOM echo, rotations, THT mapping, via-process,
  stackup, and impedance previews are captured.

## v0.1.0-2026-08-18 — initial two-USB-C design release

- Sealed the initial two-USB-C architecture with separate data and PD power
  receptacles, CH224K 15 V negotiation, TPS56637 5 V conversion, and the
  retained four-port debug-hub core.
- Archived as design evidence with a sourcing/order hold; it is superseded by
  v0.1.1 for reverse-current blocking and power-path hardening.

## Earlier unreleased v2 development

- Forked the corrected v1 authored design as a revision baseline; no v1 release
  archive is treated as v2 evidence.
- Replaced USB-B upstream with a USB-C USB 2.0 DATA receptacle.
- Replaced screw-terminal 5 V input with a separate USB-C PD POWER receptacle.
- Locked physical separation between `VBUS_DATA_SENSE` and `VBUS_PD`.
- Selected a firmwareless CH224K 15 V PD sink and TPS56637 6 A synchronous
  buck architecture, subject to exact dossier and sourcing gates.
- Preserved the purchased hub, management, port switching, interlock,
  aggregate eFuse, 3.3 V supply, USB-A, and downstream ESD core.
- Explicitly retained the standing no-firmware requirement.

The generated KiCad artifacts are now governed by the immutable release
archives above; live work remains non-orderable until a new release is sealed.
