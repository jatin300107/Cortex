$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$frontendDir = Join-Path $root "frontend"

Set-Location $frontendDir
Write-Host "Starting frontend dev server in this terminal..."
Write-Host "Open http://localhost:5173"
npm run dev -- --host 0.0.0.0 --port 5173
