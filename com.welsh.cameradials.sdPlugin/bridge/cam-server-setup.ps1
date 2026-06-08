# One-time elevated setup for the optional bridge listener: firewall allow + logon auto-start task.
# Run from an elevated PowerShell:  powershell -ExecutionPolicy Bypass -File .\cam-server-setup.ps1
$ErrorActionPreference = 'Stop'
$script = Join-Path $PSScriptRoot 'cam-server.ps1'
$cfg    = Get-Content (Join-Path (Split-Path $PSScriptRoot -Parent) 'config.json') -Raw | ConvertFrom-Json
$port   = if ($cfg.bridgePort)    { [int]$cfg.bridgePort } else { 8765 }
$lan    = if ($cfg.bridgeLanCidr) { $cfg.bridgeLanCidr }   else { '192.168.1.0/24' }

# 1) Firewall: allow inbound TCP <port> from the LAN so Home Assistant can reach the listener
Get-NetFirewallRule -DisplayName 'StreamDeck Cam Bridge' -ErrorAction SilentlyContinue | Remove-NetFirewallRule
New-NetFirewallRule -DisplayName 'StreamDeck Cam Bridge' -Direction Inbound -Action Allow `
    -Protocol TCP -LocalPort $port -Profile Any -RemoteAddress $lan | Out-Null
Write-Host "Firewall rule added (TCP $port from $lan)"

# 2) Scheduled task: start the listener hidden at logon
$taskName = 'StreamDeck Cam Bridge'
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
$action  = New-ScheduledTaskAction -Execute 'powershell.exe' `
    -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$script`""
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit 0
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings `
    -RunLevel Limited -Force | Out-Null
Write-Host 'Scheduled task registered (runs cam-server.ps1 at logon)'
Write-Host 'DONE'
