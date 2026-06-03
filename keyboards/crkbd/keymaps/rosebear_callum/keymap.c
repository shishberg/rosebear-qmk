#include QMK_KEYBOARD_H
#include "transactions.h"

#ifdef CAPS_WORD_ENABLE
#    include "caps_word.h"
#endif

enum custom_keycodes {
    UG_TOG = SAFE_RANGE,
    UG_BRIU,
    UG_BRID,
    KEY_TOG,
    KEY_BRIU,
    KEY_BRID,
    CM_LCTL,
    CM_LALT,
    CM_LSFT,
    CM_LGUI,
    CM_RGUI,
    CM_RSFT,
    CM_RALT,
    CM_RCTL,
};

static uint8_t held_callum_mods = 0;
static uint8_t used_callum_mods = 0;

static uint8_t callum_mod_for_keycode(uint16_t keycode) {
    switch (keycode) {
        case CM_LCTL:
            return MOD_BIT(KC_LCTL);
        case CM_LALT:
            return MOD_BIT(KC_LALT);
        case CM_LSFT:
            return MOD_BIT(KC_LSFT);
        case CM_LGUI:
            return MOD_BIT(KC_LGUI);
        case CM_RGUI:
            return MOD_BIT(KC_RGUI);
        case CM_RSFT:
            return MOD_BIT(KC_RSFT);
        case CM_RALT:
            return MOD_BIT(KC_RALT);
        case CM_RCTL:
            return MOD_BIT(KC_RCTL);
        default:
            return 0;
    }
}

static void clear_callum_mods(void) {
    if (held_callum_mods) {
        unregister_mods(held_callum_mods);
    }
    held_callum_mods = 0;
    used_callum_mods = 0;
    clear_oneshot_mods();
}

static bool is_callum_consuming_key(uint16_t keycode) {
    return keycode != KC_NO && keycode != KC_TRNS;
}

#ifdef CAPS_WORD_ENABLE
static void maybe_turn_on_caps_word(void) {
    if (is_caps_word_on() || (held_callum_mods & MOD_MASK_SHIFT) != MOD_MASK_SHIFT) {
        return;
    }

    const uint8_t preserved_mods = held_callum_mods & ~MOD_MASK_SHIFT;

    caps_word_on();
    held_callum_mods = preserved_mods;
    used_callum_mods &= preserved_mods;
    add_mods(preserved_mods);
    send_keyboard_report();
}
#endif

static bool process_callum_mod(uint16_t keycode, keyrecord_t *record) {
    const uint8_t mod = callum_mod_for_keycode(keycode);
    if (!mod) {
        return true;
    }

    if (record->event.pressed) {
        held_callum_mods |= mod;
        used_callum_mods &= ~mod;
        register_mods(mod);
#ifdef CAPS_WORD_ENABLE
        maybe_turn_on_caps_word();
#endif
    } else if (held_callum_mods & mod) {
        unregister_mods(mod);
        held_callum_mods &= ~mod;
        if (used_callum_mods & mod) {
            used_callum_mods &= ~mod;
        } else {
            add_oneshot_mods(mod);
        }
    }

    return false;
}

const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {
    [0] = LAYOUT_split_3x6_3(
        KC_NO, KC_Q,    KC_W,    KC_F,    KC_P,    KC_B,          KC_J,    KC_L,    KC_U,    KC_Y,    KC_QUOT, KC_NO,
        KC_NO, KC_A,    KC_R,    KC_S,    KC_T,    KC_G,          KC_M,    KC_N,    KC_E,    KC_I,    KC_O,    KC_NO,
        KC_NO, KC_Z,    KC_X,    KC_C,    KC_D,    KC_V,          KC_K,    KC_H,    KC_COMM, KC_DOT,  KC_SLSH, KC_NO,
                                 KC_TAB,  MO(1),   KC_SPC,        KC_ENT,  MO(2),   KC_BSPC
    ),

    [1] = LAYOUT_split_3x6_3(
        UG_TOG,  KC_HOME, KC_PGUP, KC_PGDN, KC_END,  KC_LCBR,      KC_RCBR, KC_7,   KC_8,    KC_9,    KC_EQL,  KEY_TOG,
        UG_BRIU, CM_LCTL, CM_LALT, CM_LSFT, CM_LGUI, KC_LPRN,      KC_RPRN, KC_4,   KC_5,    KC_6,    KC_MINS, KEY_BRIU,
        UG_BRID, KC_LEFT, KC_UP,   KC_DOWN, KC_RGHT, KC_LBRC,      KC_RBRC, KC_1,   KC_2,    KC_3,    KC_SCLN, KEY_BRID,
                                   KC_TRNS, KC_TRNS, KC_TRNS,      KC_0,    MO(3),  KC_DEL
    ),

    [2] = LAYOUT_split_3x6_3(
        UG_TOG,  KC_PLUS, KC_GRV,  KC_ASTR, KC_AMPR, KC_MUTE,      KC_NO,   KC_NO,   KC_NO,   KC_NO,   KC_DQUO, KEY_TOG,
        UG_BRIU, KC_UNDS, KC_CIRC, KC_PERC, KC_DLR,  KC_VOLU,      KC_NO,   CM_RGUI, CM_RSFT, CM_RALT, CM_RCTL, KEY_BRIU,
        UG_BRID, KC_COLN, KC_HASH, KC_AT,   KC_EXLM, KC_VOLD,      KC_NO,   KC_PIPE, KC_TILD, KC_BSLS, KC_QUES, KEY_BRID,
                                   KC_ESC,  MO(3),   KC_NO,        KC_TRNS, KC_TRNS, KC_TRNS
    ),

    [3] = LAYOUT_split_3x6_3(
        UG_TOG,  KC_NO,   KC_F9,   KC_F8,   KC_F7,   KC_NO,        KC_NO,   KC_F10,  KC_F11,  KC_F12,  KC_NO,   KEY_TOG,
        UG_BRIU, CM_LCTL, CM_LALT, CM_LSFT, CM_LGUI, KC_NO,        KC_NO,   CM_RGUI, CM_RSFT, CM_RALT, CM_RCTL, KEY_BRIU,
        UG_BRID, KC_NO,   KC_F3,   KC_F2,   KC_F1,   KC_NO,        KC_NO,   KC_F4,   KC_F5,   KC_F6,   KC_NO,   KEY_BRID,
                                   KC_TRNS, KC_TRNS, KC_TRNS,      KC_TRNS, KC_TRNS, KC_TRNS
    ),
};

#ifdef RGB_MATRIX_ENABLE
void rosebear_splash_hit(uint8_t row, uint8_t col);

typedef struct {
    uint8_t underglow_enabled;
    uint8_t key_splash_enabled;
    uint8_t underglow_brightness;
    uint8_t key_brightness;
    uint8_t hit_id;
    uint8_t hit_row;
    uint8_t hit_col;
} led_sync_t;

static led_sync_t led_state = {
    .underglow_enabled = false,
    .key_splash_enabled = false,
    .underglow_brightness = 95,
    .key_brightness = 95,
};

static const uint8_t brightness_levels[] = {
    0, 1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64, 80, 96, 112,
    RGB_MATRIX_MAXIMUM_BRIGHTNESS,
};

static uint8_t next_brightness_level(uint8_t brightness) {
    for (uint8_t i = 0; i < ARRAY_SIZE(brightness_levels); i++) {
        if (brightness_levels[i] > brightness) {
            return brightness_levels[i] > RGB_MATRIX_MAXIMUM_BRIGHTNESS
                       ? RGB_MATRIX_MAXIMUM_BRIGHTNESS
                       : brightness_levels[i];
        }
    }

    return RGB_MATRIX_MAXIMUM_BRIGHTNESS;
}

static uint8_t prev_brightness_level(uint8_t brightness) {
    uint8_t prev = 0;

    for (uint8_t i = 0; i < ARRAY_SIZE(brightness_levels); i++) {
        if (brightness_levels[i] >= brightness) {
            return prev;
        }
        prev = brightness_levels[i];
    }

    return prev > RGB_MATRIX_MAXIMUM_BRIGHTNESS ? RGB_MATRIX_MAXIMUM_BRIGHTNESS : prev;
}

static void apply_led_mode(void) {
    rgb_matrix_enable_noeeprom();
    rgb_matrix_sethsv_noeeprom(128, 210, led_state.key_brightness);
    rgb_matrix_mode_noeeprom(led_state.key_splash_enabled
                                  ? RGB_MATRIX_CUSTOM_rosebear_small_splash
                                  : RGB_MATRIX_SOLID_COLOR);
    rgb_matrix_set_flags_noeeprom(led_state.key_splash_enabled ? LED_FLAG_KEYLIGHT | LED_FLAG_MODIFIER
                                                               : LED_FLAG_NONE);
    rgb_matrix_set_color_all(0, 0, 0);
}

static void led_sync_slave_handler(uint8_t in_buflen, const void *in_data,
                                   uint8_t out_buflen, void *out_data) {
    if (in_buflen >= sizeof(led_state)) {
        static uint8_t last_hit_id = 0;
        const led_sync_t incoming = *((const led_sync_t *)in_data);

        if (incoming.key_splash_enabled && incoming.hit_id != last_hit_id) {
            rosebear_splash_hit(incoming.hit_row, incoming.hit_col);
            last_hit_id = incoming.hit_id;
        }

        led_state = *((const led_sync_t *)in_data);
        apply_led_mode();
    }
}
#endif

void keyboard_post_init_user(void) {
#ifdef RGB_MATRIX_ENABLE
    transaction_register_rpc(RPC_ID_USER_LED_SYNC, led_sync_slave_handler);
    apply_led_mode();
#endif
}

#ifdef RGB_MATRIX_ENABLE
static rgb_t get_underglow_fade_color(void) {
    return hsv_to_rgb((hsv_t){192, 210, led_state.underglow_brightness});
}

bool rgb_matrix_indicators_advanced_user(uint8_t led_min, uint8_t led_max) {
    const rgb_t rgb = get_underglow_fade_color();
    for (uint8_t i = led_min; i < led_max; i++) {
        if (g_led_config.flags[i] & LED_FLAG_UNDERGLOW) {
            if (led_state.underglow_enabled) {
                rgb_matrix_set_color(i, rgb.r, rgb.g, rgb.b);
            } else {
                rgb_matrix_set_color(i, 0, 0, 0);
            }
        } else if ((g_led_config.flags[i] & (LED_FLAG_KEYLIGHT | LED_FLAG_MODIFIER)) &&
                   !led_state.key_splash_enabled) {
            rgb_matrix_set_color(i, 0, 0, 0);
        }
    }

    return false;
}
#endif

bool process_record_user(uint16_t keycode, keyrecord_t *record) {
    if (record->event.pressed && IS_QK_MOMENTARY(keycode)) {
        clear_callum_mods();
        return true;
    }

    if (!process_callum_mod(keycode, record)) {
        return false;
    }

    if (record->event.pressed && held_callum_mods && is_callum_consuming_key(keycode)) {
        used_callum_mods |= held_callum_mods;
    }

    switch (keycode) {
        case UG_TOG:
            if (record->event.pressed) {
                clear_oneshot_mods();
#ifdef RGB_MATRIX_ENABLE
                led_state.underglow_enabled = !led_state.underglow_enabled;
                apply_led_mode();
#endif
            }
            return false;
        case UG_BRIU:
            if (record->event.pressed) {
                clear_oneshot_mods();
#ifdef RGB_MATRIX_ENABLE
                led_state.underglow_brightness =
                    next_brightness_level(led_state.underglow_brightness);
                apply_led_mode();
#endif
            }
            return false;
        case UG_BRID:
            if (record->event.pressed) {
                clear_oneshot_mods();
#ifdef RGB_MATRIX_ENABLE
                led_state.underglow_brightness =
                    prev_brightness_level(led_state.underglow_brightness);
                apply_led_mode();
#endif
            }
            return false;
        case KEY_TOG:
            if (record->event.pressed) {
                clear_oneshot_mods();
#ifdef RGB_MATRIX_ENABLE
                led_state.key_splash_enabled = !led_state.key_splash_enabled;
                apply_led_mode();
#endif
            }
            return false;
        case KEY_BRIU:
            if (record->event.pressed) {
                clear_oneshot_mods();
#ifdef RGB_MATRIX_ENABLE
                led_state.key_brightness = next_brightness_level(led_state.key_brightness);
                apply_led_mode();
#endif
            }
            return false;
        case KEY_BRID:
            if (record->event.pressed) {
                clear_oneshot_mods();
#ifdef RGB_MATRIX_ENABLE
                led_state.key_brightness = prev_brightness_level(led_state.key_brightness);
                apply_led_mode();
#endif
            }
            return false;
    }

#ifdef RGB_MATRIX_ENABLE
    if (record->event.pressed && led_state.key_splash_enabled) {
        rosebear_splash_hit(record->event.key.row, record->event.key.col);
        led_state.hit_id++;
        led_state.hit_row = record->event.key.row;
        led_state.hit_col = record->event.key.col;
    }
#endif

    return true;
}

void housekeeping_task_user(void) {
#ifdef RGB_MATRIX_ENABLE
    if (is_keyboard_master()) {
        static led_sync_t last_led_state = {0};
        static uint32_t   last_led_sync  = 0;

        if (memcmp(&led_state, &last_led_state, sizeof(led_state)) ||
            timer_elapsed32(last_led_sync) > 1000) {
            if (transaction_rpc_send(RPC_ID_USER_LED_SYNC, sizeof(led_state),
                                     &led_state)) {
                last_led_state = led_state;
                last_led_sync  = timer_read32();
            }
        }
    }
#endif
}
