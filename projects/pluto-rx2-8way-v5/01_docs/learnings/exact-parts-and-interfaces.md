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
9. YAML parse success is not schema success. Every authored rule family needs
   its canonical reader before generation, with a non-zero expected
   denominator and a bounded diagnostic instead of a traceback.
10. Stage readiness is a derived claim. A hand-maintained `true` flag cannot
    substitute for fresh receipts from every applicable reader and a findings
    ledger that names later-stage blockers.
11. Exact-code evidence should describe stable identity and ratings; volatile
    stock and price belong in dated generated evidence. A composed two-source
    verdict must grade the exact candidate-BOM hash, not prose scattered among
    dossiers.
12. A timing observer sees contiguous electrical states, so a 500-ms ALL_OFF
    marker followed by a 5-ms ALL_OFF guard is 505 ms. Derive windows, cycle
    length and capture time from the atomic schedule and make incomplete or
    signal-free observations decode to `unknown`.
13. Manufacturer examples are useful precedent but do not prove that the
    search ladder was completed. Record the strongest artifact consulted and
    name the next stronger routed artifact that was unavailable or unreached.
14. A source-only gate should not initialize PCB machinery. The current policy
    audit passes, but KiCad property assertions in its output are needless
    noise and should be removed by phase-lazy imports.
