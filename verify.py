"""Check a compiled layout against the expected key mappings and shortcut labels."""
import argparse
import ctypes as c
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
TYPING_TABLES = ("scan_codes", "extended_e0", "extended_e1", "virtual_keys")
# MSKLC uses 64-bit table pointers in both the x64 and WOW64 DLLs.
KBD_POINTER = c.c_uint64


class CharacterTable(c.Structure):
    _fields_ = [("rows", KBD_POINTER), ("columns", c.c_ubyte), ("stride", c.c_ubyte)]


class ExtendedScan(c.Structure):
    _fields_ = [("scan", c.c_ubyte), ("virtual_key", c.c_ushort)]


class KeyName(c.Structure):
    _fields_ = [("scan", c.c_ubyte), ("name", KBD_POINTER)]


class Layout(c.Structure):
    _fields_ = [
        ("modifiers", KBD_POINTER),
        ("characters", KBD_POINTER),
        ("dead_keys", KBD_POINTER),
        ("key_names", KBD_POINTER),
        ("extended_names", KBD_POINTER),
        ("dead_names", KBD_POINTER),
        ("scan_codes", KBD_POINTER),
        ("scan_count", c.c_ubyte),
        ("e0", KBD_POINTER),
        ("e1", KBD_POINTER),
        ("flags", c.c_uint32),
    ]


def keymap(path):
    dll = c.WinDLL(str(path.resolve()))
    dll.KbdLayerDescriptor.restype = c.POINTER(Layout)
    layout = dll.KbdLayerDescriptor().contents
    if not layout.flags & 1:
        raise ValueError(f"{path} must support AltGr")
    offset = layout.modifiers + c.sizeof(KBD_POINTER)
    highest_mask = c.c_ushort.from_address(offset).value
    modifiers = c.string_at(offset + 2, highest_mask + 1)
    keys = {}
    for table in c.cast(layout.characters, c.POINTER(CharacterTable)):
        if not table.rows:
            break
        row = table.rows
        while vk := c.c_ubyte.from_address(row).value:
            caps = c.c_ubyte.from_address(row + 1).value
            chars = (c.c_ushort * table.columns).from_address(row + 2)
            outputs = [chars[index] if index < len(chars) else 0xf000 for index in modifiers]
            keys[f"{vk:02x}"] = [caps, *outputs]
            row += table.stride
    return {
        "scan_codes": c.cast(layout.scan_codes, c.POINTER(c.c_ushort))[:layout.scan_count],
        "extended_e0": scan_table(layout.e0, ExtendedScan, "virtual_key"),
        "extended_e1": scan_table(layout.e1, ExtendedScan, "virtual_key"),
        "virtual_keys": keys,
        "key_names": key_names(layout.key_names),
        "extended_names": key_names(layout.extended_names),
    }


def scan_table(address, entry_type, field):
    result = {}
    if address:
        for entry in c.cast(address, c.POINTER(entry_type)):
            if not entry.scan:
                break
            result[f"{entry.scan:02x}"] = getattr(entry, field)
    return result


def key_names(address):
    return {code: c.wstring_at(name) for code, name in scan_table(address, KeyName, "name").items()}


def compare(actual, expected, tables):
    for name in tables:
        if actual[name] == expected[name]:
            continue
        if isinstance(expected[name], dict):
            for code in sorted(actual[name].keys() | expected[name].keys()):
                found, wanted = actual[name].get(code), expected[name].get(code)
                if found != wanted:
                    raise ValueError(f"{name} differs at 0x{code}, expected {wanted!r}, got {found!r}")
        raise ValueError(f"{name} differs")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path, nargs="?", help="Also compare typing with a trusted SVK DLL")
    target = "amd64" if c.sizeof(c.c_void_p) == 8 else "wow64"
    parser.add_argument("--layout", type=Path, default=ROOT / "build" / target / "ualtgr.dll")
    args = parser.parse_args()
    try:
        actual = keymap(args.layout)
        expected = json.loads((ROOT / "expected-layout.json").read_text(encoding="utf-8"))
        compare(actual, expected, (*TYPING_TABLES, "key_names", "extended_names"))
        if args.reference:
            compare(actual, keymap(args.reference), TYPING_TABLES)
    except (OSError, AttributeError, ValueError) as error:
        parser.exit(1, f"Verification failed: {error}\n")

    scans, keys = len(actual["scan_codes"]), len(actual["virtual_keys"])
    print(f"Verified {scans} scan codes, {keys} virtual keys, extended scans, and shortcut labels.")


if __name__ == "__main__":
    main()
