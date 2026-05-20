#include QMK_KEYBOARD_H
#include "transactions.h"
#include "features/achordion.h"
#ifdef RAW_ENABLE
#    include "raw_hid.h"
#endif

enum custom_keycodes {
    UG_TOG = SAFE_RANGE,
    UG_BRIU,
    UG_BRID,
    KEY_TOG,
    KEY_BRIU,
    KEY_BRID,
};

#ifdef RAW_ENABLE
enum {
    HID_LOG_MAGIC       = 0x52,
    HID_LOG_VERSION     = 1,
    HID_LOG_KEY_EVENT   = 1,
    HID_LOG_MOD_EVENT   = 2,
    HID_LOG_LAYER_EVENT = 3,
    HID_LOG_HOST_ENABLE = 16,
    HID_LOG_STATUS      = 17,
};

static bool     hid_log_enabled = false;
static uint16_t hid_log_seq     = 0;
static uint8_t  hid_log_mods    = 0;
static uint32_t hid_log_layers  = 0;

static void hid_log_put_u16(uint8_t *packet, uint8_t offset, uint16_t value) {
    packet[offset]     = value & 0xFF;
    packet[offset + 1] = value >> 8;
}

static void hid_log_put_u32(uint8_t *packet, uint8_t offset, uint32_t value) {
    packet[offset]     = value & 0xFF;
    packet[offset + 1] = (value >> 8) & 0xFF;
    packet[offset + 2] = (value >> 16) & 0xFF;
    packet[offset + 3] = (value >> 24) & 0xFF;
}

static void hid_log_send_status(void) {
    uint8_t packet[32] = {0};

    packet[0] = HID_LOG_MAGIC;
    packet[1] = HID_LOG_VERSION;
    packet[2] = HID_LOG_STATUS;
    packet[3] = hid_log_enabled;
    hid_log_put_u16(packet, 4, hid_log_seq);
    hid_log_put_u32(packet, 6, timer_read32());

    raw_hid_send(packet, sizeof(packet));
}

static uint8_t hid_log_current_mods(void) {
    return get_mods() | get_weak_mods() | get_oneshot_mods() | get_oneshot_locked_mods();
}

static void hid_log_send_state_event(uint8_t type, bool active, uint8_t changed, uint8_t real_mods,
                                     uint8_t weak_mods, uint8_t oneshot_mods,
                                     uint8_t oneshot_locked_mods) {
    uint8_t packet[32] = {0};

    packet[0] = HID_LOG_MAGIC;
    packet[1] = HID_LOG_VERSION;
    packet[2] = type;
    packet[3] = active;
    hid_log_put_u16(packet, 4, hid_log_seq++);
    hid_log_put_u32(packet, 6, timer_read32());
    hid_log_put_u16(packet, 10, timer_read());
    packet[12] = changed;
    packet[13] = real_mods;
    packet[14] = weak_mods;
    packet[15] = oneshot_mods;
    packet[16] = oneshot_locked_mods;
    packet[17] = hid_log_current_mods();
    hid_log_put_u32(packet, 20, layer_state);
    hid_log_put_u32(packet, 24, default_layer_state);

    raw_hid_send(packet, sizeof(packet));
}

static void hid_log_reset_state(void) {
    hid_log_mods   = hid_log_current_mods();
    hid_log_layers = layer_state;
}

static void hid_log_task(void) {
    if (!hid_log_enabled) {
        return;
    }

    const uint8_t real_mods            = get_mods();
    const uint8_t weak_mods            = get_weak_mods();
    const uint8_t oneshot_mods         = get_oneshot_mods();
    const uint8_t oneshot_locked_mods  = get_oneshot_locked_mods();
    const uint8_t current_mods         = real_mods | weak_mods | oneshot_mods | oneshot_locked_mods;
    const uint8_t changed_mods         = current_mods ^ hid_log_mods;

    for (uint8_t bit = 0; bit < 8; bit++) {
        const uint8_t mask = 1 << bit;
        if (changed_mods & mask) {
            hid_log_send_state_event(HID_LOG_MOD_EVENT, current_mods & mask, mask, real_mods,
                                     weak_mods, oneshot_mods, oneshot_locked_mods);
        }
    }
    hid_log_mods = current_mods;

    const uint32_t current_layers = layer_state;
    const uint32_t changed_layers = current_layers ^ hid_log_layers;
    for (uint8_t layer = 0; layer < 32; layer++) {
        const uint32_t mask = 1UL << layer;
        if (changed_layers & mask) {
            hid_log_send_state_event(HID_LOG_LAYER_EVENT, current_layers & mask, layer, real_mods,
                                     weak_mods, oneshot_mods, oneshot_locked_mods);
        }
    }
    hid_log_layers = current_layers;
}

void raw_hid_receive(uint8_t *data, uint8_t length) {
    if (length != 32 || data[0] != HID_LOG_MAGIC || data[1] != HID_LOG_VERSION) {
        return;
    }

    switch (data[2]) {
        case HID_LOG_HOST_ENABLE:
            hid_log_enabled = data[3] != 0;
            hid_log_reset_state();
            if (!hid_log_enabled) {
                hid_log_seq = 0;
            }
            hid_log_send_status();
            break;
    }
}

bool pre_process_record_user(uint16_t keycode, keyrecord_t *record) {
    if (!hid_log_enabled || IS_NOEVENT(record->event)) {
        return true;
    }

    uint8_t packet[32] = {0};

    packet[0] = HID_LOG_MAGIC;
    packet[1] = HID_LOG_VERSION;
    packet[2] = HID_LOG_KEY_EVENT;
    packet[3] = record->event.pressed;
    hid_log_put_u16(packet, 4, hid_log_seq++);
    hid_log_put_u32(packet, 6, timer_read32());
    hid_log_put_u16(packet, 10, record->event.time);
    hid_log_put_u16(packet, 12, keycode);
    packet[14] = record->event.key.row;
    packet[15] = record->event.key.col;
    packet[16] = get_highest_layer(layer_state | default_layer_state);
    packet[17] = get_mods();
    packet[18] = get_oneshot_mods();
    packet[19] = hid_log_current_mods();
    hid_log_put_u32(packet, 20, layer_state);
    hid_log_put_u32(packet, 24, default_layer_state);

    raw_hid_send(packet, sizeof(packet));
    return true;
}
#endif

const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {
    [0] = LAYOUT_split_3x6_3(
        KC_LSFT, KC_Q,               KC_W,               KC_F,               KC_P,               KC_B,         KC_J,    KC_L,               KC_U,               KC_Y,               KC_QUOT,            KC_RSFT,
        KC_LGUI, MT(MOD_LCTL, KC_A), MT(MOD_LALT, KC_R), MT(MOD_LSFT, KC_S), MT(MOD_LGUI, KC_T), KC_G,         KC_M,    MT(MOD_RGUI, KC_N), MT(MOD_RSFT, KC_E), MT(MOD_RALT, KC_I), MT(MOD_RCTL, KC_O), KC_RGUI,
        KC_LCTL, KC_Z,               KC_X,               KC_C,               KC_D,               KC_V,         KC_K,    KC_H,               KC_COMM,            KC_DOT,             KC_SLSH,            KC_RALT,
                                                       LT(3, KC_ESC),      LT(2, KC_TAB),      LT(1, KC_SPC),  LT(1, KC_ENT),  LT(2, KC_BSPC),  LT(3, KC_DEL)
    ),

    [1] = LAYOUT_split_3x6_3(
        KC_TRNS, KC_F10, KC_F7, KC_F8, KC_F9, KC_LCBR,        KC_RCBR, KC_7,    KC_8,    KC_9,    KC_EQL,  KC_TRNS,
        KC_TRNS, KC_F11, KC_F4, KC_F5, KC_F6, KC_LPRN,        KC_RPRN, KC_4,    KC_5,    KC_6,    KC_MINS, KC_TRNS,
        KC_TRNS, KC_F12, KC_F1, KC_F2, KC_F3, KC_LBRC,        KC_RBRC, KC_1,    KC_2,    KC_3,    KC_SCLN, KC_TRNS,
                              KC_TRNS, KC_TRNS, KC_TRNS,    KC_TRNS, KC_0,    KC_0
    ),

    [2] = LAYOUT_split_3x6_3(
        KC_TRNS, KC_HOME, KC_PGUP, KC_PGDN, KC_END,  KC_NO,    KC_BSLS, KC_AMPR, KC_ASTR, KC_GRV,  KC_PLUS, KC_TRNS,
        KC_TRNS, KC_LEFT, KC_UP,   KC_DOWN, KC_RGHT, KC_NO,    KC_TILD, KC_DLR,  KC_PERC, KC_CIRC, KC_UNDS, KC_TRNS,
        KC_TRNS, KC_NO,   KC_MUTE, KC_VOLD, KC_VOLU, KC_NO,    KC_PIPE, KC_EXLM, KC_AT,   KC_HASH, KC_COLN, KC_TRNS,
                                 KC_TRNS, KC_TRNS, KC_TRNS,  KC_TRNS, KC_TRNS, KC_TRNS
    ),

    [3] = LAYOUT_split_3x6_3(
        UG_TOG,  KC_NO,   KC_NO,   KC_NO,   KC_NO,   KC_NO,    KC_NO,   KC_NO,   KC_NO,   KC_NO,   KC_NO,   KEY_TOG,
        UG_BRIU, MS_LEFT, MS_UP,   MS_DOWN, MS_RGHT, KC_NO,    KC_NO,   MS_LEFT, MS_DOWN, MS_UP,   MS_RGHT, KEY_BRIU,
        UG_BRID, MS_ACL0, MS_ACL1, MS_ACL2, KC_NO,   KC_NO,    KC_NO,   MS_ACL2, MS_ACL1, MS_ACL0, KC_NO,   KEY_BRID,
                                 MS_BTN3, MS_BTN2, MS_BTN1,  MS_BTN1, MS_BTN2, MS_BTN3
    ),
};

uint16_t get_tapping_term(uint16_t keycode, keyrecord_t *record) {
    switch (keycode) {
        case MT(MOD_LCTL, KC_A):
        case MT(MOD_LALT, KC_R):
        case MT(MOD_LSFT, KC_S):
        case MT(MOD_LGUI, KC_T):
        case MT(MOD_RGUI, KC_N):
        case MT(MOD_RSFT, KC_E):
        case MT(MOD_RALT, KC_I):
        case MT(MOD_RCTL, KC_O):
            return 200;

        case LT(3, KC_ESC):
        case LT(2, KC_TAB):
        case LT(1, KC_SPC):
        case LT(1, KC_ENT):
        case LT(2, KC_BSPC):
        case LT(3, KC_DEL):
            return 160;
        default:
            return TAPPING_TERM;
    }
}

uint16_t get_quick_tap_term(uint16_t keycode, keyrecord_t *record) {
    return get_tapping_term(keycode, record);
}

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
    switch (keycode) {
        case UG_TOG:
            if (record->event.pressed) {
#ifdef RGB_MATRIX_ENABLE
                led_state.underglow_enabled = !led_state.underglow_enabled;
                apply_led_mode();
#endif
            }
            return false;
        case UG_BRIU:
            if (record->event.pressed) {
#ifdef RGB_MATRIX_ENABLE
                led_state.underglow_brightness =
                    next_brightness_level(led_state.underglow_brightness);
                apply_led_mode();
#endif
            }
            return false;
        case UG_BRID:
            if (record->event.pressed) {
#ifdef RGB_MATRIX_ENABLE
                led_state.underglow_brightness =
                    prev_brightness_level(led_state.underglow_brightness);
                apply_led_mode();
#endif
            }
            return false;
        case KEY_TOG:
            if (record->event.pressed) {
#ifdef RGB_MATRIX_ENABLE
                led_state.key_splash_enabled = !led_state.key_splash_enabled;
                apply_led_mode();
#endif
            }
            return false;
        case KEY_BRIU:
            if (record->event.pressed) {
#ifdef RGB_MATRIX_ENABLE
                led_state.key_brightness = next_brightness_level(led_state.key_brightness);
                apply_led_mode();
#endif
            }
            return false;
        case KEY_BRID:
            if (record->event.pressed) {
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

    return process_achordion(keycode, record);
}

void housekeeping_task_user(void) {
    achordion_task();
#ifdef RAW_ENABLE
    hid_log_task();
#endif
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

bool achordion_chord(uint16_t tap_hold_keycode, keyrecord_t *tap_hold_record,
                     uint16_t other_keycode, keyrecord_t *other_record) {
    return true;
}

uint16_t achordion_streak_chord_timeout(uint16_t tap_hold_keycode,
                                        uint16_t next_keycode) {
    // Approximate ZMK's require-prior-idle-ms for Rosebear's home-row mods and
    // layer-taps. ZMK looks backward and can immediately force a hold-tap to
    // tap if another key was pressed recently. Achordion cannot make that exact
    // decision, but its typing-streak logic can turn a would-be hold back into
    // a tap when the surrounding key presses look like normal typing.
    switch (tap_hold_keycode) {
        case LT(3, KC_ESC):
        case LT(2, KC_TAB):
        case LT(1, KC_SPC):
            return 125;

        case MT(MOD_LCTL, KC_A):
        case MT(MOD_LALT, KC_R):
        case MT(MOD_LSFT, KC_S):
        case MT(MOD_LGUI, KC_T):
        case MT(MOD_RGUI, KC_N):
        case MT(MOD_RSFT, KC_E):
        case MT(MOD_RALT, KC_I):
        case MT(MOD_RCTL, KC_O):
        case LT(1, KC_ENT):
        case LT(2, KC_BSPC):
        case LT(3, KC_DEL):
            return 150;

        default:
            return 0;
    }
}
