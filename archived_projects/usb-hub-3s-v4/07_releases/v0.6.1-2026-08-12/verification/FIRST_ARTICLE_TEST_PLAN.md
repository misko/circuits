# USB Hub 3S v4 first-article test plan

Status: required before `FIRST_ARTICLE_TESTED` or production claims. This plan
does not authorize an order; the JLC upload preview and Type-VII process review
remain separate pre-order gates.

## Safety and equipment

- Begin on an isolated, current-limited bench supply, not a LiPo pack. Use a
  protected 3S pack only after the bench sequence passes. Keep a nonflammable
  work surface, eye protection and a reachable input disconnect.
- Required: two DMMs, oscilloscope with short ground spring/differential probe
  where appropriate, programmable loads totaling 9 A at 5 V, four-wire
  milliohm capability, thermocouples/thermal camera, and known-good USB-A and
  USB-C breakout/cables. Log serial number, ambient temperature and instrument
  IDs with every result.
- The board is a supervised prototype with no active sustained overvoltage
  cutoff. Never connect an unattended load or claim converter fail-high
  protection from this test.

## Controlled test-point map

| Ref | Net / function | Expected use |
|---|---|---|
| TP1 | VIN | protected input after fuse/reverse-polarity stage |
| TP2 | 5VA | USB-A aggregate protected rail |
| TP3 | 5VC_RAW | USB-C regulator output before attach switch |
| TP4 | VBUSC | Type-C attach-controlled VBUS |
| TP5 | EN_BUS | master enable |
| TP6 | PG_A | USB-A converter power-good |
| TP7 | PG_C | USB-C converter power-good |
| TP8 | FAULT_C | Type-C switch fault indication |
| TP9 | FAULT_A1 | USB-A port 1 fault indication |
| TP10 | FAULT_A2 | USB-A port 2 fault indication |
| TP11 | FAULT_A3 | USB-A port 3 fault indication |
| TP12 | GND | measurement return |

TP3-TP12 are identified on the prototype PCB by reference designator rather
than a full net-name caption. Print this table beside the bench setup and verify
the refdes before every probe connection. This is a prototype-only disposition,
not permission to omit functional TP legends on a production revision.

## A. Unpowered assembly acceptance

1. Compare the received PCB against the released Gerbers and JLC preview.
   Confirm the 0.20 mm protected-via family alone received copper-paste fill and
   copper cap; reject blanket fill/cap of ordinary 0.30 mm vias.
2. Inspect every SMT part for identity, side, rotation, wetting and bridges.
   Explicitly check C22/C23 polarity, D1/D2-D6 cathodes, Q1 and all IC pin 1s.
3. Hand-solder exact F1, J1, J2-J4 and SW1 per `assembly.yaml`. Inspect all
   signal, shell and structural joints; verify connector seating, edge datum,
   mating access, switch OFF direction and terminal retention.
4. With the fuse removed and loads disconnected, measure for shorts from
   BAT+/VIN/5VA/5VC_RAW/VBUSA1-3/VBUSC to GND. Record values after settling.
   Verify the USB-A data contacts are not connected to any upstream data path
   and USB-C D+/D-/SBU remain intentionally unused.

## B. Current-limited first power

1. Fit the specified 10 A MINI fuse. Set SW1 OFF. Apply 9.0 V with a conservative
   current limit and confirm no downstream 5 V rail energizes. Record VIN,
   EN_BUS, 5VA, 5VC_RAW and input current.
2. Turn SW1 ON and raise the current limit only as justified by observed inrush.
   Confirm TP2 and TP3 regulation, TP6/TP7 power-good state, no fault assertion,
   and no abnormal temperature or audible behavior. Repeat at 12.6 V.
3. Reverse-input testing, if performed, uses a current-limited bench source only:
   verify Q1 blocks the wrong polarity without overstress, then return to correct
   polarity and repeat the no-load checks.

## C. Port behavior and protection

1. For each USB-A port independently, ramp 0 to 2.0 A while recording connector
   voltage, its FAULT test point and hottest component. Confirm the charge-only
   D+/D- signature with the intended sink/tester; do not claim USB enumeration.
2. Load all three USB-A ports to 2.0 A simultaneously. Record TP2, all receptacle
   voltages, input current, ripple and temperatures after thermal equilibrium.
3. Attach a compliant Type-C sink. Confirm Rp advertises the intended 3 A current,
   VBUSC is absent before attach and present after attach, then load to 3.0 A.
   Record TP3, TP4, receptacle/cable-end voltage, FAULT_C, ripple and temperature.
4. Exercise one output protection channel at a time with a controlled overload
   and short fixture. Confirm current limiting/fault indication and recovery;
   never use an uncontrolled wire short. Verify the aggregate TPS259827 stage
   interrupts at the documented timing/current corners and recovers as designed.
5. Run the declared worst simultaneous load. Capture startup, attach, load-step
   and unload waveforms at VIN, TP2, TP3 and TP4. Pass only if voltage/ripple,
   current-limit coordination and stability remain inside the design limits with
   no sustained oscillation or unexpected fault cycling.

## D. Interconnect and thermal qualification

1. Four-wire measure the complete Type-C delivery path hot, from J5 PCB-side
   VBUS/GND lands through the exact named cable and Raspberry Pi receptacle/entry
   path to the Pi load-plane sense points. At 3 A the complete interconnect must
   be <=39 mOhm and the Pi load plane must remain continuously acceptable.
2. At worst input voltage and simultaneous rated load, log U1/U2/U3/U4-U9, Q1,
   D1, C22/C23, fuse/holder, connectors and hotspot temperatures to equilibrium.
   Repeat inside the intended enclosure/airflow. Stop on discoloration, odor,
   unstable temperature rise or any rating-margin violation.
3. Power-cycle, switch OFF under load, detach/reattach Type-C, and repeat the
   no-load/loaded rail measurements. Retain plots, photographs and the signed
   result table. Any failure reopens the design; do not tune acceptance limits
   after seeing the result.
