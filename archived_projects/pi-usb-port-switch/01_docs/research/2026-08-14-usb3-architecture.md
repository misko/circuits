# USB 3 inline architecture and sourcing spike — 2026-08-14

This is dated commission evidence, not an executable source of part values or
live stock truth. Exact selected parts still require `02_parts/` dossiers and
Q-2SOURCE verification.

## Standards and host envelope

- Raspberry Pi documentation/product briefs report two USB 3 and two USB 2
  ports on both the full-size Pi 4 Model B and Pi 5:
  <https://www.raspberrypi.com/documentation/computers/raspberry-pi.html>
  and <https://datasheets.raspberrypi.com/rpi5/raspberry-pi-5-product-brief.pdf>.
- USB-IF calls the 5 Gb/s rate USB 3.2 Gen 1 and states backward compatibility:
  <https://www.usb.org/usb-32-0>.
- USB-IF's USB 2.0/3.2/BC1.2 drop/droop procedure revision 1.4.1 uses a
  900 mA load and 4.75 V minimum for a self-powered USB 3.2 downstream port:
  <https://www.usb.org/sites/default/files/USB20_32_BC12_Drop_Droop_1_4_1.pdf>.

## Data-path candidates observed

| Function | Candidate | Evidence observed 2026-08-14 | Commission class |
|---|---|---|---|
| SuperSpeed disconnect and loss compensation | TI TUSB522PRGER | TI specifies a dual-channel 5 Gb/s redriver, selectable EQ/de-emphasis and active-high enable with shutdown; LCSC C470964 showed 1,562 units | sourceable at standard four-layer intent; exact JLC assembly preview still owed |
| USB 2 D+/D- disconnect | TI TS3USB221ERSER | TI/LCSC identify a 1 GHz high-speed USB 2 switch with output enable; LCSC C129313 showed 300 units | sourceable; tiny UQFN escape must be checked against declared tier |
| Per-port VBUS switch | TI TPS2552DBVR | TI specifies an active-low adjustable current-limited switch with reverse-voltage protection; LCSC C46506 showed 2,755 units | sourceable at standard tier |
| Six-line connector ESD | TI TPD6E05U06RVZR | TI specifies six 0.5 pF channels for USB 3 up to 6 Gb/s and ±12 kV contact ESD; LCSC C962978 showed 4,949 units | sourceable; number/location of arrays remains a signal-integrity decision |

The TUSB522P is preferred over a passive HD3SS3212 disconnect because TI states
that the redriver is intended to compensate insertion loss across PCB or cable,
whereas the passive switch only adds insertion loss. The redriver's `EN_RXD`
has an internal pull-down and enters shutdown low, which supports the required
fail-safe state. Primary source:
<https://www.ti.com/lit/ds/symlink/tusb522p.pdf>.

## Connector candidates observed

| Function | Candidate | Evidence observed 2026-08-14 | Risk |
|---|---|---|---|
| Downstream USB 3 Type-A | FG ST-003-01-J / LCSC C2839629 or Hong Cheng HC-USB3.0-L137-ZP / C19273972 | JLC/LCSC describe 9-contact through-hole USB 3 receptacles rated 1.5 A; thousands shown for the Hong Cheng family | exact drawing, pin map, JLC stock and wave-solder fixture preview owed |
| Upstream USB 3 Type-B | Hong Cheng HC-USB3.0-L1845-BF / C7501849 | LCSC showed 3,162 units and identifies a 9-contact right-angle USB 3 Type-B receptacle | exact drawing, pin map and JLC wave-solder preview owed |

Stock figures are volatile observations only. URLs:

- <https://www.lcsc.com/product-detail/C470964.html>
- <https://www.lcsc.com/product-detail/C129313.html>
- <https://www.lcsc.com/product-detail/Power-Distribution-Switches_Texas-Instruments_C46506.html>
- <https://www.lcsc.com/product-detail/C962978.html>
- <https://jlcpcb.com/partdetail/FG-ST_003_01J/C2839629>
- <https://www.lcsc.com/product-detail/USB-Connectors_Hong-Cheng-HC-USB3-0-L1845-BF_C7501849.html>

## Manufacturing and verification consequences

- Start from JLCPCB's least-cost four-layer controlled-impedance stackup, but
  treat the order-preview stackup/impedance result as final authority:
  <https://jlcpcb.com/help/article/user-guide-to-the-jlcpcb-impedance-calculator>.
- Keep each SuperSpeed pair on one outer layer over a solid adjacent ground
  plane; minimize connector-to-protection-to-redriver distance, vias and stubs.
- Protect both exposed connector boundaries only if the insertion-loss model
  remains acceptable; TI's ESD devices provide S-parameters for pre-layout
  review: <https://www.ti.com/product/TPD6E05U06>.
- USB 3 release evidence must include the exact cable lengths, Pi port, device,
  negotiated speed and sustained transfer result. A link-up screenshot alone
  is insufficient.

