# Generate

From the repository root:

```bash
export PATH="$HOME/.nvm/versions/node/v22.12.0/bin:$HOME/.bun/bin:$PATH"
bash skills/kicad-pcb/scripts/gen_tscircuit.sh projects/usb-hub-3s-v4
```

The full staged driver is `projects/usb-hub-3s-v4/03_src/rebuild_all.sh`. It
runs preflight and semantic checks, regenerates the human schematic and KiCad
bridge from the same circuit JSON, then stops at the exact-hash independent
schematic review before any placement work is accepted.
