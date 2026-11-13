param(
    [string]$Toolkit = "${env:ProgramFiles(x86)}\Microsoft Keyboard Layout Creator 1.4",
    [string]$InnoCompiler = 'ISCC.exe'
)
$ErrorActionPreference = 'Stop'
$compiler = (Get-Item -LiteralPath (Join-Path $Toolkit 'bin\i386\kbdutool.exe')).FullName
$inno = (Get-Command $InnoCompiler -ErrorAction Stop).Source
$source = Get-Content -Encoding UTF8 -Raw -LiteralPath (Join-Path $PSScriptRoot 'ualtgr.klc')
foreach ($target in @{amd64 = '-m'; wow64 = '-o'}.GetEnumerator()) {
    $folder = Join-Path $PSScriptRoot "build\$($target.Key)"
    New-Item -ItemType Directory -Force -Path $folder | Out-Null
    Push-Location -LiteralPath $folder
    try {
        $source | Set-Content -Encoding Unicode -LiteralPath 'ualtgr.klc'
        if (Test-Path -LiteralPath 'ualtgr.dll') { Remove-Item -LiteralPath 'ualtgr.dll' }
        & $compiler -u $target.Value ualtgr.klc
        if ($LASTEXITCODE -ne 0 -or !(Test-Path -LiteralPath 'ualtgr.dll')) {
            throw "Keyboard compilation failed for $($target.Key)"
        }
    } finally {
        Pop-Location
    }
}
& $inno (Join-Path $PSScriptRoot 'setup.iss')
if ($LASTEXITCODE -ne 0) { throw 'Installer compilation failed' }
