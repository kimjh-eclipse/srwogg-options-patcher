param(
    [string]$PackPath = (Join-Path $PSScriptRoot 'data\OGG_options.bin'),
    [string]$OutputDirectory = (Join-Path $PSScriptRoot 'dist')
)
$ErrorActionPreference = 'Stop'
$metadata = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'patch-data.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not (Test-Path -LiteralPath $PackPath -PathType Leaf)) {
    throw 'Release ZIP의 patcher/OGG_options.bin을 준비한 뒤 -PackPath로 지정해 주세요.'
}
$packHash = (Get-FileHash -LiteralPath $PackPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($packHash -ne $metadata.sha256) { throw 'OGG_options.bin SHA-256이 이 소스 버전과 다릅니다.' }
$compiler = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
if (-not (Test-Path -LiteralPath $compiler)) {
    $compiler = Join-Path $env:WINDIR 'Microsoft.NET\Framework\v4.0.30319\csc.exe'
}
if (-not (Test-Path -LiteralPath $compiler)) { throw '.NET Framework C# compiler를 찾을 수 없습니다.' }
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$outputPath = (Resolve-Path -LiteralPath $OutputDirectory).Path
$generatedPath = Join-Path $outputPath 'OggOptionsPatcher.generated.cs'
$source = [IO.File]::ReadAllText((Join-Path $PSScriptRoot 'src\OggOptionsPatcher.cs'))
[IO.File]::WriteAllText($generatedPath, $source.Replace('__PACK_SHA__', $packHash), [Text.UTF8Encoding]::new($true))
$executable = Join-Path $outputPath 'OGG_Options_Patcher.exe'
& $compiler /nologo /target:winexe /optimize+ /codepage:65001 "/out:$executable" /reference:System.dll /reference:System.Core.dll /reference:System.Drawing.dll /reference:System.Windows.Forms.dll $generatedPath
if ($LASTEXITCODE -ne 0) { throw 'C# compilation failed.' }
$destinationPack = Join-Path $outputPath 'OGG_options.bin'
if ([IO.Path]::GetFullPath($PackPath) -ne $destinationPack) { Copy-Item -LiteralPath $PackPath -Destination $destinationPack -Force }
$reportPath = Join-Path $outputPath 'selftest.json'
$process = Start-Process -FilePath $executable -ArgumentList @('--selftest', '--report', ('"' + $reportPath + '"')) -WindowStyle Hidden -PassThru -Wait
if ($process.ExitCode -ne 0) { throw '패처 자체 검증에 실패했습니다.' }
$report = Get-Content -LiteralPath $reportPath -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not $report.passed -or $report.profiles -ne $metadata.profiles -or $report.checkboxes -ne $metadata.options) { throw '옵션 조합 검증에 실패했습니다.' }
Write-Output "Build and $($metadata.profiles)-profile self-test passed: $executable"
