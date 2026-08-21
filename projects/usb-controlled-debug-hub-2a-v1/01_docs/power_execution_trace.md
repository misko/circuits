# Power and control execution trace

status: first green schematic; placement/routing not started
date: 2026-08-20

## Power-up pseudo-stack

```text
attach USB-C POWER
  J_POWER exposes VBUS_PD_RAW and CC1/CC2
  F_PD -> VBUS_PD
  D_PD_TVS clamps VBUS_PD transients
  U_PD (CH224K) requests fixed 20 V / 3 A PDO
  U_PD_IN (TPS16630)
    reject default 5 V and 15 V PDOs at UVLO
    reject excessive input at OVP
    current-limit/slew VBUS_PD_PROTECTED
  in parallel from VBUS_PD_PROTECTED
    U_BUCK_A -> P5V_BANK_A -> U_AGG_A -> P5V_A_PROTECTED
      U_PWR1 -> VBUS1_SW (2 A service)
      U_PWR2 -> VBUS2_SW (2 A service)
      U_PWR_CTRL -> VBUS_CTRL (management only)
    U_BUCK_B -> P5V_BANK_B -> U_AGG_B -> P5V_B_PROTECTED
      U_PWR3 -> VBUS3_SW (2 A service)
      U_PWR4 -> VBUS4_SW (2 A service)
    U_MAIN -> 3V3_MAIN (hub, logic and data switches)
```

No 5 V bank can source the other bank. Each port's TPS259470A provides its
own current limit and true reverse-current blocking. Each TPS259827 aggregate
breaker is latch-off; cycle USB-C POWER after a persistent bank fault.

## Command pseudo-stack

```text
host enumerates J_DATA -> USB2517I hub
  internal hub port enumerates factory MCP2221A
    host software writes MCP23017 over I2C
      PWR_CMD[n] AND HUB_PRTPWR[n] -> PWR_EN[n]
        PWR_EN[n] enables port eFuse
      DATA_CMD[n] AND PWR_EN[n] -> DATA_OK[n]
        DATA_OK[n] enables the USB 2.0 analog switch
```

This is a no-project-firmware design: the MCP2221A uses factory USB HID/I2C
behavior and the MCP23017 is a register-controlled GPIO expander. Data cannot
be enabled while commanded power is disabled; power may remain enabled while
data is disconnected.

## Binding electrical checks

- Four simultaneous 2 A outputs require a 20 V / 3 A PD source.
- The mated-plug voltage floor is 4.785 V under the current 90 mOhm path
  allocation; routing extraction and hot four-wire first-article measurement
  remain mandatory.
- Port current-limit full corner is 2.080-2.646 A with stocked 1.40 kOhm
  programmers; the 3 A/contact USB1130 rating is not exceeded.
- Bank A/B aggregate breaker windows are 4.275-5.776 A, coordinated against
  the respective 5.392 A / 5.292 A downstream fault envelopes and the 6.3 A
  minimum converter valley limit.
