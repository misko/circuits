# Generate the schematic bridge

```sh
export PATH="$HOME/.bun/bin:$PATH"
bash skills/kicad-pcb/scripts/gen_tscircuit.sh projects/usb-controlled-debug-hub-v2
```

Run the schema and connectivity gates before the build. The generated KiCad
schematic is a machine bridge; the tscircuit schematic PDF is the human review
artifact. Do not generate firmware.
