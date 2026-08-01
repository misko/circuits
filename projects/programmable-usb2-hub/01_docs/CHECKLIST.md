# Pre-release checklist

- [ ] `01_docs/BRIEF.md` has no unmet criterion before release.
- [ ] Q-2SOURCE passes before schematic completion and again on order day: every selected component is active and sufficiently stocked at two independent authorized supplier pools.
- [ ] `bash 03_src/rebuild_all.sh` completes with ERC 0 errors and PCB DRC 0 violations / 0 unconnected / 0 parity.
- [ ] The complete mechanical, assembly, sourcing, twin, pin, render, policy, and red-team battery required by `07_releases/contracts.md` passes against staging.
