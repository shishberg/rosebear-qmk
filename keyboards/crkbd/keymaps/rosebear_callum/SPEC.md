# Rosebear Callum Keymap Behavior Spec

This keymap is a `crkbd/rev1` variant of `keyboards/crkbd/keymaps/rosebear`.
The QMK keymap target is `rosebear_callum`, using the tentative physical layout
in `rosebear-callum.json`, but replacing the original hold-tap behavior with
Callum-style-ish one-shot modifiers.

## Goals

- No hold-tap keys.
- Plain momentary layer keys are allowed.
- Modifier keys on layers 1, 2, and 3 use custom one-shot/held behavior.
- Caps Word is enabled by pressing both shift keys.
- LED controls and LED behavior are copied from the existing `rosebear` keymap.

## Non-Goals

- Do not use `MT(...)` mod-taps.
- Do not use `LT(...)` layer-taps.
- Do not use Achordion for this variant.
- Do not depend on tapping terms for modifier or layer behavior.

## Layers

Use four layers matching `rosebear-callum.json`:

- Layer 0: base Colemak-DH alpha layer.
- Layer 1: navigation, symbols, numbers, and left-hand one-shot modifiers.
- Layer 2: symbols/media and right-hand one-shot modifiers.
- Layer 3: function/modifier layer.

Layer access is by plain momentary layer keys, for example `MO(1)`, `MO(2)`,
and `MO(3)`. Pressing a layer key must not produce a tap keycode.

## Modifier Keys

The modifier keys on layers 1, 2, and 3 are custom Callum-style-ish modifiers:

- Ctrl
- Alt
- Shift
- GUI/Cmd

For macOS-facing naming, GUI may be referred to as Cmd in documentation, but
the firmware keycode/mod bit is QMK GUI.

Layer 1 uses the left-hand modifiers from `rosebear-callum.json`:

- `KC_LCTL`
- `KC_LALT`
- `KC_LSFT`
- `KC_LGUI`

Layer 2 uses the right-hand modifiers from `rosebear-callum.json`:

- `KC_RGUI`
- `KC_RSFT`
- `KC_RALT`
- `KC_RCTL`

Layer 3 contains both left-hand and right-hand modifier groups from
`rosebear-callum.json`. These keys use the same custom behavior as the layer 1
and layer 2 modifiers.

## Modifier State Machine

Each custom modifier key tracks whether any non-modifier key was pressed while
that modifier was held.

On modifier press:

- Register the modifier immediately as a held modifier.
- Mark the modifier as "unused while held."

While a modifier is held:

- If one or more non-modifier keys are pressed, the held modifier applies to
  those keypresses.
- Once any non-modifier key has been pressed while the modifier is held, the
  modifier is no longer eligible to become a one-shot modifier when released.
- Other custom modifier keys do not count as non-modifier keys and do not
  disqualify the first modifier from becoming one-shot.
- Layer-key presses clear modifiers as described below.

On modifier release:

- If no non-modifier key was pressed while the modifier was held, unregister
  the held modifier and queue that modifier as a one-shot modifier.
- If at least one non-modifier key was pressed while the modifier was held,
  unregister the held modifier and do not queue it as one-shot.

When one or more one-shot modifiers are queued:

- The next non-modifier host keypress receives all queued one-shot modifiers.
- After that keypress is processed, all queued one-shot modifiers are cleared.
- Multiple queued one-shot modifiers combine. For example:
  `MO(1)` down, Shift, Ctrl, `MO(1)` up, `S` sends Shift+Ctrl+S.
- Queued one-shot modifiers should not lock on double tap unless explicitly
  enabled later.
- Queued one-shot modifiers expire after 5 seconds if they are not consumed or
  cleared first.
- Do not special-case firmware command keys for one-shot consumption. If an LED
  control key or similar non-modifier command is pressed while one-shot
  modifiers are queued, it may consume the queued modifiers even though no host
  key is sent.

Examples:

- Tap Shift, then tap `S`: sends Shift+S.
- Hold Shift, tap `S`, release Shift, then tap `A`: sends Shift+S, then plain
  `A`.
- Tap Shift, tap Ctrl, then tap `S`: sends Shift+Ctrl+S.
- Hold Shift, tap `S`, tap `A`, release Shift: sends Shift+S and Shift+A, then
  queues no one-shot modifier.

## Layer Keys Clear Modifiers

Pressing any momentary layer key clears modifier state.

This includes:

- Held custom modifiers tracked by this keymap.
- Queued one-shot modifiers tracked by this keymap.
- QMK one-shot modifier state, if any QMK one-shot APIs are used internally.

Layer-key presses must not clear Caps Word.

Layer keys are the only explicit one-shot cancel keys. Do not add Escape,
Backspace, Delete, or modifier-chord cancellation unless changed later.

Examples:

- Tap Shift, press `MO(2)`, release `MO(2)`, then tap `S`: sends plain `S`.
- Hold Shift, press `MO(2)`, tap `S`, release Shift: Shift is cleared by the
  layer-key press, so `S` is not shifted.

## Caps Word

Enable QMK Caps Word.

Pressing both Shift keys enables Caps Word. This should use QMK's
`BOTH_SHIFTS_TURNS_ON_CAPS_WORD` behavior if it works cleanly with the custom
modifier implementation.

Implementation requirements:

- Add `CAPS_WORD_ENABLE = yes` in `rules.mk`.
- Add `#define BOTH_SHIFTS_TURNS_ON_CAPS_WORD` in `config.h`.
- Disable or reconfigure QMK Command if needed, because QMK's default Command
  chord can conflict with the same Left Shift + Right Shift combination.
- Pressing a layer key clears modifiers, but does not clear Caps Word.

Use the default QMK Caps Word word-breaking behavior unless changed later.

## LED Behavior

Copy the LED behavior from `keyboards/crkbd/keymaps/rosebear`:

- Keep the same custom keycodes:
  - `UG_TOG`
  - `UG_BRIU`
  - `UG_BRID`
  - `KEY_TOG`
  - `KEY_BRIU`
  - `KEY_BRID`
- Keep the same underglow toggle and brightness behavior.
- Keep the same key splash toggle and brightness behavior.
- Keep the same brightness levels.
- Keep the same RGB matrix custom `rosebear_small_splash` effect.
- Keep the same split-side LED sync behavior.
- Keep the same keypress splash trigger behavior when key splash is enabled.

LED control keys should be placed in the same physical positions used by the
existing `rosebear` keymap:

- Left outer column, top to bottom: `UG_TOG`, `UG_BRIU`, `UG_BRID`.
- Right outer column, top to bottom: `KEY_TOG`, `KEY_BRIU`, `KEY_BRID`.

LED key placement:

- Put the concrete LED keycodes on layers 1, 2, and 3.
- Do not use `KC_TRNS` for these LED positions on layers 2 and 3, because the
  controls should be directly available from each non-base layer.

## Resolved Decisions

- LED controls are present directly on layers 1, 2, and 3.
- LED controls are not special-cased for one-shot consumption.
- Layer keys are the only explicit one-shot cancel keys.
- Queued one-shot modifiers expire after 5 seconds.
- Caps Word uses QMK's default continuation and word-breaking behavior.
