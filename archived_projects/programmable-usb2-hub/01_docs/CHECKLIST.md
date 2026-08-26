# Pre-release checklist

- [ ] `01_docs/BRIEF.md` has no unmet criterion before release.
- [ ] Q-2SOURCE passes before schematic completion and again on order day: every selected component is active and sufficiently stocked at two independent authorized supplier pools.
- [ ] `bash 03_src/rebuild_all.sh` completes with ERC 0 errors and PCB DRC 0 violations / 0 unconnected / 0 parity.
- [ ] The complete mechanical, assembly, sourcing, twin, pin, render, policy, and red-team battery required by `07_releases/contracts.md` passes against staging.
- [ ] Fabrication paperwork and order preview state an exact 130 mm x 90 mm finished outline.
- [ ] F1 inspection finds one complete Keystone 3568 holder and one exact red Littelfuse 0297010.H 10 A / 32 V MINI fuse; no loose-clip construction, 20 A fuse, wire link or other rating is fitted.
- [ ] With the fuse removed, J1 positive is open to `VIN_FUSED`; with the fuse installed, continuity follows J1 -> F1 -> `VIN_FUSED` with no bypass.
- [ ] The commissioned source is <=24.0 V at J1 including accuracy, regulation, ripple and wiring/plug overshoot; nominal 24 V +/-5% sources are rejected.
- [ ] OV trip characterization across resistor/temperature corners is consistent with the calculated 24.345-26.390 V rising window.
- [ ] The selected external source/wiring is documented or pulse-tested at <=50 V open circuit and >=1.6 ohm effective source impedance for a 10/1000 us-or-shorter, <=1 ms event; broader, lower-impedance, repetitive, automotive-load-dump, and lightning sources are rejected.
- [ ] Surge qualification records <=14.563 A at D1, <=38.9 V on `VIN_PROTECTED`, and Q2 load disconnect within 5.7 us; D1 has at least 5 x 5 mm connected copper at each terminal and no thermal-spoke bottleneck.
- [ ] LTC3889 switching and controller thermal calculations use CSD18533Q5AT maximum 36 nC gate charge and the measured 250 kHz setting; the superseded LM5116/BSC016 gate-current blocker is not applicable to the selected design.
- [ ] E-MARGIN passes the complete board-to-mated-interface path. The current honest 130 mOhm bound (eFuse + PCB/joints + both receptacle contacts) is a release blocker; the detachable downstream cable is outside the commissioned `at connector` voltage boundary.
- [ ] R38-R41 are populated as 100 kOhm command pulldowns and all four final eFuse enables remain low through MCU unpowered/reset/unprogrammed states.
