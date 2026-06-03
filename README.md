# Rosebear QMK

External QMK userspace for Rosebear keymaps ported from
[Rosebear ZMK](https://github.com/shishberg/rosebear-zmk).

## Keymaps

- [`keyboards/crkbd/keymaps/rosebear`](./keyboards/crkbd/keymaps/rosebear/) - Corne (`crkbd/rev1`) Colemak-DH layout with homerow mods, layer-tap thumbs, RGB matrix handling, and Raw HID logging tools for hold-tap analysis.
- [`keyboards/crkbd/keymaps/rosebear_callum`](./keyboards/crkbd/keymaps/rosebear_callum/) - Corne (`crkbd/rev1`) Colemak-DH layout variant with Callum-style-ish one-shot modifiers, no hold-tap keys, Caps Word, and the same RGB matrix handling.
- [`keyboards/lily58/keymaps/rosebear`](./keyboards/lily58/keymaps/rosebear/) - Lily58 (`lily58/rev1`) Colemak-DH layout that uses dedicated modifier keys instead of mod-taps.

## Local Setup

Point QMK at this userspace:

```sh
qmk config user.overlay_dir="$(pwd)"
```

Build a target:

```sh
qmk compile -kb crkbd/rev1 -km rosebear
qmk compile -kb crkbd/rev1 -km rosebear_callum
qmk compile -kb lily58/rev1 -km rosebear
```

Or build every target listed in [`qmk.json`](./qmk.json):

```sh
qmk userspace-compile
```
