# PowerShell packaging script for FeishuVideoBatch
# Usage (PowerShell):
#   cd $PSScriptRoot
#   ./package.ps1

$ErrorActionPreference = 'Stop'

Write-Host "[1/6] Ensure venv and dependencies (optional)" -ForegroundColor Cyan
if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
  if (-not (Get-Command pip -ErrorAction SilentlyContinue)) {
    throw 'pip is required on PATH.'
  }
  pip install pyinstaller | Out-Host
}

Write-Host "[2/6] Prepare hooks directory" -ForegroundColor Cyan
$hooksDir = Join-Path $PSScriptRoot 'hooks'
if (-not (Test-Path $hooksDir)) { New-Item -ItemType Directory -Path $hooksDir | Out-Null }
$hookFile = Join-Path $hooksDir 'hook-workflow.py'
$hookContent = @("from PyInstaller.utils.hooks import collect_submodules", "hiddenimports = collect_submodules('workflow')", "datas = []") -join "`r`n"
Set-Content -Path $hookFile -Value $hookContent -Encoding ascii

Write-Host "[3/6] Clean previous build artifacts" -ForegroundColor Cyan
Remove-Item -Recurse -Force (Join-Path $PSScriptRoot 'build') -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force (Join-Path $PSScriptRoot 'dist') -ErrorAction SilentlyContinue
Remove-Item -Force        (Join-Path $PSScriptRoot 'FeishuVideoBatch.spec') -ErrorAction SilentlyContinue
Remove-Item -Force        (Join-Path $PSScriptRoot 'FeishuVideoBatch_win64.zip') -ErrorAction SilentlyContinue
Remove-Item -Force        (Join-Path $PSScriptRoot 'VideoBatch_console_win64.zip') -ErrorAction SilentlyContinue
Remove-Item -Force        (Join-Path $PSScriptRoot 'VideoBatch_console.spec') -ErrorAction SilentlyContinue

Write-Host "[4/6] Run PyInstaller (GUI build)" -ForegroundColor Cyan
# Optional ffmpeg include
$ffmpeg = Join-Path $PSScriptRoot 'bin\ffmpeg.exe'
$ffmpegArgs = @()
if (Test-Path $ffmpeg) {
  Write-Host "  - bundling ffmpeg.exe" -ForegroundColor DarkGreen
  $ffmpegArgs = @('--add-binary', ".\bin\ffmpeg.exe;bin")
}
Push-Location $PSScriptRoot
pyinstaller -w -F `
  video_generator_gui.py `
  --name FeishuVideoBatch `
  --paths .. `
  --additional-hooks-dir hooks `
  --add-data "..\workflow;workflow" `
  --add-data "..\pyJianYingDraft\assets;pyJianYingDraft\assets" `
  --add-data "config.json;." `
  --add-data "..\resource;resource" `
  @ffmpegArgs | Out-Host
Pop-Location

Write-Host "[5/6] Run PyInstaller (Console build)" -ForegroundColor Cyan
Push-Location $PSScriptRoot
pyinstaller -c -F `
  video_generator_gui.py `
  --name VideoBatch_console `
  --paths .. `
  --additional-hooks-dir hooks `
  --add-data "..\workflow;workflow" `
  --add-data "..\pyJianYingDraft\assets;pyJianYingDraft\assets" `
  --add-data "config.json;." `
  --add-data "..\resource;resource" `
  @ffmpegArgs | Out-Host
Pop-Location

Write-Host "[6/6] Create zips (EXE only)" -ForegroundColor Cyan
$guiExe = Join-Path $PSScriptRoot 'dist\FeishuVideoBatch.exe'
if (Test-Path $guiExe) {
  if (Test-Path (Join-Path $PSScriptRoot 'FeishuVideoBatch_win64.zip')) { Remove-Item (Join-Path $PSScriptRoot 'FeishuVideoBatch_win64.zip') -Force }
  Compress-Archive -Path $guiExe -DestinationPath (Join-Path $PSScriptRoot 'FeishuVideoBatch_win64.zip') -Force
}
$consoleExe = Join-Path $PSScriptRoot 'dist\VideoBatch_console.exe'
if (Test-Path $consoleExe) {
  if (Test-Path (Join-Path $PSScriptRoot 'VideoBatch_console_win64.zip')) { Remove-Item (Join-Path $PSScriptRoot 'VideoBatch_console_win64.zip') -Force }
  Compress-Archive -Path $consoleExe -DestinationPath (Join-Path $PSScriptRoot 'VideoBatch_console_win64.zip') -Force
}

Write-Host "Done" -ForegroundColor Green
Write-Host "  EXE: " (Join-Path $PSScriptRoot 'dist\FeishuVideoBatch.exe')
Write-Host "  ZIP: " (Join-Path $PSScriptRoot 'FeishuVideoBatch_win64.zip')
Write-Host "  EXE (console): " (Join-Path $PSScriptRoot 'dist\VideoBatch_console.exe')
Write-Host "  ZIP (console): " (Join-Path $PSScriptRoot 'VideoBatch_console_win64.zip')

