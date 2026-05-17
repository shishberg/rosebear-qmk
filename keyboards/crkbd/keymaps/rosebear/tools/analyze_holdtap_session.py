#!/usr/bin/env python3
"""Classify Monkeytype insert events that exercise Rosebear hold-tap keys."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any


HOLD_TAP_TAPS = {
    "a": "MT(MOD_LCTL, KC_A)",
    "r": "MT(MOD_LALT, KC_R)",
    "s": "MT(MOD_LSFT, KC_S)",
    "t": "MT(MOD_LGUI, KC_T)",
    "n": "MT(MOD_RGUI, KC_N)",
    "e": "MT(MOD_RSFT, KC_E)",
    "i": "MT(MOD_RALT, KC_I)",
    "o": "MT(MOD_RCTL, KC_O)",
    " ": "LT(NUM, KC_SPC)",
}

SHIFT_HOLDERS = [
    "MT(MOD_LSFT, KC_S)",
    "MT(MOD_RSFT, KC_E)",
]

# Characters reached on NUM/SYM layers. `missed_hold` is the base-layer
# character likely produced if the layer-tap is tapped instead of held while
# the partner key is pressed.
LAYER_HOLD_OUTPUTS = {
    # NUM layer.
    "}": ("NUM", "KC_RCBR", "j"),
    "7": ("NUM", "KC_7", "l"),
    "8": ("NUM", "KC_8", "u"),
    "9": ("NUM", "KC_9", "y"),
    "=": ("NUM", "KC_EQL", "'"),
    ")": ("NUM", "KC_RPRN", "m"),
    "4": ("NUM", "KC_4", "n"),
    "5": ("NUM", "KC_5", "e"),
    "6": ("NUM", "KC_6", "i"),
    "-": ("NUM", "KC_MINS", "o"),
    "]": ("NUM", "KC_RBRC", "k"),
    "1": ("NUM", "KC_1", "h"),
    "2": ("NUM", "KC_2", ","),
    "3": ("NUM", "KC_3", "."),
    ";": ("NUM", "KC_SCLN", "/"),
    # 0 can be produced by either right thumb key. If the layer hold is missed,
    # the tap result is editing, not a visible character, so there is no
    # reliable single visible wrong character to compare against.
    "0": ("NUM", "KC_0", ""),
    "{": ("NUM", "KC_LCBR", "b"),
    "(": ("NUM", "KC_LPRN", "g"),
    "[": ("NUM", "KC_LBRC", "v"),
    # SYM layer.
    "\\": ("SYM", "KC_BSLS", "j"),
    "&": ("SYM", "KC_AMPR", "l"),
    "*": ("SYM", "KC_ASTR", "u"),
    "`": ("SYM", "KC_GRV", "y"),
    "+": ("SYM", "KC_PLUS", "'"),
    "~": ("SYM", "KC_TILD", "m"),
    "$": ("SYM", "KC_DLR", "n"),
    "%": ("SYM", "KC_PERC", "e"),
    "^": ("SYM", "KC_CIRC", "i"),
    "_": ("SYM", "KC_UNDS", "o"),
    "|": ("SYM", "KC_PIPE", "k"),
    "!": ("SYM", "KC_EXLM", "h"),
    "@": ("SYM", "KC_AT", ","),
    "#": ("SYM", "KC_HASH", "."),
    ":": ("SYM", "KC_COLN", "/"),
}

LAYER_BITS = {
    "BASE": 0,
    "NUM": 1,
    "SYM": 2,
    "HOLD": 3,
}

MOD_BITS = {
    "LCTL": 0x01,
    "LSFT": 0x02,
    "LALT": 0x04,
    "LGUI": 0x08,
    "RCTL": 0x10,
    "RSFT": 0x20,
    "RALT": 0x40,
    "RGUI": 0x80,
}

MODTAP_HOLDERS = {
    MOD_BITS["LCTL"]: "MT(MOD_LCTL, KC_A)",
    MOD_BITS["LALT"]: "MT(MOD_LALT, KC_R)",
    MOD_BITS["LSFT"]: "MT(MOD_LSFT, KC_S)",
    MOD_BITS["LGUI"]: "MT(MOD_LGUI, KC_T)",
    MOD_BITS["RGUI"]: "MT(MOD_RGUI, KC_N)",
    MOD_BITS["RSFT"]: "MT(MOD_RSFT, KC_E)",
    MOD_BITS["RALT"]: "MT(MOD_RALT, KC_I)",
    MOD_BITS["RCTL"]: "MT(MOD_RCTL, KC_O)",
}

TAP_MOD_BITS = {
    "a": MOD_BITS["LCTL"],
    "r": MOD_BITS["LALT"],
    "s": MOD_BITS["LSFT"],
    "t": MOD_BITS["LGUI"],
    "n": MOD_BITS["RGUI"],
    "e": MOD_BITS["RSFT"],
    "i": MOD_BITS["RALT"],
    "o": MOD_BITS["RCTL"],
}

BROWSER_MOD_TAPS = {
    "ControlLeft": ("a", "MT(MOD_LCTL, KC_A)"),
    "AltLeft": ("r", "MT(MOD_LALT, KC_R)"),
    "MetaLeft": ("t", "MT(MOD_LGUI, KC_T)"),
    "MetaRight": ("n", "MT(MOD_RGUI, KC_N)"),
    "AltRight": ("i", "MT(MOD_RALT, KC_I)"),
    "ControlRight": ("o", "MT(MOD_RCTL, KC_O)"),
}

SHIFT_OUTPUTS = {
    **{chr(c).upper(): chr(c) for c in range(ord("a"), ord("z") + 1)},
    '"': "'",
    "?": "/",
    "<": ",",
    ">": ".",
}


class Domain(StrEnum):
    MODIFIER = "modifier"
    LAYER = "layer"


class TypedKind(StrEnum):
    PRINTABLE = "printable_character"
    NONE = "no_typed_character"


@dataclass(frozen=True)
class HoldTapObservation:
    domain: Domain
    expected_hold: bool
    resolved_hold: bool | None
    target: str
    actual: str
    mechanism: str
    typed_kind: TypedKind
    correct: bool


@dataclass(frozen=True)
class QmkState:
    mods: int = 0
    layers: int = 0


def classify_resolution(obs: HoldTapObservation) -> str:
    if obs.resolved_hold is None:
        if obs.correct:
            return "correct_unobserved"
        return "other_wrong"

    if obs.expected_hold and obs.resolved_hold:
        return "true_positive" if obs.correct else "true_positive_other_wrong"

    if obs.expected_hold and not obs.resolved_hold:
        return "false_negative"

    if not obs.expected_hold and obs.resolved_hold:
        return "false_positive"

    return "true_negative" if obs.correct else "true_negative_other_wrong"


def legacy_classification(resolution: str, obs: HoldTapObservation) -> str:
    if resolution in {"true_positive", "true_negative"}:
        return "correct"
    if resolution == "no_holder_observed":
        return "other_wrong"
    if resolution == "false_positive":
        return "hold_tap_wrong"
    if resolution == "false_negative":
        return "hold_tap_wrong"
    if resolution == "correct_unobserved":
        return "correct"
    if not obs.correct and obs.domain == Domain.MODIFIER and not obs.expected_hold and obs.actual == obs.target.upper():
        return "shifted_tap"
    return "other_wrong"


def expected_char(event: dict[str, Any]) -> str:
    target = event["targetChar"]
    if target != "":
        return target

    # Monkeytype uses an empty targetChar for word-submitting spaces.
    if event["data"] == " " or event["inputBefore"] == event["targetWord"]:
        return " "

    return ""


def clean_prefix(event: dict[str, Any]) -> bool:
    return event["targetWord"].startswith(event["inputBefore"])


def target_char_from_input(words: list[str], word_index: int, input_current: str) -> str:
    if word_index >= len(words):
        return ""

    target_word = words[word_index]
    if len(input_current) < len(target_word):
        return target_word[len(input_current)]
    if input_current == target_word:
        return " "
    return ""


def active_browser_mods(events: list[dict[str, Any]]) -> dict[int, set[str]]:
    active: set[str] = set()
    by_index: dict[int, set[str]] = {}

    for index, event in enumerate(events):
        if event["type"] == "keyup" and event.get("key") in {"Shift", "Control", "Alt", "Meta"}:
            code = event.get("code", "")
            active.discard(code)

        by_index[index] = set(active)

        if event["type"] == "keydown" and event.get("key") in {"Shift", "Control", "Alt", "Meta"}:
            code = event.get("code", "")
            if code:
                active.add(code)

    return by_index


def browser_shift_active(active_mods: set[str]) -> bool:
    return bool({"ShiftLeft", "ShiftRight"} & active_mods)


def qmk_layer_active(qmk_state: QmkState | None, layer_name: str) -> bool | None:
    if qmk_state is None:
        return None
    return bool(qmk_state.layers & (1 << LAYER_BITS[layer_name]))


def qmk_mod_active(qmk_state: QmkState | None, mask: int) -> bool | None:
    if qmk_state is None:
        return None
    return bool(qmk_state.mods & mask)


def resolved_shift_active(active_mods: set[str], qmk_state: QmkState | None) -> bool | None:
    if browser_shift_active(active_mods):
        return True
    if qmk_state is not None:
        return bool(qmk_state.mods & (MOD_BITS["LSFT"] | MOD_BITS["RSFT"]))
    return False


def parse_int(value: str, default: int = 0) -> int:
    if value == "":
        return default
    return int(value, 0)


def qmk_states_by_monkey_event(
    monkey_events: list[dict[str, Any]],
    hid_rows: list[dict[str, str]],
) -> dict[int, QmkState]:
    timed_events = [
        (int(event["wallTime"]), index)
        for index, event in enumerate(monkey_events)
        if "wallTime" in event
    ]
    if not timed_events:
        return {}

    hid_events = sorted(
        (
            (int(row["host_time_ns"]) // 1_000_000, row)
            for row in hid_rows
            if row.get("host_time_ns")
        ),
        key=lambda item: item[0],
    )
    states: dict[int, QmkState] = {}
    mods = 0
    layers = 0
    hid_index = 0

    for wall_time, event_index in timed_events:
        while hid_index < len(hid_events) and hid_events[hid_index][0] <= wall_time:
            row = hid_events[hid_index][1]
            event_type = row.get("event_type", "key") or "key"

            if row.get("all_mods"):
                mods = parse_int(row["all_mods"])
            elif row.get("mods"):
                mods = parse_int(row["mods"])

            if row.get("layer_state"):
                layers = parse_int(row["layer_state"])

            if event_type == "mod" and row.get("changed"):
                changed = parse_int(row["changed"])
                if row.get("active") == "1":
                    mods |= changed
                else:
                    mods &= ~changed

            if event_type == "layer" and row.get("changed"):
                changed_layer = int(row["changed"])
                mask = 1 << changed_layer
                if row.get("active") == "1":
                    layers |= mask
                else:
                    layers &= ~mask

            hid_index += 1

        states[event_index] = QmkState(mods=mods, layers=layers)

    return states


def hid_keycode_name(row: dict[str, str]) -> str:
    return row.get("decoded_key", "")


def decode_hid_key_names(hid_rows: list[dict[str, str]]) -> None:
    try:
        from decode_hid_log import decode_keycode, load_keycode_names
    except ImportError:
        return

    names = load_keycode_names()
    for row in hid_rows:
        if (row.get("event_type", "key") or "key") != "key" or row.get("keycode", "") == "":
            row["decoded_key"] = ""
            continue
        row["decoded_key"] = decode_keycode(int(row["keycode"], 16), names)


def qmk_holder_presence_by_monkey_event(
    monkey_events: list[dict[str, Any]],
    hid_rows: list[dict[str, str]],
    window_ms: int = 200,
) -> dict[int, set[str]]:
    timed_events = [
        (int(event["wallTime"]), index)
        for index, event in enumerate(monkey_events)
        if "wallTime" in event
    ]
    if not timed_events:
        return {}

    key_rows = sorted(
        (
            (int(row["host_time_ns"]) // 1_000_000, hid_keycode_name(row), row)
            for row in hid_rows
            if row.get("host_time_ns") and (row.get("event_type", "key") or "key") == "key"
        ),
        key=lambda item: item[0],
    )
    presence: dict[int, set[str]] = {}
    start = 0

    for wall_time, event_index in timed_events:
        while start < len(key_rows) and key_rows[start][0] < wall_time - window_ms:
            start += 1

        found: set[str] = set()
        for event_time, key_name, row in key_rows[start:]:
            if event_time > wall_time + 20:
                break
            if row.get("pressed") != "1":
                continue
            if key_name.startswith("MT("):
                found.add(key_name)
            elif key_name.startswith("LT(NUM"):
                found.add("NUM")
            elif key_name.startswith("LT(SYM"):
                found.add("SYM")
        presence[event_index] = found

    return presence


def qmk_timing_by_monkey_event(
    monkey_events: list[dict[str, Any]],
    hid_rows: list[dict[str, str]],
    window_before_ms: int = 250,
    window_after_ms: int = 20,
) -> dict[int, dict[str, str | int | bool]]:
    timed_events = [
        (int(event["wallTime"]), index)
        for index, event in enumerate(monkey_events)
        if "wallTime" in event
    ]
    if not timed_events:
        return {}

    rows = sorted(
        [row for row in hid_rows if row.get("host_time_ns")],
        key=lambda row: int(row["host_time_ns"]),
    )
    for row in rows:
        row["_host_ms"] = str(int(row["host_time_ns"]) // 1_000_000)

    episodes: list[dict[str, str | int | bool]] = []
    active: dict[tuple[str, str, str], tuple[int, dict[str, str]]] = {}

    for index, row in enumerate(rows):
        if (row.get("event_type", "key") or "key") != "key":
            continue
        key_name = hid_keycode_name(row)
        if not key_name.startswith(("LT(", "MT(")):
            continue

        identity = (row.get("row", ""), row.get("col", ""), row.get("keycode", ""))
        if row.get("pressed") == "1":
            active[identity] = (index, row)
            continue

        start = active.pop(identity, None)
        if start is None:
            continue

        start_index, start_row = start
        start_ms = int(start_row["_host_ms"])
        end_ms = int(row["_host_ms"])
        partner_delay = ""
        layer_on_delay = ""

        for inner in rows[start_index + 1 : index + 1]:
            event_type = inner.get("event_type", "key") or "key"
            inner_ms = int(inner["_host_ms"])

            if layer_on_delay == "" and event_type == "layer" and inner.get("active") == "1":
                layer_on_delay = str(inner_ms - start_ms)

            if (
                partner_delay == ""
                and event_type == "key"
                and inner.get("pressed") == "1"
                and not hid_keycode_name(inner).startswith(("LT(", "MT("))
            ):
                partner_delay = str(inner_ms - start_ms)

        episodes.append({
            "holder_key": key_name,
            "holder_start_wall_ms": start_ms,
            "holder_end_wall_ms": end_ms,
            "holder_duration_ms": end_ms - start_ms,
            "holder_partner_delay_ms": partner_delay,
            "holder_layer_on_delay_ms": layer_on_delay,
            "holder_layer_activated": layer_on_delay != "",
        })

    timing: dict[int, dict[str, str | int | bool]] = {}
    for wall_time, event_index in timed_events:
        candidates: list[dict[str, str | int | bool]] = []
        for episode in episodes:
            start_ms = int(episode["holder_start_wall_ms"])
            end_ms = int(episode["holder_end_wall_ms"])
            if start_ms > wall_time + window_after_ms:
                break
            if start_ms <= wall_time + window_after_ms and end_ms >= wall_time - window_before_ms:
                candidates.append(episode)

        if candidates:
            timing[event_index] = min(
                candidates,
                key=lambda episode: (
                    0
                    if int(episode["holder_start_wall_ms"]) <= wall_time <= int(episode["holder_end_wall_ms"])
                    else min(
                        abs(int(episode["holder_start_wall_ms"]) - wall_time),
                        abs(int(episode["holder_end_wall_ms"]) - wall_time),
                    )
                ),
            )

    return timing


def holder_observed(
    obs: HoldTapObservation,
    holders: set[str],
) -> bool:
    if not obs.expected_hold:
        return True

    if obs.domain == Domain.LAYER:
        if obs.mechanism.startswith("LT(NUM"):
            return "NUM" in holders
        if obs.mechanism.startswith("LT(SYM"):
            return "SYM" in holders

    if obs.domain == Domain.MODIFIER:
        if obs.target in SHIFT_OUTPUTS:
            return any(holder in holders for holder in SHIFT_HOLDERS)
        for holder in MODTAP_HOLDERS.values():
            if holder == obs.mechanism:
                return holder in holders

    return True


def classify(
    event: dict[str, Any],
    active_mods: set[str] | None = None,
    qmk_state: QmkState | None = None,
    holders: set[str] | None = None,
) -> list[dict[str, str | bool]]:
    target = expected_char(event)
    actual = event["data"]
    correct = bool(event["correct"])
    clean = clean_prefix(event)
    rows: list[dict[str, str | bool]] = []
    active_mods = active_mods or set()
    holders = holders or set()

    if target in HOLD_TAP_TAPS:
        tap_target = target.lower() if target != " " else " "
        resolved_hold = None
        if tap_target in TAP_MOD_BITS:
            resolved_hold = qmk_mod_active(qmk_state, TAP_MOD_BITS[tap_target])
        elif tap_target == " ":
            resolved_hold = qmk_layer_active(qmk_state, "NUM")
            if correct:
                resolved_hold = False
        if tap_target in {"s", "e"} and browser_shift_active(active_mods):
            resolved_hold = True
        elif tap_target in {"s", "e"} and correct:
            resolved_hold = False
        elif resolved_hold is None and tap_target in {"s", "e"}:
            resolved_hold = browser_shift_active(active_mods)
        observation = HoldTapObservation(
            domain=Domain.LAYER if tap_target == " " else Domain.MODIFIER,
            expected_hold=False,
            resolved_hold=resolved_hold,
            target=target,
            actual=actual,
            mechanism=HOLD_TAP_TAPS[tap_target],
            typed_kind=TypedKind.PRINTABLE,
            correct=correct,
        )
        resolution = classify_resolution(observation)
        if resolution == "false_negative" and not holder_observed(observation, holders):
            resolution = "no_holder_observed"

        rows.append({
            "dependency": "tap",
            "domain": observation.domain.value,
            "target": target,
            "actual": actual,
            "mechanism": HOLD_TAP_TAPS[tap_target],
            "resolution": resolution,
            "classification": legacy_classification(resolution, observation),
            "typed_kind": observation.typed_kind.value,
            "resolved_source": "qmk" if qmk_state is not None else "browser_or_inferred",
            "clean_prefix": clean,
        })

    if target in SHIFT_OUTPUTS:
        resolved_hold = resolved_shift_active(active_mods, qmk_state)
        observation = HoldTapObservation(
            domain=Domain.MODIFIER,
            expected_hold=True,
            resolved_hold=resolved_hold,
            target=target,
            actual=actual,
            mechanism=" or ".join(SHIFT_HOLDERS),
            typed_kind=TypedKind.PRINTABLE,
            correct=correct,
        )
        resolution = classify_resolution(observation)
        if resolution == "false_negative" and not holder_observed(observation, holders):
            resolution = "no_holder_observed"
        rows.append({
            "dependency": "hold",
            "domain": observation.domain.value,
            "target": target,
            "actual": actual,
            "mechanism": " or ".join(SHIFT_HOLDERS),
            "resolution": resolution,
            "classification": legacy_classification(resolution, observation),
            "typed_kind": observation.typed_kind.value,
            "resolved_source": "qmk" if qmk_state is not None else "browser_or_inferred",
            "clean_prefix": clean,
        })

    if target in LAYER_HOLD_OUTPUTS:
        layer, key, missed_hold = LAYER_HOLD_OUTPUTS[target]
        resolved_hold = qmk_layer_active(qmk_state, layer)
        if correct:
            resolved_hold = True
        observation = HoldTapObservation(
            domain=Domain.LAYER,
            expected_hold=True,
            resolved_hold=resolved_hold,
            target=target,
            actual=actual,
            mechanism=f"LT({layer}, ...) + {key}",
            typed_kind=TypedKind.PRINTABLE,
            correct=correct,
        )
        resolution = classify_resolution(observation)
        if resolution == "other_wrong" and missed_hold != "" and actual == missed_hold:
            resolution = "false_negative"
        if resolution == "false_negative" and not holder_observed(observation, holders):
            resolution = "no_holder_observed"
        rows.append({
            "dependency": "hold",
            "domain": observation.domain.value,
            "target": target,
            "actual": actual,
            "mechanism": f"LT({layer}, ...) + {key}",
            "resolution": resolution,
            "classification": legacy_classification(resolution, observation),
            "typed_kind": observation.typed_kind.value,
            "resolved_source": "qmk" if qmk_state is not None else "inferred",
            "clean_prefix": clean,
        })

    return rows


def classify_no_typed_modifier_event(
    event: dict[str, Any],
    words: list[str],
) -> dict[str, str | bool | int] | None:
    if event["type"] != "keydown" or event.get("repeat") or event.get("code") not in BROWSER_MOD_TAPS:
        return None

    tap_target, mechanism = BROWSER_MOD_TAPS[event["code"]]
    target = target_char_from_input(words, event["activeWordIndex"], event["inputCurrent"])
    if target != tap_target:
        return None

    obs = HoldTapObservation(
        domain=Domain.MODIFIER,
        expected_hold=False,
        resolved_hold=True,
        target=target,
        actual="",
        mechanism=mechanism,
        typed_kind=TypedKind.NONE,
        correct=False,
    )
    resolution = classify_resolution(obs)

    return {
        "t": event["t"],
        "wallTime": event.get("wallTime", ""),
        "dependency": "tap",
        "domain": obs.domain.value,
        "target": obs.target,
        "actual": obs.actual,
        "typed_kind": obs.typed_kind.value,
        "resolved_source": "browser",
        "resolution": resolution,
        "classification": legacy_classification(resolution, obs),
        "clean_prefix": True,
        "mechanism": mechanism,
        "wordIndex": event["activeWordIndex"],
        "charIndex": len(event["inputCurrent"]),
        "inputBefore": event["inputCurrent"],
        "inputAfter": event["inputCurrent"],
        "targetWord": words[event["activeWordIndex"]] if event["activeWordIndex"] < len(words) else "",
    }


def print_counts(rows: list[dict[str, Any]]) -> None:
    for clean_only in [False, True]:
        subset = [row for row in rows if row["clean_prefix"] or not clean_only]
        label = "clean-prefix only" if clean_only else "all matching events"
        print(f"\n{label}")
        print("-" * len(label))

        by_dep = Counter(row["dependency"] for row in subset)
        by_domain = Counter(row["domain"] for row in subset)
        by_resolution = Counter(row["resolution"] for row in subset)
        by_class = Counter(row["classification"] for row in subset)
        print("dependency:", dict(by_dep))
        print("domain:", dict(by_domain))
        print("resolution:", dict(by_resolution))
        print("classification:", dict(by_class))

        grouped: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
        for row in subset:
            grouped[(row["dependency"], row["target"])][row["classification"]] += 1

        print("\nby target:")
        for (dependency, target), counts in sorted(grouped.items()):
            print(f"  {dependency:4} {target!r:>4}: {dict(counts)}")


def print_examples(rows: list[dict[str, Any]], limit: int) -> None:
    likely = [
        row
        for row in rows
        if row["classification"] in {"hold_tap_wrong", "shifted_tap"}
        and row["clean_prefix"]
    ]
    print(f"\nlikely hold-tap-resolution examples, first {min(limit, len(likely))}")
    print("------------------------------------------------")
    for row in likely[:limit]:
        print(
            f"{row['dependency']:4} target={row['target']!r:<4} actual={row['actual']!r:<4} "
            f"class={row['classification']:<14} resolution={row['resolution']:<14} "
            f"word={row['wordIndex']} char={row['charIndex']} "
            f"before={row['inputBefore']!r} targetWord={row['targetWord']!r} "
            f"via={row['mechanism']}"
        )

    wrong = [row for row in rows if row["classification"] != "correct"]
    print(f"\nwrong examples, first {min(limit, len(wrong))}")
    print("--------------------------------")
    for row in wrong[:limit]:
        print(
            f"{row['dependency']:4} target={row['target']!r:<4} actual={row['actual']!r:<4} "
            f"class={row['classification']:<14} resolution={row['resolution']:<14} "
            f"clean={row['clean_prefix']} "
            f"word={row['wordIndex']} char={row['charIndex']} "
            f"before={row['inputBefore']!r} targetWord={row['targetWord']!r} "
            f"via={row['mechanism']}"
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("monkeytype_json", type=Path)
    parser.add_argument("--hid-log", type=Path, help="CSV from hid_log.py with QMK resolved state")
    parser.add_argument("--out", type=Path, help="Write classified events as CSV")
    parser.add_argument("--examples", type=int, default=30)
    args = parser.parse_args()

    session = json.loads(args.monkeytype_json.read_text())
    events = session["events"]
    start = next((event for event in events if event["type"] == "start"), None)
    words = start["words"] if start is not None else []
    active_mods = active_browser_mods(events)
    qmk_states: dict[int, QmkState] = {}
    qmk_holders: dict[int, set[str]] = {}
    qmk_timings: dict[int, dict[str, str | int | bool]] = {}
    if args.hid_log is not None:
        with args.hid_log.open(newline="") as f:
            hid_rows = list(csv.DictReader(f))
        decode_hid_key_names(hid_rows)
        qmk_states = qmk_states_by_monkey_event(events, hid_rows)
        qmk_holders = qmk_holder_presence_by_monkey_event(events, hid_rows)
        qmk_timings = qmk_timing_by_monkey_event(events, hid_rows)
    inserts = [(index, event) for index, event in enumerate(events) if event["type"] == "insert"]

    rows: list[dict[str, Any]] = []
    for event in events:
        row = classify_no_typed_modifier_event(event, words)
        if row is not None:
            rows.append(row)

    for index, event in inserts:
        for row in classify(
            event,
            active_mods[index],
            qmk_states.get(index),
            qmk_holders.get(index),
        ):
            rows.append({
                **row,
                **qmk_timings.get(index, {}),
                "t": event["t"],
                "wallTime": event.get("wallTime", ""),
                "wordIndex": event["wordIndex"],
                "charIndex": event["charIndex"],
                "inputBefore": event["inputBefore"],
                "inputAfter": event["inputAfter"],
                "targetWord": event["targetWord"],
            })
    rows.sort(key=lambda row: (row["t"], row["typed_kind"] != TypedKind.NONE.value))

    print(f"session: {session.get('id', args.monkeytype_json.name)}")
    print(f"inserts: {len(inserts)}")
    if args.hid_log is not None:
        print(f"qmk-aligned events: {len(qmk_states)}")
    print(f"hold-tap-dependent classifications: {len(rows)}")
    print_counts(rows)
    print_examples(rows, args.examples)

    if args.out is not None:
        fields = [
            "t",
            "wallTime",
            "dependency",
            "domain",
            "target",
            "actual",
            "typed_kind",
            "resolved_source",
            "resolution",
            "classification",
            "clean_prefix",
            "mechanism",
            "holder_key",
            "holder_start_wall_ms",
            "holder_end_wall_ms",
            "holder_duration_ms",
            "holder_partner_delay_ms",
            "holder_layer_on_delay_ms",
            "holder_layer_activated",
            "wordIndex",
            "charIndex",
            "inputBefore",
            "inputAfter",
            "targetWord",
        ]
        with args.out.open("w", newline="") as f:
            writer = csv.DictWriter(f, fields)
            writer.writeheader()
            writer.writerows(rows)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
