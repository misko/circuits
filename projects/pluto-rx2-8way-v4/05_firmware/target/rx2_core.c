#include "rx2_core.h"

#include <limits.h>
#include <string.h>

struct rx2_config rx2_config_default(void)
{
    const struct rx2_config config = {
        .sample_rate_hz = 30000000u,
        .ordinary_clean_samples = 8192u,
        .reference_clean_samples = 4096u,
        .blank_samples = 128u,
    };
    return config;
}

bool rx2_config_valid(const struct rx2_config *config)
{
    uint64_t ordinary;
    uint64_t reference;
    uint64_t frame;

    if (!config || config->sample_rate_hz < 2000u ||
        config->sample_rate_hz > 50000000u)
        return false;
    ordinary = (uint64_t)config->blank_samples +
               config->ordinary_clean_samples;
    reference = (uint64_t)config->blank_samples +
                config->reference_clean_samples;
    frame = 7u * ordinary + reference;
    return ordinary > RX2_PIO_OVERHEAD_SAMPLES &&
           reference > RX2_PIO_OVERHEAD_SAMPLES &&
           ordinary < (1u << 28) && reference < (1u << 28) &&
           frame <= UINT32_MAX;
}

uint32_t rx2_frame_samples(const struct rx2_config *config)
{
    if (!rx2_config_valid(config))
        return 0u;
    return 7u * (config->blank_samples + config->ordinary_clean_samples) +
           config->blank_samples + config->reference_clean_samples;
}

uint8_t rx2_gpio_code(uint8_t state)
{
    if (state >= RX2_STATE_COUNT)
        return RX2_ALL_OFF_GPIO_CODE;

    /* PE42482: V1 is the state MSB, V3 is the LSB.  Carrier GPIO order is
     * GP0=V1, GP1=V2, GP2=V3, GP3=V4, hence the three-bit reversal. */
    return (uint8_t)(((state & 0x4u) >> 2) |
                     (state & 0x2u) |
                     ((state & 0x1u) << 2));
}

uint32_t rx2_dwell_samples(const struct rx2_config *config, uint8_t state)
{
    if (!rx2_config_valid(config) || state >= RX2_STATE_COUNT)
        return 0u;
    return config->blank_samples +
           (state == 7u ? config->reference_clean_samples
                        : config->ordinary_clean_samples);
}

uint32_t rx2_schedule_word(const struct rx2_config *config, uint8_t state)
{
    uint32_t dwell = rx2_dwell_samples(config, state);
    if (!dwell)
        return 0u;
    return ((dwell - RX2_PIO_OVERHEAD_SAMPLES) << 4) |
           rx2_gpio_code(state);
}

void rx2_status_init(struct rx2_status *status)
{
    memset(status, 0, sizeof(*status));
    status->config = rx2_config_default();
}

bool rx2_select(struct rx2_status *status, uint8_t state)
{
    if (!status || state >= RX2_STATE_COUNT)
        return false;
    status->running = false;
    status->muted = false;
    status->selected_state = state;
    return true;
}

void rx2_mute(struct rx2_status *status)
{
    if (!status)
        return;
    status->running = false;
    status->muted = true;
}

void rx2_start(struct rx2_status *status)
{
    if (!status)
        return;
    status->running = true;
    status->muted = false;
    status->selected_state = 0u;
}

void rx2_stop(struct rx2_status *status)
{
    if (status)
        status->running = false;
}

bool rx2_set_config(struct rx2_status *status,
                    const struct rx2_config *config)
{
    if (!status || !rx2_config_valid(config))
        return false;
    status->running = false;
    status->config = *config;
    return true;
}

void rx2_note_transition(struct rx2_status *status)
{
    if (!status || !status->running)
        return;
    status->transition_count++;
    status->selected_state = (uint8_t)((status->selected_state + 1u) %
                                       RX2_STATE_COUNT);
    if (status->selected_state == 0u)
        status->frame_count++;
}
