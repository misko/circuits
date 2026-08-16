# tscircuit authoring source

`src/usb_controlled_debug_hub.tsx` is the connectivity source for this board.
The generated Circuit JSON and schematic are disposable build products; KiCad
owns placement, routing, DRC and fabrication output.

The board intentionally contains no project firmware. MCP2221A factory HID/I2C
behavior is used to access MCP23017 registers.
