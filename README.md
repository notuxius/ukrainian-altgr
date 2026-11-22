# Ukrainian AltGr

A native Ukrainian keyboard layout for x64 Windows 10 and 11, with the key positions and modifier behavior of the Ukrainian SVK layout by svk.pp.ua (2010). Right Alt is AltGr. The ordinary Ukrainian letters stay in their familiar positions.

## Install

1. Download and run `Ukrainian-AltGr-x64.exe` from [Releases](https://github.com/notuxius/ukrainian-altgr/releases/latest). Approve the Windows administrator prompt.
2. Open **Settings → Time & language**. Under **Language & region** (Windows 10: **Language**), open **Ukrainian → Language options → Add a keyboard** and choose **Ukrainian AltGr**. Add the Ukrainian language first if needed. Sign out and back in if the layout list was already open and hasn't refreshed.
3. Choose **Ukrainian AltGr** with **Win+Space**.

To remove it, select another layout, remove Ukrainian AltGr in the same language options, then uninstall **Ukrainian AltGr keyboard layout** from Installed apps. Windows may request a restart if the layout is in use.

## Typing

Key names below refer to their positions on a US keyboard.

| Key | Base | Shift | AltGr | Shift+AltGr |
| --- | --- | --- | --- | --- |
| Key below Esc | ’ | ' | ё | Ё |
| Backslash | ґ | Ґ | backslash | vertical bar |
| U | г | Г | ґ | Ґ |
| 2 | 2 | " | @ | ₴ |
| 4 | 4 | ; | $ | € |
| Minus | - | _ | — | – |
| Comma | б | Б | « | „ |
| Period | ю | Ю | » | “ |
| Slash | . | , | … | / |

AltGr+Space inserts a nonbreaking space. The numeric keypad decimal key types a comma when Num Lock is on.

## Build

Use Microsoft Keyboard Layout Creator 1.4 and Inno Setup 6 on Windows. Put `ISCC.exe` on PATH, then run `.\build.ps1`. For a custom tool location, pass `-Toolkit <MSKLC directory>` or `-InnoCompiler <path to ISCC.exe>`. The script builds native x64 and WOW64 layout DLLs from the UTF-8 keymap and packages them in `dist\Ukrainian-AltGr-x64.exe`.

After building, run `python -O verify.py` with 64-bit Python for the x64 DLL or 32-bit Python for the WOW64 DLL. Both are checked against the expected SVK typing behavior and this project's shortcut labels. Pass the path to a trusted SVK DLL of matching architecture as an optional argument to compare its typing tables directly.

[Microsoft Keyboard Layout Creator](https://www.microsoft.com/en-us/download/details.aspx?id=102134) · [Inno Setup](https://jrsoftware.org/isinfo.php)
