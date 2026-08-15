# Raspberry Pi four-port USB switch

Status: layout sealed; hardware-only v0.1.0 release candidate in final review.

This project is a JLCPCB-assembled inline controller for four
Raspberry Pi USB host ports. Each channel will independently support a normal
connected state, a power-only state with the USB data pair isolated, and a
fully disconnected state. Four USB 3 Type-B upstream connectors, four USB 3
Type-A downstream connectors, a 40-pin Raspberry Pi GPIO header, and a separate
regulated 5.15-5.25 V / at least 5 A input are locked.

The four identical channels attempt USB 3 Gen 1 while retaining USB 2 fallback.
USB 3 operation is a first-article qualification target, not a USB-IF compliance
claim. No device firmware or host software is included or required; safe
power/data interlocking and default-off behavior are implemented in hardware.

The commission is in `01_docs/BRIEF.md`, the electrical calculations are in
`01_docs/DESIGN_MATH.md`, and the physical qualification procedure is in
`01_docs/FIRST_ARTICLE_TEST_PLAN.md`. Current process state is in
`01_docs/STATUS.md`.
