---
id: 0003
date: 2026-08-10
status: accepted
---
# 0003 — Standards-aware power-only USB ports

## Context

Power-only does not mean connector-state rules disappear. A Type-C source must
advertise current on CC and condition VBUS on a valid sink attach. USB-A charging
signatures improve device compatibility, but BC1.2 defines a 1.5A DCP rather
than the requested 2A continuous/2.5A peak service.

## Options

- Permanently live Type-C VBUS plus static Rp — rejected because it omits the
  required attach/detach source behavior.
- USB-PD controller — rejected as unnecessary complexity for fixed 5V Pi power.
- TPS25810 attach-controlled source — selected for USB-C.
- No USB-A signature or only a passive D+/D− short — simple but less compatible.
- TPS2513A signatures plus separate TPS2557 port switches — selected for USB-A.

## Decision

Use TPS25810 for Type-C Rd detection, 3A advertisement, VBUS switching and
discharge. Use two TPS2513A devices for three local USB-A charge signatures,
with one TPS2557 per port for current limiting. Use TPD2EUSB30 at the Type-C
receptacle for the exposed CC contacts and USBLC6 at each USB-A receptacle for
the exposed charging-signature contacts. Carry no USB data or PD traffic.

## Consequences

Type-C can be described as a fixed-5V, 3A-advertising source, not as USB-PD.
USB-A can be described as charge-only with BC1.2/legacy recognition, but the
2A/2.5A available-current claim is a proprietary extension and must never be
presented as USB-IF BC1.2 current compliance. USB-C D+/D− and SBU remain
no-connect; CC1/CC2 remain separate protected attach lines. USB-A D+/D− exist
only as short local charging-signature networks.
