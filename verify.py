"""Compare the compiled x64 layout with an installed SVK DLL, without activating either."""
import argparse
import ctypes as c
from pathlib import Path


class CharacterTable(c.Structure):
    _fields_ = [("rows", c.c_void_p), ("columns", c.c_ubyte), ("stride", c.c_ubyte)]


class Layout(c.Structure):
    _fields_ = [
        ("modifiers", c.c_void_p),
        ("characters", c.POINTER(CharacterTable)),
        ("dead_keys", c.c_void_p),
        ("key_names", c.c_void_p),
        ("extended_names", c.c_void_p),
        ("dead_names", c.c_void_p),
        ("scan_codes", c.POINTER(c.c_ushort)),
        ("scan_count", c.c_ubyte),
        ("e0", c.c_void_p),
        ("e1", c.c_void_p),
        ("flags", c.c_uint32),
    ]


def keymap(path):
    dll = c.WinDLL(str(path.resolve()))
    dll.KbdLayerDescriptor.restype = c.POINTER(Layout)
    layout = dll.KbdLayerDescriptor().contents
    assert layout.flags & 1, "Layout must support AltGr"
    offset = layout.modifiers + c.sizeof(c.c_void_p)
    highest_mask = c.c_ushort.from_address(offset).value
    modifiers = c.string_at(offset + 2, highest_mask + 1)
    keys = {}
    for table in layout.characters:
        if not table.rows:
            break
        row = table.rows
        while vk := c.c_ubyte.from_address(row).value:
            caps = c.c_ubyte.from_address(row + 1).value
            chars = (c.c_ushort * table.columns).from_address(row + 2)
            outputs = tuple(chars[index] if index < len(chars) else 0xf000 for index in modifiers)
            keys[vk] = (caps, outputs)
            row += table.stride
    return layout.scan_codes[:layout.scan_count], keys


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path, help="Path to the original x64 uk-svk.dll")
    args = parser.parse_args()
    original_scans, original_keys = keymap(args.reference)
    scans, keys = keymap(Path(__file__).parent / "build/amd64/ualtgr.dll")
    assert scans == original_scans, "Scan code mappings differ"
    assert keys.keys() == original_keys.keys(), "Virtual key sets differ"
    for vk, output in original_keys.items():
        assert keys[vk] == output, f"Modifier or Caps Lock behavior differs for VK {vk:#04x}"
    print(f"Matched {len(scans)} scan codes and {len(keys)} virtual keys across all modifier states.")
