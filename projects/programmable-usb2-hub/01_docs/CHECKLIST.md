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
- [ ] Surge qualification records <=38.9 V at D1 and <=40.0 V at U4 VIN for <=1 ms under the admitted <=600 W 10/1000 us event; broader/longer source transients are rejected or U4 is replaced by a wider-input design.
- [ ] Q3-Q6 gate-drive current is below the LM5116 startup limit and switching/controller thermal calculations pass. Current BSC016N06NS arithmetic is a blocker: 107 nC x 250 kHz = 26.75 mA > 15 mA minimum limit.
- [ ] E-MARGIN passes the complete board-to-mated-interface path. The current honest 130 mOhm bound (eFuse + PCB/joints + both receptacle contacts) is a release blocker; the detachable downstream cable is outside the commissioned `at connector` voltage boundary.
- [ ] R38-R41 are populated as 100 kOhm command pulldowns and all four final eFuse enables remain low through MCU unpowered/reset/unprogrammed states.
