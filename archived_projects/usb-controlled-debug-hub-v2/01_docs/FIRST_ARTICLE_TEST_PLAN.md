# USB-controlled debug hub — first-article test plan

Status: required external work. No physical article has passed this plan, and
this document does not authorize production or payment.

## 1. Preserve the order state

Record board serial, JLC order/lot, final stackup and 90-ohm solve, Gerber
preview, resolved BOM, CPL, polarity/rotation views, all six THT mappings and
the selective 0.20-mm via fill/cap acknowledgement. Reject an unreviewed DFM
change, substitute, DNP, side, rotation, connector orientation, or via-process
change.

## 2. Incoming and unpowered inspection

1. Inspect both sides for bridges, tombstones, missing parts, connector seating,
   filled/capped via quality and exposed-pad wetting evidence. Confirm the five
   TPS259470A ground pads, the retained TPS2557 PowerPAD and USB2517 exposed
   pad are soldered. Inspect all nine `U_AGG` 0.20 mm via-in-pad sites and
   confirm the JLC order delivered complete Type VII fill and copper cap with
   no exposed void or solder drain. Confirm `F_PD` is the exact 3 A / 32 V Littelfuse fuse,
   `D_PD_TVS` is exact TVS1800DRVR with its ground bank and exposed pad
   wetted, and both USB-C receptacles are fully seated.
2. With all cables removed, record settled resistance using the exact probes
   and ranges in `03_src/rules/first_article.yaml`. Any value outside its range
   is an abort, not permission to raise the current limit.
3. Confirm `J_DATA` VBUS is not continuous with `VBUS_PD`, `P5V_REG`, or
   `P5V_PROTECTED`. Confirm every external VBUS is off with the board unpowered.

## 3. Current-limited first power

Create `01_docs/journal/first_article.json` with the complete installed set,
all exposed-pad confirmations, explicit units/probes, PD contract, input
current-limit fixture and measured values. Begin with a qualified 15 V / 3 A
USB-C PD source through a 0.30 A current-limited first-power fixture.
Run `first_article_check.py`; continue only on `AUTHORIZED`. Record no-load
`VBUS_PD`, `VBUS_PD_SW`, `P5V_REG`, `P5V_PROTECTED`, `3V3_MAIN`, input current
and component temperatures. First verify that `VBUS_PD_SW` remains off at the
default 5 V attach voltage; then confirm it rises only after the source has
negotiated 15 V. Stop on current-limit entry, odor, discoloration, oscillation,
unstable voltage, failed PD negotiation, or unexpected heating.

With a differential probe directly at the `U_PD_IN` IN/GND pads, capture
POWER cable attach, source disconnect, downstream-short interruption and the
qualified abnormal-source transient. The measured peak must remain below
28 V and within the TVS1800 8/20 us envelope; a capture at the connector or
regulator is not a substitute for the eFuse-input measurement.

## 4. Safe-state and control truth table

With no project firmware, use the MCP2221A factory HID/I2C interface and a
separately recorded host procedure. For every port, verify reset/unconfigured
state is VBUS off and data disconnected, then verify:

| PWR command | DATA command | Expected VBUS | Expected data |
|---:|---:|---|---|
| 0 | 0 | off | disconnected |
| 0 | 1 | off | disconnected by hardware interlock |
| 1 | 0 | on | disconnected |
| 1 | 1 | on | connected |

Verify independence, matching OCS behavior and recovery after control-power
loss/reset. Confirm the board never back-powers the upstream host.

For each external port, apply 5.0 V through a current-limited fixture to the
USB-A VBUS pin while the board is unpowered, then while that port is disabled.
Verify no sustained current reaches `P5V_PROTECTED`, another port, `J_POWER`,
or `J_DATA`. Repeat with the board powered and the tested port disabled. These
three states qualify the TPS259470A true reverse-current-blocking requirement.

## 5. USB and power qualification

1. Enumerate the hub and onboard management device from the single upstream
   cable. Enumerate representative low-, full- and high-speed USB 2.0 devices
   on each external port in the connected state.
2. Exercise at least 1,000 full-off, power-only and reconnect cycles per port.
   Record enumeration failures, resets, protocol errors and transferred-data
   hashes. Data-off must prevent enumeration while power-only retains VBUS.
3. Load every port individually to 0.50 A, then all four simultaneously for at
   least 30 minutes. Four-wire measure at each mated USB-A test plug; every
   output must remain 4.75–5.25 V. Record hot drop and temperature at the fuse,
   eFuse, buck, each TPS259470A, the internal TPS2557, connector and PCB
   hotspot.
4. Apply controlled overload/short fixtures one channel at a time. With the
   other three ports held at 0.50 A and the internal load active, confirm the
   local channel enters current limit/OCS without tripping `U_AGG`. Repeat with
   two simultaneous fault fixtures and confirm aggregate latch-off is safe.
   Verify that latch-off removes management power and that cycling USB-C POWER
   is the intentional and only recovery path. Record current thresholds rather
   than treating a room-temperature pass as a production guarantee.
   Separately qualify the exact power source, fuse, connector, buck and
   aggregate path at 5.78 A for 7 ms. Stop on regulator current-limit entry,
   fuse damage, output collapse outside the modeled interruption behavior, or
   a component temperature/transient limit violation.
5. Capture port capacitive startup, startup, 0.50 A load-step, abrupt removal
   of all four loads, disconnect and simultaneous switching waveforms at 10 C,
   25 C and 40 C ambient and over more than one eFuse lot. Confirm the three
   feedback resistors remain within 0–50 C during these runs. `P5V_REG` and every
   mated output must remain at or below 5.25 V, including settled ripple and
   the load-release peak.
   Retain USB 2.0 High-Speed traffic/eye evidence against the order-time JLC
   90-ohm construction. A routing waiver is not a substitute for the assembled
   measurement.

## 6. Closeout

Tabulate every result with serial/lot, equipment and calibration identity,
cables/fixtures, ambient temperature, raw captures and photographs. Any missing
measurement, unexpected behavior, process deviation or failed limit blocks
production and reopens engineering review. No firmware is generated by this
plan.
