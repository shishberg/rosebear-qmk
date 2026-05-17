MOUSEKEY_ENABLE = yes
EXTRAKEY_ENABLE = yes
RGBLIGHT_ENABLE = no
RGB_MATRIX_ENABLE = yes
RGB_MATRIX_CUSTOM_USER = yes

ROSEBEAR_HID_LOG ?= no
ifeq ($(strip $(ROSEBEAR_HID_LOG)),yes)
    RAW_ENABLE = yes
endif

SRC += features/achordion.c
CFLAGS += -Wno-error=cpp
LTO_ENABLE = yes
