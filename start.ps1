# Start the demo: API (port 8765) and app (port 5199), each in its own window, then open the browser.
# Usage (PowerShell, from the repository folder):   .\start.ps1
# If scripts are blocked:   powershell -ExecutionPolicy Bypass -File .\start.ps1

$root = Split-Path -Parent $MyInvocation.MyCommand.Path

function Test-Port($port) {
    try { return [bool](Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction Stop) } catch { return $false }
}

if (Test-Port 8765) { Write-Host "API already running on port 8765" }
else {
    Start-Process powershell -ArgumentList "-NoExit", "-Command",
        "`$host.UI.RawUI.WindowTitle = 'Demo API (8765)'; cd '$root\backend'; uv run uvicorn app.main:app --port 8765"
    Write-Host "Starting API in a new window..."
}

if (Test-Port 5199) { Write-Host "App already running on port 5199" }
else {
    Start-Process powershell -ArgumentList "-NoExit", "-Command",
        "`$host.UI.RawUI.WindowTitle = 'Demo app (5199)'; cd '$root\frontend'; npx vite --port 5199 --strictPort"
    Write-Host "Starting app in a new window..."
}

Write-Host "Waiting for the API to answer..."
for ($i = 0; $i -lt 60; $i++) {
    try { Invoke-RestMethod -Uri "http://localhost:8765/api/health" -TimeoutSec 2 | Out-Null; $ok = $true; break } catch { Start-Sleep -Seconds 1 }
}
if ($ok) { Write-Host "API is up." } else { Write-Host "API did not answer within 60 seconds; check the 'Demo API' window." }

for ($i = 0; $i -lt 30; $i++) {
    if (Test-Port 5199) { break }; Start-Sleep -Seconds 1
}
Start-Process "http://localhost:5199/leads"
Write-Host "Opened http://localhost:5199/leads  (close the two windows, or run .\stop.ps1, to stop)"
