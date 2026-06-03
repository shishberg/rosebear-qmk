#ifdef RGB_MATRIX_KEYREACTIVE_ENABLED
RGB_MATRIX_EFFECT(rosebear_small_splash)

#    ifdef RGB_MATRIX_CUSTOM_EFFECT_IMPLS

#        define ROSEBEAR_SPLASH_TICK_MS 45
#        define ROSEBEAR_SPLASH_RADIUS 34
#        define ROSEBEAR_SPLASH_VALUE_DECAY 7
#        define ROSEBEAR_SPLASH_HIT_VALUE 128

static uint8_t  rosebear_value[RGB_MATRIX_LED_COUNT];
static uint8_t  rosebear_next_value[RGB_MATRIX_LED_COUNT];
static uint16_t rosebear_splash_timer;

void rosebear_splash_hit(uint8_t row, uint8_t col) {
    uint8_t leds[LED_HITS_TO_REMEMBER];
    uint8_t led_count = rgb_matrix_map_row_column_to_led(row, col, leds);

    for (uint8_t i = 0; i < led_count; i++) {
        const uint8_t led = leds[i];
        if (led < RGB_MATRIX_LED_COUNT &&
            (g_led_config.flags[led] & (LED_FLAG_KEYLIGHT | LED_FLAG_MODIFIER))) {
            rosebear_value[led] = qadd8(rosebear_value[led], ROSEBEAR_SPLASH_HIT_VALUE);
        }
    }
}

static void rosebear_step_buffers(void) {
    for (uint8_t i = 0; i < RGB_MATRIX_LED_COUNT; i++) {
        rosebear_next_value[i] = qsub8(rosebear_value[i], ROSEBEAR_SPLASH_VALUE_DECAY);
    }

    for (uint8_t source = 0; source < RGB_MATRIX_LED_COUNT; source++) {
        if (rosebear_value[source] == 0 ||
            !(g_led_config.flags[source] & (LED_FLAG_KEYLIGHT | LED_FLAG_MODIFIER))) {
            continue;
        }

        for (uint8_t target = 0; target < RGB_MATRIX_LED_COUNT; target++) {
            if (source == target ||
                !(g_led_config.flags[target] & (LED_FLAG_KEYLIGHT | LED_FLAG_MODIFIER))) {
                continue;
            }

            const int16_t dx   = g_led_config.point[target].x - g_led_config.point[source].x;
            const int16_t dy   = g_led_config.point[target].y - g_led_config.point[source].y;
            const uint8_t dist = sqrt16((int32_t)dx * dx + (int32_t)dy * dy);
            if (dist > ROSEBEAR_SPLASH_RADIUS) {
                continue;
            }

            const uint8_t spread_drop = 28 + dist * 3;
            const uint8_t value       = qsub8(rosebear_value[source], spread_drop);
            if (value > rosebear_next_value[target]) {
                rosebear_next_value[target] = value;
            }
        }
    }

    memcpy(rosebear_value, rosebear_next_value, sizeof(rosebear_value));
}

static rgb_t rosebear_value_to_rgb(uint8_t value) {
    if (value > 170) {
        const uint8_t red = (value - 170) * 3;
        return (rgb_t){red, 255, 255};
    }

    if (value > 85) {
        const uint8_t green = (value - 85) * 3;
        return (rgb_t){0, green, 255};
    }

    return (rgb_t){0, 0, value * 3};
}

static bool rosebear_small_splash(effect_params_t *params) {
    RGB_MATRIX_USE_LIMITS(led_min, led_max);

    if (params->init) {
        memset(rosebear_value, 0, sizeof(rosebear_value));
        rosebear_splash_timer = timer_read();
    }

    if (params->iter == 0 && timer_elapsed(rosebear_splash_timer) >= ROSEBEAR_SPLASH_TICK_MS) {
        rosebear_splash_timer = timer_read();
        rosebear_step_buffers();
    }

    for (uint8_t i = led_min; i < led_max; i++) {
        RGB_MATRIX_TEST_LED_FLAGS();

        rgb_t rgb = rosebear_value_to_rgb(rosebear_value[i]);
        rgb.r     = scale8(rgb.r, rgb_matrix_config.hsv.v);
        rgb.g     = scale8(rgb.g, rgb_matrix_config.hsv.v);
        rgb.b     = scale8(rgb.b, rgb_matrix_config.hsv.v);
        rgb_matrix_set_color(i, rgb.r, rgb.g, rgb.b);
    }

    return rgb_matrix_check_finished_leds(led_max);
}

#    endif
#endif
