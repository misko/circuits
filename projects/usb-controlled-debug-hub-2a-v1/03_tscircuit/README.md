# tscircuit authoring source

`src/usb_controlled_debug_hub_2a.tsx` is the connectivity source for this board.
The generated Circuit JSON and schematic are disposable build products; KiCad
owns placement, routing, DRC and fabrication output.

The board intentionally contains no project firmware. MCP2221A factory HID/I2C
behavior is used to access MCP23017 registers. USB-C POWER requests 20 V / 3 A;
two 6 A buck banks supply four simultaneous 2 A USB-A outputs.
