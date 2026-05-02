# Rosebear QMK

QMK keymaps ported from the [Rosebear ZMK](https://github.com/shishberg/rosebear-zmk) layout (Colemak-DH).

Each board has its own subdirectory with a self-contained `keymap.json` and README:

- [`lily58/`](./lily58/) — Lily58. Ported variant with **no hold-tap** (dedicated modifiers on the top row, layer-momentary on the outer thumbs). 3 layers.
- [`crkbd/`](./crkbd/) — Corne (`crkbd/rev1`). Direct translation of the ZMK keymap, with homerow mods and layer-tap thumbs preserved. 7 layers.

Both keymaps are valid QMK Configurator `keymap.json` files — open <https://config.qmk.fm/>, **Import Keymap**, and compile.
