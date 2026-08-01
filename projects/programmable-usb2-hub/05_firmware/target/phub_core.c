#include "phub_core.h"

#include <string.h>

#define VBUS_PRESENT_ON_MV 4500u
#define VBUS_PRESENT_OFF_MV 4200u
#define MIN_CYCLE_MS 50u
#define MAX_CYCLE_MS 60000u

static bool deadline_reached(uint32_t now, uint32_t deadline)
{
    return (int32_t)(now - deadline) >= 0;
}

static void changed(struct phub_port *p, uint32_t now_ms)
{
    p->last_transition_ms = now_ms;
}

void phub_port_init(struct phub_port *p)
{
    memset(p, 0, sizeof(*p));
    p->out.data_oe_n = true; /* FSUSB42 disconnected */
}

enum phub_result phub_set_power(struct phub_port *p, bool enabled,
                                uint32_t now_ms)
{
    if (enabled && (p->fault_active || p->fault_latched))
        return PHUB_FAULT_ACTIVE;
    p->cycle_pending = false;
    if (p->power_commanded != enabled || p->out.power_en != enabled) {
        p->power_commanded = enabled;
        p->out.power_en = enabled;
        changed(p, now_ms);
    }
    return PHUB_OK;
}

enum phub_result phub_power_cycle(struct phub_port *p, uint32_t off_ms,
                                  uint32_t now_ms, uint32_t *clamped_ms)
{
    if (p->fault_active || p->fault_latched)
        return PHUB_FAULT_ACTIVE;
    if (off_ms < MIN_CYCLE_MS)
        off_ms = MIN_CYCLE_MS;
    if (off_ms > MAX_CYCLE_MS)
        off_ms = MAX_CYCLE_MS;
    if (clamped_ms)
        *clamped_ms = off_ms;
    p->power_commanded = true;
    p->out.power_en = false;
    p->cycle_restore_at_ms = now_ms + off_ms;
    p->cycle_pending = true;
    changed(p, now_ms);
    return PHUB_OK;
}

void phub_set_data(struct phub_port *p, bool connected, uint32_t now_ms)
{
    bool oe_n = !connected;
    if (p->data_commanded != connected || p->out.data_oe_n != oe_n) {
        p->data_commanded = connected;
        p->out.data_oe_n = oe_n;
        changed(p, now_ms);
    }
}

void phub_sample(struct phub_port *p, bool fault_active, uint16_t vbus_mv,
                 uint16_t current_ma, uint32_t now_ms)
{
    if (fault_active && !p->fault_active) {
        if (p->fault_count != UINT32_MAX)
            p->fault_count++;
        p->fault_latched = true;
        p->power_commanded = false;
        p->out.power_en = false;
        p->cycle_pending = false;
        changed(p, now_ms);
    }
    p->fault_active = fault_active;
    p->vbus_mv = vbus_mv;
    p->current_ma = current_ma;
    p->vbus_present = p->vbus_present ? vbus_mv > VBUS_PRESENT_OFF_MV
                                      : vbus_mv >= VBUS_PRESENT_ON_MV;
    if (p->cycle_pending && deadline_reached(now_ms,
                                             p->cycle_restore_at_ms)) {
        p->cycle_pending = false;
        if (!p->fault_active && !p->fault_latched) {
            p->power_commanded = true;
            p->out.power_en = true;
            changed(p, now_ms);
        }
    }
}

enum phub_result phub_clear_fault(struct phub_port *p, uint32_t now_ms)
{
    if (p->fault_active)
        return PHUB_FAULT_ACTIVE;
    if (p->fault_latched) {
        p->fault_latched = false;
        changed(p, now_ms);
    }
    return PHUB_OK;
}
