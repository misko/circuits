"""Hardware-independent safety state machine for the four PHUB ports.

The embedded target supplies GPIO/ADC samples and applies the returned output
levels.  Keeping this policy free of an STM32 HAL makes it host-testable and
pins the important polarity: FSUSB42 OE_N high means data disconnected.
"""

from __future__ import annotations

from dataclasses import dataclass

from phub_protocol import PortStatus, ProtocolError

VBUS_PRESENT_ON_MV = 4500
VBUS_PRESENT_OFF_MV = 4200
MIN_CYCLE_MS = 50
MAX_CYCLE_MS = 60_000


@dataclass
class OutputLevels:
    power_en: bool = False
    data_oe_n: bool = True


class PortController:
    def __init__(self, port: int):
        if not 1 <= port <= 4:
            raise ProtocolError("port must be 1..4")
        self.port = port
        self.outputs = OutputLevels()
        self.power_commanded = False
        self.data_commanded = False
        self.fault_active = False
        self.fault_latched = False
        self.fault_count = 0
        self.vbus_mv = 0
        self.current_ma = 0
        self.vbus_present = False
        self.last_transition_ms = 0
        self._cycle_restore_at: int | None = None

    def _changed(self, now_ms: int) -> None:
        self.last_transition_ms = now_ms & 0xFFFFFFFF

    def set_power(self, enabled: bool, now_ms: int) -> None:
        if enabled and (self.fault_active or self.fault_latched):
            raise ProtocolError("power enable rejected while fault is active/latched")
        enabled = bool(enabled)
        self._cycle_restore_at = None
        if self.power_commanded != enabled or self.outputs.power_en != enabled:
            self.power_commanded = enabled
            self.outputs.power_en = enabled
            self._changed(now_ms)

    def power_cycle(self, off_ms: int, now_ms: int) -> int:
        if self.fault_active or self.fault_latched:
            raise ProtocolError("power cycle rejected while fault is active/latched")
        duration = min(MAX_CYCLE_MS, max(MIN_CYCLE_MS, int(off_ms)))
        self.power_commanded = True
        self.outputs.power_en = False
        self._cycle_restore_at = now_ms + duration
        self._changed(now_ms)
        return duration

    def set_data(self, connected: bool, now_ms: int) -> None:
        connected = bool(connected)
        oe_n = not connected
        if self.data_commanded != connected or self.outputs.data_oe_n != oe_n:
            self.data_commanded = connected
            self.outputs.data_oe_n = oe_n
            self._changed(now_ms)

    def sample(self, *, fault_active: bool, vbus_mv: int, current_ma: int,
               now_ms: int) -> None:
        fault_active = bool(fault_active)
        if fault_active and not self.fault_active:
            self.fault_count = min(0xFFFFFFFF, self.fault_count + 1)
            self.fault_latched = True
            self.power_commanded = False
            self.outputs.power_en = False
            self._cycle_restore_at = None
            self._changed(now_ms)
        self.fault_active = fault_active
        self.vbus_mv = min(0xFFFF, max(0, int(vbus_mv)))
        self.current_ma = min(0xFFFF, max(0, int(current_ma)))
        if self.vbus_present:
            self.vbus_present = self.vbus_mv > VBUS_PRESENT_OFF_MV
        else:
            self.vbus_present = self.vbus_mv >= VBUS_PRESENT_ON_MV

        if self._cycle_restore_at is not None and now_ms >= self._cycle_restore_at:
            self._cycle_restore_at = None
            if not self.fault_active and not self.fault_latched:
                self.outputs.power_en = True
                self.power_commanded = True
                self._changed(now_ms)

    def clear_fault(self, now_ms: int) -> None:
        if self.fault_active:
            raise ProtocolError("cannot clear an active hardware fault")
        if self.fault_latched:
            self.fault_latched = False
            self._changed(now_ms)

    def status(self) -> PortStatus:
        return PortStatus(
            port=self.port,
            power_commanded=self.power_commanded,
            power_enabled=self.outputs.power_en,
            vbus_present=self.vbus_present,
            overcurrent=self.fault_active,
            fault_latched=self.fault_latched,
            data_commanded=self.data_commanded,
            data_enabled=not self.outputs.data_oe_n,
            vbus_mv=self.vbus_mv,
            current_ma=self.current_ma,
            fault_count=self.fault_count,
            last_transition_ms=self.last_transition_ms,
        )


class HubController:
    def __init__(self):
        self.ports = {port: PortController(port) for port in range(1, 5)}

    def port(self, number: int) -> PortController:
        try:
            return self.ports[number]
        except KeyError as exc:
            raise ProtocolError("port must be 1..4") from exc

    def safe_defaults(self, power_mask: int, data_mask: int, now_ms: int) -> None:
        for number, port in self.ports.items():
            port.set_data(bool(data_mask & (1 << (number - 1))), now_ms)
            if power_mask & (1 << (number - 1)):
                port.set_power(True, now_ms)
            else:
                port.set_power(False, now_ms)
