# Rosebear QMK

QMK keymap for a **Lily58** keyboard, ported from the [ZMK Rosebear](https://github.com/shishberg/rosebear-zmk) layout.

Colemak-DH base. Unlike the ZMK original this has **no hold-tap keys** — no homerow mods, no layer-tap thumbs. The top row holds dedicated modifiers in the columns where the ZMK homerow mods lived; layer-momentary keys live on the outer two thumb keys on each side.

The outermost pinky column on both halves is unused, so only the inner 5 columns per side are populated. There are 3 layers: `MAIN` (0), `NUM` (1), `SYM` (2).

## Layout

### MAIN (0)

```
┌─────┬─────┬─────┬─────┬─────┬─────┐               ┌─────┬─────┬─────┬─────┬─────┬─────┐
│  ∅  │LCTL │LALT │LSFT │LGUI │  ∅  │               │  ∅  │RGUI │RSFT │RALT │RCTL │  ∅  │
├─────┼─────┼─────┼─────┼─────┼─────┤               ├─────┼─────┼─────┼─────┼─────┼─────┤
│  ∅  │  Q  │  W  │  F  │  P  │  B  │               │  J  │  L  │  U  │  Y  │  '  │  ∅  │
├─────┼─────┼─────┼─────┼─────┼─────┤               ├─────┼─────┼─────┼─────┼─────┼─────┤
│  ∅  │  A  │  R  │  S  │  T  │  G  │               │  M  │  N  │  E  │  I  │  O  │  ∅  │
├─────┼─────┼─────┼─────┼─────┼─────┼─────┐   ┌─────┼─────┼─────┼─────┼─────┼─────┼─────┤
│  ∅  │  Z  │  X  │  C  │  D  │  V  │ ESC │   │ DEL │  K  │  H  │  ,  │  .  │  /  │  ∅  │
└─────┴─────┴─────┴─────┼─────┼─────┼─────┤   ├─────┼─────┼─────┼─────┼─────┴─────┴─────┘
                        │ MO  │ MO  │ TAB │   │ ENT │BSPC │ MO  │ MO  │
                        │ SYM │ NUM │     │   │     │     │ NUM │ SYM │
                        └─────┴─────┴─────┘   └─────┴─────┴─────┘
```

### NUM (1)

Top row and ESC/DEL are transparent so the MAIN-layer modifiers and ESC/DEL remain available while NUM is held. `0` sits on the outer-right thumb to complete the numpad.

```
┌─────┬─────┬─────┬─────┬─────┬─────┐               ┌─────┬─────┬─────┬─────┬─────┬─────┐
│  ∅  │ ↓   │ ↓   │ ↓   │ ↓   │  ∅  │               │  ∅  │ ↓   │ ↓   │ ↓   │ ↓   │  ∅  │
├─────┼─────┼─────┼─────┼─────┼─────┤               ├─────┼─────┼─────┼─────┼─────┼─────┤
│  ∅  │ F10 │ F7  │ F8  │ F9  │  {  │               │  }  │  7  │  8  │  9  │  =  │  ∅  │
├─────┼─────┼─────┼─────┼─────┼─────┤               ├─────┼─────┼─────┼─────┼─────┼─────┤
│  ∅  │ F11 │ F4  │ F5  │ F6  │  (  │               │  )  │  4  │  5  │  6  │  -  │  ∅  │
├─────┼─────┼─────┼─────┼─────┼─────┼─────┐   ┌─────┼─────┼─────┼─────┼─────┼─────┼─────┤
│  ∅  │ F12 │ F1  │ F2  │ F3  │  [  │  ↓  │   │  ↓  │  ]  │  1  │  2  │  3  │  ;  │  ∅  │
└─────┴─────┴─────┴─────┼─────┼─────┼─────┤   ├─────┼─────┼─────┼─────┼─────┴─────┴─────┘
                        │ ↓   │ ↓   │ ↓   │   │ ↓   │ ↓   │ ↓   │  0  │
                        └─────┴─────┴─────┘   └─────┴─────┴─────┘
```

### SYM (2)

```
┌─────┬─────┬─────┬─────┬─────┬─────┐               ┌─────┬─────┬─────┬─────┬─────┬─────┐
│  ∅  │ ↓   │ ↓   │ ↓   │ ↓   │  ∅  │               │  ∅  │ ↓   │ ↓   │ ↓   │ ↓   │  ∅  │
├─────┼─────┼─────┼─────┼─────┼─────┤               ├─────┼─────┼─────┼─────┼─────┼─────┤
│  ∅  │HOME │PGUP │PGDN │ END │  ∅  │               │  \  │  &  │  *  │  `  │  +  │  ∅  │
├─────┼─────┼─────┼─────┼─────┼─────┤               ├─────┼─────┼─────┼─────┼─────┼─────┤
│  ∅  │LEFT │ UP  │DOWN │RGHT │  ∅  │               │  ~  │  $  │  %  │  ^  │  _  │  ∅  │
├─────┼─────┼─────┼─────┼─────┼─────┼─────┐   ┌─────┼─────┼─────┼─────┼─────┼─────┼─────┤
│  ∅  │  ∅  │MUTE │VOLD │VOLU │  ∅  │  ↓  │   │  ↓  │  |  │  !  │  @  │  #  │  :  │  ∅  │
└─────┴─────┴─────┴─────┼─────┼─────┼─────┤   ├─────┼─────┼─────┼─────┼─────┴─────┴─────┘
                        │ ↓   │ ↓   │ ↓   │   │ ↓   │ ↓   │ ↓   │ ↓   │
                        └─────┴─────┴─────┘   └─────┴─────┴─────┘
```

`↓` = transparent (falls through to MAIN). `∅` = unused.

## Building

No local QMK toolchain required — [QMK Configurator](https://config.qmk.fm/) can build the firmware:

1. Open <https://config.qmk.fm/>.
2. Click **Import Keymap** and select `keymap.json` from this repo.
3. Click the green **Compile** button.
4. Download the `.hex` firmware when compilation finishes.
5. Flash each half separately using [QMK Toolbox](https://qmk.fm/toolbox) or `avrdude`. Reset by double-tapping the reset button on the Pro Micro (or bridging RST to GND).

If you prefer a local build, the file is also valid for `qmk compile -kb lily58/rev1 -km rosebear` — copy/symlink this directory into `qmk_firmware/keyboards/lily58/keymaps/rosebear/` first (or use `qmk compile keymap.json` directly).

The keyboard in `keymap.json` is set to `lily58/rev1`. If you have a Lily58 Pro / Glow variant, change that field before compiling.
