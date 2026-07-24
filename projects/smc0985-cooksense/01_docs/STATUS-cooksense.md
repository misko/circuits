# STATUS beacon — cooksense MAIN board (live head; overwritten each transition)
<!-- reader parses from here down -->
stage:   v1.2-ELECTRICAL
step:    "v1.2 electrical-correction release IN PROGRESS (external review priorities 1-7; v1.1 mechanical comb RETAINED). Pi/RP1 I2C map VERIFIED against RP1 datasheet + kernel overlay sources (GPIO4/5=I2C2 SDA/SCL, GPIO14/15=I2C3 SDA/SCL, GPIO2/3=I2C1). NTC = existing 02_parts KNTC0603/10KF3950. One-shot swap: CD74HC221M96 (TI SOIC-16, LCSC C133954, stock 2542, non-retriggerable per SCHS166F) — part.yaml written."
measure: "RP1 DS fsel table rows extracted (GPIO4=I2C2_SDA GPIO5=I2C2_SCL GPIO14=I2C3_SDA GPIO15=I2C3_SCL); HC221 DS sha256 30c3cd71"
state:   running
op_pid:  none
next:    "author BRIEF D10 + ADR-0010/0011 + DETAIL_DESIGN + pin_map, then tsx edits + E-INV, then schematic gate"
updated: 2026-07-24T13:30
