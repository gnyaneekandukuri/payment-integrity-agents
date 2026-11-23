# Reset the demo to its starting state, then start it again.
# Rebuilds the database from the seed scripts and restores the pre-reviewed cases from saved runs (no network).
# After a reset: 9 leads, Maya's Riverside lead untested, Sam's queue has 8 items, Samuel Adeyemi and
# Joseph Kim are awaiting records (upload PDFs are in demo_uploads\).
# Usage:   .\reset.ps1

$root = Split-Path -Parent $MyInvocation.MyCommand.Path

# The API must be stopped: the reset replaces the database file.
$api = Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue
foreach ($c in $api) { Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue; Write-Host "Stopped the API" }
Start-Sleep -Seconds 2

Push-Location "$root\backend"
uv run python -m tools.demo_reset
Pop-Location

& "$root\start.ps1"
