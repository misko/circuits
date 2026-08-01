#include "phub_core.h"

#include <assert.h>
#include <stdio.h>

int main(void)
{
    struct phub_port p;
    uint32_t clamped;
    phub_port_init(&p);
    assert(!p.out.power_en && p.out.data_oe_n);

    phub_set_data(&p, true, 1);
    assert(!p.out.data_oe_n);
    assert(phub_set_power(&p, true, 2) == PHUB_OK);
    assert(phub_power_cycle(&p, 1, 3, &clamped) == PHUB_OK);
    assert(clamped == 50 && !p.out.power_en);
    phub_sample(&p, false, 0, 0, 52);
    assert(!p.out.power_en);
    phub_sample(&p, false, 5000, 20, 53);
    assert(p.out.power_en && p.vbus_present);

    phub_sample(&p, true, 4900, 3795, 54);
    assert(!p.out.power_en && p.fault_latched && p.fault_count == 1);
    assert(phub_set_power(&p, true, 55) == PHUB_FAULT_ACTIVE);
    assert(phub_clear_fault(&p, 55) == PHUB_FAULT_ACTIVE);
    phub_sample(&p, false, 0, 0, 56);
    assert(phub_clear_fault(&p, 57) == PHUB_OK);
    assert(phub_set_power(&p, true, 58) == PHUB_OK);

    puts("phub_core: OK");
    return 0;
}
