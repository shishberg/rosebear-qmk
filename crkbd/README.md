# Rosebear QMK — Corne (crkbd)

A direct translation of the [Rosebear ZMK keymap](https://github.com/shishberg/rosebear-zmk) for the [Corne](https://github.com/foostan/crkbd) (crkbd) keyboard, 3x6+3 layout (`LAYOUT_split_3x6_3`).

Colemak-DH base. Homerow mods on the second row, layer-tap on the thumbs, plus a HOLD layer reachable from the inner thumbs that exposes Bluetooth-style hotkeys (mapped to `LSFT+LALT+LCTL+<key>`) and a Gaming-mode toggle.

The ZMK source is 36 keys; the Corne is 42. The extra outer pinky column on each half is `KC_NO` here.

## ZMK to QMK behaviour mapping

The ZMK keymap defines four hold-tap behaviours with per-key tapping terms:

| ZMK behaviour | tapping term | quick-tap | require-prior-idle | used for |
|---|---|---|---|---|
| `ms` (mod-tap short) | 150 ms | 150 ms | 100 ms | shift homerow mods |
| `ml` (mod-tap long)  | 200 ms | 200 ms | 150 ms | ctrl/alt/gui homerow mods |
| `ls` (layer-tap short) | 150 ms | 150 ms | 125 ms | left-thumb layer-taps |
| `ll` (layer-tap long)  | 200 ms | 200 ms | 150 ms | right-thumb layer-taps |

QMK can't easily express per-key tapping terms in `keymap.json` alone (that needs custom C in `keymap.c`). For the QMK Configurator path this keymap sets a single global `tapping_term` of **200 ms** and `quick_tap_term` of **200 ms**, which matches the `ml`/`ll` long behaviours. The 150 ms short behaviours (shift homerow mods, left-thumb layer-taps) are slightly slower as a result. ZMK's `tap-preferred` flavor matches QMK's default — we deliberately do **not** enable `PERMISSIVE_HOLD` or `HOLD_ON_OTHER_KEY_PRESS`.

ZMK's `require-prior-idle-ms` has no direct `keymap.json` equivalent. If hold-tap accidental triggers become a problem, you'll need to drop to a custom `keymap.c` and configure `TAPPING_TERM_PER_KEY` / `HOLD_ON_OTHER_KEY_PRESS` there.

Bluetooth (`&bt BT_SEL n`, `&bt BT_CLR`) and output-toggle (`&out OUT_TOG`) keys are mapped to `KC_NO` because QMK on a Corne is wired only.

| ZMK | QMK |
|---|---|
| `&kp X` | `KC_X` |
| `&trans` | `KC_TRNS` |
| `&none` | `KC_NO` |
| `&ml LCTRL A` | `MT(MOD_LCTL, KC_A)` |
| `&ms LSHFT S` | `MT(MOD_LSFT, KC_S)` |
| `&ls SYM TAB` | `LT(2, KC_TAB)` |
| `&ll NUM RET` | `LT(1, KC_ENT)` |
| `&to MAIN` | `TO(0)` |
| `&tog GAM` | `TG(3)` |
| `&kp LS(LA(LC(X)))` | `LSFT(LALT(LCTL(KC_X)))` |
| `&bt BT_SEL n`, `&out OUT_TOG` | `KC_NO` |

## Layers

`v` = transparent (falls through to a lower layer). `_` = unused (`KC_NO`).

The Corne grid here shows columns 1–6 of each half; the outermost pinky column (col 0) is omitted because it's always `_`.

### MAIN (0)

```
+------+------+------+------+------+------+   +------+------+------+------+------+------+
|  Q   |  W   |  F   |  P   |  B   |  _   |   |  _   |  J   |  L   |  U   |  Y   |  '   |
+------+------+------+------+------+------+   +------+------+------+------+------+------+
| Ctl/A| Alt/R| Sft/S| Gui/T|  G   |  _   |   |  _   |  M   | Gui/N| Sft/E| Alt/I| Ctl/O|
+------+------+------+------+------+------+   +------+------+------+------+------+------+
|  Z   |  X   |  C   |  D   |  V   |  _   |   |  _   |  K   |  H   |  ,   |  .   |  /   |
+------+------+------+------+------+------+   +------+------+------+------+------+------+
                    | SYM/ | NUM/ | HOLD |   | HOLD | NUM/ | SYM/ |
                    |  TAB |  SPC |  ESC |   |  DEL |  ENT | BSPC |
                    +------+------+------+   +------+------+------+
```

The outermost pinky column (col 0) is `_` on every layer.

### NUM (1)

```
+------+------+------+------+------+------+   +------+------+------+------+------+------+
| F10  |  F7  |  F8  |  F9  |  {   |      |   |      |  }   |  7   |  8   |  9   |  =   |
+------+------+------+------+------+------+   +------+------+------+------+------+------+
| F11  |  F4  |  F5  |  F6  |  (   |      |   |      |  )   |  4   |  5   |  6   |  -   |
+------+------+------+------+------+------+   +------+------+------+------+------+------+
| F12  |  F1  |  F2  |  F3  |  [   |      |   |      |  ]   |  1   |  2   |  3   |  ;   |
+------+------+------+------+------+------+   +------+------+------+------+------+------+
                    |  v   |  v   | MAIN |   | MAIN |  v   |  0   |
                    +------+------+------+   +------+------+------+
```

### SYM (2)

```
+------+------+------+------+------+------+   +------+------+------+------+------+------+
| HOME | PGUP | PGDN | END  |      |      |   |      |  \   |  &   |  *   |  `   |  +   |
+------+------+------+------+------+------+   +------+------+------+------+------+------+
| LEFT |  UP  | DOWN | RGHT |      |      |   |      |  ~   |  $   |  %   |  ^   |  _   |
+------+------+------+------+------+------+   +------+------+------+------+------+------+
|      | MUTE | VOLD | VOLU |      |      |   |      |  |   |  !   |  @   |  #   |  :   |
+------+------+------+------+------+------+   +------+------+------+------+------+------+
                    |  v   |  v   | MAIN |   | MAIN |  v   |  v   |
                    +------+------+------+   +------+------+------+
```

### GAM (3) — Gaming

Plain Colemak-DH on the left half (no homerow mods), so WASD-style holds work without triggering modifiers. Right-half homerow mods are kept. Reached via `TG(3)` on the HOLD layer; toggle off the same way.

Thumbs use a different layer set: left thumbs are `LT(GNUM, TAB)`, `LT(GFUN, SPC)`, `LT(HOLD, ESC)`. Right thumbs match MAIN: `LT(HOLD, DEL)`, `LT(NUM, ENT)`, `LT(SYM, BSPC)`.

### GNUM (4) — Gaming numpad

Reached by holding the left-outer thumb in GAM. Left half: `LALT 7 8 9 VOLU` / `LSFT 4 5 6 VOLD` / `LGUI 1 2 3 0`. Right half: same numpad as NUM.

### GFUN (5) — Gaming function row

Reached by holding the left-middle thumb in GAM. Left half: `LALT F7 F8 F9 F12` / `LSFT F4 F5 F6 F11` / `LGUI F1 F2 F3 F10`. Right half: same numpad as NUM.

### HOLD (6) — System / "BT"

Reached by holding either inner thumb. The right half is `LSFT(LALT(LCTL(<key>)))` versions of every right-side letter and punctuation key — useful as global hotkeys. The left-middle row carries `TG(GAM)` to flip into gaming mode. Bluetooth-related keys from the ZMK source are `KC_NO` here. The left thumbs jump to SYM and NUM via `TO(2)`/`TO(1)`; the right thumbs do the mirror.

## Building

No local QMK toolchain required — the [QMK Configurator](https://config.qmk.fm/) can build firmware:

1. Open <https://config.qmk.fm/>.
2. Click **Import Keymap** and select `keymap.json` from this directory.
3. Click the green **Compile** button.
4. Download the `.hex` (or `.uf2`, depending on your controller) firmware.
5. Flash each half separately using [QMK Toolbox](https://qmk.fm/toolbox).

For a local build:

```sh
qmk compile keymap.json
```

The keyboard field is `crkbd/rev1`. If you have a newer revision (`crkbd/r2g`, `crkbd/rev4_0`, `crkbd/rev4_1`) change that field before compiling.

## Things to double-check before flashing

- The 150 ms shift homerow mods are now 200 ms. If shift accidentally fires when you didn't want it to, you'll want a custom `keymap.c` with `TAPPING_TERM_PER_KEY`.
- `LSFT(LALT(LCTL(KC_QUOT)))` and the other "BT" hotkeys assume your OS' shortcut bindings expect that exact modifier set; the ZMK source used `LS(LA(LC(...)))` which is the same combination.
- The crkbd outer pinky column is unrouted as `KC_NO`. If you have a Corne build with that column populated, swap them in.
