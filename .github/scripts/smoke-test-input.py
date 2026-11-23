import ctypes as c
from ctypes import wintypes as w
import os
import time


user32 = c.WinDLL("user32", use_last_error=True)


def api(name, result, *arguments):
    function = getattr(user32, name)
    function.restype = result
    function.argtypes = arguments
    return function


create_window = api(
    "CreateWindowExW", w.HWND, w.DWORD, w.LPCWSTR, w.LPCWSTR, w.DWORD,
    c.c_int, c.c_int, c.c_int, c.c_int, w.HWND, w.HMENU, w.HINSTANCE, w.LPVOID,
)
destroy_window = api("DestroyWindow", w.BOOL, w.HWND)
set_foreground = api("SetForegroundWindow", w.BOOL, w.HWND)
foreground_window = api("GetForegroundWindow", w.HWND)
window_process = api("GetWindowThreadProcessId", w.DWORD, w.HWND, c.POINTER(w.DWORD))
set_focus = api("SetFocus", w.HWND, w.HWND)
get_focus = api("GetFocus", w.HWND)
set_text = api("SetWindowTextW", w.BOOL, w.HWND, w.LPCWSTR)
get_text = api("GetWindowTextW", c.c_int, w.HWND, w.LPWSTR, c.c_int)
peek_message = api("PeekMessageW", w.BOOL, c.POINTER(w.MSG), w.HWND, w.UINT, w.UINT, w.UINT)
translate_message = api("TranslateMessage", w.BOOL, c.POINTER(w.MSG))
dispatch_message = api("DispatchMessageW", c.c_ssize_t, c.POINTER(w.MSG))
current_layout = api("GetKeyboardLayout", w.HKL, w.DWORD)
load_layout = api("LoadKeyboardLayoutW", w.HKL, w.LPCWSTR, w.UINT)
activate_layout = api("ActivateKeyboardLayout", w.HKL, w.HKL, w.UINT)
unload_layout = api("UnloadKeyboardLayout", w.BOOL, w.HKL)
layout_name = api("GetKeyboardLayoutNameW", w.BOOL, w.LPWSTR)
key_name = api("GetKeyNameTextW", c.c_int, w.LONG, w.LPWSTR, c.c_int)
scan_for_vk = api("MapVirtualKeyExW", w.UINT, w.UINT, w.UINT, w.HKL)


class KeyboardInput(c.Structure):
    _fields_ = [
        ("vk", w.WORD), ("scan", w.WORD), ("flags", w.DWORD),
        ("time", w.DWORD), ("extra_info", c.c_size_t),
    ]


class MouseInput(c.Structure):
    _fields_ = [
        ("x", w.LONG), ("y", w.LONG), ("data", w.DWORD),
        ("flags", w.DWORD), ("time", w.DWORD), ("extra_info", c.c_size_t),
    ]


class InputPayload(c.Union):
    # The mouse member determines the size of the Win32 INPUT union.
    _fields_ = [("keyboard", KeyboardInput), ("mouse", MouseInput)]


class Input(c.Structure):
    _fields_ = [("kind", w.DWORD), ("payload", InputPayload)]


send_input = api("SendInput", w.UINT, w.UINT, c.POINTER(Input), c.c_int)


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def has_focus(edit):
    process = w.DWORD()
    window_process(foreground_window(), c.byref(process))
    return process.value == os.getpid() and get_focus() == edit


def pump_messages():
    message = w.MSG()
    while peek_message(c.byref(message), None, 0, 0, 1):
        translate_message(c.byref(message))
        dispatch_message(c.byref(message))


def keyboard_event(scan, released=False):
    flags = 0x8  # KEYEVENTF_SCANCODE
    if scan > 0xff:
        flags |= 0x1  # KEYEVENTF_EXTENDEDKEY
    if released:
        flags |= 0x2  # KEYEVENTF_KEYUP
    return Input(1, InputPayload(keyboard=KeyboardInput(0, scan & 0xff, flags, 0, 0)))


def check_typing(edit, chord, scan, modifiers, expected):
    require(set_text(edit, ""), "Could not clear the Unicode edit control")
    pump_messages()
    require(has_focus(edit), "The input test lost keyboard focus")
    keys = (*modifiers, scan)
    events = [keyboard_event(key) for key in keys]
    events.extend(keyboard_event(key, released=True) for key in reversed(keys))
    inputs = (Input * len(events))(*events)
    require(send_input(len(inputs), inputs, c.sizeof(Input)) == len(inputs), f"SendInput failed for {chord}")

    text = c.create_unicode_buffer(16)
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        pump_messages()
        get_text(edit, text, len(text))
        if text.value == expected:
            print(f"{chord} typed U+{ord(expected):04X}")
            return
        time.sleep(0.02)
    raise RuntimeError(f"{chord} typed {text.value!a}, expected {expected!a}")


def main():
    # A native Unicode edit control receives the same keyboard messages as a Windows app.
    edit = create_window(0x8, "EDIT", "", 0x10CF0080, 100, 100, 380, 120, None, None, None, None)
    require(edit, f"Could not create the Unicode edit control: {c.get_last_error()}")
    previous = current_layout(0)
    layout = None
    try:
        deadline = time.monotonic() + 6
        while not has_focus(edit) and time.monotonic() < deadline:
            set_foreground(edit)
            set_focus(edit)
            pump_messages()
            time.sleep(0.05)
        require(has_focus(edit), "The input test could not acquire keyboard focus")

        layout = load_layout("a7720422", 1)  # KLF_ACTIVATE
        require(layout and layout != previous, "Windows could not load the installed Ukrainian AltGr layout")
        pump_messages()
        name = c.create_unicode_buffer(9)
        require(layout_name(name) and name.value.lower() == "a7720422",
                f"Unexpected active keyboard layout {name.value!r}")

        scan = scan_for_vk(0x87, 0, layout)  # VK_F24, MAPVK_VK_TO_VSC
        label = c.create_unicode_buffer(64)
        require(scan == 0x76 and key_name(scan << 16, label, len(label)) and label.value == "F24",
                f"Expected F24 at scan 0x76, got scan {scan:#04x} and label {label.value!r}")
        print("Windows reports the F24 shortcut label for scan 0x76")

        right_alt = 0xE038
        shift = 0x2A
        for chord, scan, modifiers, expected in [
            ("U", 0x16, (), "\u0433"),
            ("AltGr+U", 0x16, (right_alt,), "\u0491"),
            ("AltGr+2", 0x03, (right_alt,), "@"),
            ("Shift+AltGr+2", 0x03, (shift, right_alt), "\u20B4"),
            ("AltGr+Space", 0x39, (right_alt,), "\u00A0"),
            ("AltGr+Minus", 0x0C, (right_alt,), "\u2014"),
        ]:
            check_typing(edit, chord, scan, modifiers, expected)
    finally:
        if layout and layout != previous:
            activate_layout(previous, 0)
            pump_messages()
            unload_layout(layout)
        destroy_window(edit)


if __name__ == "__main__":
    main()
