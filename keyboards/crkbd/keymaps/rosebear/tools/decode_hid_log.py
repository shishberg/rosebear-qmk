#!/usr/bin/env python3
"""Decode Rosebear Raw HID CSV logs into readable key events."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


QMK_ROOT = Path(__file__).resolve().parents[5]
KEYCODES_H = QMK_ROOT / "quantum" / "keycodes.h"

LAYER_NAMES = {
    0: "BASE",
    1: "NUM",
    2: "SYM",
    3: "HOLD",
}

MOD_NAMES = [
    (0x01, "LCTL"),
    (0x02, "LSFT"),
    (0x04, "LALT"),
    (0x08, "LGUI"),
    (0x10, "RCTL"),
    (0x20, "RSFT"),
    (0x40, "RALT"),
    (0x80, "RGUI"),
]

POSITION_NAMES = {
    (0, 0): "L top pinky", (0, 1): "L top ring", (0, 2): "L top middle",
    (0, 3): "L top index", (0, 4): "L top inner", (0, 5): "L top thumbward",
    (1, 0): "L home pinky", (1, 1): "L home ring", (1, 2): "L home middle",
    (1, 3): "L home index", (1, 4): "L home inner", (1, 5): "L home thumbward",
    (2, 0): "L bottom pinky", (2, 1): "L bottom ring", (2, 2): "L bottom middle",
    (2, 3): "L bottom index", (2, 4): "L bottom inner", (2, 5): "L bottom thumbward",
    (3, 3): "L thumb outer", (3, 4): "L thumb middle", (3, 5): "L thumb inner",
    (4, 0): "R top pinky", (4, 1): "R top ring", (4, 2): "R top middle",
    (4, 3): "R top index", (4, 4): "R top inner", (4, 5): "R top thumbward",
    (5, 0): "R home pinky", (5, 1): "R home ring", (5, 2): "R home middle",
    (5, 3): "R home index", (5, 4): "R home inner", (5, 5): "R home thumbward",
    (6, 0): "R bottom pinky", (6, 1): "R bottom ring", (6, 2): "R bottom middle",
    (6, 3): "R bottom index", (6, 4): "R bottom inner", (6, 5): "R bottom thumbward",
    (7, 0): "R thumb outer", (7, 1): "R thumb middle", (7, 2): "R thumb inner",
}


def load_keycode_names() -> dict[int, str]:
    names_by_value: dict[int, str] = {}
    values_by_name: dict[str, int] = {}
    assignment = re.compile(r"^\s*(KC_[A-Z0-9_]+|QK_[A-Z0-9_]+)\s*=\s*([^,]+),")

    for line in KEYCODES_H.read_text().splitlines():
        match = assignment.match(line)
        if not match:
            continue

        name, value_expr = match.groups()
        value_expr = value_expr.strip()
        value: int | None = None

        if value_expr.startswith("0x"):
            value = int(value_expr, 16)
        elif value_expr.isdigit():
            value = int(value_expr)
        elif value_expr in values_by_name:
            value = values_by_name[value_expr]

        if value is None:
            continue

        values_by_name[name] = value
        names_by_value.setdefault(value, name)

    preferred = {
        0x0000: "KC_NO",
        0x0001: "KC_TRNS",
        0x0028: "KC_ENT",
        0x0029: "KC_ESC",
        0x002A: "KC_BSPC",
        0x002B: "KC_TAB",
        0x002C: "KC_SPC",
        0x002D: "KC_MINS",
        0x002E: "KC_EQL",
        0x002F: "KC_LBRC",
        0x0030: "KC_RBRC",
        0x0031: "KC_BSLS",
        0x0033: "KC_SCLN",
        0x0034: "KC_QUOT",
        0x0035: "KC_GRV",
        0x0036: "KC_COMM",
        0x0037: "KC_DOT",
        0x0038: "KC_SLSH",
    }
    names_by_value.update(preferred)
    return names_by_value


def decode_mods(mods: int) -> str:
    found = [name for bit, name in MOD_NAMES if mods == bit]
    if found:
        return found[0]

    parts = [name for bit, name in MOD_NAMES if mods & bit == bit]
    return "|".join(parts) if parts else f"0x{mods:02x}"


def decode_modtap_mods(mods: int) -> str:
    side = 0x10 if mods & 0x10 else 0
    base = mods & 0x0F
    names = []
    for bit, name in [(0x01, "CTL"), (0x02, "SFT"), (0x04, "ALT"), (0x08, "GUI")]:
        if base & bit:
            names.append(("R" if side else "L") + name)
    return "|".join(names) if names else f"0x{mods:02x}"


def decode_keycode(kc: int, names: dict[int, str]) -> str:
    if 0x2000 <= kc <= 0x3FFF:
        mods = (kc >> 8) & 0x1F
        tap = kc & 0xFF
        return f"MT(MOD_{decode_modtap_mods(mods)}, {decode_keycode(tap, names)})"

    if 0x4000 <= kc <= 0x4FFF:
        layer = (kc >> 8) & 0x0F
        tap = kc & 0xFF
        layer_name = LAYER_NAMES.get(layer, str(layer))
        return f"LT({layer_name}, {decode_keycode(tap, names)})"

    return names.get(kc, f"0x{kc:04x}")


def decode_row(row: dict[str, str], names: dict[int, str], first_time: int, active: dict[tuple[int, int, int], int]) -> dict[str, int | str]:
    seq = int(row["seq"])
    time_ms = int(row["time_ms"])
    event_type = row.get("event_type", "key") or "key"

    if event_type == "key":
        keycode = int(row["keycode"], 16)
        r = int(row["row"])
        c = int(row["col"])
        pressed = row["pressed"] == "1"
        active_key = (r, c, keycode)
        duration_ms = ""

        if pressed:
            active[active_key] = time_ms
        else:
            down_time = active.pop(active_key, None)
            if down_time is not None:
                duration_ms = str(time_ms - down_time)

        return {
            "seq": seq,
            "t_ms": time_ms - first_time,
            "event_type": "key",
            "event": "down" if pressed else "up",
            "duration_ms": duration_ms,
            "key": decode_keycode(keycode, names),
            "pos": POSITION_NAMES.get((r, c), f"r{r}c{c}"),
            "row": r,
            "col": c,
            "layer": LAYER_NAMES.get(int(row["layer"]), row["layer"]),
            "mods": row["mods"],
            "changed": "",
            "active": "",
            "all_mods": row.get("all_mods", ""),
        }

    if event_type == "mod":
        changed = int(row["changed"], 16)
        return {
            "seq": seq,
            "t_ms": time_ms - first_time,
            "event_type": "mod",
            "event": "down" if row["active"] == "1" else "up",
            "duration_ms": "",
            "key": decode_mods(changed),
            "pos": "",
            "row": "",
            "col": "",
            "layer": "",
            "mods": row["mods"],
            "changed": row["changed"],
            "active": row["active"],
            "all_mods": row.get("all_mods", ""),
        }

    if event_type == "layer":
        layer = int(row["changed"])
        return {
            "seq": seq,
            "t_ms": time_ms - first_time,
            "event_type": "layer",
            "event": "on" if row["active"] == "1" else "off",
            "duration_ms": "",
            "key": LAYER_NAMES.get(layer, str(layer)),
            "pos": "",
            "row": "",
            "col": "",
            "layer": LAYER_NAMES.get(layer, str(layer)),
            "mods": row["mods"],
            "changed": row["changed"],
            "active": row["active"],
            "all_mods": row.get("all_mods", ""),
        }

    raise ValueError(f"unknown event_type {event_type!r}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="CSV from hid_log.py")
    parser.add_argument("--out", type=Path, help="Write decoded CSV instead of text")
    args = parser.parse_args()

    names = load_keycode_names()
    rows = list(csv.DictReader(args.input.open()))
    active: dict[tuple[int, int, int], int] = {}

    decoded = []
    first_time = int(rows[0]["time_ms"]) if rows else 0

    for row in rows:
        decoded.append(decode_row(row, names, first_time, active))

    if args.out:
        with args.out.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=decoded[0].keys() if decoded else [])
            writer.writeheader()
            writer.writerows(decoded)
    else:
        for row in decoded:
            duration = f" {row['duration_ms']}ms" if row["duration_ms"] != "" else ""
            print(
                f"{row['seq']:>4} {row['t_ms']:>7}ms {row['event_type']:<5} "
                f"{row['event']:<4}{duration:<7} "
                f"{row['key']:<24} {row['pos']} layer={row['layer']} mods={row['mods']}"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
