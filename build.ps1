param(
    [string]$Toolkit = "${env:ProgramFiles(x86)}\Microsoft Keyboard Layout Creator 1.4",
    [string]$InnoCompiler = 'ISCC.exe'
)
$ErrorActionPreference = 'Stop'
$buildDir = Join-Path $PSScriptRoot 'build'
$distDir = Join-Path $PSScriptRoot 'dist'
$stageDir = Join-Path $distDir '.staging'
$installer = Join-Path $distDir 'Ukrainian-AltGr-x64.exe'
$stagedInstaller = Join-Path $stageDir 'Ukrainian-AltGr-x64.exe'

New-Item -ItemType Directory -Force -Path $buildDir | Out-Null
$buildLock = [IO.File]::Open((Join-Path $buildDir 'build.lock'), 'OpenOrCreate', 'ReadWrite', 'None')
try {
    if (Test-Path -LiteralPath $installer -PathType Leaf) {
        Remove-Item -LiteralPath $installer
    }
    if (Test-Path -LiteralPath $stagedInstaller -PathType Leaf) {
        Remove-Item -LiteralPath $stagedInstaller
    }

    $compiler = (Get-Item -LiteralPath (Join-Path $Toolkit 'bin\i386\kbdutool.exe')).FullName
    $inno = (Get-Command $InnoCompiler -CommandType Application).Source
    $source = Get-Content -Encoding UTF8 -Raw -LiteralPath (Join-Path $PSScriptRoot 'ualtgr.klc')
    foreach ($target in @{amd64 = '-m'; wow64 = '-o'}.GetEnumerator()) {
        $folder = Join-Path $buildDir $target.Key
        New-Item -ItemType Directory -Force -Path $folder | Out-Null
        Push-Location -LiteralPath $folder
        try {
            $source | Set-Content -Encoding Unicode -LiteralPath 'ualtgr.klc'
            if (Test-Path -LiteralPath 'ualtgr.dll') { Remove-Item -LiteralPath 'ualtgr.dll' }
            & $compiler -u $target.Value ualtgr.klc
            if ($LASTEXITCODE -ne 0 -or !(Test-Path -LiteralPath 'ualtgr.dll' -PathType Leaf)) {
                throw "Keyboard compilation failed for $($target.Key)"
            }
        } finally {
            Pop-Location
        }
    }

    New-Item -ItemType Directory -Force -Path $stageDir | Out-Null
    & $inno "/O$stageDir" (Join-Path $PSScriptRoot 'setup.iss')
    if ($LASTEXITCODE -ne 0 -or !(Test-Path -LiteralPath $stagedInstaller -PathType Leaf)) {
        throw 'Installer compilation failed'
    }
    [IO.File]::Move($stagedInstaller, $installer)
} finally {
    if (Test-Path -LiteralPath $stagedInstaller -PathType Leaf) {
        Remove-Item -LiteralPath $stagedInstaller -ErrorAction SilentlyContinue
    }
    $buildLock.Dispose()
}
