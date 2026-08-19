# Changelog

## Unreleased v2 — two USB-C architecture

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

There is no v2 release yet. Generated KiCad artifacts currently present in the
worktree are inherited baseline material and cannot be fabricated as v2.

