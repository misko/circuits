# Learnings — exact parts and interfaces

1. Run exact-code source, package, and electrical-bound checks before creating
   symbols or TSX. Here, one inexpensive protection calculation prevented a
   10-V capacitor from entering the schematic behind a 10.3-V clamp.
2. A TVS is a coordinated path, not a BOM decoration. Compare its maximum
   clamp at the admitted waveform, add margin, and grade every exposed part.
3. A hardware truth-table all-off code is especially valuable. It lets passive
   pulls protect reset, programming, brownout, and unpowered-controller states
   without an extra gate IC.
4. Unique dwell lengths need framing, fixed order, disjoint tolerances, and an
   explicit `unknown` result. Timing alone cannot identify an antenna when no
   usable RF transition is observable.
5. “Advanced board” should be a measured package/geometry outcome. U1 requires
   it; the MCU and all supporting parts do not.
6. Lock stackup inputs early but solve trace geometry only with the final
   fabricator calculator and actual copper topology. Copying evaluation-board
   widths would be false precision.
7. Record source-access problems as narrow future blockers. Repeated hidden
   download retries look like a locked pipeline and do not improve evidence.
8. Sourcing has two different gates: dated catalog/stock confidence now and
   the JLC uploader allocation/population echo at order time. Passing the first
   cannot waive the second.
