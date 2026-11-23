# Ukrainian AltGr

A native Ukrainian keyboard layout for x64 Windows 10 and 11, with the key positions and modifier behavior of the Ukrainian SVK layout by svk.pp.ua (2010). Right Alt is AltGr. The ordinary Ukrainian letters stay in their familiar positions.

## Install

1. Download and run `Ukrainian-AltGr-x64.exe` from [Releases](https://github.com/notuxius/ukrainian-altgr/releases/latest). Approve the Windows administrator prompt.
2. Open **Settings** and follow the path for your Windows version. If **Ukrainian** is missing, select **Add a language** on the **Language** or **Language & region** page and install it first.

   - **Windows 10** — **Time & Language → Language → Ukrainian → Options**
   - **Windows 11** — **Time & language → Language & region → Ukrainian → More options (…) → Language options**

3. Select **Add a keyboard → Ukrainian AltGr**. Sign out and back in if the keyboard list was already open and hasn't refreshed.
4. Press **Win+Space** until **Ukrainian AltGr** is selected in the input switcher.

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
