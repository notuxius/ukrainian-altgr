param([Parameter(Mandatory)][string]$BuildCommit)

$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
$installer = Get-Item -LiteralPath (Join-Path $repo 'dist\Ukrainian-AltGr-x64.exe')
$version = $installer.VersionInfo.ProductVersion.Trim()
# Keep a fixed published baseline so a build of the latest release still tests a true upgrade.
$baselineVersion = '1.0.2'
if ([version]$version -le [version]$baselineVersion) {
    throw "Installer $version must be newer than the upgrade baseline $baselineVersion"
}
$layoutKey = 'HKLM:\SYSTEM\CurrentControlSet\Control\Keyboard Layouts\a7720422'
$appKey = 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\UkrainianAltGr_is1'
$installedDlls = @{
    amd64 = Join-Path $env:windir 'System32\ualtgr.dll'
    wow64 = Join-Path $env:windir 'SysWOW64\ualtgr.dll'
}

function Invoke-Setup([string]$Executable, [string]$Phase, [switch]$Install) {
    $log = Join-Path $env:RUNNER_TEMP "ualtgr-$Phase.log"
    $arguments = @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', ('/LOG="{0}"' -f $log))
    if ($Install) { $arguments += '/RESTARTEXITCODE=3010' }
    $process = Start-Process -FilePath $Executable -ArgumentList $arguments -WindowStyle Hidden -PassThru -Wait
    if ($process.ExitCode -ne 0) {
        if (Test-Path -LiteralPath $log) { Get-Content -LiteralPath $log }
        throw "$Phase failed ($($process.ExitCode))"
    }
}

function Get-InstalledLayout([string]$ExpectedVersion) {
    $layout = Get-ItemProperty -LiteralPath $layoutKey
    if ($layout.'Layout File' -ne 'ualtgr.dll' -or $layout.'Layout Text' -ne 'Ukrainian AltGr' -or $layout.'Layout Id' -ne '0772') {
        throw 'Incorrect keyboard layout registration'
    }
    $app = Get-ItemProperty -LiteralPath $appKey
    if ($app.DisplayVersion -ne $ExpectedVersion -or !$app.InstallLocation -or !$app.UninstallString -or
        !(Test-Path -LiteralPath ($app.UninstallString.Trim('"')) -PathType Leaf)) {
        throw "Incorrect Installed apps registration for version $ExpectedVersion"
    }
    return $app
}

function Test-BuiltPayload($App) {
    foreach ($architecture in $installedDlls.Keys) {
        $built = Get-FileHash -LiteralPath (Join-Path $repo "build\$architecture\ualtgr.dll")
        $installed = Get-FileHash -LiteralPath $installedDlls[$architecture]
        if ($built.Hash -ne $installed.Hash) { throw "Packaged DLL differs for $architecture" }
    }

    $readme = Join-Path $App.InstallLocation 'README.md'
    @'
from pathlib import Path
from subprocess import check_output
import sys

installed, repo, commit = sys.argv[1:]
actual = Path(installed).read_bytes()
expected = check_output(["git", "-C", repo, "show", f"{commit}:README.md"])
if actual.replace(b"\r\n", b"\n") != expected.replace(b"\r\n", b"\n"):
    raise SystemExit(f"Installed README differs from {commit}:README.md")
'@ | python -B - $readme $repo $BuildCommit
    if ($LASTEXITCODE -ne 0) { throw 'Installed README verification failed' }
}

function Test-InstalledInput([string]$Phase) {
    Write-Host "Checking AltGr typing and F24 after $Phase"
    python -B (Join-Path $PSScriptRoot 'smoke-test-input.py')
    if ($LASTEXITCODE -ne 0) { throw "Windows input verification failed after $Phase" }
}

function Remove-TestInstall($App, [string]$Phase) {
    Invoke-Setup ($App.UninstallString.Trim('"')) $Phase
    $paths = @($layoutKey, $appKey, $App.InstallLocation) + @($installedDlls.Values)
    $deadline = [DateTime]::UtcNow.AddSeconds(10)
    do {
        $remaining = @($paths | Where-Object { Test-Path -LiteralPath $_ })
        if (!$remaining) {
            Write-Host 'Uninstall removed the layout registration, both DLLs, and the application directory'
            return
        }
        Start-Sleep -Milliseconds 250
    } while ([DateTime]::UtcNow -lt $deadline)
    throw "Uninstall left: $($remaining -join ', ')"
}

foreach ($path in @($layoutKey, $appKey) + @($installedDlls.Values)) {
    if (Test-Path -LiteralPath $path) { throw "Expected a clean smoke-test VM, found $path" }
}

Invoke-Setup $installer.FullName 'clean-install' -Install
$clean = Get-InstalledLayout $version
Test-BuiltPayload $clean
Test-InstalledInput 'the clean install'
Write-Host "Clean $version install passed the smoke checks"
Remove-TestInstall $clean 'clean-uninstall'

$previous = Join-Path $env:RUNNER_TEMP "Ukrainian-AltGr-v$baselineVersion.exe"
Invoke-WebRequest "https://github.com/notuxius/ukrainian-altgr/releases/download/v$baselineVersion/Ukrainian-AltGr-x64.exe" -OutFile $previous
if ((Get-FileHash -LiteralPath $previous).Hash -ne '7E63EDE30F804A1F8C5A38FA74140BA022EBF67AC250D520277A26E04FCE3045') {
    throw "Unexpected v$baselineVersion installer checksum"
}
Invoke-Setup $previous 'baseline-install' -Install
$baseline = Get-InstalledLayout $baselineVersion
Invoke-Setup $installer.FullName 'upgrade' -Install
$upgraded = Get-InstalledLayout $version
if ($upgraded.InstallLocation -ne $baseline.InstallLocation -or $upgraded.UninstallString -ne $baseline.UninstallString) {
    throw 'Upgrade did not reuse the previous install'
}
Test-BuiltPayload $upgraded
Test-InstalledInput 'the upgrade'
Write-Host "Upgrade from $baselineVersion to $version passed the smoke checks"
Remove-TestInstall $upgraded 'upgrade-uninstall'
