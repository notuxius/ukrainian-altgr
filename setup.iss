#define Version "1.0.3"
#define LayoutKey "SYSTEM\CurrentControlSet\Control\Keyboard Layouts"
#define LayoutID "a7720422"
#define LayoutFile "ualtgr.dll"

[Setup]
AppId=UkrainianAltGr
AppName=Ukrainian AltGr
AppVersion={#Version}
VersionInfoVersion={#Version}.0
AppPublisher=notuxius
DefaultDirName={autopf}\Ukrainian AltGr
DisableDirPage=yes
DisableProgramGroupPage=yes
ArchitecturesAllowed=x64os
ArchitecturesInstallIn64BitMode=x64os
PrivilegesRequired=admin
OutputDir=dist
OutputBaseFilename=Ukrainian-AltGr-x64
WizardStyle=modern
UninstallDisplayName=Ukrainian AltGr keyboard layout

[Files]
Source: "build\amd64\ualtgr.dll"; DestDir: "{sys}"; Flags: replacesameversion restartreplace uninsrestartdelete
Source: "build\wow64\ualtgr.dll"; DestDir: "{syswow64}"; Flags: replacesameversion restartreplace uninsrestartdelete
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

[Registry]
Root: HKLM64; Subkey: "{#LayoutKey}\{#LayoutID}"; ValueType: string; ValueName: "Layout File"; ValueData: "{#LayoutFile}"; Flags: uninsdeletekey
Root: HKLM64; Subkey: "{#LayoutKey}\{#LayoutID}"; ValueType: string; ValueName: "Layout Text"; ValueData: "Ukrainian AltGr"
Root: HKLM64; Subkey: "{#LayoutKey}\{#LayoutID}"; ValueType: string; ValueName: "Layout Id"; ValueData: "0772"

[Code]
function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  Keys: TArrayOfString;
  I: Integer;
  Value, Key: String;
begin
  if not RegGetSubkeyNames(HKLM64, '{#LayoutKey}', Keys) then
  begin
    Result := 'Could not read the Windows keyboard layout registry.';
    Exit;
  end;
  for I := 0 to GetArrayLength(Keys) - 1 do
  begin
    Key := '{#LayoutKey}\' + Keys[I];
    if CompareText(Keys[I], '{#LayoutID}') = 0 then
    begin
      if not RegQueryStringValue(HKLM64, Key, 'Layout File', Value) or
         (CompareText(Value, '{#LayoutFile}') <> 0) then
        Result := 'Another keyboard layout is registered with this layout key.';
    end
    else if RegQueryStringValue(HKLM64, Key, 'Layout Id', Value) and
            (CompareText(Value, '0772') = 0) then
      Result := 'Another keyboard layout uses layout ID 0772.'
    else if RegQueryStringValue(HKLM64, Key, 'Layout File', Value) and
            (CompareText(Value, '{#LayoutFile}') = 0) then
      Result := 'Another keyboard layout uses ualtgr.dll.';
    if Result <> '' then Exit;
  end;
end;
