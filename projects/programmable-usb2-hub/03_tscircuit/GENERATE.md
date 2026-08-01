# generate

    export PATH="$HOME/.nvm/versions/node/v22.12.0/bin:$HOME/.bun/bin:$PATH"
    bash skills/kicad-pcb/scripts/gen_tscircuit.sh projects/programmable-usb2-hub

    # MANDATORY: regenerate the machine bridge in GRID mode (layout mode net-merges
    # buck-A BOOT_A/VCC_A — see usb-hub-3s-v2 journal/04_board.md). Then export the
    # netlist the KiCad backend consumes:
    cd projects/programmable-usb2-hub/03_tscircuit
    /usr/bin/python3 <skills>/circuit_json_to_kicad_sch.py build/circuit.json \
        -o kicad/programmable_usb2_hub.kicad_sch --project programmable_usb2_hub --mode grid \
        --net-aliases net_aliases.txt
    kicad-cli sch export netlist -o ../06_build/netlists/programmable_usb2_hub.net \
        kicad/programmable_usb2_hub.kicad_sch
