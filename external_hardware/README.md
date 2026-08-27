# External hardware facts

This registry holds measured and cited facts about devices this repository did
not design but its boards must fit, connect to, or operate with.

Each device has one directory containing:

- `README.md`: the human-readable measurement and citation record;
- `facts.yaml`: the machine-readable fact index consumed by PCB projects;
- optional evidence such as photographs or extracted vendor files.

Boards reference facts by device and fact ID from
`03_src/rules/mates.yaml`; they do not copy the values into project source.
The provenance gate resolves those references under this directory and checks
their grade, method, quote, and dimensional error-bar obligations.

This is not a project, example, part library, or archive. It is shared mutable
authority for foreign-device observations. Sealed releases retain the exact
registry terminology and bindings that existed when they were sealed.

Start with [`plutoplus_hardware/`](plutoplus_hardware/) for the current device
record. See [`contracts.md`](contracts.md) for structure and audit rules.
The naming decision is recorded in
[`ADR-0009`](../docs/decisions/0009-external-hardware-registry-path.md); the
underlying provenance model remains [`ADR-0005`](../docs/decisions/0005-imported-facts.md).
