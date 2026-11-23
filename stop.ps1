# Stop whatever is listening on the demo ports (API 8765, app 5199).
# Usage:   .\stop.ps1

foreach ($port in 8765, 5199) {
    $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if (-not $conns) { Write-Host "Nothing running on port $port"; continue }
    foreach ($c in $conns) {
        try {
            Stop-Process -Id $c.OwningProcess -Force -ErrorAction Stop
            Write-Host "Stopped process $($c.OwningProcess) on port $port"
        } catch { Write-Host "Could not stop process $($c.OwningProcess) on port $port" }
    }
}
