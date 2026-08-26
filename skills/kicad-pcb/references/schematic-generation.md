# Schematic generation and fallback

TSX/tscircuit is the forward schematic authoring path. Read
`tscircuit-folder.md` for the source tree and producer flow. This reference owns
the boundary between that producer, generated KiCad, and the narrow fallback
used when tscircuit cannot express a required construct.

## Standard path

```text
03_tscircuit/src/*.tsx
  -> pinned tsci build
  -> exact dist circuit.json
  -> circuit_json diagnostics
  -> circuit_json_to_kicad_sch conversion
  -> kicad-cli netlist/ERC/parity
  -> fresh human schematic PDF from the same circuit.json
```

The producer's exit code is not sufficient. Fail on embedded error records,
zero expected components/nets, stale output, converter-input mismatch, missing
render, ERC, parity, or semantic closure. The rebuild driver owns exact command
order; this document does not duplicate it.

Connectivity and presentation are separate claims. The generated netlist must
match intended nets, while the human PDF must show functional blocks, visible
primary signal/power flow, grouped pins, readable values, and unambiguous sheet
boundaries. A machine-correct label cloud is not a reviewed schematic.

## Fallback boundary

Use the shared Python/s-expression writer only for a construct the current TSX
adapter cannot represent. Before using it:

1. record the unsupported construct and why it is load-bearing;
2. show that a supported TSX form cannot preserve the same meaning;
3. keep part/net data in a structured source table, not scattered writer calls;
4. emit the same diagnostics, ERC, parity, semantic, and human-review subjects
   as the standard path;
5. add a tracked adapter gap so the second board needing it triggers promotion.

Fallback output is still generated. Never hand-edit `.kicad_sch` to close an
adapter gap, because regeneration will silently discard the change.

## Review layout

- Partition by function and power domain before choosing coordinates.
- Draw primary paths with wires; use labels for repeated/global or secondary
  connections where a wire would reduce readability.
- Keep connector pin order and direction legible.
- Show polarity, protection direction, supply decoupling ownership, test
  points, and intentional no-connects.
- Fit each declared sheet independently and bind the PDF to the exact circuit
  JSON/netlist subject.
- Review the PDF before placement. Do not wait for fabrication renders to find
  an unreadable schematic.

## Validation

The owning rebuild must demonstrate nonzero expected component/net counts,
fresh producer identity, converter parity, ERC/semantic closure, and an adopted
independent readability review. If TSX changed, rerun the full producer. If it
did not, the deterministic reuse flow may consume the pinned generated
schematic.
