#ifndef PHUB_CORE_H
#define PHUB_CORE_H

#include <stdbool.h>
#include <stdint.h>

enum phub_result {
    PHUB_OK = 0,
    PHUB_BAD_PORT = 1,
    PHUB_FAULT_ACTIVE = 2,
};

struct phub_outputs {
    bool power_en;
    bool data_oe_n;
};

struct phub_port {
    struct phub_outputs out;
    bool power_commanded;
    bool data_commanded;
    bool fault_active;
    bool fault_latched;
    bool vbus_present;
    bool cycle_pending;
    uint16_t vbus_mv;
    uint16_t current_ma;
    uint32_t cycle_restore_at_ms;
    uint32_t fault_count;
    uint32_t last_transition_ms;
};

void phub_port_init(struct phub_port *p);
enum phub_result phub_set_power(struct phub_port *p, bool enabled,
                                uint32_t now_ms);
enum phub_result phub_power_cycle(struct phub_port *p, uint32_t off_ms,
                                  uint32_t now_ms, uint32_t *clamped_ms);
void phub_set_data(struct phub_port *p, bool connected, uint32_t now_ms);
void phub_sample(struct phub_port *p, bool fault_active, uint16_t vbus_mv,
                 uint16_t current_ma, uint32_t now_ms);
enum phub_result phub_clear_fault(struct phub_port *p, uint32_t now_ms);

#endif
