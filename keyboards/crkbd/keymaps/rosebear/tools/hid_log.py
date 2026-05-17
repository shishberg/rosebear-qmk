#!/usr/bin/env python3
"""Capture Rosebear QMK raw key events over QMK Raw HID."""

from __future__ import annotations

import argparse
import csv
import signal
import sys
import time
from pathlib import Path

try:
    import hid
except ImportError:
    print("Missing dependency: install hidapi bindings with `python3 -m pip install hid`.", file=sys.stderr)
    raise SystemExit(2)


MAGIC = 0x52
VERSION = 1
TYPE_KEY_EVENT = 1
TYPE_MOD_EVENT = 2
TYPE_LAYER_EVENT = 3
TYPE_HOST_ENABLE = 16
TYPE_STATUS = 17
RAW_USAGE_PAGE = 0xFF60
RAW_USAGE_ID = 0x61
PACKET_SIZE = 32


def le16(data: bytes, offset: int) -> int:
    return data[offset] | (data[offset + 1] << 8)


def le32(data: bytes, offset: int) -> int:
    return data[offset] | (data[offset + 1] << 8) | (data[offset + 2] << 16) | (data[offset + 3] << 24)


def find_device_path(vid: int | None, pid: int | None) -> bytes:
    candidates = []

    for device in hid.enumerate(vid or 0, pid or 0):
        if device.get("usage_page") == RAW_USAGE_PAGE and device.get("usage") == RAW_USAGE_ID:
            candidates.append(device)

    if not candidates:
        print("No QMK Raw HID device found.", file=sys.stderr)
        print("Flash firmware with RAW_ENABLE=yes, then unplug/replug the keyboard.", file=sys.stderr)
        raise SystemExit(1)

    if len(candidates) > 1:
        print("Multiple QMK Raw HID devices found; pass --vid/--pid or --path:", file=sys.stderr)
        for device in candidates:
            path = device["path"]
            if isinstance(path, bytes):
                path = path.decode(errors="replace")
            print(
                f"  vid=0x{device['vendor_id']:04x} pid=0x{device['product_id']:04x} "
                f"product={device.get('product_string')!r} path={path}",
                file=sys.stderr,
            )
        raise SystemExit(1)

    return candidates[0]["path"]


def write_command(dev: hid.Device, enabled: bool) -> None:
    packet = bytearray(PACKET_SIZE)
    packet[0] = MAGIC
    packet[1] = VERSION
    packet[2] = TYPE_HOST_ENABLE
    packet[3] = 1 if enabled else 0
    dev.write(bytes([0]) + packet)


def decode_key_event(data: bytes) -> dict[str, int | str]:
    return {
        "host_time_ns": time.time_ns(),
        "event_type": "key",
        "seq": le16(data, 4),
        "time_ms": le32(data, 6),
        "event_time": le16(data, 10),
        "keycode": f"0x{le16(data, 12):04x}",
        "row": data[14],
        "col": data[15],
        "pressed": data[3],
        "layer": data[16],
        "mods": f"0x{data[17]:02x}",
        "oneshot_mods": f"0x{data[18]:02x}",
        "weak_mods": "",
        "oneshot_locked_mods": "",
        "all_mods": f"0x{data[19]:02x}",
        "changed": "",
        "active": "",
        "layer_state": f"0x{le32(data, 20):08x}",
        "default_layer_state": f"0x{le32(data, 24):08x}",
    }


def decode_state_event(data: bytes) -> dict[str, int | str]:
    return {
        "host_time_ns": time.time_ns(),
        "event_type": "mod" if data[2] == TYPE_MOD_EVENT else "layer",
        "seq": le16(data, 4),
        "time_ms": le32(data, 6),
        "event_time": le16(data, 10),
        "keycode": "",
        "row": "",
        "col": "",
        "pressed": "",
        "layer": "",
        "mods": f"0x{data[13]:02x}",
        "oneshot_mods": f"0x{data[15]:02x}",
        "weak_mods": f"0x{data[14]:02x}",
        "oneshot_locked_mods": f"0x{data[16]:02x}",
        "all_mods": f"0x{data[17]:02x}",
        "changed": f"0x{data[12]:02x}" if data[2] == TYPE_MOD_EVENT else str(data[12]),
        "active": data[3],
        "layer_state": f"0x{le32(data, 20):08x}",
        "default_layer_state": f"0x{le32(data, 24):08x}",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vid", type=lambda x: int(x, 0), help="USB vendor id, e.g. 0x4653")
    parser.add_argument("--pid", type=lambda x: int(x, 0), help="USB product id")
    parser.add_argument("--path", help="hidapi device path")
    parser.add_argument("--out", type=Path, default=Path("rosebear-hid-log.csv"))
    args = parser.parse_args()

    if args.path:
        dev = hid.Device(path=args.path.encode())
    else:
        dev = hid.Device(path=find_device_path(args.vid, args.pid))

    stopping = False

    def stop(_signum, _frame) -> None:
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    fields = [
        "host_time_ns",
        "event_type",
        "seq",
        "time_ms",
        "event_time",
        "keycode",
        "row",
        "col",
        "pressed",
        "layer",
        "mods",
        "oneshot_mods",
        "weak_mods",
        "oneshot_locked_mods",
        "all_mods",
        "changed",
        "active",
        "layer_state",
        "default_layer_state",
    ]

    with args.out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()

        write_command(dev, True)
        print(f"Logging to {args.out}. Press Ctrl-C to stop.", file=sys.stderr)

        try:
            while not stopping:
                data = bytes(dev.read(PACKET_SIZE, timeout=250))
                if not data:
                    continue
                if len(data) < PACKET_SIZE or data[0] != MAGIC or data[1] != VERSION:
                    continue
                if data[2] == TYPE_KEY_EVENT:
                    row = decode_key_event(data)
                    writer.writerow(row)
                    f.flush()
                elif data[2] in {TYPE_MOD_EVENT, TYPE_LAYER_EVENT}:
                    row = decode_state_event(data)
                    writer.writerow(row)
                    f.flush()
                elif data[2] == TYPE_STATUS:
                    print(
                        f"keyboard logging {'enabled' if data[3] else 'disabled'} "
                        f"seq={le16(data, 4)} time_ms={le32(data, 6)}",
                        file=sys.stderr,
                    )
        finally:
            write_command(dev, False)
            dev.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
